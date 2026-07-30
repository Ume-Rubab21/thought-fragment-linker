from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from models.brain_dump import BrainDump
from models.guardrail_event import GuardrailEvent
from services.small_model_guardrails import GuardrailFailure


class GuardrailEventPersistenceError(RuntimeError):
    """Raised when a guardrail rejection cannot be logged."""


def validate_brain_dump_ownership(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
) -> BrainDump:
    """
    Ensure that the event is attached only to a Brain Dump owned
    by the supplied user.
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
        raise GuardrailEventPersistenceError(
            "Brain Dump was not found for the current user."
        )

    return brain_dump


def log_guardrail_event(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
    attempt_number: int,
    failure: GuardrailFailure,
    raw_model_response: str | None = None,
    failure_metadata: dict[str, Any] | None = None,
    model_name: str | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    commit: bool = True,
) -> GuardrailEvent:
    """
    Store one rejected AI-output attempt.

    This function does not store an AISuggestion and does not modify
    the user's notes.
    """
    if attempt_number < 1:
        raise GuardrailEventPersistenceError(
            "attempt_number must be at least 1."
        )

    token_values = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }

    for field_name, value in token_values.items():
        if value < 0:
            raise GuardrailEventPersistenceError(
                f"{field_name} cannot be negative."
            )

    validate_brain_dump_ownership(
        db=db,
        user_id=user_id,
        brain_dump_id=brain_dump_id,
    )

    event = GuardrailEvent(
        user_id=user_id,
        brain_dump_id=brain_dump_id,
        attempt_number=attempt_number,
        failure_category=failure.category.value,
        failure_reason=failure.reason,
        raw_model_response=raw_model_response,
        failure_metadata=failure_metadata or {},
        model_name=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )

    db.add(event)

    try:
        if commit:
            db.commit()
            db.refresh(event)
        else:
            db.flush()

    except Exception as error:
        db.rollback()

        raise GuardrailEventPersistenceError(
            f"Could not save guardrail event: {error}"
        ) from error

    return event


def get_guardrail_events_for_brain_dump(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
) -> list[GuardrailEvent]:
    """
    Return only events belonging to the current user's Brain Dump.
    """
    return (
        db.query(GuardrailEvent)
        .filter(
            GuardrailEvent.user_id == user_id,
            GuardrailEvent.brain_dump_id == brain_dump_id,
        )
        .order_by(
            GuardrailEvent.attempt_number.asc(),
            GuardrailEvent.created_at.asc(),
        )
        .all()
    )


def get_recent_guardrail_events(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[GuardrailEvent]:
    safe_limit = max(
        1,
        min(limit, 100),
    )

    return (
        db.query(GuardrailEvent)
        .filter(
            GuardrailEvent.user_id == user_id
        )
        .order_by(
            GuardrailEvent.created_at.desc()
        )
        .limit(safe_limit)
        .all()
    )