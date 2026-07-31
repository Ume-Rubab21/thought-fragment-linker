from __future__ import annotations

import time
import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from models.ai_suggestion import AISuggestion
from services.brain_dump_similarity_service import (
    find_brain_dump_candidates,
)
from services.groq_config import get_groq_settings
from services.guardrail_event_service import (
    log_guardrail_event,
)
from services.model_call_service import (
    record_failed_model_call,
    record_successful_model_call,
)
from services.model_routing_service import (
    route_from_similarity_scores,
)
from services.small_model_prompt import CandidateNote
from services.small_model_service import (
    SmallModelError,
    SmallModelGuardrailFailure,
    SmallModelProviderError,
    generate_small_model_suggestion,
)
from services.suggestion_service import (
    save_ai_suggestion,
)


class SmallModelPersistenceError(RuntimeError):
    """
    Raised when the complete generation and persistence workflow fails.
    """


def generate_and_store_suggestion(
    db: Session,
    *,
    user_id: uuid.UUID,
    brain_dump_id: uuid.UUID,
    raw_text: str,
    candidate_notes: Sequence[CandidateNote] | None = None,
) -> AISuggestion:
    """
    Retrieve candidate Notes, choose the model tier, execute the model,
    log the model call, and persist one validated suggestion.
    """

    if candidate_notes is None:
        candidate_result = find_brain_dump_candidates(
            db=db,
            user_id=user_id,
            raw_text=raw_text,
        )
        active_candidate_notes = (
            candidate_result.candidate_notes
        )
        similarity_scores = (
            candidate_result.similarity_scores
        )
    else:
        active_candidate_notes = list(
            candidate_notes
        )
        similarity_scores = [
            note.similarity
            for note in active_candidate_notes
        ]

    routing = route_from_similarity_scores(
        similarity_scores
    )

    settings = get_groq_settings()

    selected_model = (
        settings.large_model
        if routing.model_tier == "large"
        else settings.small_model
    )

    started_at = time.perf_counter()

    try:
        result = generate_small_model_suggestion(
            raw_text=raw_text,
            candidate_notes=active_candidate_notes,
            model_tier=routing.model_tier,
        )

    except SmallModelGuardrailFailure as error:
        latency_ms = int(
            (time.perf_counter() - started_at)
            * 1000
        )

        try:
            for attempt_number, failure in enumerate(
                error.failures,
                start=1,
            ):
                log_guardrail_event(
                    db=db,
                    user_id=user_id,
                    brain_dump_id=brain_dump_id,
                    attempt_number=attempt_number,
                    failure=failure,
                    failure_metadata={
                        "retry_allowed": (
                            attempt_number
                            < len(error.failures)
                        ),
                        "final_failure": (
                            attempt_number
                            == len(error.failures)
                        ),
                        "source": (
                            "generate_and_store_suggestion"
                        ),
                        "routing_decision": (
                            routing.routing_decision
                        ),
                        "model_tier": (
                            routing.model_tier
                        ),
                    },
                    commit=False,
                )

            db.commit()

            record_failed_model_call(
                db=db,
                user_id=user_id,
                brain_dump_id=brain_dump_id,
                provider="groq",
                model_name=selected_model,
                routing=routing,
                latency_ms=latency_ms,
                error_message=str(error),
                commit=True,
            )

        except Exception as persistence_error:
            db.rollback()

            raise SmallModelPersistenceError(
                "The model output failed guardrails, but its "
                "failure records could not be stored: "
                f"{persistence_error}"
            ) from persistence_error

        raise

    except SmallModelProviderError as error:
        latency_ms = int(
            (time.perf_counter() - started_at)
            * 1000
        )

        record_failed_model_call(
            db=db,
            user_id=user_id,
            brain_dump_id=brain_dump_id,
            provider="groq",
            model_name=selected_model,
            routing=routing,
            latency_ms=latency_ms,
            error_message=str(error),
            commit=True,
        )

        raise

    except SmallModelError as error:
        latency_ms = int(
            (time.perf_counter() - started_at)
            * 1000
        )

        record_failed_model_call(
            db=db,
            user_id=user_id,
            brain_dump_id=brain_dump_id,
            provider="groq",
            model_name=selected_model,
            routing=routing,
            latency_ms=latency_ms,
            error_message=str(error),
            commit=True,
        )

        raise

    latency_ms = int(
        (time.perf_counter() - started_at)
        * 1000
    )

    try:
        stored_suggestion = save_ai_suggestion(
            db=db,
            user_id=user_id,
            brain_dump_id=brain_dump_id,
            result=result,
            reasoning_tier=routing.model_tier,
            commit=True,
        )

        record_successful_model_call(
            db=db,
            user_id=user_id,
            brain_dump_id=brain_dump_id,
            provider="groq",
            model_name=result.model,
            routing=routing,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            latency_ms=latency_ms,
            commit=True,
        )

    except Exception as error:
        db.rollback()

        raise SmallModelPersistenceError(
            f"Validated suggestion could not be stored: {error}"
        ) from error

    return stored_suggestion
