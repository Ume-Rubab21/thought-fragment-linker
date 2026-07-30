from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.deps import get_current_user
from database import get_db
from models.ai_suggestion import AISuggestion
from models.brain_dump import BrainDump
from models.note import Note
from models.note_embedding import DEFAULT_EMBEDDING_MODEL, NoteEmbedding
from models.user import User
from schemas.ai_suggestion_review import (
    AISuggestionDetailResponse,
    AISuggestionListItem,
    AISuggestionListResponse,
    RelatedNoteReviewItem,
)
from services.embedding_service import create_excerpt, generate_embedding
from services.suggestion_review_service import (
    SuggestionReviewNotFoundError,
    get_owned_suggestion_by_id,
    list_owned_suggestions,
)


router = APIRouter(prefix="/suggestions", tags=["suggestions"])


def _preview(value: str, limit: int = 180) -> str:
    cleaned = " ".join((value or "").split())
    return cleaned if len(cleaned) <= limit else f"{cleaned[: limit - 1]}…"


def _list_item(suggestion: AISuggestion, brain_dump: BrainDump) -> AISuggestionListItem:
    return AISuggestionListItem(
        suggestion_id=suggestion.id,
        brain_dump_id=suggestion.brain_dump_id,
        suggested_title=suggestion.suggested_title,
        summary=suggestion.summary,
        tags=list(suggestion.tags or []),
        keywords=list(suggestion.keywords or []),
        related_note_ids=[str(value) for value in (suggestion.related_note_ids or [])],
        status=suggestion.status,
        model_name=suggestion.model_name,
        total_tokens=suggestion.total_tokens,
        accepted_note_id=suggestion.accepted_note_id,
        rejection_reason=suggestion.rejection_reason,
        decided_at=suggestion.decided_at,
        created_at=suggestion.created_at,
        updated_at=suggestion.updated_at,
        brain_dump_preview=_preview(brain_dump.raw_text),
    )


def _related_notes(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_text: str,
    related_note_ids: list[str] | list[uuid.UUID],
) -> list[RelatedNoteReviewItem]:
    """Load owned related notes with live cosine-similarity scores.

    The score compares the original Brain Dump embedding with each note
    embedding, so the percentage explains why each note was suggested.
    """

    ordered_ids: list[uuid.UUID] = []
    for value in related_note_ids or []:
        try:
            ordered_ids.append(
                value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
            )
        except (TypeError, ValueError):
            continue

    if not ordered_ids:
        return []

    try:
        query_embedding = generate_embedding(brain_dump_text)
        distance_expression = (
            NoteEmbedding.embedding.cosine_distance(query_embedding)
        ).label("distance")

        rows = (
            db.query(Note, distance_expression)
            .join(NoteEmbedding, NoteEmbedding.note_id == Note.id)
            .filter(
                Note.user_id == user_id,
                Note.id.in_(ordered_ids),
                NoteEmbedding.embedding_model == DEFAULT_EMBEDDING_MODEL,
            )
            .all()
        )
    except Exception:
        # Do not fail the full suggestion page if scoring is temporarily
        # unavailable. Return the actual notes with a neutral score.
        notes = (
            db.query(Note)
            .filter(Note.user_id == user_id, Note.id.in_(ordered_ids))
            .all()
        )
        by_id = {note.id: (note, 1.0) for note in notes}
    else:
        by_id = {note.id: (note, float(distance)) for note, distance in rows}

    items: list[RelatedNoteReviewItem] = []
    for note_id in ordered_ids:
        row = by_id.get(note_id)
        if row is None:
            continue

        note, distance = row
        similarity = max(0.0, min(1.0, 1.0 - float(distance)))
        rounded_similarity = round(similarity, 6)

        items.append(
            RelatedNoteReviewItem(
                note_id=note.id,
                title=note.title,
                preview=create_excerpt(note.body_md, maximum_length=150),
                similarity_score=rounded_similarity,
                similarity_percentage=round(rounded_similarity * 100),
                created_at=note.created_at,
            )
        )

    # Highest-confidence matches first.
    return sorted(
        items,
        key=lambda item: item.similarity_score,
        reverse=True,
    )


@router.get("", response_model=AISuggestionListResponse)
def list_suggestions(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = list_owned_suggestions(
        db,
        user_id=current_user.id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return AISuggestionListResponse(
        items=[_list_item(suggestion, brain_dump) for suggestion, brain_dump in collection.rows],
        total=collection.total,
        pending=collection.pending,
        accepted=collection.accepted,
        rejected=collection.rejected,
    )


@router.get("/{suggestion_id}", response_model=AISuggestionDetailResponse)
def get_suggestion(
    suggestion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        suggestion, brain_dump = get_owned_suggestion_by_id(
            db,
            user_id=current_user.id,
            suggestion_id=suggestion_id,
        )
    except SuggestionReviewNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    base = _list_item(suggestion, brain_dump).model_dump()
    return AISuggestionDetailResponse(
        **base,
        brain_dump_text=brain_dump.raw_text,
        prompt_tokens=suggestion.prompt_tokens,
        completion_tokens=suggestion.completion_tokens,
        attempts=suggestion.attempts,
        retry_count=suggestion.retry_count,
        related_notes=_related_notes(
            db,
            user_id=current_user.id,
            brain_dump_text=brain_dump.raw_text,
            related_note_ids=list(suggestion.related_note_ids or []),
        ),
    )
