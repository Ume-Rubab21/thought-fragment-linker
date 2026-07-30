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
from models.note_link import NoteLink  # noqa: E402
from models.user import User  # noqa: E402
from schemas.small_model import SmallModelSuggestion  # noqa: E402
from services.note_link_query_service import (  # noqa: E402
    NoteLinkSourceNotFoundError,
    get_related_notes,
)
from services.note_link_service import (  # noqa: E402
    create_note_links,
)
from services.small_model_service import (  # noqa: E402
    SmallModelResult,
)
from services.suggestion_decision_service import (  # noqa: E402
    accept_suggestion,
)
from services.suggestion_service import (  # noqa: E402
    save_ai_suggestion,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Test Group 6 accepted related-note links."
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


def create_note(
    db,
    *,
    user_id: uuid.UUID,
    title: str,
    body_md: str,
) -> Note:
    note = Note(
        user_id=user_id,
        title=title,
        body_md=body_md,
        source="group6-test",
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


def create_brain_dump(
    db,
    *,
    user_id: uuid.UUID,
) -> BrainDump:
    brain_dump = BrainDump(
        user_id=user_id,
        raw_text=(
            "Implement semantic search in ThoughtLinker using "
            "PostgreSQL, pgvector, MiniLM embeddings, and cosine "
            "similarity. Link the accepted note with existing notes "
            "about pgvector and semantic search."
        ),
        status="ready",
        error_message=None,
    )

    db.add(brain_dump)
    db.commit()
    db.refresh(brain_dump)

    return brain_dump


def create_suggestion(
    db,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
    related_note_ids: list[str],
) -> AISuggestion:
    result = SmallModelResult(
        suggestion=SmallModelSuggestion(
            suggested_title=(
                "Implement Semantic Search in ThoughtLinker"
            ),
            summary=(
                "Use PostgreSQL, pgvector, and MiniLM embeddings "
                "to support semantic note retrieval."
            ),
            tags=[
                "semantic-search",
                "postgresql",
                "pgvector",
                "minilm",
            ],
            keywords=[
                "semantic-search",
                "postgresql",
                "pgvector",
                "embeddings",
            ],
            related_note_ids=related_note_ids,
        ),
        model="group6-test-model",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
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


def delete_test_data(
    *,
    brain_dump_ids: list[uuid.UUID],
    note_ids: list[uuid.UUID],
) -> None:
    cleanup_db = SessionLocal()

    try:
        cleanup_db.query(NoteLink).filter(
            NoteLink.from_note_id.in_(note_ids)
            | NoteLink.to_note_id.in_(note_ids)
        ).delete(
            synchronize_session=False
        )

        for brain_dump_id in brain_dump_ids:
            brain_dump = cleanup_db.get(
                BrainDump,
                brain_dump_id,
            )

            if brain_dump is not None:
                cleanup_db.delete(brain_dump)

        cleanup_db.commit()

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
    print("THOUGHTLINKER GROUP 6 RELATED-NOTE LINK TESTS")
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

        related_note_one = create_note(
            db,
            user_id=user.id,
            title="Using pgvector with PostgreSQL",
            body_md=(
                "pgvector stores and searches vector embeddings "
                "inside PostgreSQL."
            ),
        )

        related_note_two = create_note(
            db,
            user_id=user.id,
            title="Semantic Search for Notes",
            body_md=(
                "Semantic search retrieves notes using meaning "
                "instead of exact keyword matching."
            ),
        )

        created_note_ids.extend([
            related_note_one.id,
            related_note_two.id,
        ])

        print_pass(
            "Existing related Notes were created"
        )

        brain_dump = create_brain_dump(
            db,
            user_id=user.id,
        )

        created_brain_dump_ids.append(
            brain_dump.id
        )

        invalid_related_id = str(
            uuid.uuid4()
        )

        # SmallModelSuggestion validates related_note_ids against
        # candidate-note context that this isolated test does not provide.
        # Create the suggestion with an empty list first, then inject the
        # test IDs directly into the persisted model.
        suggestion = create_suggestion(
            db,
            user_id=user.id,
            brain_dump_id=brain_dump.id,
            related_note_ids=[],
        )

        suggestion.related_note_ids = [
            str(related_note_one.id),
            str(related_note_two.id),
            str(related_note_one.id),
            invalid_related_id,
        ]

        db.commit()
        db.refresh(suggestion)

        if suggestion.status != "pending":
            print(
                "FAILED: Suggestion was not pending."
            )
            return 1

        print_pass(
            "Suggestion with related-note IDs was created"
        )

        acceptance = accept_suggestion(
            db=db,
            user_id=user.id,
            brain_dump_id=brain_dump.id,
            title=(
                "Accepted Semantic Search Architecture"
            ),
            tags=[
                "semantic search",
                "postgresql",
                "pgvector",
                "minilm",
            ],
        )

        accepted_note = acceptance.note

        created_note_ids.append(
            accepted_note.id
        )

        if acceptance.suggestion.status != "accepted":
            print(
                "FAILED: Suggestion was not accepted."
            )
            return 1

        print_pass(
            "Suggestion was accepted"
        )

        if len(acceptance.created_links) != 2:
            print(
                "FAILED: Expected 2 links, received "
                f"{len(acceptance.created_links)}."
            )
            return 1

        print_pass(
            "Two valid related-note links were created"
        )

        linked_target_ids = {
            link.to_note_id
            for link in acceptance.created_links
        }

        expected_target_ids = {
            related_note_one.id,
            related_note_two.id,
        }

        if linked_target_ids != expected_target_ids:
            print(
                "FAILED: Created links point to incorrect Notes."
            )
            return 1

        print_pass(
            "Links point to the correct owned Notes"
        )

        if (
            invalid_related_id
            not in acceptance.skipped_related_note_ids
        ):
            print(
                "FAILED: Missing related Note was not reported "
                "as skipped."
            )
            return 1

        print_pass(
            "Missing related Note was skipped safely"
        )

        duplicate_result = create_note_links(
            db=db,
            user_id=user.id,
            from_note=accepted_note,
            related_note_ids=[
                str(related_note_one.id),
                str(related_note_two.id),
            ],
        )

        db.rollback()

        if duplicate_result.created_links:
            print(
                "FAILED: Duplicate links were created."
            )
            return 1

        print_pass(
            "Duplicate related-note links were prevented"
        )

        source_links = get_related_notes(
            db=db,
            user_id=user.id,
            note_id=accepted_note.id,
        )

        if len(source_links) != 2:
            print(
                "FAILED: Accepted Note did not return 2 "
                "related Notes."
            )
            return 1

        if not all(
            item.direction == "outgoing"
            for item in source_links
        ):
            print(
                "FAILED: Source link direction was incorrect."
            )
            return 1

        print_pass(
            "Outgoing related Notes can be queried"
        )

        incoming_links = get_related_notes(
            db=db,
            user_id=user.id,
            note_id=related_note_one.id,
        )

        matching_incoming_links = [
            item
            for item in incoming_links
            if item.note_id == accepted_note.id
            and item.direction == "incoming"
        ]

        if len(matching_incoming_links) != 1:
            print(
                "FAILED: Incoming related Note link was not found."
            )
            return 1

        print_pass(
            "Incoming related Notes can be queried"
        )

        try:
            get_related_notes(
                db=db,
                user_id=uuid.uuid4(),
                note_id=accepted_note.id,
            )

        except NoteLinkSourceNotFoundError:
            print_pass(
                "Related-note ownership protection works"
            )

        else:
            print(
                "FAILED: Another user accessed the related Notes."
            )
            return 1

        stored_link_count = (
            db.query(NoteLink)
            .filter(
                NoteLink.from_note_id
                == accepted_note.id
            )
            .count()
        )

        if stored_link_count != 2:
            print(
                "FAILED: Expected exactly 2 stored NoteLinks."
            )
            return 1

        print_pass(
            "Exactly two NoteLink rows were persisted"
        )

        print()
        print("-" * 72)
        print(f"Accepted Note ID    : {accepted_note.id}")
        print(f"Links created       : {len(acceptance.created_links)}")
        print(
            "Linked Notes        : "
            f"{[item.title for item in source_links]}"
        )
        print(
            "Skipped IDs         : "
            f"{acceptance.skipped_related_note_ids}"
        )
        print(
            "Embedding status    : "
            + (
                "ready"
                if acceptance.embedding_ready
                else "failed"
            )
        )
        print("-" * 72)

        print(
            "GROUP 6 RELATED-NOTE LINK TESTS PASSED"
        )

        return 0

    except Exception as error:
        db.rollback()

        print(
            f"FAILED: {type(error).__name__}: {error}"
        )

        return 1

    finally:
        db.close()

        try:
            delete_test_data(
                brain_dump_ids=created_brain_dump_ids,
                note_ids=created_note_ids,
            )

            print(
                "Temporary Group 6 test data deleted."
            )

        except Exception as cleanup_error:
            print(
                "WARNING: Group 6 cleanup failed: "
                f"{cleanup_error}"
            )


if __name__ == "__main__":
    raise SystemExit(main())