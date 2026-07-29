from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from groq import Groq
from pydantic import ValidationError

from schemas.small_model import SmallModelSuggestion
from services.groq_config import (
    GroqSettings,
    get_groq_settings,
)
from services.small_model_guardrails import (
    GuardrailCategory,
    GuardrailFailure,
    GuardrailValidationError,
    validate_small_model_suggestion,
)
from services.small_model_prompt import (
    CandidateNote,
    SMALL_MODEL_SYSTEM_PROMPT,
    build_small_model_user_prompt,
)


MAX_GUARDRAIL_RETRIES = 2
MAX_TOTAL_ATTEMPTS = 1 + MAX_GUARDRAIL_RETRIES


class SmallModelError(RuntimeError):
    """
    Base error for Groq small-model failures.
    """


class SmallModelConfigurationError(
    SmallModelError
):
    """
    Raised when Groq configuration is invalid.
    """


class SmallModelProviderError(
    SmallModelError
):
    """
    Raised when the Groq request itself fails.
    """


class SmallModelResponseError(
    SmallModelError
):
    """
    Raised when Groq returns unusable structured output.
    """


class SmallModelGuardrailFailure(
    SmallModelError
):
    """
    Final fail-closed result after all allowed attempts fail.
    """

    def __init__(
        self,
        failures: list[GuardrailFailure],
    ) -> None:
        self.failures = failures

        reasons = "; ".join(
            failure.reason
            for failure in failures
        )

        super().__init__(
            "No valid suggestion generated after "
            f"{len(failures)} attempt(s). "
            f"Reasons: {reasons}"
        )


@dataclass(frozen=True)
class SmallModelResult:
    suggestion: SmallModelSuggestion
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    attempts: int
    retry_count: int


@dataclass(frozen=True)
class RawSmallModelResult:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def _create_client(
    settings: GroqSettings,
) -> Groq:
    return Groq(
        api_key=settings.api_key
    )


def _extract_usage(
    response: Any,
) -> tuple[int, int, int]:
    usage = getattr(
        response,
        "usage",
        None,
    )

    if usage is None:
        return 0, 0, 0

    prompt_tokens = int(
        getattr(
            usage,
            "prompt_tokens",
            0,
        )
        or 0
    )

    completion_tokens = int(
        getattr(
            usage,
            "completion_tokens",
            0,
        )
        or 0
    )

    total_tokens = int(
        getattr(
            usage,
            "total_tokens",
            prompt_tokens + completion_tokens,
        )
        or 0
    )

    return (
        prompt_tokens,
        completion_tokens,
        total_tokens,
    )


def _request_small_model(
    client: Groq,
    settings: GroqSettings,
    raw_text: str,
    candidate_notes: Sequence[CandidateNote] | None,
    previous_error: str | None,
) -> RawSmallModelResult:
    """
    Perform one Groq request.

    Guardrail retries are controlled by the public function rather
    than being hidden inside this function.
    """
    try:
        response = client.chat.completions.create(
            model=settings.small_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        SMALL_MODEL_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        build_small_model_user_prompt(
                            raw_text=raw_text,
                            candidate_notes=candidate_notes,
                            previous_error=previous_error,
                        )
                    ),
                },
            ],
            response_format={
                "type": "json_object",
            },
            temperature=settings.temperature,
            max_completion_tokens=settings.max_tokens,
        )
    except Exception as error:
        raise SmallModelProviderError(
            f"Groq request failed: {error}"
        ) from error

    if not response.choices:
        raise SmallModelResponseError(
            "Groq returned no completion choices."
        )

    content = response.choices[0].message.content

    if not content:
        raise SmallModelResponseError(
            "Groq returned an empty response."
        )

    (
        prompt_tokens,
        completion_tokens,
        total_tokens,
    ) = _extract_usage(response)

    return RawSmallModelResult(
        content=content,
        model=settings.small_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def _parse_and_validate_response(
    raw_content: str,
    source_text: str,
    allowed_note_ids: set[int] | None,
) -> SmallModelSuggestion:
    try:
        parsed_content = json.loads(
            raw_content
        )
    except json.JSONDecodeError as error:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=(
                    GuardrailCategory.SCHEMA_VALIDATION
                ),
                reason=(
                    "The model did not return valid JSON."
                ),
            )
        ) from error

    try:
        suggestion = (
            SmallModelSuggestion.model_validate(
                parsed_content
            )
        )
    except ValidationError as error:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=(
                    GuardrailCategory.SCHEMA_VALIDATION
                ),
                reason=(
                    "The JSON did not match the required "
                    f"schema: {error}"
                ),
            )
        ) from error

    return validate_small_model_suggestion(
        source_text=source_text,
        suggestion=suggestion,
        allowed_note_ids=allowed_note_ids,
    )


def generate_small_model_suggestion(
    raw_text: str,
    candidate_notes: Sequence[CandidateNote] | None = None,
) -> SmallModelResult:
    """
    Generate and validate a structured suggestion.

    Retry policy:
        Initial request + at most 2 retries.

    Fail-closed policy:
        No suggestion object is returned when validation continues
        to fail after all attempts.
    """
    cleaned_text = raw_text.strip()

    if not cleaned_text:
        raise ValueError(
            "Brain Dump text cannot be empty."
        )

    try:
        settings = get_groq_settings()
    except RuntimeError as error:
        raise SmallModelConfigurationError(
            str(error)
        ) from error

    client = _create_client(
        settings
    )

    allowed_note_ids = (
        {
            note.id
            for note in candidate_notes
        }
        if candidate_notes
        else None
    )

    failures: list[GuardrailFailure] = []
    previous_error: str | None = None

    accumulated_prompt_tokens = 0
    accumulated_completion_tokens = 0
    accumulated_total_tokens = 0

    for attempt_number in range(
        1,
        MAX_TOTAL_ATTEMPTS + 1,
    ):
        try:
            raw_result = _request_small_model(
                client=client,
                settings=settings,
                raw_text=cleaned_text,
                candidate_notes=candidate_notes,
                previous_error=previous_error,
            )
        except SmallModelProviderError:
            # Provider failures are not schema failures. We fail
            # immediately instead of repeatedly charging/retrying
            # an invalid key or unavailable request.
            raise

        accumulated_prompt_tokens += (
            raw_result.prompt_tokens
        )

        accumulated_completion_tokens += (
            raw_result.completion_tokens
        )

        accumulated_total_tokens += (
            raw_result.total_tokens
        )

        try:
            suggestion = (
                _parse_and_validate_response(
                    raw_content=raw_result.content,
                    source_text=cleaned_text,
                    allowed_note_ids=(
                        allowed_note_ids
                    ),
                )
            )
        except GuardrailValidationError as error:
            failures.append(
                error.failure
            )

            previous_error = (
                error.failure.reason
            )

            continue

        return SmallModelResult(
            suggestion=suggestion,
            model=raw_result.model,
            prompt_tokens=(
                accumulated_prompt_tokens
            ),
            completion_tokens=(
                accumulated_completion_tokens
            ),
            total_tokens=(
                accumulated_total_tokens
            ),
            attempts=attempt_number,
            retry_count=attempt_number - 1,
        )

    # No valid object escapes this function after final failure.
    raise SmallModelGuardrailFailure(
        failures=failures
    )