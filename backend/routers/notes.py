from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, Note
from schemas.note import NoteCreate, NoteResponse
from core.deps import get_current_user

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse)
def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = Note(
        user_id=current_user.id,
        title=payload.title,
        body_md=payload.body_md,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note