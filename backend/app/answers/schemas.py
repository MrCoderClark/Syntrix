from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateAnswerRequest(BaseModel):
    body_json: dict


class UpdateAnswerRequest(BaseModel):
    body_json: dict


class RemoveAnswerRequest(BaseModel):
    reason: str


class AnswerResponse(BaseModel):
    id: UUID
    question_id: UUID
    author_id: UUID | None
    author_handle: str | None = None
    author_display_name: str | None = None
    author_avatar_url: str | None = None
    body_json: dict | None = None
    body_html: str
    score: int
    is_accepted: bool
    accepted_at: datetime | None = None
    deleted_at: datetime | None = None
    removed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AnswerListResponse(BaseModel):
    answers: list[AnswerResponse]
    count: int
