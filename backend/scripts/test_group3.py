from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path


BACKEND_DIRECTORY = Path(
    __file__
).resolve().parents[1]

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIRECTORY),
    )


# Import all models so SQLAlchemy can resolve relationships.
import models  # noqa: F401, E402

from database import SessionLocal  # noqa: E402
from models.ai_suggestion import AISuggestion  # noqa: E402
from models.brain_dump import BrainDump  # noqa: E402
from models.guardrail_event import GuardrailEvent  # noqa: E402
from models.user import User  # noqa: E402
from schemas.small_model import SmallModelSuggestion  # noqa: E402
from services.guardrail_event_service import (  # noqa: E402
    GuardrailEventPersistenceError,
    get_guardrail_events_for_brain_dump,
    log_guardrail_event,
)
from services.small_model_guardrails import (  # noqa: E402
    GuardrailCategory,
    GuardrailFailure,
)
from services.small_model_service import (  # noqa: E402
    SmallModelResult,
)
from services.suggestion_service import (  # noqa: E402
    SuggestionPersistenceError,
    get_suggestion_for_brain_dump,
    save_ai_suggestion,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Test Group 3 AI suggestion and guardrail "
            "database persistence."
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


def main() -> int:
    arguments = parse_arguments()
    db = SessionLocal()

    temporary_brain_dump: BrainDump | None = None

    print("=" * 72)
    print("THOUGHTLINKER GROUP 3 DATABASE TESTS")
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

        print(f"User               : {user.email}")
        print(f"User ID            : {user.id}")

        temporary_brain_dump = BrainDump(
            user_id=user.id,
            raw_text=(
                "Temporary Group 3 database test for semantic "
                "search using PostgreSQL, pgvector, embeddings, "
                "and cosine similarity."
            ),
            status="queued",
        )

        db.add(temporary_brain_dump)
        db.flush()

        print(
            f"Temporary BrainDump: {temporary_brain_dump.id}"
        )

        result = SmallModelResult(
            suggestion=SmallModelSuggestion(
                suggested_title=(
                    "Semantic Search Database Test"
                ),
                summary=(
                    "This temporary suggestion verifies that "
                    "validated small-model output can be stored."
                ),
                tags=[
                    "semantic-search",
                    "postgresql",
                    "pgvector",
                ],
                keywords=[
                    "semantic search",
                    "postgresql",
                    "pgvector",
                    "embeddings",
                ],
                related_note_ids=[],
            ),
            model="llama-3.1-8b-instant",
            prompt_tokens=100,
            completion_tokens=40,
            total_tokens=140,
            attempts=1,
            retry_count=0,
        )

        stored_suggestion = save_ai_suggestion(
            db=db,
            user_id=user.id,
            brain_dump_id=temporary_brain_dump.id,
            result=result,
            commit=False,
        )

        if stored_suggestion.id is None:
            print(
                "FAILED: AI suggestion did not receive an ID."
            )
            return 1

        print_pass(
            "Validated AI suggestion was inserted"
        )

        fetched_suggestion = (
            get_suggestion_for_brain_dump(
                db=db,
                user_id=user.id,
                brain_dump_id=temporary_brain_dump.id,
            )
        )

        if fetched_suggestion is None:
            print(
                "FAILED: Stored suggestion could not be queried."
            )
            return 1

        if (
            fetched_suggestion.suggested_title
            != "Semantic Search Database Test"
        ):
            print(
                "FAILED: Queried suggestion contains "
                "unexpected data."
            )
            return 1

        print_pass(
            "AI suggestion can be queried by owner"
        )

        original_suggestion_id = (
            stored_suggestion.id
        )

        updated_result = SmallModelResult(
            suggestion=SmallModelSuggestion(
                suggested_title=(
                    "Updated Semantic Search Test"
                ),
                summary=(
                    "This verifies that saving another result "
                    "updates the existing Brain Dump suggestion."
                ),
                tags=[
                    "semantic-search",
                    "postgresql",
                ],
                keywords=[
                    "semantic search",
                    "postgresql",
                ],
                related_note_ids=[],
            ),
            model="llama-3.1-8b-instant",
            prompt_tokens=110,
            completion_tokens=45,
            total_tokens=155,
            attempts=2,
            retry_count=1,
        )

        updated_suggestion = save_ai_suggestion(
            db=db,
            user_id=user.id,
            brain_dump_id=temporary_brain_dump.id,
            result=updated_result,
            commit=False,
        )

        if updated_suggestion.id != original_suggestion_id:
            print(
                "FAILED: Duplicate suggestion row was created."
            )
            return 1

        if (
            updated_suggestion.suggested_title
            != "Updated Semantic Search Test"
        ):
            print(
                "FAILED: Existing suggestion was not updated."
            )
            return 1

        suggestion_count = (
            db.query(AISuggestion)
            .filter(
                AISuggestion.brain_dump_id
                == temporary_brain_dump.id
            )
            .count()
        )

        if suggestion_count != 1:
            print(
                "FAILED: Expected exactly one suggestion "
                f"but found {suggestion_count}."
            )
            return 1

        print_pass(
            "Repeated saving updates the existing suggestion"
        )

        failure = GuardrailFailure(
            category=(
                GuardrailCategory.TAG_RELEVANCE
            ),
            reason=(
                "The tag 'cooking' is unsupported by "
                "the source Brain Dump."
            ),
        )

        stored_event = log_guardrail_event(
            db=db,
            user_id=user.id,
            brain_dump_id=temporary_brain_dump.id,
            attempt_number=1,
            failure=failure,
            raw_model_response=(
                '{"tags":["cooking"]}'
            ),
            failure_metadata={
                "test": True,
                "retry_allowed": True,
            },
            model_name="llama-3.1-8b-instant",
            prompt_tokens=90,
            completion_tokens=25,
            total_tokens=115,
            commit=False,
        )

        if stored_event.id is None:
            print(
                "FAILED: Guardrail event did not receive an ID."
            )
            return 1

        print_pass(
            "Guardrail rejection was inserted"
        )

        fetched_events = (
            get_guardrail_events_for_brain_dump(
                db=db,
                user_id=user.id,
                brain_dump_id=temporary_brain_dump.id,
            )
        )

        if len(fetched_events) != 1:
            print(
                "FAILED: Expected one guardrail event "
                f"but found {len(fetched_events)}."
            )
            return 1

        if (
            fetched_events[0].failure_category
            != GuardrailCategory.TAG_RELEVANCE.value
        ):
            print(
                "FAILED: Guardrail failure category "
                "was not stored correctly."
            )
            return 1

        print_pass(
            "Guardrail event can be queried by owner"
        )

        other_user_id = uuid.uuid4()

        try:
            save_ai_suggestion(
                db=db,
                user_id=other_user_id,
                brain_dump_id=temporary_brain_dump.id,
                result=result,
                commit=False,
            )

        except SuggestionPersistenceError:
            print_pass(
                "Suggestion ownership protection works"
            )

        else:
            print(
                "FAILED: Another user was allowed to save "
                "a suggestion against this Brain Dump."
            )
            return 1

        try:
            log_guardrail_event(
                db=db,
                user_id=other_user_id,
                brain_dump_id=temporary_brain_dump.id,
                attempt_number=1,
                failure=failure,
                commit=False,
            )

        except GuardrailEventPersistenceError:
            print_pass(
                "Guardrail-event ownership protection works"
            )

        else:
            print(
                "FAILED: Another user was allowed to log "
                "an event against this Brain Dump."
            )
            return 1

        direct_suggestion_count = (
            db.query(AISuggestion)
            .filter(
                AISuggestion.brain_dump_id
                == temporary_brain_dump.id
            )
            .count()
        )

        direct_event_count = (
            db.query(GuardrailEvent)
            .filter(
                GuardrailEvent.brain_dump_id
                == temporary_brain_dump.id
            )
            .count()
        )

        print()
        print("-" * 72)
        print(
            f"Suggestion rows     : "
            f"{direct_suggestion_count}"
        )
        print(
            f"Guardrail rows      : "
            f"{direct_event_count}"
        )
        print("-" * 72)

        print(
            "GROUP 3 DATABASE TESTS PASSED"
        )

        return 0

    except Exception as error:
        print(f"FAILED: {type(error).__name__}: {error}")
        return 1

    finally:
        # Nothing created by this test is permanently stored.
        db.rollback()
        db.close()

        print(
            "Temporary test data rolled back."
        )


if __name__ == "__main__":
    raise SystemExit(main())