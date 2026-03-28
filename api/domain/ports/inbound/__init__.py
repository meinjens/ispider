from abc import ABC, abstractmethod
from typing import Optional
from ...models import Source, SourceType, SourcePriority, Tag, Keyword, FeedItem, PushSubscription


class ISourceCommand(ABC):
    @abstractmethod
    async def add_source(self, url: str, name: str, priority: SourcePriority, tag_ids: list[int]) -> Source: ...

    @abstractmethod
    async def update_source(self, source_id: int, active: Optional[bool], priority: Optional[SourcePriority], tag_ids: Optional[list[int]]) -> Source: ...

    @abstractmethod
    async def delete_source(self, source_id: int) -> None: ...

    @abstractmethod
    async def import_opml(self, opml_content: str) -> list[Source]: ...


class ISourceQuery(ABC):
    @abstractmethod
    async def list_sources(self, active_only: bool = False) -> list[Source]: ...


class IFeedQuery(ABC):
    @abstractmethod
    async def list_items(
        self,
        source_id: Optional[int],
        tag_id: Optional[int],
        min_score: Optional[int],
        read: Optional[bool],
        limit: int,
        offset: int,
    ) -> list[FeedItem]: ...

    @abstractmethod
    async def mark_read(self, item_id: int) -> None: ...


class ITagCommand(ABC):
    @abstractmethod
    async def create_tag(self, name: str, color: str) -> Tag: ...

    @abstractmethod
    async def delete_tag(self, tag_id: int) -> None: ...


class ITagQuery(ABC):
    @abstractmethod
    async def list_tags(self) -> list[Tag]: ...


class IKeywordCommand(ABC):
    @abstractmethod
    async def create_keyword(self, term: str, threshold: int, notify: bool) -> Keyword: ...

    @abstractmethod
    async def delete_keyword(self, keyword_id: int) -> None: ...


class IKeywordQuery(ABC):
    @abstractmethod
    async def list_keywords(self) -> list[Keyword]: ...


class IPushCommand(ABC):
    @abstractmethod
    async def subscribe(self, endpoint: str, p256dh: str, auth: str) -> PushSubscription: ...


class IAIQueryCommand(ABC):
    @abstractmethod
    async def query(self, prompt: str) -> str: ...
