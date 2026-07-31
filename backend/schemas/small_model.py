from __future__ import annotations

import re
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TAG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KEYWORD_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\s\-+.#/]*$", re.IGNORECASE)


def normalize_tag(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[\s_/]+", "-", normalized)
    normalized = re.sub(r"[^a-z0-9-]", "", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized)
    normalized = normalized.strip("-")

    if len(normalized) > 30:
        normalized = normalized[:30].rstrip("-")

    return normalized


def normalize_keyword(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def normalize_unique_strings(values: list[str], normalizer) -> list[str]:
    normalized_values: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not isinstance(value, str):
            raise ValueError("Every value must be a string.")

        normalized = normalizer(value)

        if not normalized:
            raise ValueError("Empty values are not allowed.")

        if normalized not in seen:
            seen.add(normalized)
            normalized_values.append(normalized)

    return normalized_values


class SmallModelSuggestion(BaseModel):
    """Validated structured output returned by the selected model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    suggested_title: str = Field(..., min_length=3, max_length=120)
    summary: str = Field(..., min_length=10, max_length=500)
    tags: list[str] = Field(..., min_length=1, max_length=6)
    keywords: list[str] = Field(..., min_length=1, max_length=10)
    related_note_ids: list[uuid.UUID] = Field(default_factory=list, max_length=5)

    reasoning_decision: Literal[
        "new_note",
        "extend_existing",
        "uncertain",
    ] | None = None

    reasoning: str | None = Field(default=None, min_length=20, max_length=800)
    confidence_score: int | None = Field(default=None, ge=0, le=100)

    @field_validator("suggested_title", "summary")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("The text value cannot be blank.")
        return value.strip()

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value):
        if not isinstance(value, list):
            raise ValueError("Tags must be returned as a list.")
        return normalize_unique_strings(value, normalize_tag)

    @field_validator("tags")
    @classmethod
    def validate_tag_format(cls, values: list[str]) -> list[str]:
        for tag in values:
            if not TAG_PATTERN.fullmatch(tag):
                raise ValueError(f"Tag '{tag}' has an invalid format.")
        return values

    @field_validator("keywords", mode="before")
    @classmethod
    def normalize_keywords(cls, value):
        if not isinstance(value, list):
            raise ValueError("Keywords must be returned as a list.")
        return normalize_unique_strings(value, normalize_keyword)

    @field_validator("keywords")
    @classmethod
    def validate_keyword_format(cls, values: list[str]) -> list[str]:
        for keyword in values:
            if len(keyword) > 60:
                raise ValueError(f"Keyword '{keyword}' exceeds 60 characters.")
            if not KEYWORD_PATTERN.fullmatch(keyword):
                raise ValueError(f"Keyword '{keyword}' has an invalid format.")
        return values

    @field_validator("related_note_ids", mode="before")
    @classmethod
    def normalize_related_note_ids(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("related_note_ids must be a list.")

        normalized_ids: list[uuid.UUID] = []
        seen: set[uuid.UUID] = set()

        for note_id in value:
            if isinstance(note_id, bool):
                raise ValueError("Boolean values are not valid note IDs.")
            try:
                normalized_id = uuid.UUID(str(note_id))
            except (TypeError, ValueError, AttributeError) as error:
                raise ValueError(f"Invalid related note ID: {note_id}") from error
            if normalized_id not in seen:
                seen.add(normalized_id)
                normalized_ids.append(normalized_id)

        return normalized_ids
