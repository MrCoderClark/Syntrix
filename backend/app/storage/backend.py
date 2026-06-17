from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from typing import Protocol

import httpx

from app.config import get_settings
from app.storage.exif import validate_and_strip


class StorageBackend(Protocol):
    async def sign_upload(self, key: str, content_type: str, ttl: int = 300) -> str: ...
    async def finalize(self, key: str) -> dict: ...
    async def move(self, src: str, dst: str) -> None: ...
    async def delete(self, key: str) -> None: ...


class SupabaseStorageBackend:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.supabase_storage_url.rstrip("/")
        self.bucket = settings.storage_bucket
        self.service_key = settings.supabase_service_key
        self.max_bytes = settings.storage_max_size_bytes

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
        }

    async def sign_upload(self, key: str, content_type: str, ttl: int = 300) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/object/upload/sign/{self.bucket}/{key}",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"expiresIn": ttl},
            )
            resp.raise_for_status()
            data = resp.json()
            return f"{self.base_url}{data['url']}"

    async def finalize(self, key: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/object/{self.bucket}/{key}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            raw = resp.content
            content_type = resp.headers.get("content-type", "application/octet-stream")

        processed = validate_and_strip(raw, content_type, self.max_bytes)

        sha = hashlib.sha256(processed.data).hexdigest()[:16]
        ext = PurePosixPath(key).suffix or ".jpg"
        pending_key = f"pending/{sha}{ext}"

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/object/{self.bucket}/{pending_key}",
                headers={
                    **self._headers(),
                    "Content-Type": processed.content_type,
                    "x-upsert": "true",
                },
                content=processed.data,
            )

        await self.delete(key)

        public_url = f"{self.base_url}/object/public/{self.bucket}/{pending_key}"
        return {
            "key": pending_key,
            "url": public_url,
            "content_type": processed.content_type,
            "width": processed.width,
            "height": processed.height,
            "size_bytes": len(processed.data),
        }

    async def move(self, src: str, dst: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/object/move",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={
                    "bucketId": self.bucket,
                    "sourceKey": src,
                    "destinationKey": dst,
                },
            )

    async def delete(self, key: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.delete(
                f"{self.base_url}/object/{self.bucket}/{key}",
                headers=self._headers(),
            )


def get_storage_backend() -> SupabaseStorageBackend:
    return SupabaseStorageBackend()
