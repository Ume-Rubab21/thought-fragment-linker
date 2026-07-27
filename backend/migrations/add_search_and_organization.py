
import sys
from pathlib import Path

from sqlalchemy import text


BACKEND_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from database import Base, engine  # noqa: E402
import models  # noqa: E402,F401


SEARCH_VECTOR_EXPRESSION = """
setweight(
    to_tsvector(
        'english'::regconfig,
        coalesce(title, '')
    ),
    'A'
) ||
setweight(
    to_tsvector(
        'english'::regconfig,
        regexp_replace(
            coalesce(body_md, ''),
            '<[^>]+>',
            ' ',
            'g'
        )
    ),
    'B'
)
"""


def run() -> None:
    # Creates missing tables for a new database.
    Base.metadata.create_all(
        bind=engine,
    )

    statements = [
        f"""
        ALTER TABLE notes
        ADD COLUMN IF NOT EXISTS search_vector tsvector
        GENERATED ALWAYS AS (
            {SEARCH_VECTOR_EXPRESSION}
        ) STORED
        """,

        """
        CREATE INDEX IF NOT EXISTS ix_notes_search_vector
        ON notes USING GIN (search_vector)
        """,

        """
        CREATE INDEX IF NOT EXISTS ix_notes_user_updated_at
        ON notes (user_id, updated_at DESC)
        """,

        """
        CREATE INDEX IF NOT EXISTS ix_notes_user_collection
        ON notes (user_id, collection_id)
        """,

        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        uq_collections_user_lower_name
        ON collections (
            user_id,
            lower(name)
        )
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(
                text(statement),
            )

    print(
        "Day 4 migration completed successfully."
    )

    print(
        "Verified search_vector, GIN search index, "
        "filter indexes, and collection uniqueness."
    )


if __name__ == "__main__":
    run()