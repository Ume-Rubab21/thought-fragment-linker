import html
import re
import uuid

from sqlalchemy.orm import Session

from models.brain_dump import BrainDump
from models.note import Note
from services.embedding_service import upsert_note_embedding


MIN_BRAIN_DUMP_LENGTH = 3
MAX_BRAIN_DUMP_LENGTH = 20_000


class BrainDumpPipelineError(Exception):
    """Raised when Brain Dump processing cannot be completed."""


def get_brain_dump(
    db: Session,
    brain_dump_id: uuid.UUID,
) -> BrainDump:
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
    brain_dump.status = "processing"
    brain_dump.error_message = None

    db.commit()
    db.refresh(brain_dump)


def normalize_brain_dump_text(raw_text: str) -> str:
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

    cleaned_text = re.sub(
        r"[ \t]+",
        " ",
        cleaned_text,
    )

    cleaned_text = re.sub(
        r"\n{3,}",
        "\n\n",
        cleaned_text,
    )

    return cleaned_text


def generate_note_title(cleaned_text: str) -> str:
    """
    Create a readable title from the first non-empty line.
    """

    first_line = next(
        (
            line.strip()
            for line in cleaned_text.splitlines()
            if line.strip()
        ),
        "Brain Dump",
    )

    if len(first_line) > 70:
        first_line = f"{first_line[:67].rstrip()}..."

    return first_line or "Brain Dump"


def convert_text_to_html(cleaned_text: str) -> str:
    """
    Convert plain Brain Dump text into safe HTML for the rich-text editor.
    """

    paragraphs = [
        paragraph.strip()
        for paragraph in cleaned_text.split("\n\n")
        if paragraph.strip()
    ]

    html_paragraphs = []

    for paragraph in paragraphs:
        safe_paragraph = html.escape(paragraph)
        safe_paragraph = safe_paragraph.replace(
            "\n",
            "<br>",
        )

        html_paragraphs.append(
            f"<p>{safe_paragraph}</p>"
        )

    return "".join(html_paragraphs) or "<p></p>"


def create_note_from_brain_dump(
    db: Session,
    brain_dump: BrainDump,
    cleaned_text: str,
) -> Note:
    """
    Convert the processed Brain Dump into a normal note.

    Because it is inserted into the notes table, it will automatically
    appear on the All Notes, Search and Dashboard pages.
    """

    note = Note(
        user_id=brain_dump.user_id,
        title=generate_note_title(cleaned_text),
        body_md=convert_text_to_html(cleaned_text),
        source="brain_dump",
        collection_id=None,
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    # Embedding failure should not delete the saved note.
    try:
        upsert_note_embedding(
            db=db,
            note=note,
        )
    except Exception:
        db.rollback()

    return note


def mark_as_ready(
    db: Session,
    brain_dump: BrainDump,
    cleaned_text: str,
) -> None:
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

    create_note_from_brain_dump(
        db=db,
        brain_dump=brain_dump,
        cleaned_text=cleaned_text,
    )

    mark_as_ready(
        db=db,
        brain_dump=brain_dump,
        cleaned_text=cleaned_text,
    )

    return brain_dump