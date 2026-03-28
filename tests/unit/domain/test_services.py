import pytest
from unittest.mock import AsyncMock
from api.domain.models import Source, SourceType, SourcePriority, Tag, Keyword, FeedItem
from api.domain.services import SourceService, FeedService, TagService, KeywordService, AIQueryService


@pytest.mark.asyncio
async def test_source_service_add():
    repo = AsyncMock()
    repo.save.return_value = Source(id=1, url="https://heise.de/rss", name="Heise", type=SourceType.RSS)
    result = await SourceService(repo).add_source("https://heise.de/rss", "Heise", SourcePriority.HIGH, [])
    assert result.id == 1


@pytest.mark.asyncio
async def test_source_service_update_not_found():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match="not found"):
        await SourceService(repo).update_source(99, active=False, priority=None, tag_ids=None)


@pytest.mark.asyncio
async def test_source_service_import_opml():
    opml = """<?xml version="1.0"?><opml version="1.0"><body>
      <outline text="Heise" title="Heise" type="rss" xmlUrl="https://heise.de/rss"/>
      <outline text="Kein Feed" title="Kein Feed"/>
    </body></opml>"""
    repo = AsyncMock()
    repo.save.side_effect = lambda s: Source(id=1, url=s.url, name=s.name, type=s.type)
    result = await SourceService(repo).import_opml(opml)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_feed_service_mark_read():
    repo = AsyncMock()
    await FeedService(repo).mark_read(42)
    repo.mark_read.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_tag_service_create():
    repo = AsyncMock()
    repo.save.return_value = Tag(id=1, name="Tech", color="#00B37E")
    result = await TagService(repo).create_tag("Tech", "#00B37E")
    assert result.name == "Tech"


@pytest.mark.asyncio
async def test_keyword_service_create():
    repo = AsyncMock()
    repo.save.return_value = Keyword(id=1, term="OpenAI", threshold=70, notify=True)
    result = await KeywordService(repo).create_keyword("OpenAI", 70, True)
    assert result.term == "OpenAI"


@pytest.mark.asyncio
async def test_ai_query_service():
    ai = AsyncMock()
    ai.query.return_value = "Zusammenfassung."
    item_repo = AsyncMock()
    item_repo.get_all.return_value = []
    result = await AIQueryService(ai, item_repo).query("Top-Themen?")
    assert result == "Zusammenfassung."


@pytest.mark.asyncio
async def test_source_service_auto_detects_type():
    """Auto-Detect wird aufgerufen und setzt SourceType korrekt."""
    from api.domain.models import SourceType
    detector = AsyncMock(return_value=SourceType.WEB)
    repo = AsyncMock()
    repo.save.side_effect = lambda s: Source(id=1, url=s.url, name=s.name, type=s.type)

    svc = SourceService(repo, type_detector=detector)
    result = await svc.add_source("https://blog.example.com", "Blog", SourcePriority.HIGH, [])

    detector.assert_called_once_with("https://blog.example.com")
    assert result.type == SourceType.WEB


@pytest.mark.asyncio
async def test_source_service_falls_back_on_detector_error():
    """Wenn der Detector einen Fehler wirft, wird RSS als Fallback genutzt."""
    from api.domain.models import SourceType
    detector = AsyncMock(side_effect=Exception("Timeout"))
    repo = AsyncMock()
    repo.save.side_effect = lambda s: Source(id=1, url=s.url, name=s.name, type=s.type)

    svc = SourceService(repo, type_detector=detector)
    result = await svc.add_source("https://broken.example.com", "Broken", SourcePriority.LOW, [])

    assert result.type == SourceType.RSS
