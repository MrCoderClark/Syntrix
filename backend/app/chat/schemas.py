from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str | None = None
    is_private: bool = False


class RoomResponse(BaseModel):
    id: uuid.UUID
    community_id: uuid.UUID | None
    name: str
    slug: str
    description: str | None
    is_default: bool
    is_private: bool
    is_dm: bool
    created_by: uuid.UUID | None
    created_at: datetime


class RoomMemberResponse(BaseModel):
    user_id: uuid.UUID
    handle: str
    display_name: str
    avatar_url: str | None
    added_by: uuid.UUID | None
    created_at: datetime


class SendMessageRequest(BaseModel):
    body_json: dict


class MessageResponse(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    author_id: uuid.UUID | None
    author_handle: str | None = None
    author_display_name: str | None = None
    author_avatar_url: str | None = None
    body_json: dict | None
    body_html: str
    edited_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime


class EditMessageRequest(BaseModel):
    body_json: dict


class AddRoomMemberRequest(BaseModel):
    user_id: uuid.UUID
