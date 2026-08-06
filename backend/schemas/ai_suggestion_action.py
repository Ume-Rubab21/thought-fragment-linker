from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


SuggestionDecisionStatus = Literal[
    "accepted",
    "rejected",
]


class SuggestionAcceptRequest(BaseModel):
    """
    Optional user edits made before accepting the AI suggestion.

    When a field is omitted, the original AI-generated value is used.
    """

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=180,
    )

    body_md: str | None = Field(
        default=None,
        max_length=50_000,
    )

    tags: list[str] | None = Field(
        default=None,
        max_length=6,
    )

    selected_related_note_ids: list[uuid.UUID] | None = Field(
        default=None,
        description=(
            "The related notes selected by the user. "
            "When omitted, all AI-suggested related notes are linked."
        ),
    )


class SuggestionRejectRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class CreatedNoteLinkResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    link_id: uuid.UUID
    from_note_id: uuid.UUID
    to_note_id: uuid.UUID
    reason: str
    confidence: float


class SuggestionDecisionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
    )

    suggestion_id: uuid.UUID
    brain_dump_id: uuid.UUID

    decision: SuggestionDecisionStatus
    suggestion_status: str

    note_id: uuid.UUID | None = None

    embedding_status: Literal[
        "ready",
        "queued",
        "failed",
        "not-created",
    ]

    links_created: int = 0

    created_links: list[
        CreatedNoteLinkResponse
    ] = Field(
        default_factory=list,
    )

    skipped_related_note_ids: list[str] = Field(
        default_factory=list,
    )

    decided_at: datetime
    message: str