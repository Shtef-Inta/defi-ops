#!/usr/bin/env python3
"""Conservative transcript fetcher with two-pass strategy:
1. API-only for all videos. No-transcript videos are deferred.
2. yt-dlp fallback ONLY for deferred videos at the very end.
3. If yt-dlp hits 429/IP block, video is skipped and logged for manual transcription.
Normal videos never wait for problematic ones.
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, IpBlocked

try:
    from youtube_transcript_api.proxies import GenericProxyConfig
    _PROXY_SUPPORT = True
except ImportError:
    _PROXY_SUPPORT = False

# Proxy configuration: prefer Webshare rotating residential, fallback to Tor
_WEBSHARE_BASE = os.getenv("WEBSHARE_PROXY_URL", "").strip()
_TOR_PROXY = os.getenv("HTTPS_PROXY", os.getenv("https_proxy", "")).strip()
_yta_instance = None

# Parse Webshare base credentials for rotation
_WEBSHARE_USERS = []
if _WEBSHARE_BASE:
    parsed = urllib.parse.urlparse(_WEBSHARE_BASE)
    _WEBSHARE_PASS = parsed.password or ""
    _WEBSHARE_HOST = parsed.hostname or "p.webshare.io"
    _WEBSHARE_PORT = parsed.port or 80
    base_user = parsed.username or ""
    if base_user and "-" not in base_user:
        _WEBSHARE_USERS = [f"{base_user}-{i}" for i in range(1, 11)]
    else:
        _WEBSHARE_USERS = [base_user]


def _get_proxy_url():
    """Return active proxy URL. For Webshare: pick random rotating username."""
    if _WEBSHARE_USERS:
        user = random.choice(_WEBSHARE_USERS)
        return f"http://{user}:{_WEBSHARE_PASS}@{_WEBSHARE_HOST}:{_WEBSHARE_PORT}"
    return _TOR_PROXY


def _get_yta():
    global _yta_instance
    if _yta_instance is not None:
        return _yta_instance
    proxy_url = _get_proxy_url()
    if _PROXY_SUPPORT and proxy_url:
        proxy_config = GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
        _yta_instance = YouTubeTranscriptApi(proxy_config=proxy_config)
    else:
        _yta_instance = YouTubeTranscriptApi()
    return _yta_instance


# Rotate User-Agent to avoid fingerprinting
_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
]


def _get_ua():
    return random.choice(_USER_AGENTS)


def _rotate_proxy():
    """Rotate proxy circuit. For Webshare: force new connection to get fresh IP.
    For Tor: send HUP signal to build new circuits."""
    global _yta_instance
    if _WEBSHARE_USERS:
        _yta_instance = None
    elif _TOR_PROXY:
        try:
            subprocess.run(["killall", "-HUP", "tor"], capture_output=True, timeout=5)
        except Exception:
            pass


def fetch_with_api(video_id, max_retries=5):
    """Try youtube-transcript-api with proxy rotation on IP block or proxy failure."""
    for attempt in range(max_retries):
        try:
            transcript = _get_yta().fetch(video_id, languages=["ru", "en"])
            return " ".join(snippet.text for snippet in transcript), "api"
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
            return None, "no_transcript"
        except IpBlocked:
            _rotate_proxy()
            wait = 2 ** attempt * 8 + random.uniform(0, 3)
            proxy_type = "Webshare" if _WEBSHARE_USERS else "Tor"
            print(f"  IP blocked, rotating {proxy_type}, waiting {wait:.0f}s...", flush=True)
            time.sleep(wait)
        except (OSError, ConnectionError) as e:
            _rotate_proxy()
            wait = 2 ** attempt * 5 + random.uniform(0, 2)
            err_name = type(e).__name__
            print(f"  Proxy error ({err_name}), rotating, waiting {wait:.0f}s...", flush=True)
            time.sleep(wait)
        except Exception as e:
            return None, f"error:{e}"
    return None, "ip_blocked"


def fetch_with_ytdlp_no_retry(video_id, out_dir):
    """One-shot yt-dlp. If 429/IP block → abort immediately, do not retry."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_path = out_dir / f"_{video_id}"

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--cookies-from-browser", "chrome",
        "--skip-download",
        "--write-auto-sub",
        "--sub-langs", "ru,en",
        "--sub-format", "vtt",
        "--ignore-no-formats-error",
        "--no-warnings",
        "-o", str(out_path),
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        for ext in ["ru.vtt", "en.vtt"]:
            f = Path(f"{out_path}.{ext}")
            if f.exists():
                text = f.read_text(encoding="utf-8")
                lines = []
                for line in text.splitlines():
                    if re.match(r"^\d{2}:\d{2}", line) or line.strip() == "" or line.startswith("WEBVTT"):
                        continue
                    lines.append(line)
                cleaned = "\n".join(lines).strip()
                f.unlink()
                return cleaned, "ytdlp"

        stderr = result.stderr.lower()
        if "429" in stderr or "too many requests" in stderr or "ip blocked" in stderr or "sign in" in stderr:
            return None, "rate_limited"
        return None, "no_transcript"
    except Exception as e:
        return None, f"error:{e}"


