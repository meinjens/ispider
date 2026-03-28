from abc import ABC, abstractmethod
from typing import Optional
from ...models import FeedItem, ScoredItem, Source, Tag, Keyword, PushSubscription


class IItemRepository(ABC):
    @abstractmethod
    async def save(self, item: FeedItem) -> FeedItem: ...

    @abstractmethod
    async def exists_by_hash(self, url_hash: str) -> bool: ...

    @abstractmethod
    async def get_all(
        self,
        source_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        min_score: Optional[int] = None,
        read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedItem]: ...

    @abstractmethod
    async def mark_read(self, item_id: int) -> None: ...


class ISourceRepository(ABC):
    @abstractmethod
    async def save(self, source: Source) -> Source: ...

    @abstractmethod
    async def get_all(self, active_only: bool = False) -> list[Source]: ...

    @abstractmethod
    async def get_by_id(self, source_id: int) -> Optional[Source]: ...

    @abstractmethod
    async def update(self, source: Source) -> Source: ...

    @abstractmethod
    async def delete(self, source_id: int) -> None: ...


class ITagRepository(ABC):
    @abstractmethod
    async def save(self, tag: Tag) -> Tag: ...

    @abstractmethod
    async def get_all(self) -> list[Tag]: ...

    @abstractmethod
    async def delete(self, tag_id: int) -> None: ...


class IKeywordRepository(ABC):
    @abstractmethod
    async def save(self, keyword: Keyword) -> Keyword: ...

    @abstractmethod
    async def get_all(self, active_only: bool = False) -> list[Keyword]: ...

    @abstractmethod
    async def delete(self, keyword_id: int) -> None: ...


class IPushSubscriptionRepository(ABC):
    @abstractmethod
    async def save(self, sub: PushSubscription) -> PushSubscription: ...

    @abstractmethod
    async def get_all(self) -> list[PushSubscription]: ...


class IScoredItemRepository(ABC):
    @abstractmethod
    async def save(self, scored: ScoredItem) -> ScoredItem: ...

    @abstractmethod
    async def get_by_item_id(self, item_id: int) -> Optional[ScoredItem]: ...
