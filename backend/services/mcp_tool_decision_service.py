from __future__ import annotations

import json
from dataclasses import dataclass

from groq import Groq

from services.groq_config import get_groq_settings


@dataclass(frozen=True)
class ToolDecision:
    use_tool: bool
    tool_name: str | None
    reason: str
    chosen_by: str


def choose_import_tool(file_name: str, user_request: str) -> ToolDecision:
    """Let the configured model choose whether the local-file tool is required.

    A safe deterministic fallback is retained so imports still work if the
    provider is unavailable. The normal text Brain Dump flow never calls this
    tool because it already contains the source text.
    """
    try:
        settings = get_groq_settings()
        client = Groq(api_key=settings.api_key)
        response = client.chat.completions.create(
            model=settings.small_model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You route ThoughtLinker requests. Use read_local_text_file "
                        "only when the user asks to import or read the attached local "
                        "TXT/Markdown file. Return a tool call instead of prose when needed."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Request: {user_request}\nLocal file: {file_name}",
                },
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "read_local_text_file",
                    "description": "Read the imported local TXT or Markdown file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {"type": "string"}
                        },
                        "required": ["relative_path"],
                    },
                },
            }],
            tool_choice="auto",
            max_completion_tokens=100,
        )
        calls = response.choices[0].message.tool_calls or []
        if calls and calls[0].function.name == "read_local_text_file":
            return ToolDecision(True, "read_local_text_file", "The model selected the local-file reader for this import.", "model")
        return ToolDecision(False, None, "The model decided that no file tool was required.", "model")
    except Exception:
        return ToolDecision(True, "read_local_text_file", "Safe import fallback selected the local-file reader.", "fallback")
