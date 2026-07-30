from __future__ import annotations

import uuid
from collections import Counter
from decimal import Decimal
from typing import Iterable

from sqlalchemy.orm import Session

from models.model_call import ModelCall
from schemas.model_call_dashboard import (
    ModelCallDashboardItem,
    ModelCallDashboardResponse,
    ModelCallDashboardSummary,
    ModelTierCount,
    RoutingDecisionCount,
)
from services.model_cost_service import (
    estimate_model_call_cost,
)


DEFAULT_DASHBOARD_LIMIT = 25
MAX_DASHBOARD_LIMIT = 100


def _safe_limit(limit: int) -> int:
    return max(
        1,
        min(int(limit), MAX_DASHBOARD_LIMIT),
    )


def _calculate_all_large_cost(
    calls: Iterable[ModelCall],
) -> Decimal:
    total = Decimal("0")

    for model_call in calls:
        estimate = estimate_model_call_cost(
            model_tier="large",
            prompt_tokens=model_call.prompt_tokens,
            completion_tokens=model_call.completion_tokens,
        )
        total += estimate.total_cost_usd

    return total


def get_model_call_dashboard(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int = DEFAULT_DASHBOARD_LIMIT,
) -> ModelCallDashboardResponse:
    """
    Return model-routing totals and the user's latest model calls.

    The estimated savings value compares actual routed cost with the
    hypothetical cost of sending every recorded call to the configured
    large model.
    """

    all_calls = (
        db.query(ModelCall)
        .filter(ModelCall.user_id == user_id)
        .order_by(ModelCall.created_at.desc())
        .all()
    )

    latest_calls = all_calls[:_safe_limit(limit)]

    total_calls = len(all_calls)
    successful_calls = sum(
        1 for call in all_calls if call.success
    )
    failed_calls = total_calls - successful_calls

    small_model_calls = sum(
        1
        for call in all_calls
        if call.model_tier == "small"
    )
    large_model_calls = sum(
        1
        for call in all_calls
        if call.model_tier == "large"
    )

    total_tokens = sum(
        int(call.total_tokens or 0)
        for call in all_calls
    )
    total_latency_ms = sum(
        int(call.latency_ms or 0)
        for call in all_calls
    )

    average_latency_ms = (
        total_latency_ms / total_calls
        if total_calls
        else 0.0
    )

    actual_cost = sum(
        (
            Decimal(str(call.estimated_cost_usd or 0))
            for call in all_calls
        ),
        Decimal("0"),
    )

    all_large_cost = _calculate_all_large_cost(
        all_calls
    )

    estimated_savings = max(
        Decimal("0"),
        all_large_cost - actual_cost,
    )

    savings_percentage = (
        float(
            (
                estimated_savings
                / all_large_cost
                * Decimal("100")
            )
        )
        if all_large_cost > 0
        else 0.0
    )

    routing_counts = Counter(
        call.routing_decision
        for call in all_calls
    )

    tier_counts = Counter(
        call.model_tier
        for call in all_calls
    )

    return ModelCallDashboardResponse(
        summary=ModelCallDashboardSummary(
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            small_model_calls=small_model_calls,
            large_model_calls=large_model_calls,
            total_tokens=total_tokens,
            total_latency_ms=total_latency_ms,
            average_latency_ms=round(
                average_latency_ms,
                2,
            ),
            actual_cost_usd=round(
                float(actual_cost),
                8,
            ),
            estimated_all_large_cost_usd=round(
                float(all_large_cost),
                8,
            ),
            estimated_savings_usd=round(
                float(estimated_savings),
                8,
            ),
            savings_percentage=round(
                savings_percentage,
                2,
            ),
            routing_decisions=[
                RoutingDecisionCount(
                    routing_decision=decision,
                    count=count,
                )
                for decision, count
                in sorted(routing_counts.items())
            ],
            model_tiers=[
                ModelTierCount(
                    model_tier=tier,
                    count=count,
                )
                for tier, count
                in sorted(tier_counts.items())
            ],
        ),
        calls=[
            ModelCallDashboardItem.model_validate(
                call
            )
            for call in latest_calls
        ],
    )
