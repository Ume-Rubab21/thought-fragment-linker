import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=30)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().lower().split())
        if not normalized:
            raise ValueError("Tag name cannot be empty")
        return normalized


class TagUpdate(TagCreate):
    pass


class TagResponse(BaseModel):
    id: uuid.UUID
    name: str
    note_count: int = 0
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
