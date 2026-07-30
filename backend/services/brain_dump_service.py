from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from database import SessionLocal
from models.brain_dump import BrainDump
from services.brain_dump_pipeline import (
    mark_as_failed,
    run_brain_dump_pipeline,
)


logger = logging.getLogger(__name__)


def create_brain_dump(
    db: Session,
    user_id: uuid.UUID,
    raw_text: str,
) -> BrainDump:
    """
    Store the user's raw text before background processing starts.
    """

    brain_dump = BrainDump(
        user_id=user_id,
        raw_text=raw_text,
        status="queued",
        error_message=None,
    )

    db.add(brain_dump)

    try:
        db.commit()
        db.refresh(brain_dump)

    except Exception:
        db.rollback()
        raise

    return brain_dump


def process_brain_dump(
    brain_dump_id: uuid.UUID,
) -> None:
    """
    FastAPI BackgroundTasks entry point.

    A new database session is created because this function runs
    after the original HTTP request has returned.
    """

    db = SessionLocal()

    try:
        brain_dump, suggestion = run_brain_dump_pipeline(
            db=db,
            brain_dump_id=brain_dump_id,
        )

        logger.info(
            (
                "Brain Dump processing completed. "
                "brain_dump_id=%s suggestion_id=%s status=%s"
            ),
            brain_dump.id,
            suggestion.id,
            brain_dump.status,
        )

    except Exception as error:
        logger.exception(
            "Brain Dump processing failed: %s",
            brain_dump_id,
        )

        safely_mark_brain_dump_as_failed(
            db=db,
            brain_dump_id=brain_dump_id,
            error=error,
        )

    finally:
        db.close()


def safely_mark_brain_dump_as_failed(
    db: Session,
    brain_dump_id: uuid.UUID,
    error: Exception,
) -> None:
    """
    Attempt to record failure without allowing a secondary database
    error to escape the background task.
    """

    try:
        mark_as_failed(
            db=db,
            brain_dump_id=brain_dump_id,
            error=error,
        )

    except Exception:
        logger.exception(
            (
                "Could not update failed status for "
                "Brain Dump: %s"
            ),
            brain_dump_id,
        )