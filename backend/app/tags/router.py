from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.db.session import get_session
from app.models.community import Community, CommunityMembership
from app.models.tag import Tag
from app.tags.schemas import (
    TagAutocompleteItem,
    TagCreateRequest,
    TagResponse,
    TagUpdateRequest,
)

router = APIRouter(prefix="/api/communities/{slug}/tags", tags=["tags"])

SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    return SLUG_CHARS.sub("-", name.lower()).strip("-")[:50]


def _to_response(tag: Tag, community_slug: str) -> TagResponse:
    return TagResponse(
        id=str(tag.id),
        slug=tag.slug,
        name=tag.name,
        description=tag.description,
        color=tag.color,
        usage_count=tag.usage_count,
        community_slug=community_slug,
        created_at=tag.created_at,
    )


async def _resolve_community(slug: str, session: AsyncSession) -> Community:
    result = await session.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return community


async def _check_mod_or_above(user_id, community: Community, session: AsyncSession) -> None:
    if hasattr(user_id, "id"):
        uid = user_id.id
        if user_id.role == "admin":
            return
    else:
        uid = user_id

    result = await session.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community.id,
            CommunityMembership.user_id == uid,
            CommunityMembership.banned_at.is_(None),
        )
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.role not in ("mod", "owner"):
        raise HTTPException(status_code=403, detail="Mod or higher required")


@router.get("", response_model=list[TagResponse])
async def list_tags(slug: str, session: AsyncSession = Depends(get_session)):
    community = await _resolve_community(slug, session)
    result = await session.execute(
        select(Tag).where(Tag.community_id == community.id).order_by(Tag.name)
    )
    return [_to_response(t, slug) for t in result.scalars()]


@router.get("/autocomplete", response_model=list[TagAutocompleteItem])
async def autocomplete_tags(
    slug: str,
    q: str = Query(default="", max_length=50),
    session: AsyncSession = Depends(get_session),
):
    community = await _resolve_community(slug, session)
    stmt = (
        select(Tag)
        .where(Tag.community_id == community.id)
        .order_by(Tag.usage_count.desc(), Tag.name)
        .limit(10)
    )
    if q.strip():
        stmt = stmt.where(Tag.name.ilike(f"%{q.strip()}%"))
    result = await session.execute(stmt)
    return [
        TagAutocompleteItem(
            id=str(t.id),
            slug=t.slug,
            name=t.name,
            color=t.color,
            usage_count=t.usage_count,
        )
        for t in result.scalars()
    ]


@router.get("/{tag_slug}", response_model=TagResponse)
async def get_tag(slug: str, tag_slug: str, session: AsyncSession = Depends(get_session)):
    community = await _resolve_community(slug, session)
    result = await session.execute(
        select(Tag).where(Tag.community_id == community.id, Tag.slug == tag_slug)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return _to_response(tag, slug)


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(
    slug: str,
    body: TagCreateRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    community = await _resolve_community(slug, session)
    await _check_mod_or_above(user, community, session)

    tag_slug = _slugify(body.name)
    if not tag_slug:
        raise HTTPException(status_code=400, detail="Invalid tag name")

    existing = await session.execute(
        select(Tag).where(Tag.community_id == community.id, Tag.slug == tag_slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tag already exists in this community")

    tag = Tag(
        community_id=community.id,
        name=body.name,
        slug=tag_slug,
        description=body.description,
        color=body.color,
        created_by=user.id,
    )
    session.add(tag)
    await session.flush()
    return _to_response(tag, slug)


@router.patch("/{tag_slug}", response_model=TagResponse)
async def update_tag(
    slug: str,
    tag_slug: str,
    body: TagUpdateRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    community = await _resolve_community(slug, session)
    await _check_mod_or_above(user, community, session)

    result = await session.execute(
        select(Tag).where(Tag.community_id == community.id, Tag.slug == tag_slug)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if body.name is not None:
        new_slug = _slugify(body.name)
        if new_slug != tag.slug:
            dup = await session.execute(
                select(Tag).where(Tag.community_id == community.id, Tag.slug == new_slug)
            )
            if dup.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="Tag slug conflict")
            tag.slug = new_slug
        tag.name = body.name
    if body.description is not None:
        tag.description = body.description if body.description != "" else None
    if body.color is not None:
        tag.color = body.color if body.color != "" else None

    session.add(tag)
    await session.flush()
    return _to_response(tag, slug)


@router.delete("/{tag_slug}", status_code=204)
async def delete_tag(
    slug: str,
    tag_slug: str,
    user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    community = await _resolve_community(slug, session)
    if user.role != "admin":
        await _check_mod_or_above(user, community, session)

    result = await session.execute(
        select(Tag).where(Tag.community_id == community.id, Tag.slug == tag_slug)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag.usage_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Tag is used by {tag.usage_count} question(s) — remove from questions first",
        )

    await session.delete(tag)
    await session.flush()
