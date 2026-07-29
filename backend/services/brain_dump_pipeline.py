import re
import uuid

from sqlalchemy.orm import Session

from models.brain_dump import BrainDump


MIN_BRAIN_DUMP_LENGTH = 3
MAX_BRAIN_DUMP_LENGTH = 20_000


class BrainDumpPipelineError(Exception):
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
        .filter(BrainDump.id == brain_dump_id)
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


def normalize_brain_dump_text(raw_text: str) -> str:
    """
    Validate and normalize the submitted text.

    This is intentionally deterministic for Day 6.
    AI tagging and routing will be added later.
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

    # Replace repeated spaces and tabs with one space.
    cleaned_text = re.sub(
        r"[ \t]+",
        " ",
        cleaned_text,
    )

    # Replace three or more blank lines with two new lines.
    cleaned_text = re.sub(
        r"\n{3,}",
        "\n\n",
        cleaned_text,
    )

    return cleaned_text


def mark_as_ready(
    db: Session,
    brain_dump: BrainDump,
    cleaned_text: str,
) -> None:
    """
    Save the normalized text and mark processing as complete.
    """

    brain_dump.raw_text = cleaned_text
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
    Mark the Brain Dump as failed without exposing a large
    internal stack trace through the API.
    """

    db.rollback()

    brain_dump = (
        db.query(BrainDump)
        .filter(BrainDump.id == brain_dump_id)
        .first()
    )

    if brain_dump is None:
        return

    brain_dump.status = "failed"
    brain_dump.error_message = str(error)[:1000]

    db.commit()


def run_brain_dump_pipeline(
    db: Session,
    brain_dump_id: uuid.UUID,
) -> BrainDump:
    """
    Execute the Day 6 Brain Dump processing pipeline.

    Current pipeline:
        load
        → processing
        → validate
        → normalize
        → ready

    Later pipeline:
        small model
        → tags and keywords
        → embedding
        → similarity search
        → conditional model routing
        → guardrail validation
        → suggestions
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

    mark_as_ready(
        db=db,
        brain_dump=brain_dump,
        cleaned_text=cleaned_text,
    )

    return brain_dump