from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from models.note import Note
from models.note_embedding import (
    DEFAULT_EMBEDDING_MODEL,
    NoteEmbedding,
)
from services.embedding_service import (
    create_excerpt,
    generate_embedding,
)
from services.small_model_prompt import CandidateNote


DEFAULT_CANDIDATE_LIMIT = 5


class BrainDumpSimilarityError(RuntimeError):
    """Raised when Brain Dump similarity retrieval fails."""


@dataclass(frozen=True)
class BrainDumpCandidateResult:
    candidate_notes: list[CandidateNote]
    similarity_scores: list[float]


def find_brain_dump_candidates(
    db: Session,
    *,
    user_id: uuid.UUID,
    raw_text: str,
    limit: int = DEFAULT_CANDIDATE_LIMIT,
) -> BrainDumpCandidateResult:
    """
    Embed one Brain Dump and retrieve the current user's nearest Notes.

    Only Notes owned by the supplied user are eligible candidates.
    """

    cleaned_text = raw_text.strip()

    if not cleaned_text:
        raise BrainDumpSimilarityError(
            "Brain Dump text cannot be empty."
        )

    safe_limit = max(1, min(int(limit), 20))

    try:
        query_embedding = generate_embedding(cleaned_text)

        distance_expression = (
            NoteEmbedding.embedding.cosine_distance(
                query_embedding
            )
        ).label("distance")

        rows = (
            db.query(
                Note,
                distance_expression,
            )
            .join(
                NoteEmbedding,
                NoteEmbedding.note_id == Note.id,
            )
            .filter(
                Note.user_id == user_id,
                NoteEmbedding.embedding_model
                == DEFAULT_EMBEDDING_MODEL,
            )
            .order_by(
                distance_expression.asc(),
                Note.updated_at.desc(),
            )
            .limit(safe_limit)
            .all()
        )

    except Exception as error:
        raise BrainDumpSimilarityError(
            f"Could not retrieve similar Notes: {error}"
        ) from error

    candidate_notes: list[CandidateNote] = []
    similarity_scores: list[float] = []

    for note, distance in rows:
        numeric_distance = float(distance)
        similarity = max(
            0.0,
            min(1.0, 1.0 - numeric_distance),
        )

        candidate_notes.append(
            CandidateNote(
                id=note.id,
                title=note.title,
                excerpt=create_excerpt(note.body_md),
                similarity=round(similarity, 6),
            )
        )
        similarity_scores.append(
            round(similarity, 6)
        )

    return BrainDumpCandidateResult(
        candidate_notes=candidate_notes,
        similarity_scores=similarity_scores,
    )
