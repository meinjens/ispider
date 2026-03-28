import json
from typing import Optional
import redis.asyncio as aioredis


class RedisClient:
    def __init__(self, host: str = "redis", port: int = 6379):
        self._redis = aioredis.Redis(host=host, port=port, decode_responses=True)

    async def close(self) -> None:
        await self._redis.aclose()

    # ── Push-Deduplizierung ──────────────────────────────────────────────────

    async def mark_pushed(self, item_id: int, ttl_seconds: int = 86400) -> None:
        """Markiert einen Artikel als bereits gepusht (TTL: 24h)."""
        await self._redis.setex(f"pushed:{item_id}", ttl_seconds, "1")

    async def was_pushed(self, item_id: int) -> bool:
        return await self._redis.exists(f"pushed:{item_id}") == 1

    # ── Rate-Limiting für Push ───────────────────────────────────────────────

    async def increment_push_count(self, window_seconds: int = 3600) -> int:
        """Inkrementiert Push-Counter im aktuellen Zeitfenster, gibt aktuellen Wert zurück."""
        key = "push_rate"
        pipe = self._redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        result = await pipe.execute()
        return result[0]

    async def get_push_count(self) -> int:
        val = await self._redis.get("push_rate")
        return int(val) if val else 0

    # ── Allgemeines Caching ──────────────────────────────────────────────────

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        if ttl_seconds:
            await self._redis.setex(key, ttl_seconds, value)
        else:
            await self._redis.set(key, value)

    async def get(self, key: str) -> Optional[str]:
        return await self._redis.get(key)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    # ── Health-Check ─────────────────────────────────────────────────────────

    async def ping(self) -> bool:
        try:
            return await self._redis.ping()
        except Exception:
            return False
