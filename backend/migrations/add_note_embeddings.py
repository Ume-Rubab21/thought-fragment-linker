"""
Create the pgvector-backed note embeddings table.

Run from the backend folder:

    python migrations/add_note_embeddings.py
"""

import sys
from pathlib import Path

from sqlalchemy import text


BACKEND_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from database import engine  # noqa: E402


def run() -> None:
    statements = [
        """
        CREATE EXTENSION IF NOT EXISTS vector
        """,

        """
        CREATE TABLE IF NOT EXISTS note_embeddings (
            note_id UUID PRIMARY KEY
                REFERENCES notes(id)
                ON DELETE CASCADE,

            embedding VECTOR(384) NOT NULL,

            embedding_model VARCHAR(120) NOT NULL,

            created_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_note_embeddings_model
        ON note_embeddings (embedding_model)
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(
                text(statement)
            )

    print(
        "Note embeddings migration completed successfully."
    )

    print(
        "Created vector(384) storage "
        "for MiniLM embeddings."
    )


if __name__ == "__main__":
    run()