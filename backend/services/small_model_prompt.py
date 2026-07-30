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


SMALL_MODEL_SYSTEM_PROMPT = """
You are the metadata model for ThoughtLinker,
an AI-powered personal knowledge application.

Analyze one Brain Dump and return only a JSON object.

Required JSON fields:

{
  "suggested_title": "string",
  "summary": "string",
  "tags": ["string"],
  "keywords": ["string"],
  "related_note_ids": ["uuid-string"]
}

Rules:

1. suggested_title must contain 3 to 120 characters.
2. summary must contain 10 to 500 characters.
3. Return between 1 and 6 tags.
4. Return between 1 and 10 keywords.
5. Return no more than 5 related_note_ids.
6. Tags must be lowercase.
7. Use hyphens instead of spaces inside tags.
8. Tags must be specific and supported by the Brain Dump.
9. Do not return generic tags such as general, misc, notes,
   thoughts, random, other, or uncategorized.
10. Keywords must be words or short phrases supported by the input.
11. Never invent facts, topics, or database IDs.
12. related_note_ids may contain only UUID strings from the supplied
    candidate-note list.
13. When no candidate notes are supplied, related_note_ids must
    be an empty list.
14. Do not include markdown fences.
15. Do not include explanations outside the JSON object.
""".strip()


def format_candidate_notes(
    candidate_notes: Sequence[CandidateNote] | None,
) -> str:
    if not candidate_notes:
        return "No candidate notes were supplied."

    lines = []

    for note in candidate_notes:
        excerpt = note.excerpt.strip() or "No content"

        lines.append(
            f"- ID {note.id}\n"
            f"  Title: {note.title}\n"
            f"  Similarity: {note.similarity:.6f}\n"
            f"  Excerpt: {excerpt}"
        )

    return "\n".join(lines)


def build_small_model_user_prompt(
    raw_text: str,
    candidate_notes: Sequence[CandidateNote] | None = None,
    previous_error: str | None = None,
) -> str:
    cleaned_text = raw_text.strip()

    if not cleaned_text:
        raise ValueError(
            "Brain Dump text cannot be empty."
        )

    correction_section = ""

    if previous_error:
        correction_section = f"""
Your previous response was rejected by validation.

VALIDATION ERROR:
{previous_error}

Correct the problem and return a completely new JSON object.
""".strip()

    return f"""
Analyze the following Brain Dump.

BRAIN DUMP:
{cleaned_text}

CANDIDATE NOTES OWNED BY THE CURRENT USER:
{format_candidate_notes(candidate_notes)}

{correction_section}

Return exactly these fields:

- suggested_title
- summary
- tags
- keywords
- related_note_ids
""".strip()
