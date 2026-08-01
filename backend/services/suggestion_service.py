from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from models.ai_suggestion import AISuggestion
from models.brain_dump import BrainDump
from services.small_model_service import SmallModelResult


class SuggestionPersistenceError(RuntimeError):
    """Raised when a validated AI suggestion cannot be stored."""


def get_owned_brain_dump(
    db: Session,
    brain_dump_id: uuid.UUID,
    user_id: uuid.UUID,
) -> BrainDump:
    """
    Return a Brain Dump only when it belongs to the supplied user.

    This prevents one user from saving AI output against another
    user's Brain Dump.
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
        raise SuggestionPersistenceError(
            "Brain Dump was not found for the current user."
        )

    return brain_dump


def serialize_related_note_ids(
    related_note_ids: Sequence[object],
) -> list[str]:
    """
    Store note IDs safely inside JSONB.

    The project uses UUID note IDs. Group 2 currently uses simple
    candidate IDs in its isolated tests, so converting every value
    to a string keeps persistence compatible with both cases.
    """
    return [
        str(note_id)
        for note_id in related_note_ids
    ]


def save_ai_suggestion(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
    result: SmallModelResult,
    reasoning_tier: str = "small",
    commit: bool = True,
) -> AISuggestion:
    """
    Save validated small-model output.

    Because brain_dump_id has a unique constraint, this function
    updates the existing pending suggestion when one already exists
    instead of inserting a duplicate.
    """
    get_owned_brain_dump(
        db=db,
        brain_dump_id=brain_dump_id,
        user_id=user_id,
    )

    suggestion_data = result.suggestion

    existing = (
        db.query(AISuggestion)
        .filter(
            AISuggestion.brain_dump_id == brain_dump_id,
            AISuggestion.user_id == user_id,
        )
        .first()
    )

    if existing is None:
        stored_suggestion = AISuggestion(
            user_id=user_id,
            brain_dump_id=brain_dump_id,
            suggested_title=(
                suggestion_data.suggested_title
            ),
            summary=suggestion_data.summary,
            suggested_content=suggestion_data.suggested_content,
            tags=list(suggestion_data.tags),
            keywords=list(suggestion_data.keywords),
            related_note_ids=serialize_related_note_ids(
                suggestion_data.related_note_ids
            ),
            model_name=result.model,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            attempts=result.attempts,
            retry_count=result.retry_count,
            reasoning_decision=suggestion_data.reasoning_decision,
            reasoning=suggestion_data.reasoning,
            confidence_score=suggestion_data.confidence_score,
            reasoning_tier=reasoning_tier,
            status="pending",
        )

        db.add(stored_suggestion)

    else:
        stored_suggestion = existing

        stored_suggestion.suggested_title = (
            suggestion_data.suggested_title
        )
        stored_suggestion.summary = suggestion_data.summary
        stored_suggestion.suggested_content = suggestion_data.suggested_content
        stored_suggestion.tags = list(
            suggestion_data.tags
        )
        stored_suggestion.keywords = list(
            suggestion_data.keywords
        )
        stored_suggestion.related_note_ids = (
            serialize_related_note_ids(
                suggestion_data.related_note_ids
            )
        )
        stored_suggestion.model_name = result.model
        stored_suggestion.prompt_tokens = (
            result.prompt_tokens
        )
        stored_suggestion.completion_tokens = (
            result.completion_tokens
        )
        stored_suggestion.total_tokens = (
            result.total_tokens
        )
        stored_suggestion.attempts = result.attempts
        stored_suggestion.retry_count = (
            result.retry_count
        )
        stored_suggestion.reasoning_decision = suggestion_data.reasoning_decision
        stored_suggestion.reasoning = suggestion_data.reasoning
        stored_suggestion.confidence_score = suggestion_data.confidence_score
        stored_suggestion.reasoning_tier = reasoning_tier
        stored_suggestion.status = "pending"

    try:
        if commit:
            db.commit()
            db.refresh(stored_suggestion)
        else:
            db.flush()

    except Exception as error:
        db.rollback()

        raise SuggestionPersistenceError(
            f"Could not save AI suggestion: {error}"
        ) from error

    return stored_suggestion


def get_suggestion_for_brain_dump(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
) -> AISuggestion | None:
    """
    Retrieve a suggestion while preserving user ownership.
    """
    return (
        db.query(AISuggestion)
        .filter(
            AISuggestion.user_id == user_id,
            AISuggestion.brain_dump_id == brain_dump_id,
        )
        .first()
    )


def get_pending_suggestions(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[AISuggestion]:
    safe_limit = max(
        1,
        min(limit, 100),
    )

    return (
        db.query(AISuggestion)
        .filter(
            AISuggestion.user_id == user_id,
            AISuggestion.status == "pending",
        )
        .order_by(
            AISuggestion.created_at.desc()
        )
        .limit(safe_limit)
        .all()
    )


def update_suggestion_status(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
    status: str,
) -> AISuggestion:
    allowed_statuses = {
        "pending",
        "accepted",
        "rejected",
        "applied",
    }

    if status not in allowed_statuses:
        raise SuggestionPersistenceError(
            f"Unsupported suggestion status: {status}"
        )

    suggestion = get_suggestion_for_brain_dump(
        db=db,
        user_id=user_id,
        brain_dump_id=brain_dump_id,
    )

    if suggestion is None:
        raise SuggestionPersistenceError(
            "AI suggestion was not found for the current user."
        )

    suggestion.status = status

    try:
        db.commit()
        db.refresh(suggestion)

    except Exception as error:
        db.rollback()

        raise SuggestionPersistenceError(
            f"Could not update suggestion status: {error}"
        ) from error

    return suggestion