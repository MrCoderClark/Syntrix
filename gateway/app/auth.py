from __future__ import annotations

import jwt


class AuthError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def verify_token(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthError("expired")
    except jwt.InvalidTokenError:
        raise AuthError("invalid")
