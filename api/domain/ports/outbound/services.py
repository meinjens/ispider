from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from ...models import FeedItem


@dataclass
class ScoreResult:
    score: int
    reason: str
    tags: list[str]


@dataclass
class ScrapedItem:
    title: str
    url: str
    summary: Optional[str] = None
    pub_date: Optional[str] = None


class IAIProvider(ABC):
    @abstractmethod
    async def score_item(self, title: str, summary: str) -> ScoreResult: ...

    @abstractmethod
    async def scrape_page(self, html: str, source_url: str) -> list[ScrapedItem]: ...

    @abstractmethod
    async def query(self, prompt: str, context_items: list[FeedItem]) -> str: ...


class IFeedFetcher(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> list[ScrapedItem]: ...


class IPushSender(ABC):
    @abstractmethod
    async def send(self, endpoint: str, p256dh: str, auth: str, title: str, body: str, url: str) -> None: ...
