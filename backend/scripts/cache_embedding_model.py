"""
Download and cache the configured embedding model.

Run from the backend directory:

    python scripts/cache_embedding_model.py
"""

import sys
from pathlib import Path


BACKEND_DIRECTORY = (
    Path(__file__).resolve().parents[1]
)

sys.path.insert(
    0,
    str(BACKEND_DIRECTORY),
)


from models.note_embedding import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
)
from services.embedding_service import (  # noqa: E402
    MODEL_CACHE_DIRECTORY,
    get_embedding_model,
)


def main() -> None:
    print(
        "Caching embedding model:"
    )

    print(
        DEFAULT_EMBEDDING_MODEL
    )

    get_embedding_model()

    print(
        f"Model cache directory: "
        f"{MODEL_CACHE_DIRECTORY}"
    )

    print(
        "Embedding model cached successfully."
    )


if __name__ == "__main__":
    main()