from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from groq import Groq
from pydantic import ValidationError

from schemas.small_model import SmallModelSuggestion
from services.groq_config import GroqSettings, get_groq_settings
from services.small_model_guardrails import (
    GuardrailCategory,
    GuardrailFailure,
    GuardrailValidationError,
    validate_small_model_suggestion,
)
from services.small_model_prompt import (
    CandidateNote,
    LARGE_MODEL_SYSTEM_PROMPT,
    SMALL_MODEL_SYSTEM_PROMPT,
    build_small_model_user_prompt,
)

MAX_GUARDRAIL_RETRIES = 2
MAX_TOTAL_ATTEMPTS = 1 + MAX_GUARDRAIL_RETRIES


class SmallModelError(RuntimeError):
    """Base error for Groq model failures."""


class SmallModelConfigurationError(SmallModelError):
    """Raised when Groq configuration is invalid."""


class SmallModelProviderError(SmallModelError):
    """Raised when the Groq request itself fails."""


class SmallModelResponseError(SmallModelError):
    """Raised when Groq returns unusable structured output."""


class SmallModelGuardrailFailure(SmallModelError):
    """Final fail-closed result after all allowed attempts fail."""

    def __init__(self, failures: list[GuardrailFailure]) -> None:
        self.failures = failures
        reasons = "; ".join(failure.reason for failure in failures)
        super().__init__(
            "No valid suggestion generated after "
            f"{len(failures)} attempt(s). Reasons: {reasons}"
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


def _create_client(settings: GroqSettings) -> Groq:
    return Groq(api_key=settings.api_key)


def _extract_usage(response: Any) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0, 0

    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    total_tokens = int(
        getattr(usage, "total_tokens", prompt_tokens + completion_tokens) or 0
    )
    return prompt_tokens, completion_tokens, total_tokens


def _request_small_model(
    client: Groq,
    settings: GroqSettings,
    selected_model: str,
    raw_text: str,
    candidate_notes: Sequence[CandidateNote] | None,
    previous_error: str | None,
    model_tier: str,
) -> RawSmallModelResult:
    try:
        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        LARGE_MODEL_SYSTEM_PROMPT
                        if model_tier == "large"
                        else SMALL_MODEL_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": build_small_model_user_prompt(
                        raw_text=raw_text,
                        candidate_notes=candidate_notes,
                        previous_error=previous_error,
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=settings.temperature,
            max_completion_tokens=settings.max_tokens,
        )
    except Exception as error:
        raise SmallModelProviderError(f"Groq request failed: {error}") from error

    if not response.choices:
        raise SmallModelResponseError("Groq returned no completion choices.")

    content = response.choices[0].message.content
    if not content:
        raise SmallModelResponseError("Groq returned an empty response.")

    prompt_tokens, completion_tokens, total_tokens = _extract_usage(response)

    return RawSmallModelResult(
        content=content,
        model=selected_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def _normalize_reasoning_decision(value: object) -> object:
    if not isinstance(value, str):
        return value

    normalized = value.strip().lower()
    if normalized in {"new_note", "extend_existing", "uncertain"}:
        return normalized
    if "extend" in normalized or "existing note" in normalized:
        return "extend_existing"
    if (
        "new note" in normalized
        or "separate note" in normalized
        or "create a new" in normalized
        or "standalone" in normalized
    ):
        return "new_note"
    return "uncertain"


def _normalize_confidence_score(value: object) -> object:
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        numeric_value = float(value)
        if 0 <= numeric_value <= 1:
            numeric_value *= 100
        return max(0, min(100, round(numeric_value)))

    if isinstance(value, str):
        cleaned = value.strip().replace("%", "")
        try:
            numeric_value = float(cleaned)
        except ValueError:
            return value
        if 0 <= numeric_value <= 1:
            numeric_value *= 100
        return max(0, min(100, round(numeric_value)))

    return value


def _normalize_model_payload(parsed_content: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(parsed_content)

    if "reasoning_decision" in normalized:
        normalized["reasoning_decision"] = _normalize_reasoning_decision(
            normalized.get("reasoning_decision")
        )

    if "confidence_score" in normalized:
        normalized["confidence_score"] = _normalize_confidence_score(
            normalized.get("confidence_score")
        )

    if isinstance(normalized.get("tags"), list):
        normalized["tags"] = [
            tag[:30] if isinstance(tag, str) else tag
            for tag in normalized["tags"]
        ]

    return normalized


def _parse_and_validate_response(
    raw_content: str,
    source_text: str,
    allowed_note_ids: set[int] | None,
) -> SmallModelSuggestion:
    try:
        parsed_content = json.loads(raw_content)
    except json.JSONDecodeError as error:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=GuardrailCategory.SCHEMA_VALIDATION,
                reason="The model did not return valid JSON.",
            )
        ) from error

    if not isinstance(parsed_content, dict):
        raise GuardrailValidationError(
            GuardrailFailure(
                category=GuardrailCategory.SCHEMA_VALIDATION,
                reason="The model response must be a JSON object.",
            )
        )

    parsed_content = _normalize_model_payload(parsed_content)

    try:
        suggestion = SmallModelSuggestion.model_validate(parsed_content)
    except ValidationError as error:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=GuardrailCategory.SCHEMA_VALIDATION,
                reason=f"The JSON did not match the required schema: {error}",
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
    *,
    model_tier: str = "small",
) -> SmallModelResult:
    cleaned_text = raw_text.strip()
    if not cleaned_text:
        raise ValueError("Brain Dump text cannot be empty.")

    try:
        settings = get_groq_settings()
    except RuntimeError as error:
        raise SmallModelConfigurationError(str(error)) from error

    normalized_tier = model_tier.strip().lower()
    if normalized_tier == "small":
        selected_model = settings.small_model
    elif normalized_tier == "large":
        selected_model = settings.large_model
    else:
        raise ValueError("model_tier must be either 'small' or 'large'.")

    client = _create_client(settings)
    allowed_note_ids = (
        {note.id for note in candidate_notes}
        if candidate_notes
        else None
    )

    failures: list[GuardrailFailure] = []
    previous_error: str | None = None
    accumulated_prompt_tokens = 0
    accumulated_completion_tokens = 0
    accumulated_total_tokens = 0

    for attempt_number in range(1, MAX_TOTAL_ATTEMPTS + 1):
        raw_result = _request_small_model(
            client=client,
            settings=settings,
            selected_model=selected_model,
            raw_text=cleaned_text,
            candidate_notes=candidate_notes,
            previous_error=previous_error,
            model_tier=normalized_tier,
        )

        accumulated_prompt_tokens += raw_result.prompt_tokens
        accumulated_completion_tokens += raw_result.completion_tokens
        accumulated_total_tokens += raw_result.total_tokens

        try:
            suggestion = _parse_and_validate_response(
                raw_content=raw_result.content,
                source_text=cleaned_text,
                allowed_note_ids=allowed_note_ids,
            )
        except GuardrailValidationError as error:
            failures.append(error.failure)
            previous_error = error.failure.reason
            continue

        if normalized_tier == "large" and (
            suggestion.reasoning_decision is None
            or not suggestion.reasoning
            or suggestion.confidence_score is None
        ):
            failure = GuardrailFailure(
                category=GuardrailCategory.SCHEMA_VALIDATION,
                reason=(
                    "The large reasoning model must return reasoning_decision, "
                    "reasoning, and confidence_score."
                ),
            )
            failures.append(failure)
            previous_error = failure.reason
            continue

        return SmallModelResult(
            suggestion=suggestion,
            model=raw_result.model,
            prompt_tokens=accumulated_prompt_tokens,
            completion_tokens=accumulated_completion_tokens,
            total_tokens=accumulated_total_tokens,
            attempts=attempt_number,
            retry_count=attempt_number - 1,
        )

    raise SmallModelGuardrailFailure(failures=failures)
