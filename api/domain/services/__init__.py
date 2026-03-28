import hashlib
import xml.etree.ElementTree as ET
from typing import Optional

from ..models import Source, SourceType, SourcePriority, FeedItem, Tag, Keyword, PushSubscription
from ..ports.inbound import (
    ISourceCommand, ISourceQuery, IFeedQuery,
    ITagCommand, ITagQuery, IKeywordCommand, IKeywordQuery,
    IPushCommand, IAIQueryCommand,
)
from ..ports.outbound import (
    ISourceRepository, IItemRepository, ITagRepository,
    IKeywordRepository, IPushSubscriptionRepository, IScoredItemRepository,
    IAIProvider,
)


class SourceService(ISourceCommand, ISourceQuery):
    def __init__(self, source_repo: ISourceRepository, type_detector=None):
        self._repo = source_repo
        self._detector = type_detector  # callable: async (url) -> SourceType

    async def add_source(self, url: str, name: str, priority: SourcePriority, tag_ids: list[int]) -> Source:
        source_type = SourceType.RSS
        if self._detector:
            try:
                source_type = await self._detector(url)
            except Exception:
                source_type = SourceType.RSS  # Fallback
        source = Source(url=url, name=name, type=source_type, priority=priority, tag_ids=tag_ids)
        return await self._repo.save(source)

    async def update_source(self, source_id: int, active: Optional[bool], priority: Optional[SourcePriority], tag_ids: Optional[list[int]]) -> Source:
        source = await self._repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source {source_id} not found")
        if active is not None:
            source.active = active
        if priority is not None:
            source.priority = priority
        if tag_ids is not None:
            source.tag_ids = tag_ids
        return await self._repo.update(source)

    async def delete_source(self, source_id: int) -> None:
        await self._repo.delete(source_id)

    async def import_opml(self, opml_content: str) -> list[Source]:
        root = ET.fromstring(opml_content)
        sources = []
        for outline in root.iter("outline"):
            xml_url = outline.get("xmlUrl")
            title = outline.get("title") or outline.get("text") or xml_url
            if xml_url:
                source = Source(url=xml_url, name=title, type=SourceType.RSS)
                saved = await self._repo.save(source)
                sources.append(saved)
        return sources

    async def list_sources(self, active_only: bool = False) -> list[Source]:
        return await self._repo.get_all(active_only=active_only)


class FeedService(IFeedQuery):
    def __init__(self, item_repo: IItemRepository):
        self._repo = item_repo

    async def list_items(self, source_id=None, tag_id=None, min_score=None, read=None, limit=50, offset=0) -> list[FeedItem]:
        return await self._repo.get_all(source_id=source_id, tag_id=tag_id, min_score=min_score, read=read, limit=limit, offset=offset)

    async def mark_read(self, item_id: int) -> None:
        await self._repo.mark_read(item_id)


class TagService(ITagCommand, ITagQuery):
    def __init__(self, tag_repo: ITagRepository):
        self._repo = tag_repo

    async def create_tag(self, name: str, color: str) -> Tag:
        return await self._repo.save(Tag(name=name, color=color))

    async def delete_tag(self, tag_id: int) -> None:
        await self._repo.delete(tag_id)

    async def list_tags(self) -> list[Tag]:
        return await self._repo.get_all()


class KeywordService(IKeywordCommand, IKeywordQuery):
    def __init__(self, keyword_repo: IKeywordRepository):
        self._repo = keyword_repo

    async def create_keyword(self, term: str, threshold: int, notify: bool) -> Keyword:
        return await self._repo.save(Keyword(term=term, threshold=threshold, notify=notify))

    async def delete_keyword(self, keyword_id: int) -> None:
        await self._repo.delete(keyword_id)

    async def list_keywords(self) -> list[Keyword]:
        return await self._repo.get_all()


class PushService(IPushCommand):
    def __init__(self, push_repo: IPushSubscriptionRepository):
        self._repo = push_repo

    async def subscribe(self, endpoint: str, p256dh: str, auth: str) -> PushSubscription:
        return await self._repo.save(PushSubscription(endpoint=endpoint, p256dh=p256dh, auth=auth))


class AIQueryService(IAIQueryCommand):
    def __init__(self, ai_provider: IAIProvider, item_repo: IItemRepository):
        self._ai = ai_provider
        self._items = item_repo

    async def query(self, prompt: str) -> str:
        context = await self._items.get_all(limit=30)
        return await self._ai.query(prompt, context)
