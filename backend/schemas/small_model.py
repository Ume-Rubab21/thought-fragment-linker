from __future__ import annotations

import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


TAG_PATTERN = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)

KEYWORD_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9\s\-+.#/]*$",
    re.IGNORECASE,
)


def normalize_tag(value: str) -> str:
    """
    Convert a model-generated tag into the canonical format.

    Examples:
        "Semantic Search" -> "semantic-search"
        "  PostgreSQL  "  -> "postgresql"
        "React_Hooks"     -> "react-hooks"
    """
    normalized = value.strip().lower()

    normalized = re.sub(
        r"[\s_/]+",
        "-",
        normalized,
    )

    normalized = re.sub(
        r"[^a-z0-9-]",
        "",
        normalized,
    )

    normalized = re.sub(
        r"-{2,}",
        "-",
        normalized,
    )

    return normalized.strip("-")


def normalize_keyword(value: str) -> str:
    """
    Normalize keywords while allowing useful phrases.
    """
    normalized = value.strip().lower()

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized


def normalize_unique_strings(
    values: list[str],
    normalizer,
) -> list[str]:
    """
    Normalize values and remove duplicates while preserving order.
    """
    normalized_values: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not isinstance(value, str):
            raise ValueError(
                "Every value must be a string."
            )

        normalized = normalizer(value)

        if not normalized:
            raise ValueError(
                "Empty values are not allowed."
            )

        if normalized not in seen:
            seen.add(normalized)
            normalized_values.append(normalized)

    return normalized_values


class SmallModelSuggestion(BaseModel):
    """
    Validated structured output returned by the Groq small model.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    suggested_title: str = Field(
        ...,
        min_length=3,
        max_length=120,
    )

    summary: str = Field(
        ...,
        min_length=10,
        max_length=500,
    )

    tags: list[str] = Field(
        ...,
        min_length=1,
        max_length=6,
    )

    keywords: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
    )

    related_note_ids: list[int] = Field(
        default_factory=list,
        max_length=5,
    )

    @field_validator(
        "suggested_title",
        "summary",
    )
    @classmethod
    def reject_blank_text(
        cls,
        value: str,
    ) -> str:
        if not value.strip():
            raise ValueError(
                "The text value cannot be blank."
            )

        return value.strip()

    @field_validator(
        "tags",
        mode="before",
    )
    @classmethod
    def normalize_tags(
        cls,
        value,
    ):
        if not isinstance(value, list):
            raise ValueError(
                "Tags must be returned as a list."
            )

        return normalize_unique_strings(
            value,
            normalize_tag,
        )

    @field_validator("tags")
    @classmethod
    def validate_tag_format(
        cls,
        values: list[str],
    ) -> list[str]:
        for tag in values:
            if len(tag) > 30:
                raise ValueError(
                    f"Tag '{tag}' exceeds 30 characters."
                )

            if not TAG_PATTERN.fullmatch(tag):
                raise ValueError(
                    f"Tag '{tag}' has an invalid format."
                )

        return values

    @field_validator(
        "keywords",
        mode="before",
    )
    @classmethod
    def normalize_keywords(
        cls,
        value,
    ):
        if not isinstance(value, list):
            raise ValueError(
                "Keywords must be returned as a list."
            )

        return normalize_unique_strings(
            value,
            normalize_keyword,
        )

    @field_validator("keywords")
    @classmethod
    def validate_keyword_format(
        cls,
        values: list[str],
    ) -> list[str]:
        for keyword in values:
            if len(keyword) > 60:
                raise ValueError(
                    f"Keyword '{keyword}' exceeds 60 characters."
                )

            if not KEYWORD_PATTERN.fullmatch(keyword):
                raise ValueError(
                    f"Keyword '{keyword}' has an invalid format."
                )

        return values

    @field_validator(
        "related_note_ids",
        mode="before",
    )
    @classmethod
    def normalize_related_note_ids(
        cls,
        value,
    ):
        if value is None:
            return []

        if not isinstance(value, list):
            raise ValueError(
                "related_note_ids must be a list."
            )

        normalized_ids: list[int] = []
        seen: set[int] = set()

        for note_id in value:
            if isinstance(note_id, bool):
                raise ValueError(
                    "Boolean values are not valid note IDs."
                )

            try:
                normalized_id = int(note_id)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid related note ID: {note_id}"
                ) from error

            if normalized_id <= 0:
                raise ValueError(
                    "Related note IDs must be positive integers."
                )

            if normalized_id not in seen:
                seen.add(normalized_id)
                normalized_ids.append(normalized_id)

        return normalized_ids