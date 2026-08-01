from __future__ import annotations

import re
import uuid
from collections import Counter
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from core.deps import get_current_user
from database import get_db
from models.collection import Collection
from models.note import Note
from models.note_link import NoteLink
from models.tag import Tag
from models.user import User
from schemas.knowledge_graph import (
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphResponse,
)


router = APIRouter(
    prefix="/knowledge-graph",
    tags=["knowledge-graph"],
)

MAX_CANDIDATES = 200


def plain_text(value: str | None, limit: int = 220) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", value or "")
    cleaned = " ".join(cleaned.split())
    return cleaned[:limit]


def note_query(db: Session, user_id: uuid.UUID):
    return (
        db.query(Note)
        .options(
            joinedload(Note.tags),
        )
        .filter(Note.user_id == user_id)
    )


def apply_filters(
    query,
    search: str | None,
    tag_id: uuid.UUID | None,
    collection_id: uuid.UUID | None,
):
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Note.title.ilike(term),
                Note.body_md.ilike(term),
            )
        )

    if tag_id is not None:
        query = query.filter(
            Note.tags.any(Tag.id == tag_id)
        )

    if collection_id is not None:
        query = query.filter(
            Note.collection_id == collection_id
        )

    return query


def load_links(
    db: Session,
    user_id: uuid.UUID,
    note_ids: set[uuid.UUID],
) -> list[NoteLink]:
    if not note_ids:
        return []

    return (
        db.query(NoteLink)
        .filter(
            NoteLink.user_id == user_id,
            NoteLink.from_note_id.in_(note_ids),
            NoteLink.to_note_id.in_(note_ids),
        )
        .all()
    )


def degree_map(links: list[NoteLink]) -> Counter:
    values: Counter = Counter()

    for link in links:
        values[link.from_note_id] += 1
        values[link.to_note_id] += 1

    return values


def serialize_graph(
    db: Session,
    current_user: User,
    notes: list[Note],
    total_note_count: int,
    filtered_note_count: int,
    focus_note_id: uuid.UUID | None,
) -> KnowledgeGraphResponse:
    note_ids = {note.id for note in notes}
    links = load_links(
        db,
        current_user.id,
        note_ids,
    )
    degrees = degree_map(links)

    collection_ids = {
        note.collection_id
        for note in notes
        if note.collection_id is not None
    }
    collections = (
        db.query(Collection)
        .filter(
            Collection.user_id == current_user.id,
            Collection.id.in_(collection_ids),
        )
        .all()
        if collection_ids
        else []
    )
    collection_names = {
        collection.id: collection.name
        for collection in collections
    }

    nodes: list[KnowledgeGraphNode] = []
    edges: list[KnowledgeGraphEdge] = []

    for note in notes:
        tag_names = sorted(tag.name for tag in note.tags)

        nodes.append(
            KnowledgeGraphNode(
                id=f"note:{note.id}",
                entity_id=note.id,
                kind="note",
                label=note.title,
                subtitle="Note",
                preview=plain_text(note.body_md),
                collection_id=note.collection_id,
                collection_name=collection_names.get(note.collection_id),
                tags=tag_names,
                updated_at=note.updated_at,
                weight=max(
                    1,
                    degrees.get(note.id, 0) + len(tag_names),
                ),
            )
        )

    for link in links:
        edges.append(
            KnowledgeGraphEdge(
                id=f"link:{link.id}",
                source=f"note:{link.from_note_id}",
                target=f"note:{link.to_note_id}",
                kind="related",
                confidence=link.confidence,
                label=link.reason,
            )
        )

    seen_tags: set[uuid.UUID] = set()

    for note in notes:
        for tag in note.tags:
            tag_node_id = f"tag:{tag.id}"

            if tag.id not in seen_tags:
                seen_tags.add(tag.id)
                nodes.append(
                    KnowledgeGraphNode(
                        id=tag_node_id,
                        entity_id=tag.id,
                        kind="tag",
                        label=tag.name,
                        subtitle="Tag",
                        weight=max(1, len(tag.notes)),
                    )
                )

            edges.append(
                KnowledgeGraphEdge(
                    id=f"tagged:{note.id}:{tag.id}",
                    source=f"note:{note.id}",
                    target=tag_node_id,
                    kind="tagged",
                    label="Tagged with",
                )
            )

    return KnowledgeGraphResponse(
        nodes=nodes,
        edges=edges,
        total_note_count=total_note_count,
        filtered_note_count=filtered_note_count,
        visible_note_count=len(notes),
        tag_count=len(seen_tags),
        connection_count=len(links),
        focus_note_id=focus_note_id,
        truncated=filtered_note_count > len(notes),
    )


