"""
Add human-decision fields to ai_suggestions.

Run from the backend directory:

    python migrations/add_accepted_note_to_ai_suggestions.py
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
        ALTER TABLE ai_suggestions
        ADD COLUMN IF NOT EXISTS
            accepted_note_id UUID NULL
        """,

        """
        ALTER TABLE ai_suggestions
        ADD COLUMN IF NOT EXISTS
            rejection_reason VARCHAR(500) NULL
        """,

        """
        ALTER TABLE ai_suggestions
        ADD COLUMN IF NOT EXISTS
            decided_at TIMESTAMP WITHOUT TIME ZONE NULL
        """,

        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname =
                    'fk_ai_suggestions_accepted_note'
            ) THEN
                ALTER TABLE ai_suggestions
                ADD CONSTRAINT
                    fk_ai_suggestions_accepted_note
                FOREIGN KEY (accepted_note_id)
                REFERENCES notes(id)
                ON DELETE SET NULL;
            END IF;
        END
        $$
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_ai_suggestions_accepted_note_id
        ON ai_suggestions (
            accepted_note_id
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_ai_suggestions_user_status
        ON ai_suggestions (
            user_id,
            status
        )
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(
                text(statement)
            )

    print(
        "AI suggestion decision migration "
        "completed successfully."
    )

    print(
        "Added accepted_note_id, rejection_reason, "
        "and decided_at."
    )


if __name__ == "__main__":
    run()