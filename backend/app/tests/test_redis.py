import pytest

from app.redis import get_redis, publish_event


@pytest.fixture
async def redis_conn():
    r = get_redis()
    yield r
    await r.aclose()


async def test_publish_event_reaches_subscriber(redis_conn):
    channel = "syntrix:test:roundtrip"

    pubsub = redis_conn.pubsub()
    await pubsub.subscribe(channel)
    # drain subscribe confirmation
    await pubsub.get_message(timeout=1)

    await publish_event(channel, "test.ping", {"msg": "hello"})

    msg = await pubsub.get_message(timeout=2)
    assert msg is not None
    assert msg["type"] == "message"

    import json

    envelope = json.loads(msg["data"])
    assert envelope["type"] == "test.ping"
    assert envelope["payload"]["msg"] == "hello"
    assert "ts" in envelope

    await pubsub.unsubscribe(channel)
    await pubsub.aclose()
