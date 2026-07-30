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


import models  # noqa: F401, E402

from database import SessionLocal  # noqa: E402
from models.ai_suggestion import AISuggestion  # noqa: E402
from models.brain_dump import BrainDump  # noqa: E402
from models.note import Note  # noqa: E402
from models.note_embedding import NoteEmbedding  # noqa: E402
from models.user import User  # noqa: E402
from schemas.small_model import SmallModelSuggestion  # noqa: E402
from services.suggestion_decision_service import (  # noqa: E402
    SuggestionDecisionConflictError,
    SuggestionDecisionNotFoundError,
    accept_suggestion,
    reject_suggestion,
)
from services.suggestion_service import (  # noqa: E402
    save_ai_suggestion,
)
from services.small_model_service import (  # noqa: E402
    SmallModelResult,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Test Group 5 suggestion accept and reject workflows."
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


def create_test_brain_dump(
    db,
    *,
    user_id: uuid.UUID,
    suffix: str,
) -> BrainDump:
    brain_dump = BrainDump(
        user_id=user_id,
        raw_text=(
            "ThoughtLinker should use PostgreSQL, pgvector, "
            "MiniLM embeddings, and cosine similarity for "
            f"semantic search. Test: {suffix}"
        ),
        status="ready",
        error_message=None,
    )

    db.add(brain_dump)
    db.commit()
    db.refresh(brain_dump)

    return brain_dump


def create_test_suggestion(
    db,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
) -> AISuggestion:
    result = SmallModelResult(
        suggestion=SmallModelSuggestion(
            suggested_title=(
                "Semantic Search with PostgreSQL"
            ),
            summary=(
                "A note about implementing semantic search using "
                "pgvector and MiniLM embeddings."
            ),
            tags=[
                "semantic-search",
                "postgresql",
                "pgvector",
            ],
            keywords=[
                "semantic-search",
                "postgresql",
                "embeddings",
                "cosine-similarity",
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

    return save_ai_suggestion(
        db=db,
        user_id=user_id,
        brain_dump_id=brain_dump_id,
        result=result,
        commit=True,
    )


def delete_test_brain_dumps(
    brain_dump_ids: list[uuid.UUID],
) -> None:
    cleanup_db = SessionLocal()

    try:
        for brain_dump_id in brain_dump_ids:
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


def delete_test_notes(
    note_ids: list[uuid.UUID],
) -> None:
    cleanup_db = SessionLocal()

    try:
        for note_id in note_ids:
            note = cleanup_db.get(
                Note,
                note_id,
            )

            if note is not None:
                cleanup_db.delete(note)

        cleanup_db.commit()

    except Exception:
        cleanup_db.rollback()
        raise

    finally:
        cleanup_db.close()


def main() -> int:
    arguments = parse_arguments()
    db = SessionLocal()

    created_brain_dump_ids: list[uuid.UUID] = []
    created_note_ids: list[uuid.UUID] = []

    print("=" * 72)
    print("THOUGHTLINKER GROUP 5 DECISION TESTS")
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
                f"FAILED: User '{arguments.email}' was not found."
            )
            return 1

        print(f"User email          : {user.email}")
        print(f"User ID             : {user.id}")

        accept_dump = create_test_brain_dump(
            db,
            user_id=user.id,
            suffix="accept",
        )

        created_brain_dump_ids.append(
            accept_dump.id
        )

        accept_ai_suggestion = create_test_suggestion(
            db,
            user_id=user.id,
            brain_dump_id=accept_dump.id,
        )

        if accept_ai_suggestion.status != "pending":
            print(
                "FAILED: New suggestion was not pending."
            )
            return 1

        print_pass(
            "Pending suggestion was created"
        )

        
        acceptance=accept_suggestion(
            db=db,
            user_id=user.id,
            brain_dump_id=accept_dump.id,
            title="Edited Semantic Search Note",
            body_md=(
                    "<p>This note was accepted from an "
                    "AI suggestion.</p>"
                ),
                tags=[
                    "Semantic Search",
                    "PostgreSQL",
                    "semantic search",
                ],
            )
        
        accepted_suggestion = acceptance.suggestion
        note = acceptance.note
        embedding_ready = acceptance.embedding_ready
        
        created_note_ids.append(
            note.id
        )

        if accepted_suggestion.status != "accepted":
            print(
                "FAILED: Suggestion was not marked accepted."
            )
            return 1

        if accepted_suggestion.accepted_note_id != note.id:
            print(
                "FAILED: accepted_note_id was not stored."
            )
            return 1

        print_pass(
            "Suggestion was marked accepted"
        )

        if note.title != "Edited Semantic Search Note":
            print(
                "FAILED: User-edited title was not stored."
            )
            return 1

        if note.source != "brain-dump-ai":
            print(
                "FAILED: Note source was not stored correctly."
            )
            return 1

        print_pass(
            "Accepted suggestion created a real Note"
        )

        note_tag_names = sorted(
            tag.name
            for tag in note.tags
        )

        expected_tag_names = sorted([
            "semantic-search",
            "postgresql",
        ])

        if note_tag_names != expected_tag_names:
            print(
                "FAILED: Tags were not normalized correctly. "
                f"Received: {note_tag_names}"
            )
            return 1

        print_pass(
            "Suggested tags were normalized and attached"
        )

        try:
            accept_suggestion(
                db=db,
                user_id=user.id,
                brain_dump_id=accept_dump.id,
            )

        except SuggestionDecisionConflictError:
            print_pass(
                "Accepted suggestion cannot be accepted twice"
            )

        else:
            print(
                "FAILED: Accepted suggestion was accepted twice."
            )
            return 1

        reject_dump = create_test_brain_dump(
            db,
            user_id=user.id,
            suffix="reject",
        )

        created_brain_dump_ids.append(
            reject_dump.id
        )

        create_test_suggestion(
            db,
            user_id=user.id,
            brain_dump_id=reject_dump.id,
        )

        note_count_before_rejection = (
            db.query(Note)
            .filter(
                Note.user_id == user.id
            )
            .count()
        )

        rejected_suggestion = reject_suggestion(
            db=db,
            user_id=user.id,
            brain_dump_id=reject_dump.id,
            reason="The suggestion needs more detail.",
        )

        note_count_after_rejection = (
            db.query(Note)
            .filter(
                Note.user_id == user.id
            )
            .count()
        )

        if rejected_suggestion.status != "rejected":
            print(
                "FAILED: Suggestion was not marked rejected."
            )
            return 1

        if (
            rejected_suggestion.rejection_reason
            != "The suggestion needs more detail."
        ):
            print(
                "FAILED: Rejection reason was not stored."
            )
            return 1

        print_pass(
            "Suggestion was marked rejected"
        )

        if (
            note_count_after_rejection
            != note_count_before_rejection
        ):
            print(
                "FAILED: Rejecting the suggestion created a Note."
            )
            return 1

        print_pass(
            "Rejecting a suggestion created no Note"
        )

        try:
            reject_suggestion(
                db=db,
                user_id=user.id,
                brain_dump_id=reject_dump.id,
            )

        except SuggestionDecisionConflictError:
            print_pass(
                "Rejected suggestion cannot be decided twice"
            )

        else:
            print(
                "FAILED: Rejected suggestion was decided twice."
            )
            return 1

        try:
            accept_suggestion(
                db=db,
                user_id=uuid.uuid4(),
                brain_dump_id=reject_dump.id,
            )

        except SuggestionDecisionNotFoundError:
            print_pass(
                "Suggestion ownership protection works"
            )

        else:
            print(
                "FAILED: Another user accessed the suggestion."
            )
            return 1

        embedding_row = db.get(
            NoteEmbedding,
            note.id,
        )

        print()
        print("-" * 72)
        print(f"Accepted note ID    : {note.id}")
        print(f"Accepted title      : {note.title}")
        print(f"Tags                : {note_tag_names}")
        print(
            "Embedding status    : "
            + (
                "ready"
                if embedding_ready
                else "failed"
            )
        )
        print(
            "Embedding row       : "
            + (
                "present"
                if embedding_row is not None
                else "missing"
            )
        )
        print(
            "Rejected reason     : "
            f"{rejected_suggestion.rejection_reason}"
        )
        print("-" * 72)

        print(
            "GROUP 5 DECISION TESTS PASSED"
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
            delete_test_brain_dumps(
                created_brain_dump_ids
            )

            delete_test_notes(
                created_note_ids
            )

            print(
                "Temporary Group 5 test data deleted."
            )

        except Exception as cleanup_error:
            print(
                "WARNING: Test cleanup failed: "
                f"{cleanup_error}"
            )


if __name__ == "__main__":
    raise SystemExit(main())