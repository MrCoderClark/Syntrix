from __future__ import annotations

from typing import TYPE_CHECKING

from app.protocol import (
    PRESENCE_UPDATE,
    TYPING_START,
    TYPING_STOP,
    Envelope,
    make_envelope,
)

if TYPE_CHECKING:
    from app.connections import ConnectionManager
    from app.presence import PresenceManager


async def handle_client_message(
    envelope: Envelope,
    user_id: str,
    connections: ConnectionManager,
    presence: PresenceManager,
    redis_publish: object,  # async callable(channel, data)
) -> None:
    if envelope.type == TYPING_START:
        room_id = envelope.payload.get("room_id")
        if not room_id:
            return
        presence.start_typing(user_id, room_id)
        msg = make_envelope(TYPING_START, {"user_id": user_id}, room_id=room_id)
        await _broadcast_to_room(connections, room_id, msg, exclude=user_id)

    elif envelope.type == TYPING_STOP:
        room_id = envelope.payload.get("room_id")
        if not room_id:
            return
        presence.stop_typing(user_id, room_id)
        msg = make_envelope(TYPING_STOP, {"user_id": user_id}, room_id=room_id)
        await _broadcast_to_room(connections, room_id, msg, exclude=user_id)

    elif envelope.type == "ping":
        return

    elif envelope.type == PRESENCE_UPDATE:
        status = envelope.payload.get("status", "online")
        custom = envelope.payload.get("custom_status")
        await presence.set_status(user_id, status, custom_status=custom)
        msg = make_envelope(PRESENCE_UPDATE, {
            "user_id": user_id,
            "status": status,
            "custom_status": custom or "",
        })
        await redis_publish(f"syntrix:presence:{user_id}", msg)

    else:
        # Forward to Redis for backend processing
        await redis_publish(
            f"syntrix:client:{envelope.type}",
            make_envelope(envelope.type, {**envelope.payload, "user_id": user_id}),
        )


async def _broadcast_to_room(
    connections: ConnectionManager,
    room_id: str,
    message: str,
    exclude: str | None = None,
) -> None:
    for uid in connections.get_room_users(room_id):
        if uid == exclude:
            continue
        for ws in connections.get_sockets(uid):
            try:
                await ws.send_text(message)
            except Exception:
                pass
