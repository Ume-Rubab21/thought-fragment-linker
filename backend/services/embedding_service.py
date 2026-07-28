from functools import lru_cache

from sentence_transformers import SentenceTransformer

from models.note_embedding import (
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
)
from utils.rich_text import rich_text_to_plain_text


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load MiniLM once per backend process and reuse it.

    The first call downloads and loads the model.
    Later calls reuse the same object.
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
    Combine a clean title and rich-text body before embedding.
    """
    clean_title = " ".join(
        (title or "").split()
    )

    clean_body = rich_text_to_plain_text(
        body_html
    )

    prepared = "\n\n".join(
        part
        for part in (
            clean_title,
            clean_body,
        )
        if part
    ).strip()

    return prepared or "Untitled note"


def generate_embedding(
    text: str,
) -> list[float]:
    """
    Generate one normalized 384-dimensional embedding.
    """
    cleaned_text = " ".join(
        (text or "").split()
    )

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
            "Unexpected embedding size: "
            f"expected {EMBEDDING_DIMENSIONS}, "
            f"got {len(values)}"
        )

    return values