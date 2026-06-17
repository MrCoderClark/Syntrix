from __future__ import annotations

import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.auth.rate_limit import check_rate_limit
from app.db.session import get_session
from app.storage.backend import get_storage_backend
from app.storage.exif import ALLOWED_MIMES, ImageValidationError
from app.storage.schemas import (
    FinalizeRequest,
    FinalizeResponse,
    SignUploadRequest,
    SignUploadResponse,
)

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/sign", response_model=SignUploadResponse)
async def sign_upload(
    body: SignUploadRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    if body.content_type not in ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail=f"Unsupported type: {body.content_type}")

    conn = await session.connection()
    allowed = await check_rate_limit(
        conn,
        key=f"upload_sign:{user.id}",
        max_tokens=100,
        refill_rate=100 / 3600,
        cost=1,
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Upload rate limit exceeded")

    ext = body.filename.rsplit(".", 1)[-1] if "." in body.filename else "bin"
    key = f"tmp/{secrets.token_hex(16)}.{ext}"
    backend = get_storage_backend()
    upload_url = await backend.sign_upload(key, body.content_type, ttl=300)

    return SignUploadResponse(key=key, upload_url=upload_url, expires_in=300)


@router.post("/finalize", response_model=FinalizeResponse)
async def finalize_upload(
    body: FinalizeRequest,
    user: CurrentUser,
):
    if not body.key.startswith("tmp/"):
        raise HTTPException(status_code=400, detail="Key must start with tmp/")

    backend = get_storage_backend()
    try:
        result = await backend.finalize(body.key)
    except ImageValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

    return FinalizeResponse(**result)


@router.post("/sweep-orphans", status_code=200)
async def sweep_orphans(user: CurrentUser):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    backend = get_storage_backend()
    # Phase 1: simple sweep — list and delete all objects in tmp/
    # A proper age-based filter requires the Supabase Storage list API
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{backend.base_url}/object/list/{backend.bucket}",
                headers={**backend._headers(), "Content-Type": "application/json"},
                json={"prefix": "tmp/", "limit": 1000},
            )
            resp.raise_for_status()
            objects = resp.json()
            for obj in objects:
                await backend.delete(f"tmp/{obj['name']}")
        return {"status": "sweep complete", "deleted": len(objects)}
    except Exception:
        return {"status": "sweep complete", "deleted": 0}
