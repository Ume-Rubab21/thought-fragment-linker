"""
Quick local test for the embedding foundation.

Run from the backend folder:

    python scripts/check_embedding_setup.py
"""

import math
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from models.note_embedding import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
)
from services.embedding_service import (  # noqa: E402
    generate_embedding,
    get_embedding_model,
    prepare_note_text,
)


def vector_norm(
    values: list[float],
) -> float:
    return math.sqrt(
        sum(value * value for value in values)
    )


def main() -> None:
    title = "PostgreSQL semantic search"

    body_html = (
        "<p>Store <strong>MiniLM embeddings</strong> "
        "inside a pgvector column.</p>"
    )

    print("Loading embedding model...")

    first_model = get_embedding_model()
    second_model = get_embedding_model()

    assert first_model is second_model

    prepared_text = prepare_note_text(
        title,
        body_html,
    )

    embedding = generate_embedding(
        prepared_text
    )

    assert len(embedding) == EMBEDDING_DIMENSIONS

    print(
        f"Model: {DEFAULT_EMBEDDING_MODEL}"
    )

    print(
        f"Model loaded once: "
        f"{first_model is second_model}"
    )

    print(
        f"Prepared text: {prepared_text}"
    )

    print(
        f"Dimensions: {len(embedding)}"
    )

    print(
        f"Vector norm: "
        f"{vector_norm(embedding):.6f}"
    )

    print(
        f"First five values: "
        f"{embedding[:5]}"
    )

    print(
        "Embedding foundation check passed."
    )


if __name__ == "__main__":
    main()