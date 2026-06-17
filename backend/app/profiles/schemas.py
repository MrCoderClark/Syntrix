from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

HANDLE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_]{1,22}[a-zA-Z0-9]$")
AUDIENCE_TAGS = ("gamer", "it", "dev")


class ProfileResponse(BaseModel):
    id: str
    handle: str
    display_name: str
    avatar_url: str | None
    bio: str | None
    audience_tag: str | None
    role: str
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    handle: str | None = Field(default=None, min_length=3, max_length=24)
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    audience_tag: str | None = None

    @field_validator("handle")
    @classmethod
    def validate_handle(cls, v: str | None) -> str | None:
        if v is not None and not HANDLE_RE.match(v):
            raise ValueError(
                "Handle must be 3-24 chars, alphanumeric + underscore, "
                "cannot start or end with underscore"
            )
        return v

    @field_validator("audience_tag")
    @classmethod
    def validate_audience_tag(cls, v: str | None) -> str | None:
        if v is not None and v not in AUDIENCE_TAGS:
            raise ValueError(f"audience_tag must be one of {AUDIENCE_TAGS}")
        return v
