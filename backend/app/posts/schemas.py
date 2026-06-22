from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MarkDuplicateRequest(BaseModel):
    duplicate_of_id: UUID


class PostTagResponse(BaseModel):
    id: str
    slug: str
    name: str
    color: str | None


class CreatePostRequest(BaseModel):
    community_id: UUID
    title: str = Field(min_length=1, max_length=300)
    body_json: dict
    post_type: str = "discussion"
    tag_ids: list[UUID] = Field(default_factory=list)

    @field_validator("post_type")
    @classmethod
    def validate_post_type(cls, v: str) -> str:
        if v not in ("discussion", "question"):
            raise ValueError("post_type must be 'discussion' or 'question'")
        return v


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
    post_type: str = "discussion"
    answer_count: int = 0
    has_accepted_answer: bool = False
    duplicate_of_id: UUID | None = None
    duplicate_of_title: str | None = None
    tags: list[PostTagResponse] = Field(default_factory=list)
    deleted_at: datetime | None = None
    removed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    posts: list[PostResponse]
    next_cursor: str | None = None
