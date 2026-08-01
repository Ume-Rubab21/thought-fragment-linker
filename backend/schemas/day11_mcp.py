from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MCPToolInfo(BaseModel):
    tool_name: str
    chosen_by: Literal["model", "fallback"]
    reason: str
    file_name: str
    extension: str
    characters: int
    pages: int | None = None
    ocr_used: bool = False
    ocr_pages: list[int] = Field(default_factory=list)
    image_regions_ocrd: int = 0
    warnings: list[str] = Field(default_factory=list)


class BrainDumpFileImportResponse(BaseModel):
    brain_dump_id: uuid.UUID
    status: str
    imported_text: str = Field(max_length=20_000)
    tool: MCPToolInfo
    created_at: datetime


class MCPServerInspectResponse(BaseModel):
    server_name: str
    transport: str
    tools: list[str]
    supported_extensions: list[str]
    max_file_bytes: int