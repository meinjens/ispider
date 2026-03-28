from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from .database import get_session
from .settings import settings
from ..adapters.outbound.postgres.repositories import (
    SourceRepository, ItemRepository, ScoredItemRepository,
    TagRepository, KeywordRepository, PushSubscriptionRepository,
)
from ..adapters.outbound.anthropic.provider import AnthropicProvider
from ..adapters.outbound.rss.detector import detect_source_type
from ..domain.services import (
    SourceService, FeedService, TagService,
    KeywordService, PushService, AIQueryService,
)


def _ai_provider() -> AnthropicProvider:
    return AnthropicProvider(
        api_key=settings.anthropic_api_key,
        query_model=settings.anthropic_model_query,
        batch_model=settings.anthropic_model_batch,
    )


def get_source_service(session: AsyncSession = Depends(get_session)) -> SourceService:
    return SourceService(SourceRepository(session), type_detector=detect_source_type)


def get_feed_service(session: AsyncSession = Depends(get_session)) -> FeedService:
    return FeedService(ItemRepository(session))


def get_tag_service(session: AsyncSession = Depends(get_session)) -> TagService:
    return TagService(TagRepository(session))


def get_keyword_service(session: AsyncSession = Depends(get_session)) -> KeywordService:
    return KeywordService(KeywordRepository(session))


def get_push_service(session: AsyncSession = Depends(get_session)) -> PushService:
    return PushService(PushSubscriptionRepository(session))


def get_ai_query_service(session: AsyncSession = Depends(get_session)) -> AIQueryService:
    return AIQueryService(_ai_provider(), ItemRepository(session))
