import json
from unittest.mock import MagicMock, patch

from src.db import init_db
from src.ingest_twitter_oembed import fetch_tweet_by_url


def _mock_oembed_response(text: str):
    html = f'<blockquote class="twitter-tweet"><p dir="ltr" lang="en">{text}</p>&mdash; Name (@handle) <a href="https://twitter.com/handle/status/123">Date</a></blockquote>'
    return json.dumps({"html": html}).encode("utf-8")


def test_fetch_and_insert(tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file))

    tweet_text = "Bitcoin to 100k soon 🚀"
    mock_bytes = _mock_oembed_response(tweet_text)

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_bytes
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = fetch_tweet_by_url("https://twitter.com/EvanLuthra/status/1234567890123456789", db_path=str(db_file))

    assert result["inserted"] is True
    assert result["tweet_id"] == "1234567890123456789"
    assert result["handle"] == "EvanLuthra"
    assert result["text"] == tweet_text
    assert result["error"] is None


def test_dedup_skips_second_insert(tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file))

    tweet_text = "DeFi is the future"
    mock_bytes = _mock_oembed_response(tweet_text)

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_bytes
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    url = "https://x.com/EvanLuthra/status/9876543210987654321"

    with patch("urllib.request.urlopen", return_value=mock_resp):
        first = fetch_tweet_by_url(url, db_path=str(db_file))
    assert first["inserted"] is True

    with patch("urllib.request.urlopen", return_value=mock_resp):
        second = fetch_tweet_by_url(url, db_path=str(db_file))
    assert second["inserted"] is False
    assert second["error"] is None


def test_fallback_on_oembed_failure(tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file))

    with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
        result = fetch_tweet_by_url("https://twitter.com/EvanLuthra/status/111", db_path=str(db_file))

    assert result["inserted"] is False
    assert result["error"] is not None
    assert "oEmbed fetch failed" in result["error"]
