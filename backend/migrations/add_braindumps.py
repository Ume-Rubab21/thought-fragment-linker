"""
Create the braindumps table.

Run from the backend folder:

    python migrations/add_braindumps.py
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
        CREATE TABLE IF NOT EXISTS braindumps (
            id UUID PRIMARY KEY,

            user_id UUID NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,

            raw_text TEXT NOT NULL,

            status VARCHAR(20) NOT NULL
                DEFAULT 'queued',

            error_message TEXT NULL,

            created_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT ck_braindumps_status
                CHECK (
                    status IN (
                        'queued',
                        'processing',
                        'ready',
                        'failed'
                    )
                )
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_braindumps_user_id
        ON braindumps (user_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_braindumps_status
        ON braindumps (status)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_braindumps_user_created_at
        ON braindumps (user_id, created_at DESC)
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(
                text(statement)
            )

    print(
        "Braindumps migration completed successfully."
    )

    print(
        "Created braindumps table with "
        "queued, processing, ready and failed statuses."
    )


if __name__ == "__main__":
    run()