from __future__ import annotations

import sys
import uuid
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from schemas.small_model import SmallModelSuggestion
from services.small_model_guardrails import (
    GuardrailValidationError,
    validate_small_model_suggestion,
)
from services.small_model_prompt import SMALL_MODEL_SYSTEM_PROMPT

SOURCE = """--- Page 1 ---
ThoughtLinker PDF Import Test
PostgreSQL supports pgvector for semantic search. Embeddings represent text as vectors. Cosine similarity retrieves related notes. HNSW indexes improve retrieval speed. Precision at k and Recall at k are evaluation metrics.
Expected knowledge gaps: chunking strategy and production monitoring.
"""

GOOD = SmallModelSuggestion(
    suggested_title="Evaluating PostgreSQL Semantic Search",
    summary="A structured overview of pgvector retrieval, indexing, and evaluation.",
    suggested_content=(
        "PostgreSQL can support semantic retrieval through pgvector, which stores "
        "embeddings and compares them using cosine similarity. HNSW indexing can "
        "reduce retrieval latency as a note collection grows. Search quality should "
        "be measured with ranking metrics such as Precision at k and Recall at k, "
        "while chunking and production monitoring should be defined separately."
    ),
    tags=["postgresql", "semantic-search"],
    keywords=["pgvector", "cosine similarity"],
    related_note_ids=[],
    reasoning_decision=None, reasoning=None, confidence_score=None,
)
validate_small_model_suggestion(SOURCE, GOOD, set())

BAD = GOOD.model_copy(update={"suggested_content": SOURCE})
try:
    validate_small_model_suggestion(SOURCE, BAD, set())
except GuardrailValidationError:
    pass
else:
    raise AssertionError("Copied source content was not rejected")

assert "suggested_content" in SMALL_MODEL_SYSTEM_PROMPT
assert "not a copy" in SMALL_MODEL_SYSTEM_PROMPT.lower()
print("FINAL AI CONTENT TRANSFORMATION TEST PASSED")