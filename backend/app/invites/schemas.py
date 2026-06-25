from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateInviteRequest(BaseModel):
    target_type: str = Field(pattern=r"^(room|community)$")
    target_id: uuid.UUID
    invited_user_id: uuid.UUID


class InviteResponse(BaseModel):
    id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    target_name: str | None = None
    invited_by: uuid.UUID
    invited_by_handle: str | None = None
    invited_user_id: uuid.UUID
    status: str
    created_at: datetime
    responded_at: datetime | None
