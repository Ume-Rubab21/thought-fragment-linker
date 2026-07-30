from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path


BACKEND_DIRECTORY = (
    Path(__file__).resolve().parents[1]
)

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIRECTORY),
    )


# Import model registrations before using SQLAlchemy relationships.
import models  # noqa: F401, E402

from database import SessionLocal  # noqa: E402
from models.ai_suggestion import AISuggestion  # noqa: E402
from models.brain_dump import BrainDump  # noqa: E402
from models.guardrail_event import GuardrailEvent  # noqa: E402
from models.user import User  # noqa: E402
from services.brain_dump_pipeline import (  # noqa: E402
    normalize_brain_dump_text,
    run_brain_dump_pipeline,
)
from services.brain_dump_query_service import (  # noqa: E402
    BrainDumpNotFoundError,
    BrainDumpSuggestionNotReadyError,
    get_brain_dump_suggestion,
)
from services.brain_dump_service import (  # noqa: E402
    create_brain_dump,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Test the Group 4 Brain Dump and "
            "small-model integration."
        )
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Email address of an existing ThoughtLinker user.",
    )

    return parser.parse_args()


def print_pass(message: str) -> None:
    print(f"PASS: {message}")


def delete_test_brain_dump(
    brain_dump_id: uuid.UUID | None,
) -> None:
    """
    Remove committed test data.

    Deleting the Brain Dump also removes its suggestion and guardrail
    events through the database ON DELETE CASCADE constraints.
    """

    if brain_dump_id is None:
        return

    cleanup_db = SessionLocal()

    try:
        brain_dump = (
            cleanup_db.query(BrainDump)
            .filter(
                BrainDump.id == brain_dump_id
            )
            .first()
        )

        if brain_dump is not None:
            cleanup_db.delete(brain_dump)
            cleanup_db.commit()

    except Exception:
        cleanup_db.rollback()
        raise

    finally:
        cleanup_db.close()


