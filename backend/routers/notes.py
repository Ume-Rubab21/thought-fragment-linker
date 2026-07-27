import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from core.deps import get_current_user
from database import get_db
from models import Collection, Note, User
from schemas.note import NoteCreate, NoteResponse, NoteUpdate


router = APIRouter(
    prefix="/notes",
    tags=["notes"],
)


def get_owned_note_or_404(
    note_id: uuid.UUID,
    db: Session,
    current_user: User,
) -> Note:
    note = (
        db.query(Note)
        .filter(
            Note.id == note_id,
            Note.user_id == current_user.id,
        )
        .first()
    )

    if not note:
        raise HTTPException(
            status_code=404,
            detail="Note not found",
        )

    return note


def validate_collection_ownership(
    collection_id: Optional[uuid.UUID],
    db: Session,
    current_user: User,
) -> None:
    if collection_id is None:
        return

    collection = (
        db.query(Collection.id)
        .filter(
            Collection.id == collection_id,
            Collection.user_id == current_user.id,
        )
        .first()
    )

    if not collection:
        raise HTTPException(
            status_code=400,
            detail="Invalid collection",
        )


def apply_note_filters(
    query,
    collection_id=None,
    tag=None,
):
    if collection_id is not None:
        query = query.filter(
            Note.collection_id == collection_id,
        )

    if tag:
        query = query.filter(
            Note.tags.any(
                name=tag.strip().lower(),
            )
        )

    return query


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_collection_ownership(
        payload.collection_id,
        db,
        current_user,
    )

    note = Note(
        user_id=current_user.id,
        title=payload.title,
        body_md=payload.body_md,
        collection_id=payload.collection_id,
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


@router.get(
    "",
    response_model=List[NoteResponse],
)
def list_notes(
    collection_id: Optional[uuid.UUID] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Note).filter(
        Note.user_id == current_user.id,
    )

    query = apply_note_filters(
        query,
        collection_id=collection_id,
        tag=tag,
    )

    return query.order_by(
        Note.updated_at.desc(),
        Note.created_at.desc(),
    ).all()


@router.get(
    "/search",
    response_model=List[NoteResponse],
)
def search_notes(
    q: str = "",
    collection_id: Optional[uuid.UUID] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cleaned_query = q.strip()

    query = db.query(Note).filter(
        Note.user_id == current_user.id,
    )

    query = apply_note_filters(
        query,
        collection_id=collection_id,
        tag=tag,
    )

    if not cleaned_query:
        return query.order_by(
            Note.updated_at.desc(),
        ).all()

    search_query = func.websearch_to_tsquery(
        "english",
        cleaned_query,
    )

    rank = func.ts_rank_cd(
        Note.search_vector,
        search_query,
    )

    # Used only as a partial-word fallback.
    plain_body = func.regexp_replace(
        Note.body_md,
        "<[^>]+>",
        " ",
        "g",
    )

    like_value = f"%{cleaned_query}%"

    query = query.filter(
        or_(
            Note.search_vector.op("@@")(
                search_query,
            ),
            Note.title.ilike(like_value),
            plain_body.ilike(like_value),
        )
    )

    return query.order_by(
        rank.desc(),
        Note.updated_at.desc(),
    ).all()


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
)
def get_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_note_or_404(
        note_id,
        db,
        current_user,
    )


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
)
def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = get_owned_note_or_404(
        note_id,
        db,
        current_user,
    )

    supplied_fields = payload.model_fields_set

    if "title" in supplied_fields:
        note.title = payload.title

    if "body_md" in supplied_fields:
        note.body_md = payload.body_md or ""

    if "collection_id" in supplied_fields:
        validate_collection_ownership(
            payload.collection_id,
            db,
            current_user,
        )

        note.collection_id = payload.collection_id

    db.commit()
    db.refresh(note)

    return note


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = get_owned_note_or_404(
        note_id,
        db,
        current_user,
    )

    db.delete(note)
    db.commit()

    return None