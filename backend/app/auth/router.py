from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, decode_access_token, hash_refresh_token
from app.auth.oauth import fetch_user_info, oauth
from app.auth.rate_limit import check_rate_limit
from app.config import get_settings
from app.db.session import get_session
from app.models import OAuthIdentity, RefreshToken, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _generate_handle(name: str) -> str:
    base = "".join(c if c.isalnum() else "_" for c in name.lower())[:20].strip("_")
    if not base:
        base = "user"
    suffix = secrets.token_hex(3)
    return f"{base}_{suffix}"


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.jwt_access_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.jwt_refresh_expire_days * 86400,
        path="/api/auth/refresh",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")


@router.get("/login/{provider}")
async def login(provider: str, request: Request):
    settings = get_settings()
    allowed = ("github", "google", "discord")
    if provider not in allowed:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    client = oauth.create_client(provider)
    redirect_uri = f"{settings.oauth_redirect_base_url}/api/auth/callback/{provider}"
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/callback/{provider}")
async def callback(
    provider: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    settings = get_settings()
    allowed = ("github", "google", "discord")
    if provider not in allowed:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    client_ip = request.client.host if request.client else "unknown"
    conn = await session.connection()
    allowed_rl = await check_rate_limit(
        conn, key=f"oauth_cb:{client_ip}", max_tokens=30, refill_rate=30 / 900, cost=1
    )
    if not allowed_rl:
        raise HTTPException(status_code=429, detail="Too many login attempts")

    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)
    info = await fetch_user_info(provider, token)

    stmt = select(OAuthIdentity).where(
        OAuthIdentity.provider == provider,
        OAuthIdentity.provider_sub == info["sub"],
    )
    result = await session.execute(stmt)
    oi = result.scalar_one_or_none()

    if oi:
        user = oi.user
        if oi.email != info.get("email"):
            oi.email = info.get("email")
    else:
        user = User(
            handle=_generate_handle(info["name"]),
            display_name=info["name"],
            avatar_url=info.get("avatar_url"),
        )
        session.add(user)
        await session.flush()
        oi = OAuthIdentity(
            user_id=user.id,
            provider=provider,
            provider_sub=info["sub"],
            email=info.get("email"),
        )
        session.add(oi)

    access_token = create_access_token(user_id=user.id, role=user.role)
    raw_refresh = secrets.token_urlsafe(64)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days),
    )
    session.add(rt)
    await session.flush()

    response = Response(status_code=302)
    response.headers["location"] = settings.frontend_url
    _set_auth_cookies(response, access_token, raw_refresh)
    return response


@router.post("/refresh")
async def refresh(request: Request, session: AsyncSession = Depends(get_session)):
    raw_refresh = request.cookies.get("refresh_token")
    if not raw_refresh:
        raise HTTPException(status_code=401, detail="No refresh token")

    token_hash = hash_refresh_token(raw_refresh)
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > datetime.now(UTC),
    )
    result = await session.execute(stmt)
    rt = result.scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    rt.revoked_at = datetime.now(UTC)
    user = await session.get(User, rt.user_id)
    if not user or user.suspended_at:
        raise HTTPException(status_code=403, detail="Account suspended")

    settings = get_settings()
    access_token = create_access_token(user_id=user.id, role=user.role)
    new_raw = secrets.token_urlsafe(64)
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_raw),
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days),
    )
    session.add(new_rt)
    await session.flush()

    response = Response(status_code=200)
    _set_auth_cookies(response, access_token, new_raw)
    return response


@router.post("/logout")
async def logout(request: Request, session: AsyncSession = Depends(get_session)):
    raw_refresh = request.cookies.get("refresh_token")
    if raw_refresh:
        token_hash = hash_refresh_token(raw_refresh)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
        result = await session.execute(stmt)
        rt = result.scalar_one_or_none()
        if rt:
            rt.revoked_at = datetime.now(UTC)

    response = Response(status_code=200)
    _clear_auth_cookies(response)
    return response


@router.get("/me")
async def me(request: Request, session: AsyncSession = Depends(get_session)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token") from None
    user = await session.get(User, uuid.UUID(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {
        "id": str(user.id),
        "handle": user.handle,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "role": user.role,
    }
