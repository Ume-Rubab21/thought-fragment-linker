import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, delete

from database import get_db
from models import User, Tag, Note, note_tags
from schemas.tag import TagCreate, TagUpdate, TagResponse
from core.deps import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])


def get_owned_tag_or_404(tag_id: uuid.UUID, db: Session, current_user: User) -> Tag:
    tag = (
        db.query(Tag)
        .filter(Tag.id == tag_id, Tag.user_id == current_user.id)
        .first()
    )
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


def get_or_create_tag(name: str, db: Session, current_user: User) -> Tag:
    normalized = name.strip().lower()
    tag = (
        db.query(Tag)
        .filter(Tag.user_id == current_user.id, Tag.name == normalized)
        .first()
    )
    if tag:
        return tag

    tag = Tag(user_id=current_user.id, name=normalized)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = get_or_create_tag(payload.name, db, current_user)
    tag.note_count = (
        db.query(func.count(note_tags.c.note_id))
        .filter(note_tags.c.tag_id == tag.id)
        .scalar()
    )
    return tag


@router.get("", response_model=List[TagResponse])
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(Tag, func.count(note_tags.c.note_id))
        .outerjoin(note_tags, Tag.id == note_tags.c.tag_id)
        .filter(Tag.user_id == current_user.id)
        .group_by(Tag.id)
        .order_by(Tag.name)
        .all()
    )
    tags = []
    for tag, count in results:
        tag.note_count = count
        tags.append(tag)
    return tags


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: uuid.UUID,
    payload: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = get_owned_tag_or_404(tag_id, db, current_user)
    duplicate = (
        db.query(Tag)
        .filter(
            Tag.user_id == current_user.id,
            Tag.name == payload.name,
            Tag.id != tag.id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="A tag with this name already exists")

    tag.name = payload.name
    db.commit()
    db.refresh(tag)
    tag.note_count = (
        db.query(func.count(note_tags.c.note_id))
        .filter(note_tags.c.tag_id == tag.id)
        .scalar()
    )
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = get_owned_tag_or_404(tag_id, db, current_user)
    db.execute(delete(note_tags).where(note_tags.c.tag_id == tag.id))
    db.delete(tag)
    db.commit()
    return None


@router.post("/notes/{note_id}", response_model=TagResponse)
def attach_tag_to_note(
    note_id: uuid.UUID,
    payload: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == current_user.id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    tag = get_or_create_tag(payload.name, db, current_user)
    if tag not in note.tags:
        note.tags.append(tag)
        db.commit()
    tag.note_count = (
        db.query(func.count(note_tags.c.note_id))
        .filter(note_tags.c.tag_id == tag.id)
        .scalar()
    )
    return tag


@router.delete("/notes/{note_id}/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag_from_note(
    note_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == current_user.id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    tag = get_owned_tag_or_404(tag_id, db, current_user)
    if tag in note.tags:
        note.tags.remove(tag)
        db.commit()
    return None
