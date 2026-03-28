import json
import pytest
from unittest.mock import AsyncMock
from api.adapters.outbound.anthropic.provider import AnthropicProvider
from api.domain.models import FeedItem


@pytest.fixture
def provider():
    return AnthropicProvider(api_key="test", query_model="claude-sonnet-4-6")


@pytest.mark.asyncio
async def test_score_item_parses_valid_response(provider):
    provider._call = AsyncMock(return_value=json.dumps({"score": 82, "reason": "Wichtig", "tags": ["tech"]}))
    result = await provider.score_item("OpenAI GPT-5", "Details...")
    assert result.score == 82
    assert "tech" in result.tags


@pytest.mark.asyncio
async def test_score_item_handles_invalid_json(provider):
    provider._call = AsyncMock(return_value="kein json")
    result = await provider.score_item("Titel", "Text")
    assert result.score == 0
    assert result.reason == "Parsing-Fehler"


@pytest.mark.asyncio
async def test_scrape_page_returns_items(provider):
    provider._call = AsyncMock(return_value=json.dumps([
        {"title": "Artikel 1", "url": "https://x.com/1", "summary": "Text", "pub_date": None},
    ]))
    result = await provider.scrape_page("<html>", "https://x.com")
    assert len(result) == 1
    assert result[0].title == "Artikel 1"


@pytest.mark.asyncio
async def test_scrape_page_skips_empty_titles(provider):
    provider._call = AsyncMock(return_value=json.dumps([
        {"title": "", "url": "https://x.com/1"},
        {"title": "Gültig", "url": "https://x.com/2"},
    ]))
    result = await provider.scrape_page("<html>", "https://x.com")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_scrape_page_handles_invalid_json(provider):
    provider._call = AsyncMock(return_value="kein json")
    assert await provider.scrape_page("<html>", "https://x.com") == []


@pytest.mark.asyncio
async def test_query_includes_context(provider):
    provider._call = AsyncMock(return_value="Antwort.")
    items = [FeedItem(id=1, source_id=1, url="https://a.com", url_hash="h1", title="Titel A", description="Text A")]
    result = await provider.query("Was ist neu?", items)
    assert result == "Antwort."
    user_arg = provider._call.call_args[0][2]
    assert "Titel A" in user_arg
