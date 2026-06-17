from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateCommentRequest(BaseModel):
    body_json: dict
    parent_comment_id: UUID | None = None


class RemoveCommentRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class CommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    author_id: UUID | None
    author_handle: str | None = None
    author_display_name: str | None = None
    author_avatar_url: str | None = None
    parent_id: UUID | None
    depth: int
    body_html: str
    score: int
    deleted_at: datetime | None = None
    removed_at: datetime | None = None
    created_at: datetime
    children: list[CommentResponse] = []


CommentResponse.model_rebuild()


class CommentListResponse(BaseModel):
    comments: list[CommentResponse]
    total_count: int
