from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from models.ai_suggestion import AISuggestion
from services.guardrail_event_service import (
    log_guardrail_event,
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
    Generate a validated suggestion and save it to ai_suggestions.

    Behaviour:
        Valid output:
            Save one pending AISuggestion.

        Guardrail failure after all retries:
            Save the recorded failures to guardrail_events.
            Do not save an AISuggestion.

        Provider/configuration failure:
            Raise the error without creating a fake suggestion.
    """
    try:
        result = generate_small_model_suggestion(
            raw_text=raw_text,
            candidate_notes=candidate_notes,
        )

    except SmallModelGuardrailFailure as error:
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
                    },
                    commit=False,
                )

            db.commit()

        except Exception as persistence_error:
            db.rollback()

            raise SmallModelPersistenceError(
                "The model output failed guardrails, but its "
                "guardrail events could not be stored: "
                f"{persistence_error}"
            ) from persistence_error

        raise

    except SmallModelProviderError:
        # Invalid API key, network failure, rate limit, or provider
        # failure must not result in a stored suggestion.
        raise

    except SmallModelError:
        raise

    try:
        stored_suggestion = save_ai_suggestion(
            db=db,
            user_id=user_id,
            brain_dump_id=brain_dump_id,
            result=result,
            commit=True,
        )

    except Exception as error:
        db.rollback()

        raise SmallModelPersistenceError(
            f"Validated suggestion could not be stored: {error}"
        ) from error

    return stored_suggestion