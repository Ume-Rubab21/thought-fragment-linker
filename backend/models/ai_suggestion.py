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
    Stores AI output only after it has passed schema validation
    and all deterministic guardrails.

    This record does not create a Note, Tag, or relationship yet.
    That integration belongs to the next Day 7 group.
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