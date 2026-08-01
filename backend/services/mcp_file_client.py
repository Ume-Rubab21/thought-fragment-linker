from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


BACKEND_DIR = Path(__file__).resolve().parents[1]
SERVER_SCRIPT = BACKEND_DIR / "mcp_server" / "local_file_server.py"


@dataclass(frozen=True)
class MCPFileReadResult:
    tool_name: str
    file_name: str
    extension: str
    characters: int
    content: str
    pages: int | None = None
    ocr_used: bool = False
    ocr_pages: list[int] = field(default_factory=list)
    image_regions_ocrd: int = 0
    warnings: list[str] = field(default_factory=list)


def _decode_tool_result(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured

    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise RuntimeError("The MCP server returned an unreadable response.")


async def read_file_through_mcp(relative_path: str) -> MCPFileReadResult:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT)],
        cwd=str(BACKEND_DIR),
    )

    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            if "read_local_text_file" not in names:
                raise RuntimeError("The local-file MCP tool is not registered.")

            result = await session.call_tool(
                "read_local_text_file",
                {"relative_path": relative_path},
            )
            payload = _decode_tool_result(result)

    return MCPFileReadResult(
        tool_name=str(payload["tool"]),
        file_name=str(payload["file_name"]),
        extension=str(payload["extension"]),
        characters=int(payload["characters"]),
        content=str(payload["content"]),
        pages=int(payload["pages"]) if payload.get("pages") is not None else None,
        ocr_used=bool(payload.get("ocr_used", False)),
        ocr_pages=[int(value) for value in payload.get("ocr_pages", [])],
        image_regions_ocrd=int(payload.get("image_regions_ocrd", 0)),
        warnings=[str(value) for value in payload.get("warnings", [])],
    )


def read_file_through_mcp_sync(relative_path: str) -> MCPFileReadResult:
    return asyncio.run(read_file_through_mcp(relative_path))
