import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest


@pytest.fixture
def jwt_secret():
    return "test-secret-key-for-gateway"


@pytest.fixture
def make_token(jwt_secret):
    def _make(
        user_id: uuid.UUID | None = None,
        role: str = "member",
        expires_delta: timedelta = timedelta(hours=1),
    ) -> str:
        if user_id is None:
            user_id = uuid.uuid4()
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "role": role,
            "iat": now,
            "exp": now + expires_delta,
        }
        return jwt.encode(payload, jwt_secret, algorithm="HS256")

    return _make
