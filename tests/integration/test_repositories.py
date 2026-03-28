import pytest
from datetime import datetime, timedelta
from api.adapters.outbound.postgres.repositories import (
    SourceRepository, ItemRepository, TagRepository,
    KeywordRepository, ScoredItemRepository,
)
from api.domain.models import Source, SourceType, SourcePriority, FeedItem, Tag, Keyword, ScoredItem


@pytest.mark.asyncio
async def test_source_repo_save_and_list(db_session):
    repo = SourceRepository(db_session)
    saved = await repo.save(Source(url="https://heise.de/rss", name="Heise", type=SourceType.RSS))
    assert saved.id is not None
    assert len(await repo.get_all()) == 1


@pytest.mark.asyncio
async def test_source_repo_active_filter(db_session):
    repo = SourceRepository(db_session)
    await repo.save(Source(url="https://active.com/rss", name="Active", type=SourceType.RSS))
    inactive = await repo.save(Source(url="https://inactive.com/rss", name="Inactive", type=SourceType.RSS))
    inactive.active = False
    await repo.update(inactive)
    active = await repo.get_all(active_only=True)
    assert len(active) == 1 and active[0].url == "https://active.com/rss"


@pytest.mark.asyncio
async def test_source_repo_get_by_id_not_found(db_session):
    assert await SourceRepository(db_session).get_by_id(9999) is None


@pytest.mark.asyncio
async def test_source_repo_delete(db_session):
    repo = SourceRepository(db_session)
    saved = await repo.save(Source(url="https://delete.me/rss", name="Del", type=SourceType.RSS))
    await repo.delete(saved.id)
    assert await repo.get_by_id(saved.id) is None


@pytest.mark.asyncio
async def test_item_repo_exists_by_hash(db_session):
    src = await SourceRepository(db_session).save(Source(url="https://x.com/rss", name="X", type=SourceType.RSS))
    repo = ItemRepository(db_session)
    await repo.save(FeedItem(source_id=src.id, url="https://x.com/a", url_hash="h123", title="Art"))
    assert await repo.exists_by_hash("h123") is True
    assert await repo.exists_by_hash("nonexistent") is False


@pytest.mark.asyncio
async def test_item_repo_ordered_by_date(db_session):
    src = await SourceRepository(db_session).save(Source(url="https://x.com/rss", name="X", type=SourceType.RSS))
    repo = ItemRepository(db_session)
    now = datetime.utcnow()
    await repo.save(FeedItem(source_id=src.id, url="https://x.com/old", url_hash="h_old", title="Alt", pub_date=now - timedelta(hours=2)))
    await repo.save(FeedItem(source_id=src.id, url="https://x.com/new", url_hash="h_new", title="Neu", pub_date=now))
    items = await repo.get_all()
    assert items[0].title == "Neu"


@pytest.mark.asyncio
async def test_item_repo_mark_read(db_session):
    src = await SourceRepository(db_session).save(Source(url="https://x.com/rss", name="X", type=SourceType.RSS))
    repo = ItemRepository(db_session)
    item = await repo.save(FeedItem(source_id=src.id, url="https://x.com/1", url_hash="h1", title="Art"))
    await repo.mark_read(item.id)
    assert len(await repo.get_all(read=True)) == 1


@pytest.mark.asyncio
async def test_tag_repo_crud(db_session):
    repo = TagRepository(db_session)
    tag = await repo.save(Tag(name="Tech", color="#00ff00"))
    assert tag.id is not None
    await repo.delete(tag.id)
    assert len(await repo.get_all()) == 0


@pytest.mark.asyncio
async def test_scored_item_repo(db_session):
    src = await SourceRepository(db_session).save(Source(url="https://x.com/rss", name="X", type=SourceType.RSS))
    item = await ItemRepository(db_session).save(FeedItem(source_id=src.id, url="https://x.com/a", url_hash="ha", title="Art"))
    repo = ScoredItemRepository(db_session)
    saved = await repo.save(ScoredItem(item_id=item.id, score=75, reason="Relevant", keywords_matched=["OpenAI"]))
    assert saved.id is not None
    found = await repo.get_by_item_id(item.id)
    assert found.score == 75 and "OpenAI" in found.keywords_matched
