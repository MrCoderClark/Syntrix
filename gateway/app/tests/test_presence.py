import asyncio
import time

import pytest
import pytest_asyncio

from app.presence import PresenceManager

VALID_STATUSES = {"online", "idle", "dnd", "invisible"}


@pytest_asyncio.fixture
async def redis():
    import redis.asyncio as aioredis

    r = aioredis.from_url("redis://localhost:6379/1", decode_responses=True)
    await r.flushdb()
    yield r
    await r.flushdb()
    await r.aclose()


@pytest_asyncio.fixture
async def pm(redis):
    return PresenceManager(redis, presence_ttl=10)


async def test_set_and_get_status(pm):
    await pm.set_status("u1", "online")
    info = await pm.get_status("u1")
    assert info is not None
    assert info["status"] == "online"
    assert info["custom_status"] == ""
    assert abs(int(info["last_seen"]) - int(time.time())) < 2


async def test_set_status_with_custom(pm):
    await pm.set_status("u1", "dnd", custom_status="In a meeting")
    info = await pm.get_status("u1")
    assert info["custom_status"] == "In a meeting"


async def test_get_status_unknown_user(pm):
    assert await pm.get_status("nobody") is None


async def test_heartbeat_refreshes_last_seen(pm):
    await pm.set_status("u1", "online")
    t1 = int((await pm.get_status("u1"))["last_seen"])
    await asyncio.sleep(0.05)
    await pm.heartbeat("u1")
    t2 = int((await pm.get_status("u1"))["last_seen"])
    assert t2 >= t1


async def test_remove_clears_presence(pm):
    await pm.set_status("u1", "online")
    await pm.remove("u1")
    assert await pm.get_status("u1") is None


async def test_get_online_users(pm):
    await pm.set_status("u1", "online")
    await pm.set_status("u2", "idle")
    await pm.set_status("u3", "invisible")
    online = await pm.get_online_users()
    # invisible users should NOT appear in online list
    assert "u1" in online
    assert "u2" in online
    assert "u3" not in online


async def test_typing_start_stop(pm):
    pm.start_typing("u1", "room1")
    assert "u1" in pm.get_typing("room1")
    pm.stop_typing("u1", "room1")
    assert "u1" not in pm.get_typing("room1")


async def test_typing_empty_room(pm):
    assert pm.get_typing("empty-room") == set()
