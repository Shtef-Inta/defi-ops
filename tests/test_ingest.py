import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src import ingest
from src import ingest_rss
from src import ingest_telegram
from src import ingest_twitter
from src import ingest_wallets
from src import ingest_youtube
from src.db import init_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_syndication_html(tweets: list[dict]) -> bytes:
    """Build a minimal syndication HTML page embedding tweets in __NEXT_DATA__."""
    entries = []
    for t in tweets:
        entries.append({"type": "tweet", "content": {"tweet": t}})
    payload = {"props": {"pageProps": {"timeline": {"entries": entries}}}}
    html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        f"{json.dumps(payload)}"
        "</script></html>"
    )
    return html.encode("utf-8")


def _fake_youtube_rss(video_id: str, title: str = "Test Video") -> bytes:
    """Minimal YouTube RSS Atom entry."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mrss/">
  <title>Test Channel</title>
  <entry>
    <id>yt:video:{video_id}</id>
    <yt:videoId>{video_id}</yt:videoId>
    <yt:channelId>UCxxxxxxxxxxxxxxxxxxx</yt:channelId>
    <title>{title}</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v={video_id}"/>
    <author><name>TestChannel</name><uri>https://www.youtube.com/channel/UCxxx</uri></author>
    <published>2025-04-21T12:00:00+00:00</published>
    <media:group>
      <media:title>{title}</media:title>
      <media:description>Description here</media:description>
    </media:group>
  </entry>
</feed>"""
    return xml.encode("utf-8")


def _fake_rss_xml(title: str = "Test Article", link: str = "https://example.com/1") -> bytes:
    """Minimal RSS 2.0 feed."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <pubDate>Mon, 21 Apr 2025 12:00:00 GMT</pubDate>
      <description>Test description</description>
      <guid>{link}</guid>
    </item>
  </channel>
</rss>"""
    return xml.encode("utf-8")


# ---------------------------------------------------------------------------
# Twitter
# ---------------------------------------------------------------------------


def test_parse_twitter_handles_reads_sources_yaml(tmp_path, monkeypatch):
    yaml = """
twitter:
  defi_core:
    - aave
    - uniswap
  researchers:
    - DefiIgnas
  risk_overlay:
    - peckshieldalert
  analytics:
    - tokenterminal
  infra:
    - ethereum
youtube:
  official:
    - handle: aavelabs
"""
    fake_path = tmp_path / "sources.yaml"
    fake_path.write_text(yaml)
    monkeypatch.setattr(
        "src.ingest_twitter.Path",
        lambda *args, **kwargs: fake_path
        if str(args[0]).endswith("sources.yaml")
        else Path(*args, **kwargs),
    )
    handles = ingest_twitter._parse_twitter_handles(fake_path.read_text())
    by_family = {h: f for h, f in handles}
    assert by_family["aave"] == "official"
    assert by_family["uniswap"] == "official"
    assert by_family["DefiIgnas"] == "research"
    assert by_family["peckshieldalert"] == "risk_overlay"
    assert by_family["tokenterminal"] == "aggregator"
    assert by_family["ethereum"] == "official"


def test_fetch_twitter_inserts_and_dedupes(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))
    conn.close()

    monkeypatch.setattr(
        "src.ingest_twitter._parse_twitter_handles",
        lambda _text: [("aave", "official")],
    )

    tweets = [
        {
            "id_str": "111",
            "full_text": "Aave V4 is live on mainnet",
            "created_at": "Mon Apr 21 12:00:00 +0000 2025",
            "user": {"screen_name": "aave"},
        },
        {
            "id_str": "112",
            "full_text": "Emergency pause on L2 due to anomaly",
            "created_at": "Mon Apr 21 13:00:00 +0000 2025",
            "user": {"screen_name": "aave"},
        },
    ]
    fake_html = _fake_syndication_html(tweets)

    monkeypatch.setattr("src.ingest_twitter._fetch_syndication", lambda handle, timeout=15: fake_html)
    monkeypatch.setattr("src.ingest_twitter.time", lambda s: None)

    res1 = ingest.fetch_twitter(db_path=str(db_file))
    assert res1["inserted"] == 2
    assert res1["skipped"] == 0
    assert res1["failed"] == 0

    res2 = ingest.fetch_twitter(db_path=str(db_file))
    assert res2["inserted"] == 0
    assert res2["skipped"] == 2
    assert res2["failed"] == 0

    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM signals ORDER BY source_id").fetchall()
    assert len(rows) == 2
    assert rows[0]["source_id"] == "111"
    assert rows[0]["sentiment"] == "bullish"
    assert rows[1]["source_id"] == "112"
    assert rows[1]["sentiment"] == "bearish"
    conn.close()


