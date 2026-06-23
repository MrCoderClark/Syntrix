from __future__ import annotations

import json
import time

from pydantic import BaseModel, ValidationError

# Event type constants
MESSAGE_CREATED = "message.created"
MESSAGE_EDITED = "message.edited"
MESSAGE_DELETED = "message.deleted"
TYPING_START = "typing.start"
TYPING_STOP = "typing.stop"
PRESENCE_UPDATE = "presence.update"
ROOM_USER_JOINED = "room.user_joined"
ROOM_USER_LEFT = "room.user_left"
SYSTEM_INVITED = "system.invited"
SYSTEM_KICKED = "system.kicked"
TOKEN_EXPIRING = "token_expiring"

# Client → server message types the gateway handles locally
CLIENT_LOCAL_TYPES = {TYPING_START, TYPING_STOP, PRESENCE_UPDATE}


class ProtocolError(Exception):
    pass


class Envelope(BaseModel):
    type: str
    payload: dict
    ts: int = 0
    room_id: str | None = None


def parse_client_message(raw: str) -> Envelope:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ProtocolError(f"invalid JSON: {exc}")
    try:
        return Envelope.model_validate(data)
    except ValidationError as exc:
        raise ProtocolError(f"invalid envelope: {exc}")


def make_envelope(
    event_type: str,
    payload: dict,
    room_id: str | None = None,
) -> str:
    data: dict = {
        "type": event_type,
        "payload": payload,
        "ts": int(time.time()),
    }
    if room_id is not None:
        data["room_id"] = room_id
    return json.dumps(data)
