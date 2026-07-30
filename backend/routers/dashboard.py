from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.deps import get_current_user
from database import get_db
from models.collection import Collection
from models.note import Note
from models.note_link import NoteLink
from models.tag import Tag, note_tags
from models.user import User
from schemas.dashboard import (
    DashboardRecentNote,
    DashboardSummaryResponse,
    DashboardTopTag,
)


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all Dashboard data using small aggregate queries.

    This avoids loading every note, tag relationship, and collection merely
    to calculate four counters and five recent rows.
    """
    user_id = current_user.id

    note_count = (
        db.query(func.count(Note.id))
        .filter(Note.user_id == user_id)
        .scalar()
        or 0
    )
    tag_count = (
        db.query(func.count(Tag.id))
        .filter(Tag.user_id == user_id)
        .scalar()
        or 0
    )
    collection_count = (
        db.query(func.count(Collection.id))
        .filter(Collection.user_id == user_id)
        .scalar()
        or 0
    )
    connection_count = (
        db.query(func.count(NoteLink.id))
        .filter(NoteLink.user_id == user_id)
        .scalar()
        or 0
    )

    recent_rows = (
        db.query(Note.id, Note.title, Note.body_md, Note.updated_at)
        .filter(Note.user_id == user_id)
        .order_by(Note.updated_at.desc(), Note.created_at.desc())
        .limit(5)
        .all()
    )

    top_tag_rows = (
        db.query(
            Tag.id,
            Tag.name,
            func.count(Note.id).label("note_count"),
        )
        .outerjoin(note_tags, note_tags.c.tag_id == Tag.id)
        .outerjoin(
            Note,
            (Note.id == note_tags.c.note_id)
            & (Note.user_id == user_id),
        )
        .filter(Tag.user_id == user_id)
        .group_by(Tag.id, Tag.name)
        .order_by(func.count(Note.id).desc(), Tag.name.asc())
        .limit(5)
        .all()
    )

    return DashboardSummaryResponse(
        note_count=int(note_count),
        tag_count=int(tag_count),
        collection_count=int(collection_count),
        connection_count=int(connection_count),
        recent_notes=[
            DashboardRecentNote(
                id=row.id,
                title=row.title,
                body_md=row.body_md or "",
                updated_at=row.updated_at,
            )
            for row in recent_rows
        ],
        top_tags=[
            DashboardTopTag(
                id=row.id,
                name=row.name,
                note_count=int(row.note_count or 0),
            )
            for row in top_tag_rows
        ],
    )
