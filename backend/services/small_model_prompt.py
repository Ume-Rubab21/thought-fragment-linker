from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateNote:
    id: uuid.UUID
    title: str
    excerpt: str = ""
    similarity: float = 0.0


COMMON_OUTPUT_RULES = """
Return one JSON object with exactly these fields:

{
  "suggested_title": "string",
  "summary": "string",
  "suggested_content": "string",
  "tags": ["string"],
  "keywords": ["string"],
  "related_note_ids": ["uuid-string"],
  "reasoning_decision": null,
  "reasoning": null,
  "confidence_score": null
}

CONTENT TRANSFORMATION RULES:
1. suggested_content must be a polished note, not a copy of the source.
2. Rewrite in clear, natural language while preserving supported facts.
3. Reorganize related ideas into coherent paragraphs or short sections.
4. Remove PDF page markers, headers, footers, filenames, test labels,
   import instructions, repeated lines, OCR noise, and document boilerplate.
5. Do not reproduce long source sentences verbatim unless an exact technical
   term or short definition must be preserved.
6. Do not mention that the content came from a PDF, OCR, MCP, file import,
   Brain Dump, or AI unless that fact is itself the subject of the document.
7. Do not include lines such as "Page 1", "Expected knowledge gaps",
   "PDF Import Test", or similar testing scaffolding in suggested_content.
8. Keep the meaning accurate. Never invent facts, citations, measurements,
   people, claims, or conclusions that are absent from the source.
9. For a list of disconnected ideas, synthesize them into an organized note.
10. For already well-written source material, still improve structure,
    concision, transitions, and readability rather than copying it unchanged.

METADATA RULES:
11. suggested_title must contain 3 to 120 characters.
12. summary must contain 10 to 500 characters and briefly describe the
    rewritten note, not the import process.
13. Return between 1 and 6 specific lowercase tags using hyphens.
14. Return between 1 and 10 grounded keywords.
15. Return no more than 5 related_note_ids.
16. Never invent database IDs. IDs must come from the candidate list.
17. If no candidates are supplied, related_note_ids must be empty.
18. Do not include markdown fences or text outside the JSON object.
""".strip()


SMALL_MODEL_SYSTEM_PROMPT = f"""
You are ThoughtLinker's note-writing and metadata model.
Transform the user's raw or imported content into a useful, polished note.

{COMMON_OUTPUT_RULES}

For this small tier, set reasoning_decision, reasoning, and confidence_score
all to null.
""".strip()


LARGE_MODEL_SYSTEM_PROMPT = f"""
You are ThoughtLinker's reasoning and note-writing model.
Transform the user's raw or imported content into a useful, polished note,
then decide whether it should become a new note or extend a supplied note.

{COMMON_OUTPUT_RULES}

For this large tier:
- reasoning_decision must be new_note, extend_existing, or uncertain.
- reasoning must be a concise user-facing explanation.
- confidence_score must be an integer from 0 to 100.
- When choosing extend_existing, include the strongest candidate UUID.
""".strip()


def format_candidate_notes(
    candidate_notes: Sequence[CandidateNote] | None,
) -> str:
    if not candidate_notes:
        return "No candidate notes were supplied."

    lines: list[str] = []

    for note in candidate_notes:
        excerpt = note.excerpt.strip() or "No content"
        lines.append(
            f"- ID {note.id}\n"
            f"  Title: {note.title}\n"
            f"  Similarity: {note.similarity:.6f}\n"
            f"  Excerpt: {excerpt}"
        )

    return "\n".join(lines)

def build_small_model_user_prompt(raw_text: str, candidate_notes: Sequence[CandidateNote] | None=None, previous_error: str | None=None) -> str:
    cleaned_text=raw_text.strip()
    if not cleaned_text:
        raise ValueError("Brain Dump text cannot be empty.")
    correction=""
    if previous_error:
        correction=f"""Your previous response was rejected.
VALIDATION ERROR:
{previous_error}
Return a completely new JSON object and correct the problem."""
    return f"""
Create a polished ThoughtLinker note from the source below.

SOURCE CONTENT:
{cleaned_text}

CANDIDATE NOTES OWNED BY THE CURRENT USER:
{format_candidate_notes(candidate_notes)}

{correction}

Remember: suggested_content must be meaningfully rewritten and organized,
not copied from SOURCE CONTENT.
""".strip()
