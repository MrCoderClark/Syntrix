from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

import redis.asyncio as aioredis

if TYPE_CHECKING:
    from app.connections import ConnectionManager

logger = logging.getLogger(__name__)


class PubSubListener:
    def __init__(self, redis: aioredis.Redis, connections: ConnectionManager) -> None:
        self._redis = redis
        self._connections = connections
        self._pubsub = redis.pubsub()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._pubsub.aclose()

    async def subscribe_room(self, room_id: str) -> None:
        await self._pubsub.subscribe(f"syntrix:room:{room_id}")

    async def unsubscribe_room(self, room_id: str) -> None:
        await self._pubsub.unsubscribe(f"syntrix:room:{room_id}")

    async def subscribe_user(self, user_id: str) -> None:
        await self._pubsub.subscribe(
            f"syntrix:presence:{user_id}",
            f"syntrix:system:{user_id}",
        )

    async def unsubscribe_user(self, user_id: str) -> None:
        await self._pubsub.unsubscribe(
            f"syntrix:presence:{user_id}",
            f"syntrix:system:{user_id}",
        )

    async def _listen(self) -> None:
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                channel = message["channel"]
                data = message["data"]
                await self._dispatch(channel, data)
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("PubSubListener error")

    async def _dispatch(self, channel: str, data: str) -> None:
        try:
            envelope = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return

        # Determine target user(s) from channel pattern
        # syntrix:room:{room_id} → broadcast to room members
        # syntrix:presence:{user_id} → broadcast to users sharing rooms with this user
        # syntrix:system:{user_id} → send to specific user
        parts = channel.split(":")

        if len(parts) >= 3 and parts[1] == "room":
            room_id = parts[2]
            for uid in self._connections.get_room_users(room_id):
                await self._send_to_user(uid, data)

        elif len(parts) >= 3 and parts[1] == "system":
            target_user = parts[2]
            await self._send_to_user(target_user, data)

        elif len(parts) >= 3 and parts[1] == "presence":
            source_user = parts[2]
            notified: set[str] = set()
            for room_id in self._connections.get_user_rooms(source_user):
                for uid in self._connections.get_room_users(room_id):
                    if uid != source_user and uid not in notified:
                        await self._send_to_user(uid, data)
                        notified.add(uid)

    async def _send_to_user(self, user_id: str, data: str) -> None:
        for ws in self._connections.get_sockets(user_id):
            try:
                await ws.send_text(data)
            except Exception:
                pass
