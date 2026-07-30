from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


ModelTier = Literal[
    "small",
    "large",
]

RoutingDecision = Literal[
    "small-related",
    "large-ambiguous",
    "small-new-topic",
]


class RoutingThresholds(BaseModel):
    """
    Similarity thresholds used by the model router.

    similarity > high
        Clearly related; use the small model.

    low <= similarity <= high
        Ambiguous; escalate to the large model.

    similarity < low
        New topic; use the small model.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
    )

    low: float = Field(
        default=0.35,
        ge=0,
        le=1,
    )

    high: float = Field(
        default=0.70,
        ge=0,
        le=1,
    )

    @model_validator(mode="after")
    def validate_threshold_order(
        self,
    ) -> "RoutingThresholds":
        if self.low > self.high:
            raise ValueError(
                "The low routing threshold cannot be greater "
                "than the high routing threshold."
            )

        return self


class RoutingEvaluation(BaseModel):
    """
    Routing result produced before the selected model is called.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
    )

    highest_similarity: float = Field(
        ge=0,
        le=1,
    )

    low_threshold: float = Field(
        ge=0,
        le=1,
    )

    high_threshold: float = Field(
        ge=0,
        le=1,
    )

    model_tier: ModelTier

    routing_decision: RoutingDecision

    routing_reason: str = Field(
        min_length=1,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_threshold_order(
        self,
    ) -> "RoutingEvaluation":
        if self.low_threshold > self.high_threshold:
            raise ValueError(
                "The low routing threshold cannot be greater "
                "than the high routing threshold."
            )

        return self


class ModelCallCreate(BaseModel):
    """
    Internal payload used to record one AI model call.
    """

    model_config = ConfigDict(
        protected_namespaces=(),
    )

    user_id: uuid.UUID
    brain_dump_id: uuid.UUID | None = None

    provider: str = Field(
        min_length=1,
        max_length=50,
    )

    model_name: str = Field(
        min_length=1,
        max_length=150,
    )

    model_tier: ModelTier

    call_purpose: str = Field(
        default="brain-dump-suggestion",
        min_length=1,
        max_length=80,
    )

    routing_decision: RoutingDecision

    routing_reason: str = Field(
        min_length=1,
        max_length=500,
    )

    highest_similarity: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    low_threshold: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    high_threshold: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    prompt_tokens: int = Field(
        default=0,
        ge=0,
    )

    completion_tokens: int = Field(
        default=0,
        ge=0,
    )

    total_tokens: int = Field(
        default=0,
        ge=0,
    )

    latency_ms: int = Field(
        default=0,
        ge=0,
    )

    estimated_cost_usd: float = Field(
        default=0,
        ge=0,
    )

    success: bool = True

    error_message: str | None = None

    @model_validator(mode="after")
    def validate_model_call(
        self,
    ) -> "ModelCallCreate":
        if (
            self.low_threshold is not None
            and self.high_threshold is not None
            and self.low_threshold > self.high_threshold
        ):
            raise ValueError(
                "The low routing threshold cannot be greater "
                "than the high routing threshold."
            )

        calculated_total = (
            self.prompt_tokens
            + self.completion_tokens
        )

        if (
            self.total_tokens != 0
            and self.total_tokens != calculated_total
        ):
            raise ValueError(
                "total_tokens must equal prompt_tokens plus "
                "completion_tokens."
            )

        if self.total_tokens == 0:
            self.total_tokens = calculated_total

        if self.success and self.error_message:
            raise ValueError(
                "A successful model call cannot contain an "
                "error message."
            )

        return self


class ModelCallResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
    )

    id: uuid.UUID
    user_id: uuid.UUID
    brain_dump_id: uuid.UUID | None

    provider: str
    model_name: str
    model_tier: ModelTier
    call_purpose: str

    routing_decision: RoutingDecision
    routing_reason: str

    highest_similarity: float | None
    low_threshold: float | None
    high_threshold: float | None

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    latency_ms: int
    estimated_cost_usd: float

    success: bool
    error_message: str | None

    created_at: datetime