@router.get(
    "",
    response_model=KnowledgeGraphResponse,
)
def get_knowledge_graph(
    search: str | None = Query(default=None, max_length=200),
    tag_id: uuid.UUID | None = None,
    collection_id: uuid.UUID | None = None,
    sort: Literal[
        "connected",
        "updated",
        "created",
        "title",
    ] = "connected",
    limit: int = Query(default=20, ge=5, le=50),
    focus_note_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_note_count = (
        db.query(Note.id)
        .filter(Note.user_id == current_user.id)
        .count()
    )

    if focus_note_id is not None:
        focus_note = (
            note_query(db, current_user.id)
            .filter(Note.id == focus_note_id)
            .first()
        )

        if not focus_note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Focused note was not found",
            )

        direct_links = (
            db.query(NoteLink)
            .filter(
                NoteLink.user_id == current_user.id,
                or_(
                    NoteLink.from_note_id == focus_note_id,
                    NoteLink.to_note_id == focus_note_id,
                ),
            )
            .all()
        )

        neighbour_ids: set[uuid.UUID] = set()

        for link in direct_links:
            neighbour_ids.add(link.from_note_id)
            neighbour_ids.add(link.to_note_id)

        neighbour_ids.discard(focus_note_id)

        neighbours = (
            note_query(db, current_user.id)
            .filter(Note.id.in_(neighbour_ids))
            .all()
            if neighbour_ids
            else []
        )

        # Keep the focused graph readable even for a highly connected hub.
        neighbours = sorted(
            neighbours,
            key=lambda note: note.updated_at,
            reverse=True,
        )[:20]

        visible_notes = [focus_note, *neighbours]

        return serialize_graph(
            db=db,
            current_user=current_user,
            notes=visible_notes,
            total_note_count=total_note_count,
            filtered_note_count=len(visible_notes),
            focus_note_id=focus_note_id,
        )

    filtered_query = apply_filters(
        note_query(db, current_user.id),
        search=search,
        tag_id=tag_id,
        collection_id=collection_id,
    )

    filtered_note_count = filtered_query.count()

    candidates = (
        filtered_query
        .order_by(Note.updated_at.desc())
        .limit(MAX_CANDIDATES)
        .all()
    )

    candidate_ids = {note.id for note in candidates}
    candidate_links = load_links(
        db,
        current_user.id,
        candidate_ids,
    )
    degrees = degree_map(candidate_links)

    if sort == "connected":
        candidates.sort(
            key=lambda note: (
                degrees.get(note.id, 0),
                note.updated_at,
            ),
            reverse=True,
        )
    elif sort == "created":
        candidates.sort(
            key=lambda note: note.created_at,
            reverse=True,
        )
    elif sort == "title":
        candidates.sort(
            key=lambda note: note.title.lower(),
        )
    else:
        candidates.sort(
            key=lambda note: note.updated_at,
            reverse=True,
        )

    visible_notes = candidates[:limit]

    return serialize_graph(
        db=db,
        current_user=current_user,
        notes=visible_notes,
        total_note_count=total_note_count,
        filtered_note_count=filtered_note_count,
        focus_note_id=None,
    )
