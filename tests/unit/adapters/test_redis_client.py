import pytest
import fakeredis.aioredis
from unittest.mock import patch, AsyncMock
from api.adapters.outbound.redis.client import RedisClient


@pytest.fixture
async def redis_client():
    """RedisClient mit fakeredis backend."""
    client = RedisClient.__new__(RedisClient)
    client._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client._redis.aclose()


@pytest.mark.asyncio
async def test_ping(redis_client):
    assert await redis_client.ping() is True


@pytest.mark.asyncio
async def test_mark_and_check_pushed(redis_client):
    assert await redis_client.was_pushed(42) is False
    await redis_client.mark_pushed(42)
    assert await redis_client.was_pushed(42) is True


@pytest.mark.asyncio
async def test_push_rate_counter(redis_client):
    assert await redis_client.get_push_count() == 0
    count1 = await redis_client.increment_push_count()
    count2 = await redis_client.increment_push_count()
    assert count1 == 1
    assert count2 == 2
    assert await redis_client.get_push_count() == 2


@pytest.mark.asyncio
async def test_set_and_get(redis_client):
    await redis_client.set("mykey", "myvalue")
    assert await redis_client.get("mykey") == "myvalue"


@pytest.mark.asyncio
async def test_delete(redis_client):
    await redis_client.set("key", "val")
    await redis_client.delete("key")
    assert await redis_client.get("key") is None


@pytest.mark.asyncio
async def test_get_nonexistent_key(redis_client):
    assert await redis_client.get("does_not_exist") is None
