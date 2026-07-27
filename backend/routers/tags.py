import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.deps import get_current_user
from database import get_db
from models import Note, Tag, User
from schemas.tag import TagCreate, TagResponse, TagUpdate


router = APIRouter(
    prefix="/tags",
    tags=["tags"],
)


def normalize_tag_name(name: str) -> str:
    """Normalize tags so Day4, day4 and DAY4 become the same tag."""
    normalized = " ".join(name.strip().lower().split())

    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tag name cannot be empty",
        )

    if len(normalized) > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tag name cannot exceed 50 characters",
        )

    return normalized


def get_owned_tag_or_404(
    tag_id: uuid.UUID,
    db: Session,
    current_user: User,
) -> Tag:
    tag = (
        db.query(Tag)
        .filter(
            Tag.id == tag_id,
            Tag.user_id == current_user.id,
        )
        .first()
    )

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    return tag


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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return note


def serialize_tag(tag: Tag) -> dict:
    return {
        "id": tag.id,
        "name": tag.name,
        "created_at": getattr(tag, "created_at", None),
        "note_count": len(tag.notes),
    }


@router.get(
    "",
    response_model=List[TagResponse],
)
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tags = (
        db.query(Tag)
        .filter(Tag.user_id == current_user.id)
        .order_by(Tag.name.asc())
        .all()
    )

    return [serialize_tag(tag) for tag in tags]


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tag(
    payload: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_name = normalize_tag_name(payload.name)

    existing_tag = (
        db.query(Tag)
        .filter(
            Tag.user_id == current_user.id,
            func.lower(Tag.name) == normalized_name,
        )
        .first()
    )

    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tag with this name already exists",
        )

    tag = Tag(
        user_id=current_user.id,
        name=normalized_name,
    )

    db.add(tag)
    db.commit()
    db.refresh(tag)

    return serialize_tag(tag)


@router.put(
    "/{tag_id}",
    response_model=TagResponse,
)
def update_tag(
    tag_id: uuid.UUID,
    payload: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = get_owned_tag_or_404(
        tag_id,
        db,
        current_user,
    )

    normalized_name = normalize_tag_name(payload.name)

    duplicate = (
        db.query(Tag)
        .filter(
            Tag.user_id == current_user.id,
            Tag.id != tag.id,
            func.lower(Tag.name) == normalized_name,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tag with this name already exists",
        )

    tag.name = normalized_name

    db.commit()
    db.refresh(tag)

    return serialize_tag(tag)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tag(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = get_owned_tag_or_404(
        tag_id,
        db,
        current_user,
    )

    # Remove this tag from all associated notes before deleting it.
    tag.notes.clear()

    db.delete(tag)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/notes/{note_id}",
    response_model=TagResponse,
)
def attach_tag_to_note(
    note_id: uuid.UUID,
    payload: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = get_owned_note_or_404(
        note_id,
        db,
        current_user,
    )

    normalized_name = normalize_tag_name(payload.name)

    tag = (
        db.query(Tag)
        .filter(
            Tag.user_id == current_user.id,
            func.lower(Tag.name) == normalized_name,
        )
        .first()
    )

    if not tag:
        tag = Tag(
            user_id=current_user.id,
            name=normalized_name,
        )

        db.add(tag)
        db.flush()

    if tag not in note.tags:
        note.tags.append(tag)

    db.commit()
    db.refresh(tag)

    return serialize_tag(tag)


@router.delete(
    "/notes/{note_id}/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_tag_from_note(
    note_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = get_owned_note_or_404(
        note_id,
        db,
        current_user,
    )

    tag = get_owned_tag_or_404(
        tag_id,
        db,
        current_user,
    )

    if tag in note.tags:
        note.tags.remove(tag)
        db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)