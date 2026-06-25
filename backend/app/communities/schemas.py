from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,38}[a-z0-9]$")


class CommunityResponse(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    color: str
    owner_id: str
    member_count: int = 0
    is_private: bool = False
    created_at: datetime


class CommunityCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=3, max_length=40)
    description: str | None = Field(default=None, max_length=1000)
    color: str = Field(default="#1e3a5f", pattern=r"^#[0-9a-fA-F]{6}$")
    is_private: bool = False

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not SLUG_RE.match(v):
            raise ValueError("Slug must be 3-40 lowercase chars, digits, hyphens, underscores")
        return v


class CommunityUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class CommunityRequestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=3, max_length=40)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not SLUG_RE.match(v):
            raise ValueError("Slug must be 3-40 lowercase chars, digits, hyphens, underscores")
        return v


class MemberResponse(BaseModel):
    user_id: str
    handle: str
    display_name: str
    avatar_url: str | None
    role: str
    joined_at: datetime
