import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.deps import get_current_user
from database import get_db
from models import Collection, Note, User
from schemas.collection import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
)


router = APIRouter(
    prefix="/collections",
    tags=["collections"],
)


def clean_collection_name(name: str) -> str:
    """Remove unnecessary spaces while preserving capitalization."""
    cleaned = " ".join(name.strip().split())

    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Collection name cannot be empty",
        )

    if len(cleaned) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Collection name cannot exceed 100 characters",
        )

    return cleaned


def get_owned_collection_or_404(
    collection_id: uuid.UUID,
    db: Session,
    current_user: User,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    return collection


def serialize_collection(
    collection: Collection,
    note_count: int,
) -> dict:
    return {
        "id": collection.id,
        "name": collection.name,
        "created_at": getattr(collection, "created_at", None),
        "note_count": note_count,
    }


@router.get(
    "",
    response_model=List[CollectionResponse],
)
def list_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = (
        db.query(
            Collection,
            func.count(Note.id).label("note_count"),
        )
        .outerjoin(
            Note,
            (Note.collection_id == Collection.id)
            & (Note.user_id == current_user.id),
        )
        .filter(Collection.user_id == current_user.id)
        .group_by(Collection.id)
        .order_by(Collection.name.asc())
        .all()
    )

    return [
        serialize_collection(collection, note_count)
        for collection, note_count in results
    ]


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_collection(
    payload: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cleaned_name = clean_collection_name(payload.name)

    duplicate = (
        db.query(Collection)
        .filter(
            Collection.user_id == current_user.id,
            func.lower(Collection.name) == cleaned_name.lower(),
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A collection with this name already exists",
        )

    collection = Collection(
        user_id=current_user.id,
        name=cleaned_name,
    )

    db.add(collection)
    db.commit()
    db.refresh(collection)

    return serialize_collection(collection, 0)


@router.put(
    "/{collection_id}",
    response_model=CollectionResponse,
)
def update_collection(
    collection_id: uuid.UUID,
    payload: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = get_owned_collection_or_404(
        collection_id,
        db,
        current_user,
    )

    cleaned_name = clean_collection_name(payload.name)

    duplicate = (
        db.query(Collection)
        .filter(
            Collection.user_id == current_user.id,
            Collection.id != collection.id,
            func.lower(Collection.name) == cleaned_name.lower(),
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A collection with this name already exists",
        )

    collection.name = cleaned_name

    db.commit()
    db.refresh(collection)

    note_count = (
        db.query(func.count(Note.id))
        .filter(
            Note.user_id == current_user.id,
            Note.collection_id == collection.id,
        )
        .scalar()
    )

    return serialize_collection(
        collection,
        note_count or 0,
    )


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = get_owned_collection_or_404(
        collection_id,
        db,
        current_user,
    )

    # Keep the notes but move them back to the Unfiled state.
    (
        db.query(Note)
        .filter(
            Note.user_id == current_user.id,
            Note.collection_id == collection.id,
        )
        .update(
            {Note.collection_id: None},
            synchronize_session=False,
        )
    )

    db.delete(collection)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)