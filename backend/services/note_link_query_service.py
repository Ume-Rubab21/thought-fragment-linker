from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.note import Note
from models.note_link import NoteLink


class NoteLinkQueryError(RuntimeError):
    """Base error for related-note queries."""


class NoteLinkSourceNotFoundError(
    NoteLinkQueryError
):
    """Raised when the requested source Note is unavailable."""


@dataclass(frozen=True)
class RelatedNoteResult:
    link_id: uuid.UUID
    note_id: uuid.UUID
    title: str
    reason: str
    confidence: float
    source: str
    direction: str


def get_owned_note(
    db: Session,
    *,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
) -> Note:
    """
    Return a Note only when it belongs to the authenticated user.
    """

    note = (
        db.query(Note)
        .filter(
            Note.id == note_id,
            Note.user_id == user_id,
        )
        .first()
    )

    if note is None:
        raise NoteLinkSourceNotFoundError(
            "Note was not found."
        )

    return note


def get_related_notes(
    db: Session,
    *,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
) -> list[RelatedNoteResult]:
    """
    Return all approved incoming and outgoing links for a Note.

    Every returned Note and NoteLink must belong to the authenticated
    user.
    """

    get_owned_note(
        db=db,
        user_id=user_id,
        note_id=note_id,
    )

    links = (
        db.query(NoteLink)
        .filter(
            NoteLink.user_id == user_id,
            or_(
                NoteLink.from_note_id == note_id,
                NoteLink.to_note_id == note_id,
            ),
        )
        .order_by(
            NoteLink.confidence.desc(),
            NoteLink.created_at.desc(),
        )
        .all()
    )

    results: list[RelatedNoteResult] = []

    for link in links:
        if link.from_note_id == note_id:
            related_note_id = link.to_note_id
            direction = "outgoing"
        else:
            related_note_id = link.from_note_id
            direction = "incoming"

        related_note = (
            db.query(Note)
            .filter(
                Note.id == related_note_id,
                Note.user_id == user_id,
            )
            .first()
        )

        if related_note is None:
            continue

        results.append(
            RelatedNoteResult(
                link_id=link.id,
                note_id=related_note.id,
                title=related_note.title,
                reason=link.reason,
                confidence=link.confidence,
                source=link.source,
                direction=direction,
            )
        )

    return results