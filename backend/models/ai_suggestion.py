import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from database import Base


class AISuggestion(Base):
    """
    Stores validated AI output generated for one Brain Dump.

    A suggestion begins as pending. The authenticated user can later
    accept it to create a real Note or reject it without creating one.
    """

    __tablename__ = "ai_suggestions"

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

    brain_dump_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "braindumps.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    suggested_title = Column(
        String(120),
        nullable=False,
    )

    summary = Column(
        Text,
        nullable=False,
    )

    suggested_content = Column(
        Text,
        nullable=True,
    )

    tags = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    keywords = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    related_note_ids = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    model_name = Column(
        String(120),
        nullable=False,
    )

    prompt_tokens = Column(
        Integer,
        nullable=False,
        default=0,
    )

    completion_tokens = Column(
        Integer,
        nullable=False,
        default=0,
    )

    total_tokens = Column(
        Integer,
        nullable=False,
        default=0,
    )

    attempts = Column(
        Integer,
        nullable=False,
        default=1,
    )

    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    accepted_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "notes.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    rejection_reason = Column(
        String(500),
        nullable=True,
    )

    reasoning_decision = Column(
        String(30),
        nullable=True,
    )

    reasoning = Column(
        Text,
        nullable=True,
    )

    confidence_score = Column(
        Integer,
        nullable=True,
    )

    reasoning_tier = Column(
        String(20),
        nullable=False,
        default="small",
    )

    decided_at = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
    )

    brain_dump = relationship(
        "BrainDump",
    )

    accepted_note = relationship(
        "Note",
        foreign_keys=[
            accepted_note_id,
        ],
    )