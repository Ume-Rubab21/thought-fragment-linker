import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DashboardRecentNote(BaseModel):
    id: uuid.UUID
    title: str
    body_md: str = ""
    updated_at: datetime


class DashboardTopTag(BaseModel):
    id: uuid.UUID
    name: str
    note_count: int = 0


class DashboardSummaryResponse(BaseModel):
    note_count: int = 0
    tag_count: int = 0
    collection_count: int = 0
    connection_count: int = 0
    recent_notes: list[DashboardRecentNote] = Field(default_factory=list)
    top_tags: list[DashboardTopTag] = Field(default_factory=list)
