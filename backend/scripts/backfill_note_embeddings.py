"""
Generate embeddings for existing notes.

Run missing embeddings only:

    python scripts/backfill_note_embeddings.py

Regenerate every note:

    python scripts/backfill_note_embeddings.py --force

Limit the run:

    python scripts/backfill_note_embeddings.py --limit 10
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import or_


BACKEND_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from database import SessionLocal  # noqa: E402
from models.note import Note  # noqa: E402
from models.note_embedding import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    NoteEmbedding,
)
from services.embedding_service import (  # noqa: E402
    upsert_note_embedding,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate MiniLM embeddings for stored notes."
        )
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate embeddings for every note.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of notes to process.",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    db = SessionLocal()

    try:
        query = db.query(Note)

        if not arguments.force:
            query = (
                query.outerjoin(
                    NoteEmbedding,
                    NoteEmbedding.note_id == Note.id,
                )
                .filter(
                    or_(
                        NoteEmbedding.note_id.is_(None),
                        NoteEmbedding.embedding_model
                        != DEFAULT_EMBEDDING_MODEL,
                    )
                )
            )

        query = query.order_by(
            Note.created_at.asc()
        )

        if arguments.limit is not None:
            if arguments.limit < 1:
                raise ValueError(
                    "--limit must be at least 1"
                )

            query = query.limit(arguments.limit)

        notes = query.all()

        if not notes:
            print(
                "No notes require embedding backfill."
            )
            return

        print(
            f"Processing {len(notes)} note(s)..."
        )

        successful = 0
        failed = 0

        for position, note in enumerate(
            notes,
            start=1,
        ):
            print(
                f"[{position}/{len(notes)}] "
                f"Embedding: {note.title}"
            )

            if upsert_note_embedding(db, note):
                successful += 1
            else:
                failed += 1

        print()
        print("Embedding backfill finished.")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

    finally:
        db.close()


if __name__ == "__main__":
    main()