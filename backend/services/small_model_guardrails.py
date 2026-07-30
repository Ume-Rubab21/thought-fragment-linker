from __future__ import annotations

import re
import uuid
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from enum import Enum

from schemas.small_model import SmallModelSuggestion


class GuardrailCategory(str, Enum):
    SCHEMA_VALIDATION = "schema_validation"
    TAG_VOCABULARY = "tag_vocabulary"
    TAG_RELEVANCE = "tag_relevance"
    KEYWORD_RELEVANCE = "keyword_relevance"
    REFERENTIAL_VALIDATION = "referential_validation"
    EMPTY_SOURCE = "empty_source"
    PROVIDER_FAILURE = "provider_failure"


@dataclass(frozen=True)
class GuardrailFailure:
    category: GuardrailCategory
    reason: str


class GuardrailValidationError(ValueError):
    """
    Raised when structured model output fails a guardrail.
    """

    def __init__(
        self,
        failure: GuardrailFailure,
    ) -> None:
        self.failure = failure

        super().__init__(
            f"{failure.category.value}: {failure.reason}"
        )


GENERIC_TAGS = {
    "general",
    "misc",
    "miscellaneous",
    "other",
    "random",
    "stuff",
    "thing",
    "things",
    "thought",
    "thoughts",
    "note",
    "notes",
    "brain-dump",
    "uncategorized",
    "unknown",
}

GENERIC_KEYWORDS = {
    "general",
    "misc",
    "random",
    "something",
    "stuff",
    "thing",
    "things",
    "thought",
    "thoughts",
}

# A small vocabulary map permits useful conceptual tags when the exact
# tag is not written in the source text.
TAG_ALIASES: dict[str, set[str]] = {
    "frontend": {
        "react",
        "jsx",
        "browser",
        "css",
        "responsive",
        "sidebar",
        "component",
        "components",
    },
    "backend": {
        "fastapi",
        "python",
        "api",
        "endpoint",
        "server",
        "database",
    },
    "database": {
        "postgres",
        "postgresql",
        "sql",
        "pgvector",
        "table",
        "query",
    },
    "semantic-search": {
        "semantic",
        "similarity",
        "embedding",
        "embeddings",
        "pgvector",
        "cosine",
        "vector",
    },
    "embeddings": {
        "embedding",
        "embeddings",
        "minilm",
        "vector",
        "vectors",
    },
    "artificial-intelligence": {
        "ai",
        "model",
        "llm",
        "groq",
        "llama",
        "prompt",
    },
    "machine-learning": {
        "machine",
        "learning",
        "model",
        "training",
        "dataset",
    },
    "fitness": {
        "exercise",
        "workout",
        "gym",
        "running",
        "health",
    },
    "productivity": {
        "task",
        "tasks",
        "planning",
        "routine",
        "focus",
        "schedule",
    },
}

TOKEN_PATTERN = re.compile(
    r"[a-z0-9+#.]+",
    re.IGNORECASE,
)


def tokenize(value: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_PATTERN.findall(value)
        if len(token) >= 2
    }


def split_tag_tokens(tag: str) -> set[str]:
    return {
        token
        for token in tag.split("-")
        if token
    }


def validate_source_text(
    source_text: str,
) -> str:
    cleaned_text = source_text.strip()

    if not cleaned_text:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=GuardrailCategory.EMPTY_SOURCE,
                reason="Brain Dump text cannot be empty.",
            )
        )

    if len(cleaned_text) < 10:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=GuardrailCategory.EMPTY_SOURCE,
                reason=(
                    "Brain Dump text is too short to generate "
                    "reliable metadata."
                ),
            )
        )

    return cleaned_text


def validate_tag_vocabulary(
    tags: Sequence[str],
) -> None:
    for tag in tags:
        if tag in GENERIC_TAGS:
            raise GuardrailValidationError(
                GuardrailFailure(
                    category=GuardrailCategory.TAG_VOCABULARY,
                    reason=(
                        f"Tag '{tag}' is too generic to be useful."
                    ),
                )
            )

        if tag.isdigit():
            raise GuardrailValidationError(
                GuardrailFailure(
                    category=GuardrailCategory.TAG_VOCABULARY,
                    reason=(
                        f"Tag '{tag}' cannot contain only numbers."
                    ),
                )
            )


