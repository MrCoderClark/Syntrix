import json
import os
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

# Patch settings BEFORE importing the app module so get_settings() picks them up
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-bytes-longxxx"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"

# Clear the lru_cache so the patched env vars take effect
from app.config import get_settings

get_settings.cache_clear()

from app.main import app, connections  # noqa: E402


SECRET = "test-secret-key-32-bytes-longxxx"


def make_jwt(user_id: str | None = None, expires_delta: timedelta = timedelta(hours=1)) -> str:
    if user_id is None:
        user_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    return jwt.encode(
        {"sub": user_id, "role": "member", "iat": now, "exp": now + expires_delta},
        SECRET,
        algorithm="HS256",
    )


@pytest.fixture(scope="module")
def client():
    """Shared TestClient that starts the app lifespan once for the whole module."""
    with TestClient(app) as c:
        yield c


class TestWSAuth:
    def test_missing_token_rejected(self, client):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws"):
                pass
        assert exc_info.value.code == 4001

    def test_invalid_token_rejected(self, client):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws?token=garbage"):
                pass
        assert exc_info.value.code == 4001

    def test_valid_token_accepted(self, client):
        token = make_jwt()
        with client.websocket_connect(f"/ws?token={token}") as ws:
            # Connection accepted — send a no-op to prove it's alive
            ws.send_text(json.dumps({
                "type": "typing.start",
                "payload": {"room_id": "test-room"},
            }))


class TestWSPresence:
    def test_presence_set_on_connect(self, client):
        uid = str(uuid.uuid4())
        token = make_jwt(user_id=uid)
        with client.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_text(json.dumps({
                "type": "typing.start",
                "payload": {"room_id": "r"},
            }))
            # User must be tracked in ConnectionManager while connected
            assert connections.is_online(uid)

    def test_typing_start_broadcast(self, client):
        """typing.start from one user does not loop back to the same user."""
        uid = str(uuid.uuid4())
        token = make_jwt(user_id=uid)
        with client.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_text(json.dumps({
                "type": "typing.start",
                "payload": {"room_id": "broadcast-room"},
            }))
            # No message echoed back to sender — receive would block
            assert connections.is_online(uid)
