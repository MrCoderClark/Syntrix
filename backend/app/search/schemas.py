from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SearchPostResult(BaseModel):
    id: str
    title: str
    community_slug: str | None
    community_name: str | None
    author_handle: str | None
    score: int
    comment_count: int
    created_at: datetime


class SearchCommunityResult(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    color: str
    member_count: int


class SearchUserResult(BaseModel):
    id: str
    handle: str
    display_name: str
    avatar_url: str | None


class SearchTagResult(BaseModel):
    id: str
    slug: str
    name: str
    color: str | None
    community_slug: str
    usage_count: int


class SearchResponse(BaseModel):
    posts: list[SearchPostResult]
    communities: list[SearchCommunityResult]
    users: list[SearchUserResult]
    tags: list[SearchTagResult] = Field(default_factory=list)
