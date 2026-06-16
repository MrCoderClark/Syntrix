import uuid
from datetime import timedelta

import pytest

from app.auth.jwt import create_access_token, decode_access_token, hash_refresh_token


def test_create_and_decode_access_token():
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, role="member")
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "member"


def test_expired_token_raises():
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, role="member", expires_delta=timedelta(seconds=-1))
    with pytest.raises(Exception):
        decode_access_token(token)


def test_invalid_token_raises():
    with pytest.raises(Exception):
        decode_access_token("not.a.jwt")


def test_hash_refresh_token_is_deterministic():
    raw = "test-token-value"
    h1 = hash_refresh_token(raw)
    h2 = hash_refresh_token(raw)
    assert h1 == h2
    assert h1 != raw
