from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


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
    def clean_raw_text(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Brain dump text cannot be empty."
            )

        return cleaned


class BrainDumpResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    raw_text: str
    status: BrainDumpStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class BrainDumpStatusResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    status: BrainDumpStatus
    error_message: str | None = None
    updated_at: datetime


class BrainDumpSuggestionResponse(BaseModel):
        
    model_config = ConfigDict(
        protected_namespaces=(),
    )
    """
    Response returned when the frontend requests the generated
    suggestion for a Brain Dump.
    """

    brain_dump_id: uuid.UUID
    brain_dump_status: BrainDumpStatus

    suggestion_id: uuid.UUID
    suggested_title: str
    summary: str

    tags: list[str]
    keywords: list[str]
    related_note_ids: list[str]

    model_name: str

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    attempts: int
    retry_count: int

    suggestion_status: str

    created_at: datetime
    updated_at: datetime