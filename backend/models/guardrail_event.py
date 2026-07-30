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


class GuardrailEvent(Base):
    """
    Stores one rejected AI-output attempt.

    A Brain Dump may have multiple GuardrailEvent records because
    the small model can make an initial attempt and up to two retries.
    """

    __tablename__ = "guardrail_events"

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

    attempt_number = Column(
        Integer,
        nullable=False,
    )

    failure_category = Column(
        String(80),
        nullable=False,
        index=True,
    )

    failure_reason = Column(
        Text,
        nullable=False,
    )

    raw_model_response = Column(
        Text,
        nullable=True,
    )

    failure_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
    )

    model_name = Column(
        String(120),
        nullable=True,
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

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
    )

    brain_dump = relationship(
        "BrainDump",
    )