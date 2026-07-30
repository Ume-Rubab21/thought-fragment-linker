from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.ai_suggestion import AISuggestion
from models.brain_dump import BrainDump


class SuggestionReviewNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class SuggestionReviewCollection:
    rows: list[tuple[AISuggestion, BrainDump]]
    total: int
    pending: int
    accepted: int
    rejected: int


def _base_query(db: Session, user_id: uuid.UUID):
    return (
        db.query(AISuggestion, BrainDump)
        .join(BrainDump, BrainDump.id == AISuggestion.brain_dump_id)
        .filter(
            AISuggestion.user_id == user_id,
            BrainDump.user_id == user_id,
        )
    )


def list_owned_suggestions(
    db: Session,
    *,
    user_id: uuid.UUID,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> SuggestionReviewCollection:
    allowed = {"pending", "accepted", "rejected"}
    normalized_status = status.strip().lower() if status else None

    if normalized_status and normalized_status not in allowed:
        normalized_status = None

    count_rows = (
        db.query(AISuggestion.status, func.count(AISuggestion.id))
        .join(BrainDump, BrainDump.id == AISuggestion.brain_dump_id)
        .filter(
            AISuggestion.user_id == user_id,
            BrainDump.user_id == user_id,
        )
        .group_by(AISuggestion.status)
        .all()
    )
    counts = {str(item_status): int(count) for item_status, count in count_rows}

    query = _base_query(db, user_id)
    if normalized_status:
        query = query.filter(AISuggestion.status == normalized_status)

    safe_limit = max(1, min(int(limit), 100))
    safe_offset = max(0, int(offset))
    rows = (
        query.order_by(AISuggestion.created_at.desc())
        .offset(safe_offset)
        .limit(safe_limit)
        .all()
    )

    return SuggestionReviewCollection(
        rows=rows,
        total=sum(counts.values()),
        pending=counts.get("pending", 0),
        accepted=counts.get("accepted", 0),
        rejected=counts.get("rejected", 0),
    )


def get_owned_suggestion_by_id(
    db: Session,
    *,
    user_id: uuid.UUID,
    suggestion_id: uuid.UUID,
) -> tuple[AISuggestion, BrainDump]:
    row = (
        _base_query(db, user_id)
        .filter(AISuggestion.id == suggestion_id)
        .first()
    )

    if row is None:
        raise SuggestionReviewNotFoundError("AI suggestion was not found.")

    return row
