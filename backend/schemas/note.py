import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NoteCreate(BaseModel):
    title: str
    body_md: str = ""


class NoteUpdate(BaseModel):
    # Both optional — lets the frontend send just the field that
    # changed, without having to resend the whole note every time.
    title: Optional[str] = None
    body_md: Optional[str] = None


class NoteResponse(BaseModel):
    id: uuid.UUID
    title: str
    body_md: str
    source: str
    collection_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True