import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from core.deps import get_current_user
from database import get_db
from models.brain_dump import BrainDump
from models.user import User
from schemas.brain_dump import (
    BrainDumpCreate,
    BrainDumpResponse,
    BrainDumpStatusResponse,
)
from services.brain_dump_service import (
    create_brain_dump,
    process_brain_dump,
)


router = APIRouter(
    prefix="/brain-dumps",
    tags=["brain-dumps"],
)


def get_owned_brain_dump_or_404(
    brain_dump_id: uuid.UUID,
    db: Session,
    current_user: User,
) -> BrainDump:
    brain_dump = (
        db.query(BrainDump)
        .filter(
            BrainDump.id == brain_dump_id,
            BrainDump.user_id == current_user.id,
        )
        .first()
    )

    if not brain_dump:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain dump not found",
        )

    return brain_dump


@router.post(
    "",
    response_model=BrainDumpResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_brain_dump(
    payload: BrainDumpCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Store raw text immediately and process it in the background.
    """

    brain_dump = create_brain_dump(
        db=db,
        user_id=current_user.id,
        raw_text=payload.raw_text,
    )

    background_tasks.add_task(
        process_brain_dump,
        brain_dump.id,
    )

    return brain_dump


@router.get(
    "/{brain_dump_id}/status",
    response_model=BrainDumpStatusResponse,
)
def get_brain_dump_status(
    brain_dump_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_brain_dump_or_404(
        brain_dump_id,
        db,
        current_user,
    )


@router.get(
    "/{brain_dump_id}",
    response_model=BrainDumpResponse,
)
def get_brain_dump(
    brain_dump_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_brain_dump_or_404(
        brain_dump_id,
        db,
        current_user,
    )