from __future__ import annotations

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
    """Let the configured model choose whether the local document tool is required."""
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
                        "when the user asks to import or read an attached local TXT, "
                        "Markdown, or PDF document. The tool extracts native PDF text "
                        "and uses OCR for scanned pages and text inside images. Return "
                        "a tool call instead of prose when the document must be read."
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
                    "description": (
                        "Read an imported local TXT, Markdown, or PDF document. "
                        "PDFs may contain native text, scans, or images with text."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {"relative_path": {"type": "string"}},
                        "required": ["relative_path"],
                    },
                },
            }],
            tool_choice="auto",
            max_completion_tokens=100,
        )
        calls = response.choices[0].message.tool_calls or []
        if calls and calls[0].function.name == "read_local_text_file":
            return ToolDecision(
                True,
                "read_local_text_file",
                "The model selected the local document reader for this import.",
                "model",
            )
        return ToolDecision(
            False,
            None,
            "The model decided that no file tool was required.",
            "model",
        )
    except Exception:
        return ToolDecision(
            True,
            "read_local_text_file",
            "Safe import fallback selected the local document reader.",
            "fallback",
        )
