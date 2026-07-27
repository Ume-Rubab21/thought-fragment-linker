import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            raise ValueError("Collection name cannot be empty")
        return cleaned


class CollectionUpdate(CollectionCreate):
    pass


class CollectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    note_count: Optional[int] = None

    class Config:
        from_attributes = True