def process_channel(video_file, out_dir, delay_min=5.0, delay_max=10.0, resume=True):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(video_file) as f:
        videos = json.load(f)

    channel_name = Path(video_file).stem
    print(f"Processing {channel_name}: {len(videos)} videos")

    progress_file = out_dir / "_progress.json"
    manual_file = out_dir / "_manual_transcribe.json"
    done_ids = set()
    deferred_ids = set()
    manual_ids = set()

    if resume and progress_file.exists():
        try:
            progress = json.loads(progress_file.read_text())
            done_ids = set(progress.get("done", []))
            deferred_ids = set(progress.get("deferred", []))
            manual_ids = set(progress.get("manual", []))
            print(f"  Resuming: {len(done_ids)} done, {len(deferred_ids)} deferred, {len(manual_ids)} manual")
        except Exception:
            pass

    if resume and manual_file.exists():
        try:
            manual_data = json.loads(manual_file.read_text())
            manual_ids = set(manual_data.get("videos", []))
        except Exception:
            pass

    results = {
        "channel": channel_name,
        "total": len(videos),
        "done": list(done_ids),
        "deferred": list(deferred_ids),
        "manual": list(manual_ids),
        "ok": 0,
        "failed": 0,
        "no_transcript": 0,
    }

    todo = [v for v in videos if v["id"] not in done_ids and v["id"] not in manual_ids]
    todo.sort(key=lambda v: v.get("upload_date", ""), reverse=True)
    api_todo = [v for v in todo if v["id"] not in deferred_ids]
    fallback_todo = [v for v in todo if v["id"] in deferred_ids]

    # ── PASS 1: API only ──
    print(f"\n[PASS 1] API-only for {len(api_todo)} videos...")
    for i, v in enumerate(api_todo):
        vid = v["id"]
        title = v["title"]

        _rotate_proxy()

        print(f"[{channel_name}] {i+1}/{len(api_todo)} {vid}...", flush=True)

        text, source = fetch_with_api(vid)

        if text:
            results["ok"] += 1
            out_file = out_dir / f"{vid}.txt"
            out_file.write_text(f"# {title}\n\n{text}", encoding="utf-8")
            print(f"  -> OK ({source}, {len(text)} chars)", flush=True)
        elif source == "no_transcript":
            results["no_transcript"] += 1
            deferred_ids.add(vid)
            print(f"  -> NO TRANSCRIPT (deferred)", flush=True)
        elif source == "ip_blocked":
            print(f"  -> IP BLOCKED — skipping, will retry via next proxy", flush=True)
        else:
            results["failed"] += 1
            print(f"  -> FAILED ({source})", flush=True)

        results["done"].append(vid)
        done_ids.add(vid)
        results["deferred"] = list(deferred_ids)
        progress_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))

        if i < len(api_todo) - 1:
            delay = random.uniform(delay_min, delay_max)
            time.sleep(delay)

    # ── PASS 2: Fallback only for deferred videos ──
    fallback_queue = [v for v in videos if v["id"] in deferred_ids and v["id"] not in done_ids and v["id"] not in manual_ids]
    if fallback_queue:
        print(f"\n[PASS 2] Fallback for {len(fallback_queue)} deferred videos...")
        for i, v in enumerate(fallback_queue):
            vid = v["id"]
            title = v["title"]

            print(f"[{channel_name}] fallback {i+1}/{len(fallback_queue)} {vid}...", flush=True)

            text, source = fetch_with_ytdlp_no_retry(vid, out_dir)

            if text:
                results["ok"] += 1
                out_file = out_dir / f"{vid}.txt"
                out_file.write_text(f"# {title}\n\n{text}", encoding="utf-8")
                deferred_ids.discard(vid)
                print(f"  -> OK (ytdlp, {len(text)} chars)", flush=True)
            elif source == "rate_limited":
                manual_ids.add(vid)
                deferred_ids.discard(vid)
                print(f"  -> RATE LIMITED — sending to manual transcription", flush=True)
            else:
                deferred_ids.discard(vid)
                print(f"  -> NO TRANSCRIPT via fallback", flush=True)

            results["done"].append(vid)
            done_ids.add(vid)
            results["deferred"] = list(deferred_ids)
            results["manual"] = list(manual_ids)
            progress_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))

            manual_file.write_text(json.dumps({
                "channel": channel_name,
                "count": len(manual_ids),
                "videos": sorted(list(manual_ids)),
            }, ensure_ascii=False, indent=2))

            if i < len(fallback_queue) - 1:
                delay = random.uniform(delay_min, delay_max)
                time.sleep(delay)

    print(f"\n{channel_name} done: {results['ok']} OK, {results['failed']} failed, {results['no_transcript']} no transcript, {len(manual_ids)} manual")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--videos", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--delay-min", type=float, default=5.0)
    parser.add_argument("--delay-max", type=float, default=10.0)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    process_channel(args.videos, args.out_dir, args.delay_min, args.delay_max, not args.no_resume)


if __name__ == "__main__":
    main()
