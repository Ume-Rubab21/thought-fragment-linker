from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class ModelCall(Base):
    """
    Records one AI model execution and its routing decision.

    A model call may happen while processing a Brain Dump before a
    permanent Note has been created, so brain_dump_id is the primary
    workflow reference.
    """

    __tablename__ = "model_calls"

    __table_args__ = (
        CheckConstraint(
            "highest_similarity IS NULL OR "
            "(highest_similarity >= 0 AND highest_similarity <= 1)",
            name="ck_model_calls_similarity_range",
        ),
        CheckConstraint(
            "low_threshold IS NULL OR "
            "(low_threshold >= 0 AND low_threshold <= 1)",
            name="ck_model_calls_low_threshold_range",
        ),
        CheckConstraint(
            "high_threshold IS NULL OR "
            "(high_threshold >= 0 AND high_threshold <= 1)",
            name="ck_model_calls_high_threshold_range",
        ),
        CheckConstraint(
            "low_threshold IS NULL OR "
            "high_threshold IS NULL OR "
            "low_threshold <= high_threshold",
            name="ck_model_calls_threshold_order",
        ),
        CheckConstraint(
            "prompt_tokens >= 0",
            name="ck_model_calls_prompt_tokens_non_negative",
        ),
        CheckConstraint(
            "completion_tokens >= 0",
            name="ck_model_calls_completion_tokens_non_negative",
        ),
        CheckConstraint(
            "total_tokens >= 0",
            name="ck_model_calls_total_tokens_non_negative",
        ),
        CheckConstraint(
            "latency_ms >= 0",
            name="ck_model_calls_latency_non_negative",
        ),
        CheckConstraint(
            "estimated_cost_usd >= 0",
            name="ck_model_calls_cost_non_negative",
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

    brain_dump_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "braindumps.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    provider = Column(
        String(50),
        nullable=False,
    )

    model_name = Column(
        String(150),
        nullable=False,
    )

    model_tier = Column(
        String(20),
        nullable=False,
    )

    call_purpose = Column(
        String(80),
        nullable=False,
        default="brain-dump-suggestion",
    )

    routing_decision = Column(
        String(40),
        nullable=False,
    )

    routing_reason = Column(
        String(500),
        nullable=False,
    )

    highest_similarity = Column(
        Float,
        nullable=True,
    )

    low_threshold = Column(
        Float,
        nullable=True,
    )

    high_threshold = Column(
        Float,
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

    latency_ms = Column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_cost_usd = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    success = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    user = relationship(
        "User",
    )

    brain_dump = relationship(
        "BrainDump",
    )