import json
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .orm import SourceORM, FeedItemORM, ScoredItemORM, TagORM, KeywordORM, PushSubscriptionORM
from ....domain.models import Source, SourceType, SourcePriority, FeedItem, ScoredItem, Tag, Keyword, PushSubscription
from ....domain.ports.outbound import (
    ISourceRepository, IItemRepository, IScoredItemRepository,
    ITagRepository, IKeywordRepository, IPushSubscriptionRepository,
)


# ── Mappers ──────────────────────────────────────────────────────────────────

def _source_to_domain(orm: SourceORM) -> Source:
    return Source(
        id=orm.id, url=orm.url, name=orm.name,
        type=SourceType(orm.type if isinstance(orm.type, str) else orm.type.value),
        priority=SourcePriority(orm.priority if isinstance(orm.priority, str) else orm.priority.value),
        active=orm.active, error_count=orm.error_count,
        tag_ids=[t.id for t in orm.tags],  # tags müssen eager geladen sein
        created_at=orm.created_at, last_fetched_at=orm.last_fetched_at,
    )


def _item_to_domain(orm: FeedItemORM) -> FeedItem:
    return FeedItem(
        id=orm.id, source_id=orm.source_id, url=orm.url,
        url_hash=orm.url_hash, title=orm.title,
        description=orm.description, raw_content=orm.raw_content,
        pub_date=orm.pub_date, created_at=orm.created_at, read=orm.read,
    )


# ── Repositories ─────────────────────────────────────────────────────────────

class SourceRepository(ISourceRepository):
    def __init__(self, session: AsyncSession):
        self._s = session

    async def save(self, source: Source) -> Source:
        orm = SourceORM(
            url=source.url, name=source.name,
            type=source.type.value, priority=source.priority.value,
        )
        self._s.add(orm)
        await self._s.flush()
        # Eager reload mit Tags
        result = await self._s.execute(
            select(SourceORM).where(SourceORM.id == orm.id).options(selectinload(SourceORM.tags))
        )
        orm = result.scalar_one()
        await self._s.commit()
        return _source_to_domain(orm)

    async def get_all(self, active_only: bool = False) -> list[Source]:
        q = select(SourceORM).options(selectinload(SourceORM.tags))
        if active_only:
            q = q.where(SourceORM.active == True)
        result = await self._s.execute(q)
        return [_source_to_domain(r) for r in result.scalars().all()]

    async def get_by_id(self, source_id: int) -> Optional[Source]:
        result = await self._s.execute(
            select(SourceORM).where(SourceORM.id == source_id).options(selectinload(SourceORM.tags))
        )
        orm = result.scalar_one_or_none()
        return _source_to_domain(orm) if orm else None

    async def update(self, source: Source) -> Source:
        result = await self._s.execute(
            select(SourceORM).where(SourceORM.id == source.id).options(selectinload(SourceORM.tags))
        )
        orm = result.scalar_one()
        orm.active = source.active
        orm.priority = source.priority.value
        orm.name = source.name
        await self._s.commit()
        await self._s.refresh(orm)
        return _source_to_domain(orm)

    async def delete(self, source_id: int) -> None:
        result = await self._s.execute(
            select(SourceORM).where(SourceORM.id == source_id)
        )
        orm = result.scalar_one_or_none()
        if orm:
            await self._s.delete(orm)
            await self._s.commit()


class ItemRepository(IItemRepository):
    def __init__(self, session: AsyncSession):
        self._s = session

    async def save(self, item: FeedItem) -> FeedItem:
        orm = FeedItemORM(
            source_id=item.source_id, url=item.url, url_hash=item.url_hash,
            title=item.title, description=item.description,
            raw_content=item.raw_content, pub_date=item.pub_date,
        )
        self._s.add(orm)
        await self._s.commit()
        await self._s.refresh(orm)
        return _item_to_domain(orm)

    async def exists_by_hash(self, url_hash: str) -> bool:
        result = await self._s.execute(
            select(FeedItemORM.id).where(FeedItemORM.url_hash == url_hash)
        )
        return result.scalar_one_or_none() is not None

    async def get_all(self, source_id=None, tag_id=None, min_score=None, read=None, limit=50, offset=0) -> list[FeedItem]:
        q = select(FeedItemORM).order_by(FeedItemORM.pub_date.desc())
        if source_id is not None:
            q = q.where(FeedItemORM.source_id == source_id)
        if read is not None:
            q = q.where(FeedItemORM.read == read)
        if min_score is not None:
            q = q.join(ScoredItemORM).where(ScoredItemORM.score >= min_score)
        q = q.limit(limit).offset(offset)
        result = await self._s.execute(q)
        return [_item_to_domain(r) for r in result.scalars().all()]

    async def mark_read(self, item_id: int) -> None:
        await self._s.execute(
            update(FeedItemORM).where(FeedItemORM.id == item_id).values(read=True)
        )
        await self._s.commit()