def main() -> int:
    arguments = parse_arguments()

    db = SessionLocal()
    test_brain_dump_id: uuid.UUID | None = None

    print("=" * 72)
    print("THOUGHTLINKER GROUP 4 INTEGRATION TESTS")
    print("=" * 72)

    try:
        user = (
            db.query(User)
            .filter(
                User.email == arguments.email
            )
            .first()
        )

        if user is None:
            print(
                "FAILED: No user exists with email "
                f"'{arguments.email}'."
            )
            return 1

        print(f"User email          : {user.email}")
        print(f"User ID             : {user.id}")

        original_text = (
            "  PostgreSQL    supports vector search.\r\n"
            "\r\n"
            "\r\n"
            "I am building semantic search for ThoughtLinker "
            "using pgvector, MiniLM embeddings, and cosine "
            "similarity. The system should suggest useful tags "
            "and keywords for this Brain Dump.  "
        )

        normalized_text = normalize_brain_dump_text(
            original_text
        )

        if "    " in normalized_text:
            print(
                "FAILED: Repeated spaces were not normalized."
            )
            return 1

        if "\r" in normalized_text:
            print(
                "FAILED: Line endings were not normalized."
            )
            return 1

        print_pass(
            "Brain Dump text normalization works"
        )

        brain_dump = create_brain_dump(
            db=db,
            user_id=user.id,
            raw_text=original_text,
        )

        test_brain_dump_id = brain_dump.id

        if brain_dump.status != "queued":
            print(
                "FAILED: New Brain Dump did not receive "
                "queued status."
            )
            return 1

        print(
            f"Test Brain Dump ID   : {brain_dump.id}"
        )

        print_pass(
            "Brain Dump was stored before AI processing"
        )

        try:
            get_brain_dump_suggestion(
                db=db,
                user_id=user.id,
                brain_dump_id=brain_dump.id,
            )

        except BrainDumpSuggestionNotReadyError:
            print_pass(
                "Suggestion is blocked while status is queued"
            )

        else:
            print(
                "FAILED: Queued Brain Dump returned "
                "a suggestion."
            )
            return 1

        processed_brain_dump, stored_suggestion = (
            run_brain_dump_pipeline(
                db=db,
                brain_dump_id=brain_dump.id,
            )
        )

        if processed_brain_dump.status != "ready":
            print(
                "FAILED: Expected ready status but received "
                f"'{processed_brain_dump.status}'."
            )
            return 1

        print_pass(
            "Brain Dump pipeline reached ready status"
        )

        if stored_suggestion.id is None:
            print(
                "FAILED: AI suggestion did not receive an ID."
            )
            return 1

        print_pass(
            "Validated AI suggestion was persisted"
        )

        if (
            processed_brain_dump.raw_text
            != normalized_text
        ):
            print(
                "FAILED: Normalized text was not stored."
            )
            return 1

        print_pass(
            "Normalized Brain Dump text was persisted"
        )

        queried_brain_dump, queried_suggestion = (
            get_brain_dump_suggestion(
                db=db,
                user_id=user.id,
                brain_dump_id=brain_dump.id,
            )
        )

        if queried_brain_dump.id != brain_dump.id:
            print(
                "FAILED: Query service returned "
                "the wrong Brain Dump."
            )
            return 1

        if (
            queried_suggestion.id
            != stored_suggestion.id
        ):
            print(
                "FAILED: Query service returned "
                "the wrong suggestion."
            )
            return 1

        print_pass(
            "Suggestion can be queried by its owner"
        )

        other_user_id = uuid.uuid4()

        try:
            get_brain_dump_suggestion(
                db=db,
                user_id=other_user_id,
                brain_dump_id=brain_dump.id,
            )

        except BrainDumpNotFoundError:
            print_pass(
                "Suggestion ownership protection works"
            )

        else:
            print(
                "FAILED: Another user could access "
                "the Brain Dump suggestion."
            )
            return 1

        suggestion_count = (
            db.query(AISuggestion)
            .filter(
                AISuggestion.brain_dump_id
                == brain_dump.id
            )
            .count()
        )

        if suggestion_count != 1:
            print(
                "FAILED: Expected one AI suggestion, "
                f"but found {suggestion_count}."
            )
            return 1

        print_pass(
            "Exactly one AI suggestion was stored"
        )

        guardrail_count = (
            db.query(GuardrailEvent)
            .filter(
                GuardrailEvent.brain_dump_id
                == brain_dump.id
            )
            .count()
        )

        print()
        print("-" * 72)
        print(
            f"Brain Dump status   : "
            f"{processed_brain_dump.status}"
        )
        print(
            f"Suggestion ID       : "
            f"{stored_suggestion.id}"
        )
        print(
            f"Suggested title     : "
            f"{stored_suggestion.suggested_title}"
        )
        print(
            f"Tags                : "
            f"{stored_suggestion.tags}"
        )
        print(
            f"Keywords            : "
            f"{stored_suggestion.keywords}"
        )
        print(
            f"Model               : "
            f"{stored_suggestion.model_name}"
        )
        print(
            f"Attempts            : "
            f"{stored_suggestion.attempts}"
        )
        print(
            f"Retries             : "
            f"{stored_suggestion.retry_count}"
        )
        print(
            f"Guardrail events    : "
            f"{guardrail_count}"
        )
        print("-" * 72)

        print(
            "GROUP 4 INTEGRATION TESTS PASSED"
        )

        return 0

    except Exception as error:
        print(
            f"FAILED: {type(error).__name__}: {error}"
        )
        return 1

    finally:
        db.close()

        try:
            delete_test_brain_dump(
                test_brain_dump_id
            )

            if test_brain_dump_id is not None:
                print(
                    "Temporary Group 4 test data deleted."
                )

        except Exception as cleanup_error:
            print(
                "WARNING: Temporary test data could not "
                f"be deleted: {cleanup_error}"
            )


if __name__ == "__main__":
    raise SystemExit(main())