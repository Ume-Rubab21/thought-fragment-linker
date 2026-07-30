from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoutingDecisionCount(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
    )

    routing_decision: str
    count: int = Field(ge=0)


class ModelTierCount(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
    )

    model_tier: str
    count: int = Field(ge=0)


class ModelCallDashboardSummary(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
    )

    total_calls: int = Field(ge=0)
    successful_calls: int = Field(ge=0)
    failed_calls: int = Field(ge=0)

    small_model_calls: int = Field(ge=0)
    large_model_calls: int = Field(ge=0)

    total_tokens: int = Field(ge=0)
    total_latency_ms: int = Field(ge=0)
    average_latency_ms: float = Field(ge=0)

    actual_cost_usd: float = Field(ge=0)
    estimated_all_large_cost_usd: float = Field(ge=0)
    estimated_savings_usd: float = Field(ge=0)
    savings_percentage: float = Field(ge=0)

    routing_decisions: list[RoutingDecisionCount]
    model_tiers: list[ModelTierCount]


class ModelCallDashboardItem(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
    )

    id: uuid.UUID
    brain_dump_id: uuid.UUID | None

    provider: str
    model_name: str
    model_tier: str
    call_purpose: str

    routing_decision: str
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


class ModelCallDashboardResponse(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
    )

    summary: ModelCallDashboardSummary
    calls: list[ModelCallDashboardItem]