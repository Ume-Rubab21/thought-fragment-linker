import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = BACKEND_DIR / "mcp_workspace" / "imports"
WORKSPACE = Path(
    os.getenv(
        "THOUGHTLINKER_MCP_WORKSPACE",
        str(DEFAULT_WORKSPACE),
    )
).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".md"}
MAX_FILE_BYTES = 2 * 1024 * 1024

mcp = FastMCP("ThoughtLinker Local File Server")


def resolve_safe_file(relative_path: str) -> Path:
    candidate = (WORKSPACE / relative_path).resolve()

    try:
        candidate.relative_to(WORKSPACE)
    except ValueError as error:
        raise ValueError(
            "The requested file is outside the MCP workspace."
        ) from error

    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Only .txt and .md files are supported."
        )

    if not candidate.is_file():
        raise FileNotFoundError(
            "The requested file does not exist."
        )

    if candidate.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(
            "The file exceeds the 2 MB import limit."
        )

    return candidate


@mcp.tool()
def read_local_text_file(
    relative_path: str,
) -> dict[str, Any]:
    """Read one UTF-8 .txt or .md file from the protected import workspace."""
    path = resolve_safe_file(relative_path)

    try:
        text = path.read_text(
            encoding="utf-8-sig",
        )
    except UnicodeDecodeError as error:
        raise ValueError(
            "The imported file must use UTF-8 text encoding."
        ) from error

    cleaned = text.replace(
        "\x00",
        "",
    ).strip()

    if not cleaned:
        raise ValueError(
            "The imported file is empty."
        )

    return {
        "tool": "read_local_text_file",
        "file_name": path.name,
        "extension": path.suffix.lower(),
        "characters": len(cleaned),
        "content": cleaned,
    }


if __name__ == "__main__":
    mcp.run(
        transport="stdio",
    )
