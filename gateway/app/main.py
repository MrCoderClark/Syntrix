from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager

import anyio
import redis.asyncio as aioredis
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.auth import AuthError, verify_token
from app.config import get_settings
from app.connections import ConnectionManager
from app.handlers import handle_client_message
from app.presence import PresenceManager
from app.protocol import TOKEN_EXPIRING, ProtocolError, make_envelope, parse_client_message
from app.pubsub import PubSubListener

logger = logging.getLogger(__name__)

connections = ConnectionManager()
_redis: aioredis.Redis | None = None
_presence: PresenceManager | None = None
_pubsub_listener: PubSubListener | None = None


@asynccontextmanager
async def lifespan(app: Starlette):
    global _redis, _presence, _pubsub_listener
    settings = get_settings()
    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    _presence = PresenceManager(_redis, presence_ttl=settings.presence_ttl)
    _pubsub_listener = PubSubListener(_redis, connections)
    await _pubsub_listener.start()
    yield
    await _pubsub_listener.stop()
    await _redis.aclose()


async def ws_endpoint(websocket: WebSocket) -> None:
    settings = get_settings()
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="missing token")
        return

    try:
        payload = verify_token(token, settings.jwt_secret_key)
    except AuthError:
        await websocket.close(code=4001, reason="unauthorized")
        return

    user_id = payload["sub"]
    token_exp = payload.get("exp", 0)

    await websocket.accept()
    connections.add(user_id, websocket)
    await _presence.set_status(user_id, "online")
    await _pubsub_listener.subscribe_user(user_id)

    # Schedule token expiry warning
    expiry_task = asyncio.create_task(
        _token_expiry_warning(websocket, token_exp)
    )

    try:
        while True:
            # Use anyio.move_on_after so heartbeat timeout works correctly under
            # anyio's cancellation model (asyncio.wait_for is incompatible with
            # anyio CancelScope used by Starlette's TestClient and production server).
            with anyio.move_on_after(settings.heartbeat_timeout) as cancel_scope:
                try:
                    data = await websocket.receive_text()
                except WebSocketDisconnect:
                    return

            if cancel_scope.cancelled_caught:
                logger.info("Heartbeat timeout for user %s", user_id)
                return

            await _presence.heartbeat(user_id)

            try:
                envelope = parse_client_message(data)
            except ProtocolError:
                continue

            await handle_client_message(
                envelope,
                user_id,
                connections,
                _presence,
                _redis.publish,
            )
    except Exception:
        logger.exception("Unexpected error in ws_endpoint for user %s", user_id)
    finally:
        expiry_task.cancel()
        connections.remove(user_id, websocket)
        if not connections.is_online(user_id):
            await _presence.remove(user_id)
            await _pubsub_listener.unsubscribe_user(user_id)
        try:
            await websocket.close()
        except Exception:
            pass


async def _token_expiry_warning(websocket: WebSocket, exp: int) -> None:
    warning_before = 60
    now = time.time()
    delay = exp - now - warning_before
    if delay > 0:
        await asyncio.sleep(delay)
        try:
            msg = make_envelope(TOKEN_EXPIRING, {"seconds_remaining": warning_before})
            await websocket.send_text(msg)
        except Exception:
            pass


app = Starlette(
    routes=[WebSocketRoute("/ws", ws_endpoint)],
    lifespan=lifespan,
)
