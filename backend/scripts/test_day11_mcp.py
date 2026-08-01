from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from mcp_server.local_file_server import WORKSPACE, read_local_text_file
from services.mcp_file_client import read_file_through_mcp
from services.mcp_tool_decision_service import choose_import_tool


def main() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    sample = WORKSPACE / "day11-test.md"
    sample.write_text(
        "# Semantic Search Notes\n\n"
        "PostgreSQL pgvector stores embeddings. "
        "I still need evaluation metrics and an indexing strategy.",
        encoding="utf-8",
    )

    try:
        direct = read_local_text_file("day11-test.md")
        assert direct["tool"] == "read_local_text_file"
        assert "pgvector" in direct["content"]

        through_protocol = asyncio.run(read_file_through_mcp("day11-test.md"))
        assert through_protocol.tool_name == "read_local_text_file"
        assert through_protocol.extension == ".md"
        assert through_protocol.characters > 20

        decision = choose_import_tool(
            "day11-test.md",
            "Import this Markdown file as a Brain Dump.",
        )
        assert decision.use_tool is True
        assert decision.tool_name == "read_local_text_file"

        print("MCP server: ThoughtLinker Local File Server")
        print("Registered tool: read_local_text_file")
        print(f"Tool chosen by: {decision.chosen_by}")
        print(f"Imported characters: {through_protocol.characters}")
        print("DAY 11 MCP LOCAL-FILE IMPORT TEST PASSED")
    finally:
        sample.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
