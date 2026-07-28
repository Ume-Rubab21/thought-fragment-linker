import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from schemas.tag import TagResponse
from utils.rich_text import sanitize_rich_text


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)

    # The existing name is retained for database/API compatibility.
    # This field now stores sanitized rich-text HTML.
    body_md: str = ""

    collection_id: Optional[uuid.UUID] = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Title cannot be empty")

        return cleaned

    @field_validator("body_md")
    @classmethod
    def clean_body(cls, value: str) -> str:
        return sanitize_rich_text(value)


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=180,
    )

    body_md: Optional[str] = None
    collection_id: Optional[uuid.UUID] = None

    @field_validator("title")
    @classmethod
    def clean_optional_title(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Title cannot be empty")

        return cleaned

    @field_validator("body_md")
    @classmethod
    def clean_optional_body(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        return sanitize_rich_text(value)


class NoteResponse(BaseModel):
    id: uuid.UUID
    title: str
    body_md: str
    source: str
    collection_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class RelatedNoteResponse(BaseModel):
    id: uuid.UUID
    title: str
    excerpt: str

    # Cosine similarity: larger means more similar.
    similarity: float

    # Cosine distance: smaller means more similar.
    distance: float

    embedding_model: str

    collection_id: Optional[uuid.UUID] = None
    updated_at: datetime

    tags: List[TagResponse] = Field(
        default_factory=list
    )