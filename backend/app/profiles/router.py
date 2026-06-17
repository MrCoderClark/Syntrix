from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.db.session import get_session
from app.models import User
from app.profiles.schemas import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/api/users", tags=["profiles"])


def _to_response(user: User) -> ProfileResponse:
    return ProfileResponse(
        id=str(user.id),
        handle=user.handle,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        audience_tag=user.audience_tag,
        role=user.role,
        created_at=user.created_at,
    )


@router.get("/{handle}", response_model=ProfileResponse)
async def get_profile(handle: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.handle == handle))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.patch("/me", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    if body.handle is not None and body.handle != user.handle:
        existing = await session.execute(select(User).where(User.handle == body.handle))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Handle already taken")
        user.handle = body.handle

    if body.display_name is not None:
        user.display_name = body.display_name
    if body.bio is not None:
        user.bio = body.bio
    if body.audience_tag is not None:
        user.audience_tag = body.audience_tag
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url

    session.add(user)
    await session.flush()
    return _to_response(user)
