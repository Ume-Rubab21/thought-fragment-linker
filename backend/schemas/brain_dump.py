import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


BrainDumpStatus = Literal[
    "queued",
    "processing",
    "ready",
    "failed",
]


class BrainDumpCreate(BaseModel):
    raw_text: str = Field(
        min_length=3,
        max_length=20_000,
    )

    @field_validator("raw_text")
    @classmethod
    def clean_raw_text(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Brain dump text cannot be empty"
            )

        return cleaned


class BrainDumpResponse(BaseModel):
    id: uuid.UUID
    raw_text: str
    status: BrainDumpStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrainDumpStatusResponse(BaseModel):
    id: uuid.UUID
    status: BrainDumpStatus
    error_message: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True