def tag_is_grounded(
    tag: str,
    source_tokens: set[str],
) -> bool:
    tag_tokens = split_tag_tokens(tag)

    if tag_tokens and tag_tokens.issubset(source_tokens):
        return True

    if tag_tokens.intersection(source_tokens):
        return True

    alias_tokens = TAG_ALIASES.get(tag, set())

    if alias_tokens.intersection(source_tokens):
        return True

    return False


def validate_tag_relevance(
    source_text: str,
    tags: Sequence[str],
) -> None:
    source_tokens = tokenize(source_text)

    ungrounded_tags = [
        tag
        for tag in tags
        if not tag_is_grounded(
            tag,
            source_tokens,
        )
    ]

    if ungrounded_tags:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=GuardrailCategory.TAG_RELEVANCE,
                reason=(
                    "The following tags are not supported by "
                    f"the source text: {ungrounded_tags}"
                ),
            )
        )


def validate_keyword_relevance(
    source_text: str,
    keywords: Sequence[str],
) -> None:
    source_tokens = tokenize(source_text)

    grounded_keywords = 0
    unsupported_keywords: list[str] = []

    for keyword in keywords:
        keyword_tokens = tokenize(keyword)

        if keyword_tokens.intersection(source_tokens):
            grounded_keywords += 1
        else:
            unsupported_keywords.append(keyword)

    # Permit a limited number of inferred phrases, but require most
    # keywords to be supported by the source text.
    required_grounded_count = max(
        1,
        (len(keywords) + 1) // 2,
    )

    if grounded_keywords < required_grounded_count:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=GuardrailCategory.KEYWORD_RELEVANCE,
                reason=(
                    "Too many keywords are unsupported by the "
                    f"source text: {unsupported_keywords}"
                ),
            )
        )

    for keyword in keywords:
        if keyword in GENERIC_KEYWORDS:
            raise GuardrailValidationError(
                GuardrailFailure(
                    category=GuardrailCategory.KEYWORD_RELEVANCE,
                    reason=(
                        f"Keyword '{keyword}' is too generic."
                    ),
                )
            )


def validate_related_note_ids(
    suggested_note_ids: Sequence[uuid.UUID],
    allowed_note_ids: Collection[uuid.UUID] | None,
) -> None:
    """
    Confirm that every model-selected ID came from the user's
    candidate-note list.

    The caller must build allowed_note_ids using a database query
    filtered by the current authenticated user's ID.
    """
    if not suggested_note_ids:
        return

    if allowed_note_ids is None:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=(
                    GuardrailCategory.REFERENTIAL_VALIDATION
                ),
                reason=(
                    "Related note IDs were returned even though "
                    "no candidate-note list was provided."
                ),
            )
        )

    allowed_ids = {
        uuid.UUID(str(note_id))
        for note_id in allowed_note_ids
    }

    invalid_ids = [
        note_id
        for note_id in suggested_note_ids
        if note_id not in allowed_ids
    ]

    if invalid_ids:
        raise GuardrailValidationError(
            GuardrailFailure(
                category=(
                    GuardrailCategory.REFERENTIAL_VALIDATION
                ),
                reason=(
                    "The model returned note IDs that do not "
                    "belong to the allowed user-specific "
                    f"candidate list: {invalid_ids}"
                ),
            )
        )


def validate_small_model_suggestion(
    source_text: str,
    suggestion: SmallModelSuggestion,
    allowed_note_ids: Collection[uuid.UUID] | None = None,
) -> SmallModelSuggestion:
    """
    Run all deterministic guardrails.

    Returns the suggestion only when every check passes.
    """
    cleaned_source = validate_source_text(
        source_text
    )

    validate_tag_vocabulary(
        suggestion.tags
    )

    validate_tag_relevance(
        cleaned_source,
        suggestion.tags,
    )

    validate_keyword_relevance(
        cleaned_source,
        suggestion.keywords,
    )

    validate_related_note_ids(
        suggestion.related_note_ids,
        allowed_note_ids,
    )

    return suggestion