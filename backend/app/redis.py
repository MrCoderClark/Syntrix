from __future__ import annotations

import json
import time

import redis.asyncio as aioredis

from app.config import get_settings

_pool: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _pool


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def publish_event(
    channel: str,
    event_type: str,
    payload: dict,
    room_id: str | None = None,
) -> None:
    envelope: dict = {
        "type": event_type,
        "payload": payload,
        "ts": int(time.time()),
    }
    if room_id is not None:
        envelope["room_id"] = room_id
    r = get_redis()
    await r.publish(channel, json.dumps(envelope))
