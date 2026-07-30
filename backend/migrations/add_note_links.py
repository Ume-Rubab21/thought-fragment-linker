"""
Create the note_links table.

Run from the backend directory:

    python migrations/add_note_links.py
"""

import sys
from pathlib import Path

from sqlalchemy import text


BACKEND_DIRECTORY = (
    Path(__file__).resolve().parents[1]
)

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIRECTORY),
    )


from database import engine  # noqa: E402


def run() -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS note_links (
            id UUID PRIMARY KEY,

            user_id UUID NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,

            from_note_id UUID NOT NULL
                REFERENCES notes(id)
                ON DELETE CASCADE,

            to_note_id UUID NOT NULL
                REFERENCES notes(id)
                ON DELETE CASCADE,

            reason VARCHAR(500) NOT NULL,

            confidence DOUBLE PRECISION NOT NULL,

            source VARCHAR(40) NOT NULL
                DEFAULT 'brain-dump-ai',

            created_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT uq_note_links_from_to
                UNIQUE (
                    from_note_id,
                    to_note_id
                ),

            CONSTRAINT ck_note_links_no_self_link
                CHECK (
                    from_note_id <> to_note_id
                ),

            CONSTRAINT ck_note_links_confidence_range
                CHECK (
                    confidence >= 0
                    AND confidence <= 1
                )
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_note_links_user_id
        ON note_links (
            user_id
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_note_links_from_note_id
        ON note_links (
            from_note_id
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_note_links_to_note_id
        ON note_links (
            to_note_id
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_note_links_user_from_note
        ON note_links (
            user_id,
            from_note_id
        )
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(
                text(statement)
            )

    print(
        "Note links migration completed successfully."
    )

    print(
        "Created note_links table and indexes."
    )


if __name__ == "__main__":
    run()