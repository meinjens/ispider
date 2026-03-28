import pytest
from unittest.mock import AsyncMock, MagicMock, patch

SAMPLE_RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
  <item>
    <title>Artikel mit HTML</title>
    <link>https://example.com/1</link>
    <description><![CDATA[<p>Text <b>fett</b>.</p>]]></description>
    <pubDate>Mon, 01 Jan 2024 10:00:00 +0000</pubDate>
  </item>
  <item>
    <title>Artikel ohne Summary</title>
    <link>https://example.com/2</link>
  </item>
</channel></rss>"""


def _mock_client(text):
    resp = MagicMock()
    resp.text = text
    resp.raise_for_status = MagicMock()
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.get = AsyncMock(return_value=resp)
    return client


@pytest.mark.asyncio
async def test_rss_fetcher_parses_items():
    from api.adapters.outbound.rss.fetcher import RssFetcher
    with patch("api.adapters.outbound.rss.fetcher.httpx.AsyncClient", return_value=_mock_client(SAMPLE_RSS)):
        result = await RssFetcher().fetch("https://example.com/feed.rss")
    assert len(result) == 2
    assert result[0].url == "https://example.com/1"


@pytest.mark.asyncio
async def test_rss_fetcher_strips_html():
    from api.adapters.outbound.rss.fetcher import RssFetcher
    with patch("api.adapters.outbound.rss.fetcher.httpx.AsyncClient", return_value=_mock_client(SAMPLE_RSS)):
        result = await RssFetcher().fetch("https://example.com/feed.rss")
    assert "<p>" not in (result[0].summary or "")
    assert "Text" in (result[0].summary or "")


@pytest.mark.asyncio
async def test_rss_fetcher_handles_missing_summary():
    from api.adapters.outbound.rss.fetcher import RssFetcher
    with patch("api.adapters.outbound.rss.fetcher.httpx.AsyncClient", return_value=_mock_client(SAMPLE_RSS)):
        result = await RssFetcher().fetch("https://example.com/feed.rss")
    assert result[1].summary is None