def test_fetch_twitter_graceful_empty_timeline(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setattr(
        "src.ingest_twitter._parse_twitter_handles",
        lambda _text: [("aave", "official")],
    )
    monkeypatch.setattr("src.ingest_twitter._fetch_syndication", lambda handle, timeout=15: None)

    res = ingest.fetch_twitter(db_path=str(db_file))
    assert res["failed"] == 1
    assert res["inserted"] == 0


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------


def test_parse_youtube_channels_reads_sources_yaml():
    yaml = """
youtube:
  official:
    - handle: aavelabs
      name: Aave Labs
      url: https://www.youtube.com/@aavelabs
      protocol: aave
      source_family: official
    - handle: uniswap
      name: Uniswap Labs
      protocol: uniswap
      source_family: official
  research:
    - handle: bankless
      name: Bankless
      source_family: research
"""
    channels = ingest_youtube._parse_youtube_channels(yaml)
    assert len(channels) == 3
    assert channels[0]["handle"] == "aavelabs"
    assert channels[0]["protocol"] == "aave"
    assert channels[1]["handle"] == "uniswap"
    assert channels[2]["source_family"] == "research"


def test_parse_youtube_rss_extracts_entries():
    xml = _fake_youtube_rss("abc123", "Launch Day")
    entries = ingest_youtube._parse_youtube_rss(xml)
    assert len(entries) == 1
    assert entries[0]["video_id"] == "abc123"
    assert entries[0]["title"] == "Launch Day"
    assert "youtube.com/watch?v=abc123" in entries[0]["url"]


def test_fetch_youtube_inserts_and_dedupes(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setattr(
        "src.ingest_youtube._parse_youtube_channels",
        lambda _text: [
            {
                "handle": "aavelabs",
                "protocol": "aave",
                "source_family": "official",
            }
        ],
    )
    monkeypatch.setattr(
        "src.ingest_youtube._resolve_channel_id",
        lambda handle, timeout=15: "UCfakechannel",
    )
    monkeypatch.setattr(
        "src.ingest_youtube._fetch_youtube_rss",
        lambda channel_id, timeout=15: _fake_youtube_rss("v1", "Aave V4 Launch"),
    )

    res1 = ingest.fetch_youtube(db_path=str(db_file))
    assert res1["inserted"] == 1
    assert res1["skipped"] == 0
    assert res1["failed"] == 0

    res2 = ingest.fetch_youtube(db_path=str(db_file))
    assert res2["inserted"] == 0
    assert res2["skipped"] == 1
    assert res2["failed"] == 0

    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM signals WHERE source_family = 'official' AND source_id = 'v1'").fetchone()
    assert row is not None
    assert row["protocol"] == "aave"
    assert row["sentiment"] == "bullish"
    conn.close()


def test_fetch_youtube_graceful_missing_channel(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setattr(
        "src.ingest_youtube._parse_youtube_channels",
        lambda _text: [{"handle": "missing", "source_family": "official"}],
    )
    monkeypatch.setattr("src.ingest_youtube._resolve_channel_id", lambda handle, timeout=15: None)

    res = ingest.fetch_youtube(db_path=str(db_file))
    assert res["failed"] == 1
    assert res["inserted"] == 0


# ---------------------------------------------------------------------------
# Unified entry
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# RSS
# ---------------------------------------------------------------------------


def test_parse_rss_sources_reads_sources_yaml():
    yaml = """
rss:
  aggregators:
    - name: The Defiant RSS
      url: https://thedefiant.io/feed
      source_family: aggregator
      enabled: true
  governance:
    - name: Aave Governance
      url: https://governance.aave.com/latest.rss
      source_family: governance
      protocol: aave
      enabled: true
"""
    sources = ingest_rss._parse_rss_sources(yaml)
    assert len(sources) == 2
    assert sources[0]["name"] == "The Defiant RSS"
    assert sources[0]["source_family"] == "aggregator"
    assert sources[1]["protocol"] == "aave"


def test_parse_rss_feed_extracts_items():
    xml = _fake_rss_xml("Aave V4 Launch", "https://example.com/aave-v4")
    entries = ingest_rss._parse_rss_feed(xml)
    assert len(entries) == 1
    assert entries[0]["title"] == "Aave V4 Launch"
    assert entries[0]["url"] == "https://example.com/aave-v4"
    assert entries[0]["guid"] == "https://example.com/aave-v4"


def test_fetch_rss_inserts_and_dedupes(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setattr(
        "src.ingest_rss._parse_rss_sources",
        lambda _text: [
            {"name": "Test Feed", "url": "https://example.com/rss", "source_family": "aggregator", "enabled": "true"}
        ],
    )
    monkeypatch.setattr(
        "src.ingest_rss._fetch_rss",
        lambda url, timeout=15: _fake_rss_xml("New DeFi Protocol", "https://example.com/1"),
    )

    res1 = ingest.fetch_rss(db_path=str(db_file))
    assert res1["inserted"] == 1
    assert res1["skipped"] == 0
    assert res1["failed"] == 0

    res2 = ingest.fetch_rss(db_path=str(db_file))
    assert res2["inserted"] == 0
    assert res2["skipped"] == 1
    assert res2["failed"] == 0


def test_fetch_rss_graceful_empty_feed(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setattr(
        "src.ingest_rss._parse_rss_sources",
        lambda _text: [
            {"name": "Bad Feed", "url": "https://example.com/rss", "source_family": "aggregator", "enabled": "true"}
        ],
    )
    monkeypatch.setattr("src.ingest_rss._fetch_rss", lambda url, timeout=15: None)

    res = ingest.fetch_rss(db_path=str(db_file))
    assert res["failed"] == 1
    assert res["inserted"] == 0


# ---------------------------------------------------------------------------
# Unified entry
# ---------------------------------------------------------------------------


def _fake_etherscan_json(tx_hash: str = "0xabc", timestamp: str = "1713700800") -> bytes:
    payload = {
        "status": "1",
        "result": [
            {
                "hash": tx_hash,
                "timeStamp": timestamp,
                "from": "0xaaa",
                "to": "0xbbb",
                "value": "1000000000000000000",
            }
        ],
    }
    return json.dumps(payload).encode("utf-8")


def test_parse_wallets():
    yaml = """
wallets:
  reference:
    - address: "0xABC"
      name: vitalik.eth
      chain: ethereum
      enabled: true
"""
    wallets = ingest_wallets._parse_wallets(yaml)
    assert len(wallets) == 1
    assert wallets[0]["address"] == "0xABC"
    assert wallets[0]["name"] == "vitalik.eth"
    assert wallets[0]["_group"] == "reference"


def test_fetch_wallets_inserts_and_dedupes(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setattr(
        "src.ingest_wallets._parse_wallets",
        lambda _text: [
            {"address": "0xABC", "name": "Test", "chain": "ethereum", "enabled": "true", "_group": "reference"}
        ],
    )
    fake_txs = [
        {"hash": "0xabc", "timeStamp": "1713700800", "from": "0xaaa", "to": "0xbbb", "value": "1000000000000000000"}
    ]
    monkeypatch.setattr("src.ingest_wallets._fetch_etherscan_txs", lambda *a, **k: fake_txs)

    res1 = ingest.fetch_wallets(db_path=str(db_file))
    assert res1["inserted"] == 1
    assert res1["skipped"] == 0

    res2 = ingest.fetch_wallets(db_path=str(db_file))
    assert res2["inserted"] == 0
    assert res2["skipped"] == 1


def test_fetch_wallets_graceful_empty(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setattr(
        "src.ingest_wallets._parse_wallets",
        lambda _text: [
            {"address": "0xABC", "name": "Test", "chain": "ethereum", "enabled": "true", "_group": "reference"}
        ],
    )
    monkeypatch.setattr("src.ingest_wallets._fetch_etherscan_txs", lambda *a, **k: [])

    res = ingest.fetch_wallets(db_path=str(db_file))
    assert res["failed"] == 1
    assert res["inserted"] == 0


def test_ingest_all_runs_all(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setattr(
        "src.ingest_twitter._parse_twitter_handles",
        lambda _text: [("aave", "official")],
    )
    monkeypatch.setattr("src.ingest_twitter._fetch_syndication", lambda handle, timeout=15: None)
    monkeypatch.setattr("src.ingest_youtube._parse_youtube_channels", lambda _text: [])
    monkeypatch.setattr("src.ingest_rss._parse_rss_sources", lambda _text: [])
    monkeypatch.setattr("src.ingest_wallets._parse_wallets", lambda _text: [])
    monkeypatch.setattr("src.ingest_telegram._parse_telegram_channels", lambda _text: [])

    result = ingest.ingest_all(db_path=str(db_file))
    assert "twitter" in result
    assert "youtube" in result
    assert "rss" in result
    assert "wallets" in result
    assert "telegram" in result


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------


def test_parse_telegram_channels():
    yaml = """
telegram:
  channels:
    - handle: DeFiLlama_News
      source_family: aggregator
      enabled: true
    - handle: aave_official
      source_family: official
      enabled: false
"""
    channels = ingest_telegram._parse_telegram_channels(yaml)
    assert len(channels) == 1
    assert channels[0]["handle"] == "DeFiLlama_News"


def test_fetch_telegram_inserts_and_dedupes(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setenv("TELEGRAM_API_ID", "12345")
    monkeypatch.setenv("TELEGRAM_API_HASH", "deadbeef")

    monkeypatch.setattr(
        "src.ingest_telegram._parse_telegram_channels",
        lambda _text: [
            {"handle": "TestChan", "source_family": "aggregator", "enabled": "true"}
        ],
    )

    class FakeMessage:
        def __init__(self, msg_id, text, date):
            self.id = msg_id
            self.text = text
            self.date = date

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def start(self):
            pass

        def disconnect(self):
            pass

        def get_entity(self, handle):
            return handle

        def iter_messages(self, entity, limit):
            now = datetime.now(timezone.utc)
            return [
                FakeMessage(1, "Hello DeFi", now),
                FakeMessage(2, "Second msg", now),
            ]

    res = ingest.fetch_telegram(
        db_path=str(db_file),
        _client_factory=lambda *a, **k: FakeClient(*a, **k),
    )
    print("RES", res)
    assert res["inserted"] == 2
    assert res["skipped"] == 0

    res2 = ingest.fetch_telegram(
        db_path=str(db_file),
        _client_factory=lambda *a, **k: FakeClient(*a, **k),
    )
    assert res2["inserted"] == 0
    assert res2["skipped"] == 2


def test_fetch_telegram_graceful_no_credentials(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()

    monkeypatch.setattr(
        "src.ingest_telegram._parse_telegram_channels",
        lambda _text: [
            {"handle": "TestChan", "source_family": "aggregator", "enabled": "true"}
        ],
    )
    monkeypatch.setenv("TELEGRAM_API_ID", "")
    monkeypatch.setenv("TELEGRAM_API_HASH", "")

    res = ingest.fetch_telegram(db_path=str(db_file))
    assert res["failed"] == 1
    assert res["inserted"] == 0
