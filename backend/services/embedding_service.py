import logging
from datetime import datetime
from functools import lru_cache
from typing import Optional

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from models.note import Note
from models.note_embedding import (
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
    NoteEmbedding,
)
from utils.rich_text import rich_text_to_plain_text


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load MiniLM once per backend process.

    The first call downloads/loads the model.
    Later calls reuse the cached model instance.
    """
    return SentenceTransformer(
        DEFAULT_EMBEDDING_MODEL,
        device="cpu",
    )


def prepare_note_text(
    title: str,
    body_html: str | None,
) -> str:
    """
    Combine the note title and plain-text body for embedding.
    """
    clean_title = " ".join((title or "").split())
    clean_body = rich_text_to_plain_text(body_html)

    prepared_text = "\n\n".join(
        part
        for part in (clean_title, clean_body)
        if part
    ).strip()

    return prepared_text or "Untitled note"


def generate_embedding(text: str) -> list[float]:
    """
    Generate one normalized 384-dimensional MiniLM vector.
    """
    cleaned_text = " ".join((text or "").split())

    if not cleaned_text:
        raise ValueError(
            "Cannot generate an embedding for empty text"
        )

    model = get_embedding_model()

    vector = model.encode(
        cleaned_text,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    values = vector.astype(float).tolist()

    if len(values) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "Unexpected embedding dimensions: "
            f"expected {EMBEDDING_DIMENSIONS}, "
            f"received {len(values)}"
        )

    return values


def generate_note_embedding(note: Note) -> list[float]:
    """
    Prepare and embed one SQLAlchemy Note object.
    """
    prepared_text = prepare_note_text(
        note.title,
        note.body_md,
    )

    return generate_embedding(prepared_text)


def upsert_note_embedding(
    db: Session,
    note: Note,
) -> bool:
    """
    Create or update the embedding row for a note.

    Returns True when successful.

    Returns False when embedding generation or database
    persistence fails. The note itself remains saved because
    note creation/update is committed before this function runs.
    """
    try:
        vector = generate_note_embedding(note)

        embedding_record = db.get(
            NoteEmbedding,
            note.id,
        )

        now = datetime.utcnow()

        if embedding_record is None:
            embedding_record = NoteEmbedding(
                note_id=note.id,
                embedding=vector,
                embedding_model=DEFAULT_EMBEDDING_MODEL,
                created_at=now,
                updated_at=now,
            )

            db.add(embedding_record)

        else:
            embedding_record.embedding = vector
            embedding_record.embedding_model = (
                DEFAULT_EMBEDDING_MODEL
            )
            embedding_record.updated_at = now

        db.commit()

        logger.info(
            "Embedding saved for note %s using %s",
            note.id,
            DEFAULT_EMBEDDING_MODEL,
        )

        return True

    except Exception:
        db.rollback()

        logger.exception(
            "Embedding generation failed for note %s",
            note.id,
        )

        return False


def ensure_note_embedding(
    db: Session,
    note: Note,
) -> Optional[NoteEmbedding]:
    """
    Return the note's embedding.

    Generate it on demand when it is missing or was created
    with a different embedding model.
    """
    embedding_record = db.get(
        NoteEmbedding,
        note.id,
    )

    if (
        embedding_record is not None
        and embedding_record.embedding_model
        == DEFAULT_EMBEDDING_MODEL
    ):
        return embedding_record

    embedding_created = upsert_note_embedding(
        db,
        note,
    )

    if not embedding_created:
        return None

    return db.get(
        NoteEmbedding,
        note.id,
    )


def create_excerpt(
    body_html: str | None,
    maximum_length: int = 180,
) -> str:
    """
    Create a short plain-text preview for related-note results.
    """
    plain_text = rich_text_to_plain_text(body_html)

    if not plain_text:
        return "No content"

    if len(plain_text) <= maximum_length:
        return plain_text

    return (
        plain_text[: maximum_length - 1]
        .rstrip()
        + "…"
    )


def find_related_notes(
    db: Session,
    note: Note,
    limit: int = 5,
) -> Optional[list[dict]]:
    """
    Find semantically related notes using cosine distance.

    Returns None when the source note's embedding could not
    be generated.

    No similarity threshold is applied here because threshold
    calibration belongs to the next phase.
    """
    source_embedding = ensure_note_embedding(
        db,
        note,
    )

    if source_embedding is None:
        return None

    distance_expression = (
        NoteEmbedding.embedding.cosine_distance(
            source_embedding.embedding
        )
    ).label("distance")

    results = (
        db.query(
            Note,
            NoteEmbedding.embedding_model,
            distance_expression,
        )
        .join(
            NoteEmbedding,
            NoteEmbedding.note_id == Note.id,
        )
        .filter(
            Note.user_id == note.user_id,
            Note.id != note.id,
            NoteEmbedding.embedding_model
            == DEFAULT_EMBEDDING_MODEL,
        )
        .order_by(
            distance_expression.asc(),
            Note.updated_at.desc(),
        )
        .limit(limit)
        .all()
    )

    related_notes = []

    for related_note, model_name, distance in results:
        numeric_distance = float(distance)
        similarity = 1.0 - numeric_distance

        related_notes.append(
            {
                "id": related_note.id,
                "title": related_note.title,
                "excerpt": create_excerpt(
                    related_note.body_md
                ),
                "similarity": round(
                    similarity,
                    6,
                ),
                "distance": round(
                    numeric_distance,
                    6,
                ),
                "embedding_model": model_name,
                "collection_id": (
                    related_note.collection_id
                ),
                "updated_at": (
                    related_note.updated_at
                ),
                "tags": related_note.tags,
            }
        )

    return related_notes