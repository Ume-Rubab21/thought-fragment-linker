from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeGraphNode(BaseModel):
    id: str
    entity_id: uuid.UUID
    kind: Literal["note", "tag", "collection"]
    label: str
    subtitle: str = ""
    preview: str = ""
    collection_id: uuid.UUID | None = None
    collection_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None
    weight: int = Field(default=1, ge=1)


class KnowledgeGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    kind: Literal["related", "tagged", "collected"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    label: str = ""


class KnowledgeGraphResponse(BaseModel):
    nodes: list[KnowledgeGraphNode]
    edges: list[KnowledgeGraphEdge]
    total_note_count: int
    filtered_note_count: int
    visible_note_count: int
    tag_count: int
    connection_count: int
    focus_note_id: uuid.UUID | None = None
    truncated: bool = False
