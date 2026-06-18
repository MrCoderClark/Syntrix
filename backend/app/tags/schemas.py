from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class TagResponse(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    color: str | None
    usage_count: int
    community_slug: str
    created_at: datetime


class TagCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    color: str | None = Field(default=None, max_length=7)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is not None and not COLOR_RE.match(v):
            raise ValueError("Color must be a hex color like #1e3a5f")
        return v


class TagUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    color: str | None = Field(default=None, max_length=7)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is not None and v != "" and not COLOR_RE.match(v):
            raise ValueError("Color must be a hex color like #1e3a5f")
        return v


class TagAutocompleteItem(BaseModel):
    id: str
    slug: str
    name: str
    color: str | None
    usage_count: int
