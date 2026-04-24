#!/usr/bin/env python3
"""YouTube transcript orchestrator — fetches transcripts for all enabled channels.

Runs continuously: for each channel, updates video list, then fetches transcripts.
Never stops. Integrated with watchdog. Routes through Webshare proxy.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

WEBSHARE_PROXY = os.getenv("WEBSHARE_PROXY_URL", "")
TOR_PROXY = os.getenv("HTTPS_PROXY", "")
ACTIVE_PROXY = WEBSHARE_PROXY or TOR_PROXY


def load_youtube_channels():
    """Load enabled YouTube channels from sources.yaml and sources_autodiscovered.yaml."""
    channels = []
    for path in ["config/sources.yaml", "config/sources_autodiscovered.yaml"]:
        p = Path(path)
        if not p.exists():
            continue
        data = yaml.safe_load(p.read_text()) or {}
        for group, items in data.get("youtube", {}).items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and item.get("enabled", True):
                    channels.append(item)
                elif isinstance(item, str):
                    channels.append({"handle": item, "name": item, "source_family": "research"})
    seen = set()
    unique = []
    for ch in channels:
        h = ch.get("handle", "").lower().lstrip("@")
        if h and h not in seen:
            seen.add(h)
            unique.append(ch)
    return unique


def get_or_refresh_video_list(channel, max_age_hours=24):
    """Get video list from cache or fetch via yt-dlp if stale/missing."""
    handle = channel["handle"].lstrip("@")
    cache_path = Path(f"state/youtube_video_lists/{handle}.json")
    
    if cache_path.exists():
        age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
        if age_hours < max_age_hours:
            return json.loads(cache_path.read_text())
    
    url = f"https://www.youtube.com/@{handle}/videos"
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--cookies-from-browser", "chrome",
        "--flat-playlist", "-J",
        "--playlist-end", "1000",
        url,
    ]
    env = os.environ.copy()
    if WEBSHARE_PROXY:
        env["WEBSHARE_PROXY_URL"] = WEBSHARE_PROXY
    if ACTIVE_PROXY:
        env["HTTPS_PROXY"] = ACTIVE_PROXY
    elif "HTTPS_PROXY" in env:
        del env["HTTPS_PROXY"]
    
    print(f"[FETCH LIST] @{handle} ...", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
        if result.returncode != 0:
            print(f"  yt-dlp error: {result.stderr[:200]}", flush=True)
            return json.loads(cache_path.read_text()) if cache_path.exists() else []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line.startswith("{"):
                data = json.loads(line)
                entries = data.get("entries", [])
                videos = [{"id": e["id"], "title": e.get("title", "")} for e in entries if e.get("id")]
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(videos, indent=2, ensure_ascii=False))
                print(f"  -> {len(videos)} videos cached", flush=True)
                return videos
    except Exception as e:
        print(f"  Exception: {e}", flush=True)
        return json.loads(cache_path.read_text()) if cache_path.exists() else []
    
    return []


def run_fetcher(channel, delay_min=5, delay_max=10):
    """Run conservative transcript fetcher for a single channel."""
    handle = channel["handle"].lstrip("@")
    video_file = Path(f"state/youtube_video_lists/{handle}.json")
    out_dir = Path(f"state/youtube_transcripts/{handle}")
    
    if not video_file.exists():
        print(f"  No video list for @{handle}, skipping", flush=True)
        return
    
    cmd = [
        sys.executable,
        "scripts/fetch_transcripts_conservative.py",
        "--videos", str(video_file),
        "--out-dir", str(out_dir),
        "--delay-min", str(delay_min),
        "--delay-max", str(delay_max),
    ]
    
    env = os.environ.copy()
    if WEBSHARE_PROXY:
        env["WEBSHARE_PROXY_URL"] = WEBSHARE_PROXY
    if ACTIVE_PROXY:
        env["HTTPS_PROXY"] = ACTIVE_PROXY
    elif "HTTPS_PROXY" in env:
        del env["HTTPS_PROXY"]
    
    print(f"[TRANSCRIPTS] @{handle} starting...", flush=True)
    try:
        subprocess.run(cmd, env=env, timeout=7200)
    except subprocess.TimeoutExpired:
        print(f"  Timeout after 2h for @{handle}", flush=True)
    print(f"[TRANSCRIPTS] @{handle} done", flush=True)


def main():
    channels = load_youtube_channels()
    print(f"[ORCHESTRATOR] Loaded {len(channels)} YouTube channels")
    for ch in channels[:5]:
        print(f"  - {ch['handle']}")
    if len(channels) > 5:
        print(f"  ... and {len(channels)-5} more")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'='*50}\nCYCLE {cycle}\n{'='*50}", flush=True)
        
        for channel in channels:
            handle = channel["handle"].lstrip("@")
            
            videos = get_or_refresh_video_list(channel)
            if not videos:
                print(f"[@{handle}] No videos, skipping", flush=True)
                continue
            
            out_dir = Path(f"state/youtube_transcripts/{handle}")
            done = len([f for f in out_dir.glob("*.txt") if not f.name.startswith("_")])
            total = len(videos)
            
            if done >= total:
                print(f"[@{handle}] {done}/{total} COMPLETE", flush=True)
                continue
            
            remaining = total - done
            print(f"[@{handle}] {done}/{total} done, {remaining} remaining — fetching...", flush=True)
            
            run_fetcher(channel)
            
            time.sleep(10)
        
        print(f"\n[CYCLE {cycle}] All channels checked. Sleeping 30 min...", flush=True)
        time.sleep(1800)


if __name__ == "__main__":
    main()
