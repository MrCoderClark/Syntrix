from unittest.mock import MagicMock

import pytest

from app.connections import ConnectionManager


@pytest.fixture
def mgr():
    return ConnectionManager()


@pytest.fixture
def fake_ws():
    return MagicMock(name="ws")


def test_add_and_get_sockets(mgr, fake_ws):
    mgr.add("user1", fake_ws)
    assert fake_ws in mgr.get_sockets("user1")
    assert mgr.is_online("user1")


def test_remove_returns_rooms(mgr, fake_ws):
    mgr.add("user1", fake_ws)
    mgr.subscribe_room("room1", "user1")
    mgr.subscribe_room("room2", "user1")
    rooms = mgr.remove("user1", fake_ws)
    assert rooms == {"room1", "room2"}
    assert not mgr.is_online("user1")


def test_remove_one_of_multiple_sockets(mgr):
    ws1, ws2 = MagicMock(), MagicMock()
    mgr.add("user1", ws1)
    mgr.add("user1", ws2)
    rooms = mgr.remove("user1", ws1)
    # still online via ws2
    assert mgr.is_online("user1")
    assert rooms == set()  # not removed from rooms yet


def test_get_sockets_unknown_user(mgr):
    assert mgr.get_sockets("nobody") == set()


def test_room_subscribe_and_members(mgr, fake_ws):
    mgr.add("user1", fake_ws)
    mgr.add("user2", MagicMock())
    mgr.subscribe_room("room1", "user1")
    mgr.subscribe_room("room1", "user2")
    assert mgr.get_room_users("room1") == {"user1", "user2"}


def test_unsubscribe_room(mgr, fake_ws):
    mgr.add("user1", fake_ws)
    mgr.subscribe_room("room1", "user1")
    mgr.unsubscribe_room("room1", "user1")
    assert "user1" not in mgr.get_room_users("room1")


def test_get_user_rooms(mgr, fake_ws):
    mgr.add("user1", fake_ws)
    mgr.subscribe_room("r1", "user1")
    mgr.subscribe_room("r2", "user1")
    assert mgr.get_user_rooms("user1") == {"r1", "r2"}
