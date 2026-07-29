from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIRECTORY = Path(
    __file__
).resolve().parents[1]

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIRECTORY),
    )


from services.small_model_prompt import CandidateNote
from services.small_model_service import (
    SmallModelError,
    generate_small_model_suggestion,
)


def main() -> int:
    source_text = """
I am extending my semantic search implementation.
My existing PostgreSQL vector-search note already explains
pgvector, but I now want to document cosine similarity and
how related notes are ranked.
""".strip()

    candidate_notes = [
        CandidateNote(
            id=10,
            title="PostgreSQL Vector Search",
        ),
        CandidateNote(
            id=20,
            title="React State Management",
        ),
        CandidateNote(
            id=30,
            title="Daily Fitness Routine",
        ),
    ]

    try:
        result = generate_small_model_suggestion(
            raw_text=source_text,
            candidate_notes=candidate_notes,
        )
    except SmallModelError as error:
        print(f"FAILED: {error}")
        return 1

    print(
        result.suggestion.model_dump_json(
            indent=2
        )
    )

    print(f"Attempts: {result.attempts}")
    print(f"Retries : {result.retry_count}")

    allowed_ids = {
        note.id
        for note in candidate_notes
    }

    returned_ids = set(
        result.suggestion.related_note_ids
    )

    if not returned_ids.issubset(
        allowed_ids
    ):
        print(
            "FAILED: Model returned an unknown note ID."
        )
        return 1

    print(
        "PASS: All related note IDs are valid."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())