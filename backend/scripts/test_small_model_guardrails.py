from __future__ import annotations

import sys
from pathlib import Path

from pydantic import ValidationError


BACKEND_DIRECTORY = Path(
    __file__
).resolve().parents[1]

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIRECTORY),
    )


from schemas.small_model import (
    SmallModelSuggestion,
)
from services.small_model_guardrails import (
    GuardrailValidationError,
    validate_small_model_suggestion,
)


SOURCE_TEXT = """
I am building semantic search for my note application.
The backend uses PostgreSQL with pgvector, while MiniLM
creates embeddings. Related notes are ranked using cosine
similarity.
""".strip()


def print_pass(
    test_name: str,
) -> None:
    print(f"PASS: {test_name}")


def print_fail(
    test_name: str,
    reason: str,
) -> None:
    print(
        f"FAIL: {test_name}\n"
        f"      {reason}"
    )


def test_valid_suggestion() -> bool:
    name = "Valid suggestion passes"

    suggestion = SmallModelSuggestion(
        suggested_title=(
            "Semantic Search for Notes"
        ),
        summary=(
            "The application uses PostgreSQL, pgvector "
            "and MiniLM to find semantically related notes."
        ),
        tags=[
            "PostgreSQL",
            "Semantic Search",
            "MiniLM",
        ],
        keywords=[
            "pgvector",
            "embeddings",
            "cosine similarity",
        ],
        related_note_ids=[10, 20],
    )

    try:
        validated = validate_small_model_suggestion(
            source_text=SOURCE_TEXT,
            suggestion=suggestion,
            allowed_note_ids={10, 20, 30},
        )
    except Exception as error:
        print_fail(name, str(error))
        return False

    assert validated.tags == [
        "postgresql",
        "semantic-search",
        "minilm",
    ]

    assert validated.related_note_ids == [
        10,
        20,
    ]

    print_pass(name)
    return True


def test_duplicate_normalization() -> bool:
    name = "Duplicate tags are normalized"

    suggestion = SmallModelSuggestion(
        suggested_title="PostgreSQL Search",
        summary=(
            "The note describes PostgreSQL semantic "
            "search using vectors."
        ),
        tags=[
            " PostgreSQL ",
            "postgresql",
            "Semantic Search",
            "semantic-search",
        ],
        keywords=[
            "pgvector",
            "PGVECTOR",
            "cosine similarity",
        ],
        related_note_ids=[],
    )

    if suggestion.tags != [
        "postgresql",
        "semantic-search",
    ]:
        print_fail(
            name,
            f"Unexpected tags: {suggestion.tags}",
        )
        return False

    if suggestion.keywords != [
        "pgvector",
        "cosine similarity",
    ]:
        print_fail(
            name,
            (
                "Unexpected keywords: "
                f"{suggestion.keywords}"
            ),
        )
        return False

    print_pass(name)
    return True


def test_too_many_tags() -> bool:
    name = "More than 6 tags are rejected"

    try:
        SmallModelSuggestion(
            suggested_title="Invalid Tags",
            summary=(
                "This response intentionally contains "
                "too many tags for validation."
            ),
            tags=[
                "one",
                "two",
                "three",
                "four",
                "five",
                "six",
                "seven",
            ],
            keywords=["validation"],
        )
    except ValidationError:
        print_pass(name)
        return True

    print_fail(
        name,
        "Seven tags were incorrectly accepted.",
    )
    return False


def test_generic_tag() -> bool:
    name = "Generic vocabulary is rejected"

    suggestion = SmallModelSuggestion(
        suggested_title="Semantic Search",
        summary=(
            "This note describes semantic search using "
            "PostgreSQL and vector embeddings."
        ),
        tags=[
            "postgresql",
            "general",
        ],
        keywords=[
            "semantic search",
            "pgvector",
        ],
    )

    try:
        validate_small_model_suggestion(
            source_text=SOURCE_TEXT,
            suggestion=suggestion,
        )
    except GuardrailValidationError:
        print_pass(name)
        return True

    print_fail(
        name,
        "The generic tag was incorrectly accepted.",
    )
    return False


def test_unrelated_tag() -> bool:
    name = "Unrelated tags are rejected"

    suggestion = SmallModelSuggestion(
        suggested_title="Semantic Search",
        summary=(
            "This note describes semantic search using "
            "PostgreSQL and embeddings."
        ),
        tags=[
            "postgresql",
            "cooking",
        ],
        keywords=[
            "pgvector",
            "embeddings",
        ],
    )

    try:
        validate_small_model_suggestion(
            source_text=SOURCE_TEXT,
            suggestion=suggestion,
        )
    except GuardrailValidationError:
        print_pass(name)
        return True

    print_fail(
        name,
        "The unrelated tag was incorrectly accepted.",
    )
    return False


def test_fake_related_note_id() -> bool:
    name = "Unknown related-note IDs are rejected"

    suggestion = SmallModelSuggestion(
        suggested_title="Related Search Notes",
        summary=(
            "This note describes semantic search with "
            "PostgreSQL and vector embeddings."
        ),
        tags=[
            "postgresql",
            "semantic-search",
        ],
        keywords=[
            "pgvector",
            "embeddings",
        ],
        related_note_ids=[
            10,
            999999,
        ],
    )

    try:
        validate_small_model_suggestion(
            source_text=SOURCE_TEXT,
            suggestion=suggestion,
            allowed_note_ids={
                10,
                20,
                30,
            },
        )
    except GuardrailValidationError:
        print_pass(name)
        return True

    print_fail(
        name,
        "The unknown note ID was incorrectly accepted.",
    )
    return False


def test_ids_without_candidates() -> bool:
    name = (
        "Related IDs without candidate notes are rejected"
    )

    suggestion = SmallModelSuggestion(
        suggested_title="Related Search Notes",
        summary=(
            "This note describes semantic search with "
            "PostgreSQL and vector embeddings."
        ),
        tags=[
            "postgresql",
            "semantic-search",
        ],
        keywords=[
            "pgvector",
            "embeddings",
        ],
        related_note_ids=[10],
    )

    try:
        validate_small_model_suggestion(
            source_text=SOURCE_TEXT,
            suggestion=suggestion,
            allowed_note_ids=None,
        )
    except GuardrailValidationError:
        print_pass(name)
        return True

    print_fail(
        name,
        (
            "Related IDs were accepted without an "
            "allowed candidate list."
        ),
    )
    return False


def main() -> int:
    print("=" * 72)
    print("THOUGHTLINKER GROUP 2 GUARDRAIL TESTS")
    print("=" * 72)

    tests = [
        test_valid_suggestion,
        test_duplicate_normalization,
        test_too_many_tags,
        test_generic_tag,
        test_unrelated_tag,
        test_fake_related_note_id,
        test_ids_without_candidates,
    ]

    results = [
        test()
        for test in tests
    ]

    passed = sum(results)
    total = len(results)

    print()
    print("-" * 72)
    print(f"Passed: {passed}/{total}")
    print("-" * 72)

    if passed != total:
        print("GROUP 2 GUARDRAIL TESTS FAILED")
        return 1

    print("GROUP 2 GUARDRAIL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())