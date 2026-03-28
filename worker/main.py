import asyncio
import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("ispider.worker")

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.config.settings import settings
from api.config.database import AsyncSessionFactory, create_tables
from api.adapters.outbound.postgres.repositories import (
    SourceRepository, ItemRepository, ScoredItemRepository,
    KeywordRepository, PushSubscriptionRepository,
)
from api.adapters.outbound.anthropic.provider import AnthropicProvider
from api.adapters.outbound.rss.fetcher import RssFetcher
from api.adapters.outbound.scraper.web_scraper import WebScraper
from api.adapters.outbound.webpush.sender import WebPushSender
from api.adapters.outbound.redis.client import RedisClient
from api.domain.models import FeedItem, ScoredItem, SourceType


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


async def process_source(source, session, ai, rss, scraper, push, redis: RedisClient) -> int:
    item_repo = ItemRepository(session)
    scored_repo = ScoredItemRepository(session)
    keyword_repo = KeywordRepository(session)
    push_repo = PushSubscriptionRepository(session)

    fetcher = rss if source.type == SourceType.RSS else scraper
    try:
        scraped = await fetcher.fetch(source.url)
    except Exception as e:
        logger.warning("Fetch fehlgeschlagen [%s]: %s", source.name, e)
        return 0

    keywords = await keyword_repo.get_all(active_only=True)
    subscriptions = await push_repo.get_all()
    new_count = 0

    for si in scraped:
        url_hash = _url_hash(si.url)
        if await item_repo.exists_by_hash(url_hash):
            continue

        saved = await item_repo.save(FeedItem(
            source_id=source.id,
            url=si.url,
            url_hash=url_hash,
            title=si.title,
            description=si.summary,
        ))
        new_count += 1

        # KI-Scoring
        try:
            score_result = await ai.score_item(saved.title, saved.description or "")
        except Exception as e:
            logger.warning("Scoring fehlgeschlagen für '%s': %s", saved.title[:50], e)
            continue

        # Keyword-Matching
        haystack = (saved.title + " " + (saved.description or "")).lower()
        matched = [kw.term for kw in keywords if kw.term.lower() in haystack]

        await scored_repo.save(ScoredItem(
            item_id=saved.id,
            score=score_result.score,
            reason=score_result.reason,
            keywords_matched=matched,
        ))

        # Push-Trigger mit Rate-Limit und Deduplizierung
        should_push = score_result.score >= settings.push_score_threshold or bool(matched)
        already_pushed = await redis.was_pushed(saved.id)

        if should_push and not already_pushed and subscriptions:
            push_count = await redis.get_push_count()
            if push_count < settings.push_rate_limit_per_hour:
                for sub in subscriptions:
                    try:
                        await push.send(
                            sub.endpoint, sub.p256dh, sub.auth,
                            saved.title, score_result.reason, saved.url,
                        )
                    except Exception as e:
                        logger.warning("Push fehlgeschlagen: %s", e)
                await redis.mark_pushed(saved.id)
                await redis.increment_push_count()
            else:
                logger.info("Push-Rate-Limit erreicht, überspringe: %s", saved.title[:50])

    logger.info("[%s] %d neue Artikel", source.name, new_count)
    return new_count


async def fetch_all():
    logger.info("Feed-Fetch-Zyklus gestartet")
    redis = RedisClient(host=settings.redis_host, port=settings.redis_port)

    async with AsyncSessionFactory() as session:
        sources = await SourceRepository(session).get_all(active_only=True)
        if not sources:
            logger.info("Keine aktiven Quellen konfiguriert")
            return

        ai = AnthropicProvider(
            api_key=settings.anthropic_api_key,
            query_model=settings.anthropic_model_query,
            batch_model=settings.anthropic_model_batch,
        )
        rss = RssFetcher()
        scraper = WebScraper(ai)
        push = WebPushSender(
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_subject},
        )

        tasks = [
            process_source(s, session, ai, rss, scraper, push, redis)
            for s in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        errors = [r for r in results if isinstance(r, Exception)]
        total = sum(r for r in results if isinstance(r, int))

        if errors:
            for e in errors:
                logger.error("Quelle fehlgeschlagen: %s", e)

        logger.info("Zyklus abgeschlossen — %d neue Artikel, %d Fehler", total, len(errors))

    await redis.close()


async def main():
    await create_tables()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        fetch_all,
        "interval",
        minutes=settings.fetch_interval_minutes,
        next_run_time=datetime.now(),
    )
    scheduler.start()
    logger.info("Worker gestartet, Intervall: %d min", settings.fetch_interval_minutes)
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
