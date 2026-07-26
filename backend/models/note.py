import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base
from models.tag import note_tags


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
    source = Column(String, nullable=False, default="manual")

    # Now a real foreign key, since the collections table exists.
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tags = relationship("Tag", secondary=note_tags, backref="notes")