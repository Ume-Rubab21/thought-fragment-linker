from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from models.brain_dump import BrainDump
from models.model_call import ModelCall
from models.user import User
from schemas.model_routing import (
    ModelCallCreate,
    RoutingEvaluation,
)
from services.model_cost_service import (
    ModelCostEstimate,
    estimate_model_call_cost,
)


class ModelCallLoggingError(RuntimeError):
    """Base error for model-call logging."""


class ModelCallOwnershipError(
    ModelCallLoggingError
):
    """Raised when model-call references do not belong to the user."""


@dataclass(frozen=True)
class RecordedModelCall:
    model_call: ModelCall
    cost_estimate: ModelCostEstimate


def verify_model_call_ownership(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID | None,
) -> None:
    """
    Verify that the user exists and owns the referenced Brain Dump.
    """

    user_exists = (
        db.query(User.id)
        .filter(
            User.id == user_id,
        )
        .first()
    )

    if user_exists is None:
        raise ModelCallOwnershipError(
            "The model-call user was not found."
        )

    if brain_dump_id is None:
        return

    brain_dump_exists = (
        db.query(BrainDump.id)
        .filter(
            BrainDump.id == brain_dump_id,
            BrainDump.user_id == user_id,
        )
        .first()
    )

    if brain_dump_exists is None:
        raise ModelCallOwnershipError(
            "The Brain Dump does not belong to the "
            "specified user."
        )


def create_model_call(
    db: Session,
    *,
    payload: ModelCallCreate,
    commit: bool = True,
) -> ModelCall:
    """
    Persist one validated model-call record.

    Set commit=False when the caller manages a larger transaction.
    """

    verify_model_call_ownership(
        db=db,
        user_id=payload.user_id,
        brain_dump_id=payload.brain_dump_id,
    )

    model_call = ModelCall(
        user_id=payload.user_id,
        brain_dump_id=payload.brain_dump_id,
        provider=payload.provider,
        model_name=payload.model_name,
        model_tier=payload.model_tier,
        call_purpose=payload.call_purpose,
        routing_decision=(
            payload.routing_decision
        ),
        routing_reason=payload.routing_reason,
        highest_similarity=(
            payload.highest_similarity
        ),
        low_threshold=payload.low_threshold,
        high_threshold=payload.high_threshold,
        prompt_tokens=payload.prompt_tokens,
        completion_tokens=(
            payload.completion_tokens
        ),
        total_tokens=payload.total_tokens,
        latency_ms=payload.latency_ms,
        estimated_cost_usd=(
            payload.estimated_cost_usd
        ),
        success=payload.success,
        error_message=payload.error_message,
    )

    db.add(model_call)

    try:
        if commit:
            db.commit()
            db.refresh(model_call)
        else:
            db.flush()

    except Exception:
        db.rollback()
        raise

    return model_call


def record_successful_model_call(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID | None,
    provider: str,
    model_name: str,
    routing: RoutingEvaluation,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
    call_purpose: str = (
        "brain-dump-suggestion"
    ),
    commit: bool = True,
) -> RecordedModelCall:
    """
    Calculate cost and record a successful model execution.
    """

    cost_estimate = estimate_model_call_cost(
        model_tier=routing.model_tier,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    payload = ModelCallCreate(
        user_id=user_id,
        brain_dump_id=brain_dump_id,
        provider=provider,
        model_name=model_name,
        model_tier=routing.model_tier,
        call_purpose=call_purpose,
        routing_decision=(
            routing.routing_decision
        ),
        routing_reason=routing.routing_reason,
        highest_similarity=(
            routing.highest_similarity
        ),
        low_threshold=(
            routing.low_threshold
        ),
        high_threshold=(
            routing.high_threshold
        ),
        prompt_tokens=(
            cost_estimate.prompt_tokens
        ),
        completion_tokens=(
            cost_estimate.completion_tokens
        ),
        total_tokens=(
            cost_estimate.total_tokens
        ),
        latency_ms=max(
            int(latency_ms),
            0,
        ),
        estimated_cost_usd=float(
            cost_estimate.total_cost_usd
        ),
        success=True,
        error_message=None,
    )

    model_call = create_model_call(
        db=db,
        payload=payload,
        commit=commit,
    )

    return RecordedModelCall(
        model_call=model_call,
        cost_estimate=cost_estimate,
    )


def record_failed_model_call(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID | None,
    provider: str,
    model_name: str,
    routing: RoutingEvaluation,
    latency_ms: int,
    error_message: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    call_purpose: str = (
        "brain-dump-suggestion"
    ),
    commit: bool = True,
) -> RecordedModelCall:
    """
    Record a failed model execution while preserving routing, latency,
    token usage, and estimated cost.
    """

    cleaned_error = (
        error_message.strip()
        or "Unknown model-call failure."
    )

    cost_estimate = estimate_model_call_cost(
        model_tier=routing.model_tier,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    payload = ModelCallCreate(
        user_id=user_id,
        brain_dump_id=brain_dump_id,
        provider=provider,
        model_name=model_name,
        model_tier=routing.model_tier,
        call_purpose=call_purpose,
        routing_decision=(
            routing.routing_decision
        ),
        routing_reason=routing.routing_reason,
        highest_similarity=(
            routing.highest_similarity
        ),
        low_threshold=(
            routing.low_threshold
        ),
        high_threshold=(
            routing.high_threshold
        ),
        prompt_tokens=(
            cost_estimate.prompt_tokens
        ),
        completion_tokens=(
            cost_estimate.completion_tokens
        ),
        total_tokens=(
            cost_estimate.total_tokens
        ),
        latency_ms=max(
            int(latency_ms),
            0,
        ),
        estimated_cost_usd=float(
            cost_estimate.total_cost_usd
        ),
        success=False,
        error_message=cleaned_error,
    )

    model_call = create_model_call(
        db=db,
        payload=payload,
        commit=commit,
    )

    return RecordedModelCall(
        model_call=model_call,
        cost_estimate=cost_estimate,
    )