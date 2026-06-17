from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreatePostRequest(BaseModel):
    community_id: UUID
    title: str = Field(min_length=1, max_length=300)
    body_json: dict


class UpdatePostRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    body_json: dict | None = None


class RemovePostRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class PostResponse(BaseModel):
    id: UUID
    community_id: UUID
    community_slug: str | None = None
    community_name: str | None = None
    author_id: UUID | None
    author_handle: str | None = None
    author_display_name: str | None = None
    author_avatar_url: str | None = None
    title: str
    body_json: dict | None = None
    body_html: str
    score: int
    comment_count: int
    is_pinned: bool
    deleted_at: datetime | None = None
    removed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    posts: list[PostResponse]
    next_cursor: str | None = None
