import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.adapters.outbound.rss.detector import detect_source_type
from api.domain.models import SourceType


def _mock_response(content_type: str, body: str = ""):
    resp = MagicMock()
    resp.headers = {"content-type": content_type}
    resp.text = body
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client(resp):
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.get = AsyncMock(return_value=resp)
    return client


@pytest.mark.asyncio
async def test_detects_rss_by_content_type():
    with patch("api.adapters.outbound.rss.detector.httpx.AsyncClient",
               return_value=_patch_client(_mock_response("application/rss+xml"))):
        assert await detect_source_type("https://heise.de/rss") == SourceType.RSS


@pytest.mark.asyncio
async def test_detects_atom_by_content_type():
    with patch("api.adapters.outbound.rss.detector.httpx.AsyncClient",
               return_value=_patch_client(_mock_response("application/atom+xml"))):
        assert await detect_source_type("https://example.com/atom") == SourceType.RSS


@pytest.mark.asyncio
async def test_detects_rss_via_html_link():
    html = '<html><head><link rel="alternate" type="application/rss+xml" href="/feed"></head></html>'
    with patch("api.adapters.outbound.rss.detector.httpx.AsyncClient",
               return_value=_patch_client(_mock_response("text/html", html))):
        assert await detect_source_type("https://blog.example.com") == SourceType.RSS


@pytest.mark.asyncio
async def test_detects_web_for_plain_html():
    html = "<html><body><p>Ein Blog ohne Feed-Link.</p></body></html>"
    with patch("api.adapters.outbound.rss.detector.httpx.AsyncClient",
               return_value=_patch_client(_mock_response("text/html", html))):
        assert await detect_source_type("https://blog.example.com") == SourceType.WEB


@pytest.mark.asyncio
async def test_falls_back_to_web_on_http_error():
    import httpx
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.get = AsyncMock(side_effect=httpx.ConnectError("timeout"))
    with patch("api.adapters.outbound.rss.detector.httpx.AsyncClient", return_value=client):
        assert await detect_source_type("https://unreachable.example.com") == SourceType.WEB
