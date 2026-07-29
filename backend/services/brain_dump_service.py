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
    db.commit()
    db.refresh(brain_dump)

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
        run_brain_dump_pipeline(
            db=db,
            brain_dump_id=brain_dump_id,
        )

        logger.info(
            "Brain Dump processing completed: %s",
            brain_dump_id,
        )

    except Exception as exc:
        logger.exception(
            "Brain Dump processing failed: %s",
            brain_dump_id,
        )

        try:
            mark_as_failed(
                db=db,
                brain_dump_id=brain_dump_id,
                error=exc,
            )
        except Exception:
            logger.exception(
                "Could not update failed status for Brain Dump: %s",
                brain_dump_id,
            )

    finally:
        db.close()