import json
import time

import pytest

from app.protocol import (
    PRESENCE_UPDATE,
    ROOM_SUBSCRIBE,
    ROOM_UNSUBSCRIBE,
    TYPING_START,
    TYPING_STOP,
    Envelope,
    ProtocolError,
    make_envelope,
    parse_client_message,
)


def test_parse_valid_typing_start():
    raw = json.dumps({"type": "typing.start", "payload": {"room_id": "abc"}})
    env = parse_client_message(raw)
    assert env.type == "typing.start"
    assert env.payload == {"room_id": "abc"}


def test_parse_rejects_missing_type():
    raw = json.dumps({"payload": {"room_id": "abc"}})
    with pytest.raises(ProtocolError):
        parse_client_message(raw)


def test_parse_rejects_invalid_json():
    with pytest.raises(ProtocolError):
        parse_client_message("not json {{{")


def test_parse_rejects_missing_payload():
    raw = json.dumps({"type": "typing.start"})
    with pytest.raises(ProtocolError):
        parse_client_message(raw)


def test_make_envelope_roundtrip():
    json_str = make_envelope("presence.update", {"status": "online"}, room_id="r1")
    data = json.loads(json_str)
    assert data["type"] == "presence.update"
    assert data["payload"]["status"] == "online"
    assert data["room_id"] == "r1"
    assert abs(data["ts"] - int(time.time())) < 2


def test_make_envelope_no_room_id():
    json_str = make_envelope("token_expiring", {"seconds_remaining": 60})
    data = json.loads(json_str)
    assert "room_id" not in data


def test_event_type_constants():
    assert TYPING_START == "typing.start"
    assert TYPING_STOP == "typing.stop"
    assert PRESENCE_UPDATE == "presence.update"


def test_room_subscribe_constant():
    assert ROOM_SUBSCRIBE == "room.subscribe"


def test_room_unsubscribe_constant():
    assert ROOM_UNSUBSCRIBE == "room.unsubscribe"
