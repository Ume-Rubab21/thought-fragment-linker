from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from models.note import Note
from models.note_link import NoteLink


DEFAULT_LINK_REASON = (
    "Suggested by ThoughtLinker AI as a semantically related note."
)

DEFAULT_LINK_CONFIDENCE = 0.75
MAX_RELATED_NOTE_LINKS = 5


@dataclass(frozen=True)
class NoteLinkCreationResult:
    """
    Result returned after processing related-note suggestions.
    """

    created_links: list[NoteLink]
    skipped_note_ids: list[str]


def normalize_related_note_ids(
    values: list[object] | None,
) -> tuple[list[uuid.UUID], list[str]]:
    """
    Convert related-note values into unique UUID objects.

    Invalid IDs are returned separately so they can be skipped safely.
    """

    normalized_ids: list[uuid.UUID] = []
    skipped_ids: list[str] = []
    seen: set[uuid.UUID] = set()

    for value in values or []:
        raw_value = str(value).strip()

        if not raw_value:
            continue

        try:
            note_id = uuid.UUID(raw_value)

        except (TypeError, ValueError, AttributeError):
            skipped_ids.append(raw_value)
            continue

        if note_id in seen:
            continue

        seen.add(note_id)
        normalized_ids.append(note_id)

        if len(normalized_ids) >= MAX_RELATED_NOTE_LINKS:
            break

    return normalized_ids, skipped_ids


def get_owned_related_notes(
    db: Session,
    *,
    user_id: uuid.UUID,
    related_note_ids: list[uuid.UUID],
    excluded_note_id: uuid.UUID,
) -> tuple[list[Note], list[str]]:
    """
    Return only related Notes owned by the authenticated user.

    Missing, deleted, cross-user, and self-referencing Notes are skipped.
    """

    if not related_note_ids:
        return [], []

    notes = (
        db.query(Note)
        .filter(
            Note.id.in_(related_note_ids),
            Note.user_id == user_id,
            Note.id != excluded_note_id,
        )
        .all()
    )

    notes_by_id = {
        note.id: note
        for note in notes
    }

    owned_notes: list[Note] = []
    skipped_ids: list[str] = []

    for note_id in related_note_ids:
        note = notes_by_id.get(note_id)

        if note is None:
            skipped_ids.append(str(note_id))
            continue

        owned_notes.append(note)

    return owned_notes, skipped_ids


def create_note_links(
    db: Session,
    *,
    user_id: uuid.UUID,
    from_note: Note,
    related_note_ids: list[object] | None,
    reason: str = DEFAULT_LINK_REASON,
    confidence: float = DEFAULT_LINK_CONFIDENCE,
) -> NoteLinkCreationResult:
    """
    Create user-approved links from the newly accepted Note to valid
    related Notes.

    The caller controls the transaction. This function flushes changes
    but does not commit them.
    """

    if from_note.user_id != user_id:
        raise ValueError(
            "The source note does not belong to the authenticated user."
        )

    normalized_ids, invalid_ids = (
        normalize_related_note_ids(
            related_note_ids,
        )
    )

    owned_notes, unavailable_ids = (
        get_owned_related_notes(
            db=db,
            user_id=user_id,
            related_note_ids=normalized_ids,
            excluded_note_id=from_note.id,
        )
    )

    cleaned_reason = reason.strip()

    if not cleaned_reason:
        cleaned_reason = DEFAULT_LINK_REASON

    cleaned_reason = cleaned_reason[:500]

    safe_confidence = min(
        max(float(confidence), 0.0),
        1.0,
    )

    created_links: list[NoteLink] = []

    for related_note in owned_notes:
        existing_link = (
            db.query(NoteLink)
            .filter(
                NoteLink.user_id == user_id,
                NoteLink.from_note_id == from_note.id,
                NoteLink.to_note_id == related_note.id,
            )
            .first()
        )

        if existing_link is not None:
            continue

        link = NoteLink(
            user_id=user_id,
            from_note_id=from_note.id,
            to_note_id=related_note.id,
            reason=cleaned_reason,
            confidence=safe_confidence,
            source="brain-dump-ai",
        )

        db.add(link)
        created_links.append(link)

    if created_links:
        db.flush()

    return NoteLinkCreationResult(
        created_links=created_links,
        skipped_note_ids=[
            *invalid_ids,
            *unavailable_ids,
        ],
    )