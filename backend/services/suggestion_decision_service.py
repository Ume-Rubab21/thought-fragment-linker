from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.ai_suggestion import AISuggestion
from models.brain_dump import BrainDump
from models.note import Note
from models.note_link import NoteLink
from models.tag import Tag
from services.embedding_service import (
    upsert_note_embedding,
)
from services.note_link_service import (
    NoteLinkCreationResult,
    create_note_links,
)


class SuggestionDecisionError(RuntimeError):
    """Base error for suggestion decisions."""


class SuggestionDecisionNotFoundError(
    SuggestionDecisionError
):
    """Raised when the suggestion does not belong to the user."""


class SuggestionDecisionConflictError(
    SuggestionDecisionError
):
    """Raised when a suggestion has already been decided."""


class SuggestionDecisionValidationError(
    SuggestionDecisionError
):
    """Raised when edited acceptance values are invalid."""


@dataclass(frozen=True)
class SuggestionAcceptanceResult:
    suggestion: AISuggestion
    note: Note
    embedding_ready: bool
    created_links: list[NoteLink]
    skipped_related_note_ids: list[str]


def normalize_tag_name(
    value: str,
) -> str:
    normalized = "-".join(
        value.strip().lower().split()
    )

    normalized = normalized.strip("-")

    if not normalized:
        raise SuggestionDecisionValidationError(
            "Tag names cannot be empty."
        )

    if len(normalized) > 50:
        raise SuggestionDecisionValidationError(
            "Tag names cannot exceed 50 characters."
        )

    return normalized


def normalize_tags(
    values: list[str],
) -> list[str]:
    normalized_tags: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = normalize_tag_name(
            value
        )

        if normalized in seen:
            continue

        seen.add(normalized)
        normalized_tags.append(normalized)

    if len(normalized_tags) > 6:
        raise SuggestionDecisionValidationError(
            "A maximum of 6 tags is allowed."
        )

    return normalized_tags


def get_owned_suggestion(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
) -> AISuggestion:
    """
    Retrieve a suggestion only when the suggestion and Brain Dump both
    belong to the authenticated user.
    """

    suggestion = (
        db.query(AISuggestion)
        .join(
            BrainDump,
            BrainDump.id
            == AISuggestion.brain_dump_id,
        )
        .filter(
            AISuggestion.brain_dump_id
            == brain_dump_id,
            AISuggestion.user_id == user_id,
            BrainDump.user_id == user_id,
        )
        .first()
    )

    if suggestion is None:
        raise SuggestionDecisionNotFoundError(
            "AI suggestion was not found."
        )

    return suggestion


def ensure_pending(
    suggestion: AISuggestion,
) -> None:
    if suggestion.status != "pending":
        raise SuggestionDecisionConflictError(
            "This AI suggestion has already been "
            f"{suggestion.status}."
        )


def find_or_create_tag(
    db: Session,
    *,
    user_id: uuid.UUID,
    name: str,
) -> Tag:
    tag = (
        db.query(Tag)
        .filter(
            Tag.user_id == user_id,
            func.lower(Tag.name) == name.lower(),
        )
        .first()
    )

    if tag is not None:
        return tag

    tag = Tag(
        user_id=user_id,
        name=name,
    )

    db.add(tag)
    db.flush()

    return tag


def accept_suggestion(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
    title: str | None = None,
    body_md: str | None = None,
    tags: list[str] | None = None,
) -> SuggestionAcceptanceResult:
    """
    Accept a pending suggestion and create its permanent records.

    Transactional database work:

        Create Note
        → create/reuse Tags
        → attach Tags
        → validate related Note IDs
        → create NoteLink rows
        → mark suggestion accepted
        → commit

    Embedding generation runs after the accepted Note has been committed.
    """

    suggestion = get_owned_suggestion(
        db=db,
        user_id=user_id,
        brain_dump_id=brain_dump_id,
    )

    ensure_pending(suggestion)

    brain_dump = (
        db.query(BrainDump)
        .filter(
            BrainDump.id == brain_dump_id,
            BrainDump.user_id == user_id,
        )
        .first()
    )

    if brain_dump is None:
        raise SuggestionDecisionNotFoundError(
            "Brain Dump was not found."
        )

    accepted_title = (
        title.strip()
        if title is not None
        else suggestion.suggested_title.strip()
    )

    if not accepted_title:
        raise SuggestionDecisionValidationError(
            "The accepted note title cannot be empty."
        )

    if len(accepted_title) > 180:
        raise SuggestionDecisionValidationError(
            "The accepted note title cannot exceed "
            "180 characters."
        )

    accepted_body = (
        body_md.strip()
        if body_md is not None
        else brain_dump.raw_text.strip()
    )

    accepted_tag_values = normalize_tags(
        tags
        if tags is not None
        else list(suggestion.tags or [])
    )

    note = Note(
        user_id=user_id,
        title=accepted_title,
        body_md=accepted_body,
        source="brain-dump-ai",
    )

    db.add(note)

    try:
        db.flush()

        for tag_name in accepted_tag_values:
            tag = find_or_create_tag(
                db=db,
                user_id=user_id,
                name=tag_name,
            )

            if tag not in note.tags:
                note.tags.append(tag)

        link_result: NoteLinkCreationResult = (
            create_note_links(
                db=db,
                user_id=user_id,
                from_note=note,
                related_note_ids=(
                    suggestion.related_note_ids or []
                ),
            )
        )

        suggestion.status = "accepted"
        suggestion.accepted_note_id = note.id
        suggestion.decided_at = datetime.utcnow()
        suggestion.rejection_reason = None

        db.commit()

        db.refresh(note)
        db.refresh(suggestion)

        for link in link_result.created_links:
            db.refresh(link)

    except Exception:
        db.rollback()
        raise

    embedding_ready = upsert_note_embedding(
        db=db,
        note=note,
    )

    db.refresh(note)
    db.refresh(suggestion)

    return SuggestionAcceptanceResult(
        suggestion=suggestion,
        note=note,
        embedding_ready=embedding_ready,
        created_links=link_result.created_links,
        skipped_related_note_ids=(
            link_result.skipped_note_ids
        ),
    )


def reject_suggestion(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
    reason: str | None = None,
) -> AISuggestion:
    """
    Reject a pending suggestion without creating a Note or NoteLink.
    """

    suggestion = get_owned_suggestion(
        db=db,
        user_id=user_id,
        brain_dump_id=brain_dump_id,
    )

    ensure_pending(suggestion)

    cleaned_reason = (
        reason.strip()
        if reason
        else None
    )

    suggestion.status = "rejected"
    suggestion.accepted_note_id = None
    suggestion.rejection_reason = (
        cleaned_reason[:500]
        if cleaned_reason
        else None
    )
    suggestion.decided_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(suggestion)

    except Exception:
        db.rollback()
        raise

    return suggestion