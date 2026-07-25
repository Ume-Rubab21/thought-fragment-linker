import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Every note belongs to exactly one user — this is what makes
    # per-user isolation possible. Every query on notes MUST filter
    # by user_id, or one user could see another's notes.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=False)
    body_md = Column(Text, nullable=False, default="")

    # 'manual' | 'braindump' | 'mcp' — tracks how the note was created.
    # Only 'manual' is used for now (Day 3); the others come later.
    source = Column(String, nullable=False, default="manual")

    # No foreign key yet — the collections table doesn't exist until
    # a later day. Left as a plain nullable column for now; we'll add
    # the real foreign key constraint once collections exist.
    collection_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)