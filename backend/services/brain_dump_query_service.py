from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from models.ai_suggestion import AISuggestion
from models.brain_dump import BrainDump


class BrainDumpQueryError(RuntimeError):
    """Base exception for Brain Dump query operations."""


class BrainDumpNotFoundError(BrainDumpQueryError):
    """Raised when the Brain Dump does not belong to the user."""


class BrainDumpSuggestionNotReadyError(BrainDumpQueryError):
    """Raised when processing has not completed successfully."""


class BrainDumpSuggestionNotFoundError(BrainDumpQueryError):
    """Raised when no stored AI suggestion exists."""


def get_owned_brain_dump(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
) -> BrainDump:
    """
    Retrieve a Brain Dump only when it belongs to the current user.
    """

    brain_dump = (
        db.query(BrainDump)
        .filter(
            BrainDump.id == brain_dump_id,
            BrainDump.user_id == user_id,
        )
        .first()
    )

    if brain_dump is None:
        raise BrainDumpNotFoundError(
            "Brain dump not found."
        )

    return brain_dump


def get_brain_dump_suggestion(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
) -> tuple[BrainDump, AISuggestion]:
    """
    Retrieve the validated AI suggestion for a user's Brain Dump.

    The suggestion can be returned only after the Brain Dump reaches
    the ready status.
    """

    brain_dump = get_owned_brain_dump(
        db=db,
        user_id=user_id,
        brain_dump_id=brain_dump_id,
    )

    if brain_dump.status in {
        "queued",
        "processing",
    }:
        raise BrainDumpSuggestionNotReadyError(
            "Brain dump processing is not complete yet."
        )

    if brain_dump.status == "failed":
        failure_reason = (
            brain_dump.error_message
            or "Brain dump processing failed."
        )

        raise BrainDumpSuggestionNotReadyError(
            failure_reason
        )

    suggestion = (
        db.query(AISuggestion)
        .filter(
            AISuggestion.user_id == user_id,
            AISuggestion.brain_dump_id == brain_dump_id,
        )
        .first()
    )

    if suggestion is None:
        raise BrainDumpSuggestionNotFoundError(
            "AI suggestion was not found for this brain dump."
        )

    return brain_dump, suggestion