class ScoredItemRepository(IScoredItemRepository):
    def __init__(self, session: AsyncSession):
        self._s = session

    async def save(self, scored: ScoredItem) -> ScoredItem:
        orm = ScoredItemORM(
            item_id=scored.item_id, score=scored.score, reason=scored.reason,
            keywords_matched=json.dumps(scored.keywords_matched),
        )
        self._s.add(orm)
        await self._s.commit()
        await self._s.refresh(orm)
        scored.id = orm.id
        return scored

    async def get_by_item_id(self, item_id: int) -> Optional[ScoredItem]:
        result = await self._s.execute(
            select(ScoredItemORM).where(ScoredItemORM.item_id == item_id)
        )
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return ScoredItem(
            id=orm.id, item_id=orm.item_id, score=orm.score, reason=orm.reason,
            keywords_matched=json.loads(orm.keywords_matched or "[]"),
            notified_at=orm.notified_at, scored_at=orm.scored_at,
        )


class TagRepository(ITagRepository):
    def __init__(self, session: AsyncSession):
        self._s = session

    async def save(self, tag: Tag) -> Tag:
        orm = TagORM(name=tag.name, color=tag.color)
        self._s.add(orm)
        await self._s.commit()
        await self._s.refresh(orm)
        return Tag(id=orm.id, name=orm.name, color=orm.color)

    async def get_all(self) -> list[Tag]:
        result = await self._s.execute(select(TagORM))
        return [Tag(id=r.id, name=r.name, color=r.color) for r in result.scalars().all()]

    async def delete(self, tag_id: int) -> None:
        result = await self._s.execute(select(TagORM).where(TagORM.id == tag_id))
        orm = result.scalar_one_or_none()
        if orm:
            await self._s.delete(orm)
            await self._s.commit()


class KeywordRepository(IKeywordRepository):
    def __init__(self, session: AsyncSession):
        self._s = session

    async def save(self, keyword: Keyword) -> Keyword:
        orm = KeywordORM(term=keyword.term, threshold=keyword.threshold, notify=keyword.notify)
        self._s.add(orm)
        await self._s.commit()
        await self._s.refresh(orm)
        return Keyword(id=orm.id, term=orm.term, threshold=orm.threshold, notify=orm.notify)

    async def get_all(self, active_only: bool = False) -> list[Keyword]:
        q = select(KeywordORM)
        if active_only:
            q = q.where(KeywordORM.active == True)
        result = await self._s.execute(q)
        return [
            Keyword(id=r.id, term=r.term, threshold=r.threshold, notify=r.notify, active=r.active)
            for r in result.scalars().all()
        ]

    async def delete(self, keyword_id: int) -> None:
        result = await self._s.execute(select(KeywordORM).where(KeywordORM.id == keyword_id))
        orm = result.scalar_one_or_none()
        if orm:
            await self._s.delete(orm)
            await self._s.commit()


class PushSubscriptionRepository(IPushSubscriptionRepository):
    def __init__(self, session: AsyncSession):
        self._s = session

    async def save(self, sub: PushSubscription) -> PushSubscription:
        orm = PushSubscriptionORM(endpoint=sub.endpoint, p256dh=sub.p256dh, auth=sub.auth)
        self._s.add(orm)
        await self._s.commit()
        await self._s.refresh(orm)
        return PushSubscription(id=orm.id, endpoint=orm.endpoint, p256dh=orm.p256dh, auth=orm.auth)

    async def get_all(self) -> list[PushSubscription]:
        result = await self._s.execute(select(PushSubscriptionORM))
        return [
            PushSubscription(id=r.id, endpoint=r.endpoint, p256dh=r.p256dh, auth=r.auth)
            for r in result.scalars().all()
        ]
