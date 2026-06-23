from __future__ import annotations

import time
from collections import defaultdict

import redis.asyncio as aioredis

# Redis key patterns (prefixed for namespace isolation)
_PRESENCE_KEY = "syntrix:presence:{user_id}"
_ONLINE_SET = "syntrix:presence:online"


class PresenceManager:
    def __init__(self, redis: aioredis.Redis, presence_ttl: int = 120) -> None:
        self._redis = redis
        self._ttl = presence_ttl
        self._typing: dict[str, set[str]] = defaultdict(set)

    async def set_status(
        self,
        user_id: str,
        status: str,
        custom_status: str | None = None,
    ) -> None:
        now = int(time.time())
        key = _PRESENCE_KEY.format(user_id=user_id)
        pipe = self._redis.pipeline()
        pipe.hset(
            key,
            mapping={
                "status": status,
                "custom_status": custom_status or "",
                "last_seen": str(now),
            },
        )
        pipe.expire(key, self._ttl)
        if status == "invisible":
            pipe.zrem(_ONLINE_SET, user_id)
        else:
            pipe.zadd(_ONLINE_SET, {user_id: now})
        await pipe.execute()

    async def get_status(self, user_id: str) -> dict | None:
        key = _PRESENCE_KEY.format(user_id=user_id)
        data = await self._redis.hgetall(key)
        return data if data else None

    async def heartbeat(self, user_id: str) -> None:
        now = int(time.time())
        key = _PRESENCE_KEY.format(user_id=user_id)
        pipe = self._redis.pipeline()
        pipe.hset(key, "last_seen", str(now))
        pipe.expire(key, self._ttl)
        # refresh online set score only if user is in it (gt=True: only update if new score > existing)
        pipe.zadd(_ONLINE_SET, {user_id: now}, gt=True)
        await pipe.execute()

    async def remove(self, user_id: str) -> None:
        key = _PRESENCE_KEY.format(user_id=user_id)
        pipe = self._redis.pipeline()
        pipe.delete(key)
        pipe.zrem(_ONLINE_SET, user_id)
        await pipe.execute()

    async def get_online_users(self, limit: int = 100) -> list[str]:
        return await self._redis.zrevrange(_ONLINE_SET, 0, limit - 1)

    # Typing — in-memory only, not persisted to Redis
    def start_typing(self, user_id: str, room_id: str) -> None:
        self._typing[room_id].add(user_id)

    def stop_typing(self, user_id: str, room_id: str) -> None:
        self._typing[room_id].discard(user_id)
        if not self._typing[room_id]:
            del self._typing[room_id]

    def get_typing(self, room_id: str) -> set[str]:
        return self._typing.get(room_id, set())
