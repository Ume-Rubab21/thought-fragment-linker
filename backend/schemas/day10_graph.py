from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeGapResponse(BaseModel):
    title: str
    description: str
    evidence: str


class BrainDumpGapResponse(BaseModel):
    brain_dump_id: str
    gaps: list[KnowledgeGapResponse] = Field(default_factory=list)


class BrainDumpGraphResponse(BaseModel):
    engine: str
    available: bool
    nodes: list[str]
    edges: list[list[str]]
    fallback: str
