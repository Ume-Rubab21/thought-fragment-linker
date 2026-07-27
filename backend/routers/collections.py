import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import User, Collection, Note
from schemas.collection import CollectionCreate, CollectionUpdate, CollectionResponse
from core.deps import get_current_user

router = APIRouter(prefix="/collections", tags=["collections"])


def get_owned_collection_or_404(
    collection_id: uuid.UUID, db: Session, current_user: User
) -> Collection:
    collection = (
        db.query(Collection)
        .filter(
            Collection.id == collection_id,
            Collection.user_id == current_user.id,
        )
        .first()
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


def ensure_unique_name(name: str, db: Session, current_user: User, exclude_id=None):
    query = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        func.lower(Collection.name) == name.lower(),
    )
    if exclude_id is not None:
        query = query.filter(Collection.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=409, detail="A collection with this name already exists")


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(
    payload: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_unique_name(payload.name, db, current_user)
    collection = Collection(user_id=current_user.id, name=payload.name)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    collection.note_count = 0
    return collection


@router.get("", response_model=List[CollectionResponse])
def list_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Collection, func.count(Note.id))
        .outerjoin(
            Note,
            (Note.collection_id == Collection.id) & (Note.user_id == current_user.id),
        )
        .filter(Collection.user_id == current_user.id)
        .group_by(Collection.id)
        .order_by(Collection.name)
        .all()
    )

    collections = []
    for collection, count in rows:
        collection.note_count = count
        collections.append(collection)
    return collections


@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: uuid.UUID,
    payload: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = get_owned_collection_or_404(collection_id, db, current_user)
    ensure_unique_name(payload.name, db, current_user, exclude_id=collection.id)
    collection.name = payload.name
    db.commit()
    db.refresh(collection)
    collection.note_count = (
        db.query(func.count(Note.id))
        .filter(Note.user_id == current_user.id, Note.collection_id == collection.id)
        .scalar()
    )
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = get_owned_collection_or_404(collection_id, db, current_user)

    # Notes are not deleted when their flat grouping is removed.
    db.query(Note).filter(
        Note.user_id == current_user.id,
        Note.collection_id == collection.id,
    ).update({Note.collection_id: None}, synchronize_session=False)

    db.delete(collection)
    db.commit()
    return None
