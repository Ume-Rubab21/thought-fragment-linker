from __future__ import annotations

import os
import re
import uuid

from sqlalchemy.orm import Session

from models.ai_suggestion import AISuggestion
from models.brain_dump import BrainDump
from services.small_model_persistence import (
    generate_and_store_suggestion,
)


MIN_BRAIN_DUMP_LENGTH = 3
MAX_BRAIN_DUMP_LENGTH = 20_000


class BrainDumpPipelineError(RuntimeError):
    """Raised when Brain Dump processing cannot be completed."""


def get_brain_dump(
    db: Session,
    brain_dump_id: uuid.UUID,
) -> BrainDump:
    """
    Load the Brain Dump that needs to be processed.
    """

    brain_dump = (
        db.query(BrainDump)
        .filter(
            BrainDump.id == brain_dump_id
        )
        .first()
    )

    if brain_dump is None:
        raise BrainDumpPipelineError(
            f"Brain Dump {brain_dump_id} was not found."
        )

    return brain_dump


def mark_as_processing(
    db: Session,
    brain_dump: BrainDump,
) -> None:
    """
    Mark the Brain Dump as currently being processed.
    """

    brain_dump.status = "processing"
    brain_dump.error_message = None

    db.commit()
    db.refresh(brain_dump)


def normalize_brain_dump_text(
    raw_text: str,
) -> str:
    """
    Validate and normalize the submitted Brain Dump text.
    """

    if raw_text is None:
        raise BrainDumpPipelineError(
            "Brain Dump text is missing."
        )

    cleaned_text = raw_text.strip()

    if len(cleaned_text) < MIN_BRAIN_DUMP_LENGTH:
        raise BrainDumpPipelineError(
            "Brain Dump text must contain at least 3 characters."
        )

    if len(cleaned_text) > MAX_BRAIN_DUMP_LENGTH:
        raise BrainDumpPipelineError(
            "Brain Dump text cannot exceed 20,000 characters."
        )

    # Normalize Windows and old Mac line endings.
    cleaned_text = cleaned_text.replace(
        "\r\n",
        "\n",
    ).replace(
        "\r",
        "\n",
    )

    # Replace repeated spaces and tabs with one space.
    cleaned_text = re.sub(
        r"[ \t]+",
        " ",
        cleaned_text,
    )

    # Replace three or more consecutive newlines with two.
    cleaned_text = re.sub(
        r"\n{3,}",
        "\n\n",
        cleaned_text,
    )

    return cleaned_text


def save_normalized_text(
    db: Session,
    brain_dump: BrainDump,
    cleaned_text: str,
) -> None:
    """
    Save normalized text before contacting the AI provider.

    This ensures that the user's submitted content remains stored
    even when Groq or another later processing step fails.
    """

    brain_dump.raw_text = cleaned_text

    db.commit()
    db.refresh(brain_dump)


def mark_as_ready(
    db: Session,
    brain_dump: BrainDump,
) -> None:
    """
    Mark processing as complete after the validated AI suggestion
    has been stored successfully.
    """

    brain_dump.status = "ready"
    brain_dump.error_message = None

    db.commit()
    db.refresh(brain_dump)


def mark_as_failed(
    db: Session,
    brain_dump_id: uuid.UUID,
    error: Exception,
) -> None:
    """
    Mark the Brain Dump as failed without exposing a large internal
    stack trace through the API.
    """

    db.rollback()

    brain_dump = (
        db.query(BrainDump)
        .filter(
            BrainDump.id == brain_dump_id
        )
        .first()
    )

    if brain_dump is None:
        return

    error_message = str(error).strip()

    if not error_message:
        error_message = type(error).__name__

    brain_dump.status = "failed"
    brain_dump.error_message = error_message[:1000]

    db.commit()
    db.refresh(brain_dump)


def run_plain_brain_dump_pipeline(
    db: Session,
    brain_dump_id: uuid.UUID,
) -> tuple[BrainDump, AISuggestion]:
    """
    Execute the Brain Dump processing pipeline with Group 7 routing.

    Flow:
        Load Brain Dump
        → Mark as processing
        → Normalize text
        → Save normalized text
        → Retrieve similar user-owned Notes
        → Evaluate similarity routing
        → Call the selected Groq model
        → Log model usage, latency, cost and route
        → Validate schema
        → Apply guardrails
        → Store validated AI suggestion
        → Mark Brain Dump as ready

    This function does not automatically create a Note, Tag,
    embedding, collection, or note relationship.
    """

    brain_dump = get_brain_dump(
        db=db,
        brain_dump_id=brain_dump_id,
    )

    mark_as_processing(
        db=db,
        brain_dump=brain_dump,
    )

    cleaned_text = normalize_brain_dump_text(
        brain_dump.raw_text
    )

    save_normalized_text(
        db=db,
        brain_dump=brain_dump,
        cleaned_text=cleaned_text,
    )

    fast_mode = os.getenv(
        "BRAIN_DUMP_FAST_MODE",
        "true",
    ).strip().lower() not in {"0", "false", "no", "off"}

    stored_suggestion = generate_and_store_suggestion(
        db=db,
        user_id=brain_dump.user_id,
        brain_dump_id=brain_dump.id,
        raw_text=cleaned_text,
        candidate_notes=[] if fast_mode else None,
    )

    mark_as_ready(
        db=db,
        brain_dump=brain_dump,
    )

    return brain_dump, stored_suggestion

def run_brain_dump_pipeline(
    db: Session,
    brain_dump_id: uuid.UUID,
) -> tuple[BrainDump, AISuggestion]:
    """Run the Day 10 LangGraph workflow with a safe plain-pipeline fallback."""
    use_langgraph = os.getenv(
        "BRAIN_DUMP_USE_LANGGRAPH",
        "true",
    ).strip().lower() not in {"0", "false", "no", "off"}

    if use_langgraph:
        try:
            from services.brain_dump_graph import (
                LangGraphUnavailableError,
                run_brain_dump_graph,
            )
            return run_brain_dump_graph(
                db=db,
                brain_dump_id=brain_dump_id,
            )
        except (ImportError, LangGraphUnavailableError):
            # The roadmap explicitly permits the working plain pipeline
            # when LangGraph is unavailable. Processing/model errors are
            # not swallowed and therefore cannot trigger duplicate calls.
            pass

    return run_plain_brain_dump_pipeline(
        db=db,
        brain_dump_id=brain_dump_id,
    )
