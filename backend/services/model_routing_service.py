from __future__ import annotations

from collections.abc import Iterable

from schemas.model_routing import RoutingEvaluation, RoutingThresholds


DEFAULT_LOW_THRESHOLD = 0.35
DEFAULT_HIGH_THRESHOLD = 0.70


class ModelRoutingError(RuntimeError):
    """Base error for model-routing operations."""


class InvalidSimilarityScoreError(ModelRoutingError):
    """Raised when a similarity score is outside the valid range."""


def normalize_similarity_score(value: float | int) -> float:
    """Convert a similarity value to a float between 0 and 1."""
    try:
        score = float(value)
    except (TypeError, ValueError) as error:
        raise InvalidSimilarityScoreError(
            f"Invalid similarity score: {value!r}."
        ) from error

    if not 0 <= score <= 1:
        raise InvalidSimilarityScoreError(
            "Similarity scores must be between 0 and 1."
        )

    return score


def get_highest_similarity(
    similarity_scores: Iterable[float | int] | None,
) -> float:
    """Return the highest valid score, or 0.0 when none exist."""
    if similarity_scores is None:
        return 0.0

    normalized_scores = [
        normalize_similarity_score(score)
        for score in similarity_scores
    ]

    if not normalized_scores:
        return 0.0

    return max(normalized_scores)


def evaluate_model_route(
    *,
    highest_similarity: float,
    thresholds: RoutingThresholds | None = None,
) -> RoutingEvaluation:
    """Select the model tier using deterministic similarity thresholds."""
    score = normalize_similarity_score(highest_similarity)

    active_thresholds = thresholds or RoutingThresholds(
        low=DEFAULT_LOW_THRESHOLD,
        high=DEFAULT_HIGH_THRESHOLD,
    )

    if score > active_thresholds.high:
        return RoutingEvaluation(
            highest_similarity=score,
            low_threshold=active_thresholds.low,
            high_threshold=active_thresholds.high,
            model_tier="small",
            routing_decision="small-related",
            routing_reason=(
                "The highest similarity score is above the high threshold, "
                "so the Brain Dump is clearly related to existing notes and "
                "can be handled by the small model."
            ),
        )

    if score >= active_thresholds.low:
        return RoutingEvaluation(
            highest_similarity=score,
            low_threshold=active_thresholds.low,
            high_threshold=active_thresholds.high,
            model_tier="large",
            routing_decision="large-ambiguous",
            routing_reason=(
                "The highest similarity score falls between the low and high "
                "thresholds, so the relation is ambiguous and requires the "
                "large reasoning model."
            ),
        )

    return RoutingEvaluation(
        highest_similarity=score,
        low_threshold=active_thresholds.low,
        high_threshold=active_thresholds.high,
        model_tier="small",
        routing_decision="small-new-topic",
        routing_reason=(
            "The highest similarity score is below the low threshold, so the "
            "Brain Dump is treated as a new topic and can be handled by the "
            "small model."
        ),
    )


def route_from_similarity_scores(
    similarity_scores: Iterable[float | int] | None,
    *,
    thresholds: RoutingThresholds | None = None,
) -> RoutingEvaluation:
    """Calculate the highest score and return a routing evaluation."""
    highest_similarity = get_highest_similarity(similarity_scores)

    return evaluate_model_route(
        highest_similarity=highest_similarity,
        thresholds=thresholds,
    )