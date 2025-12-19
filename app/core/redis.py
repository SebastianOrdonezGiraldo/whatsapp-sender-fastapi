"""Redis configuration and connection management."""

import redis.asyncio as aioredis
from redis.asyncio import Redis
from rq import Queue
from redis import Redis as SyncRedis

from app.core.config import get_settings

settings = get_settings()


# Async Redis client
async def get_redis() -> Redis:
    """Get async Redis client."""
    return await aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


# Sync Redis for RQ (RQ doesn't support async yet)
def get_sync_redis() -> SyncRedis:
    """Get sync Redis client for RQ."""
    return SyncRedis.from_url(settings.redis_url)


# RQ Queues
def get_campaign_queue() -> Queue:
    """Get RQ queue for campaign processing."""
    redis_conn = get_sync_redis()
    return Queue("campaigns", connection=redis_conn)


def get_message_queue() -> Queue:
    """Get RQ queue for message sending."""
    redis_conn = get_sync_redis()
    return Queue("messages", connection=redis_conn, default_timeout=3600)


async def close_redis(redis_client: Redis) -> None:
    """Close Redis connection."""
    await redis_client.close()