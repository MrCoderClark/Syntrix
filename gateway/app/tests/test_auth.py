import uuid
from datetime import timedelta

import pytest

from app.auth import AuthError, verify_token


def test_valid_token_returns_payload(jwt_secret, make_token):
    uid = uuid.uuid4()
    token = make_token(user_id=uid)
    payload = verify_token(token, jwt_secret)
    assert payload["sub"] == str(uid)
    assert payload["role"] == "member"


def test_expired_token_raises(jwt_secret, make_token):
    token = make_token(expires_delta=timedelta(seconds=-1))
    with pytest.raises(AuthError, match="expired"):
        verify_token(token, jwt_secret)


def test_invalid_token_raises(jwt_secret):
    with pytest.raises(AuthError, match="invalid"):
        verify_token("not.a.jwt", jwt_secret)


def test_wrong_secret_raises(make_token):
    token = make_token()
    with pytest.raises(AuthError, match="invalid"):
        verify_token(token, "wrong-secret")
