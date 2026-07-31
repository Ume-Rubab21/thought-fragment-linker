from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SuggestionStatus = Literal["pending", "accepted", "rejected"]


class RelatedNoteReviewItem(BaseModel):
    """A real note that the AI suggested linking to the accepted note."""

    model_config = ConfigDict(from_attributes=True)

    note_id: uuid.UUID
    title: str
    preview: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    similarity_percentage: int = Field(ge=0, le=100)
    created_at: datetime


class AISuggestionListItem(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
    )

    suggestion_id: uuid.UUID
    brain_dump_id: uuid.UUID
    suggested_title: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    related_note_ids: list[str] = Field(default_factory=list)
    status: str
    model_name: str
    total_tokens: int
    accepted_note_id: uuid.UUID | None = None
    rejection_reason: str | None = None
    reasoning_decision: str | None = None
    reasoning: str | None = None
    confidence_score: int | None = Field(default=None, ge=0, le=100)
    reasoning_tier: str = "small"
    decided_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    brain_dump_preview: str


class AISuggestionListResponse(BaseModel):
    items: list[AISuggestionListItem]
    total: int
    pending: int
    accepted: int
    rejected: int


class AISuggestionDetailResponse(AISuggestionListItem):
    brain_dump_text: str
    prompt_tokens: int
    completion_tokens: int
    attempts: int
    retry_count: int
    related_notes: list[RelatedNoteReviewItem] = Field(default_factory=list)
