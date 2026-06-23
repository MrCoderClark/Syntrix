from __future__ import annotations

from collections import defaultdict
from typing import Any


class ConnectionManager:
    def __init__(self) -> None:
        self._user_sockets: dict[str, set[Any]] = defaultdict(set)
        self._room_users: dict[str, set[str]] = defaultdict(set)
        self._user_rooms: dict[str, set[str]] = defaultdict(set)

    def add(self, user_id: str, ws: Any) -> None:
        self._user_sockets[user_id].add(ws)

    def remove(self, user_id: str, ws: Any) -> set[str]:
        sockets = self._user_sockets.get(user_id)
        if sockets:
            sockets.discard(ws)
        if not sockets:
            self._user_sockets.pop(user_id, None)
            rooms = self._user_rooms.pop(user_id, set())
            for room_id in rooms:
                self._room_users[room_id].discard(user_id)
                if not self._room_users[room_id]:
                    del self._room_users[room_id]
            return rooms
        return set()

    def get_sockets(self, user_id: str) -> set[Any]:
        return self._user_sockets.get(user_id, set())

    def is_online(self, user_id: str) -> bool:
        return bool(self._user_sockets.get(user_id))

    def subscribe_room(self, room_id: str, user_id: str) -> None:
        self._room_users[room_id].add(user_id)
        self._user_rooms[user_id].add(room_id)

    def unsubscribe_room(self, room_id: str, user_id: str) -> None:
        self._room_users[room_id].discard(user_id)
        if not self._room_users[room_id]:
            del self._room_users[room_id]
        self._user_rooms[user_id].discard(room_id)

    def get_room_users(self, room_id: str) -> set[str]:
        return self._room_users.get(room_id, set())

    def get_user_rooms(self, user_id: str) -> set[str]:
        return self._user_rooms.get(user_id, set())
