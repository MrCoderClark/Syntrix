from __future__ import annotations

import re
from dataclasses import dataclass

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/og", tags=["og"])

_og_cache: dict[str, OGData | None] = {}


@dataclass
class OGData:
    title: str | None
    description: str | None
    image: str | None
    site_name: str | None
    url: str


def _parse_og_tags(html: str, url: str) -> OGData:
    def get_og(prop: str) -> str | None:
        match = re.search(
            rf'<meta\s+(?:property|name)=["\']og:{prop}["\']\s+content=["\']([^"\']*)["\']',
            html,
            re.IGNORECASE,
        )
        if not match:
            match = re.search(
                rf'<meta\s+content=["\']([^"\']*)["\']'
                rf'\s+(?:property|name)=["\']og:{prop}["\']',
                html,
                re.IGNORECASE,
            )
        return match.group(1) if match else None

    return OGData(
        title=get_og("title"),
        description=get_og("description"),
        image=get_og("image"),
        site_name=get_og("site_name"),
        url=url,
    )


async def fetch_og(url: str) -> OGData | None:
    if url in _og_cache:
        return _og_cache[url]

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Syntrix/1.0 bot"})
            resp.raise_for_status()
            html_text = resp.text[:50_000]
            data = _parse_og_tags(html_text, url)
            _og_cache[url] = data
            return data
    except Exception:
        _og_cache[url] = None
        return None


@router.get("")
async def get_og_data(url: str):
    data = await fetch_og(url)
    if data is None:
        return {
            "url": url,
            "title": None,
            "description": None,
            "image": None,
            "site_name": None,
        }
    return {
        "url": data.url,
        "title": data.title,
        "description": data.description,
        "image": data.image,
        "site_name": data.site_name,
    }
