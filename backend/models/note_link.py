import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class NoteLink(Base):
    """
    Stores a user-approved relationship between two notes.

    AI may suggest related notes, but a NoteLink is created only after
    the authenticated user accepts the Brain Dump suggestion.
    """

    __tablename__ = "note_links"

    __table_args__ = (
        UniqueConstraint(
            "from_note_id",
            "to_note_id",
            name="uq_note_links_from_to",
        ),
        CheckConstraint(
            "from_note_id <> to_note_id",
            name="ck_note_links_no_self_link",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_note_links_confidence_range",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    from_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "notes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    to_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "notes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    reason = Column(
        String(500),
        nullable=False,
    )

    confidence = Column(
        Float,
        nullable=False,
    )

    source = Column(
        String(40),
        nullable=False,
        default="brain-dump-ai",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
    )

    from_note = relationship(
        "Note",
        foreign_keys=[
            from_note_id,
        ],
    )

    to_note = relationship(
        "Note",
        foreign_keys=[
            to_note_id,
        ],
    )