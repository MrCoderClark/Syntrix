from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException

from app.auth.deps import CurrentUser


def can(action: str, **kwargs: Any):
    async def _check(user: CurrentUser) -> None:
        if action == "is_authenticated":
            return

        raise HTTPException(
            status_code=403,
            detail=f"Permission check '{action}' not implemented yet",
        )

    return Depends(_check)
