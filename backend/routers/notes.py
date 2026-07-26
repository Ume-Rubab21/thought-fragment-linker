import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Note
from schemas.note import NoteCreate, NoteUpdate, NoteResponse
from core.deps import get_current_user

router = APIRouter(prefix="/notes", tags=["notes"])


def get_owned_note_or_404(note_id: uuid.UUID, db: Session, current_user: User) -> Note:
    """Shared lookup used by get/update/delete — fetches a note only
    if it belongs to the current user. Returns 404 (not 403) if it
    belongs to someone else, so we never reveal that the note exists
    at all to a user who shouldn't see it."""
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == current_user.id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


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


@router.get("", response_model=List[NoteResponse])
def list_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # The user_id filter here is what makes per-user isolation real —
    # this ALWAYS filters by the logged-in user, never returns
    # everyone's notes.
    notes = (
        db.query(Note)
        .filter(Note.user_id == current_user.id)
        .order_by(Note.created_at.desc())
        .all()
    )
    return notes


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_note_or_404(note_id, db, current_user)


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = get_owned_note_or_404(note_id, db, current_user)

    # Only touch fields the caller actually sent — this is what
    # NoteUpdate's Optional fields (defaulting to None) enable.
    if payload.title is not None:
        note.title = payload.title
    if payload.body_md is not None:
        note.body_md = payload.body_md

    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = get_owned_note_or_404(note_id, db, current_user)
    db.delete(note)
    db.commit()
    # 204 No Content — the standard REST response for a successful
    # delete. Nothing to return since the resource no longer exists.
    return None