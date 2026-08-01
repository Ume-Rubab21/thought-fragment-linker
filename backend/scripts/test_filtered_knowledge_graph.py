from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from routers.knowledge_graph import MAX_CANDIDATES
from schemas.knowledge_graph import KnowledgeGraphResponse


def main() -> None:
    assert MAX_CANDIDATES == 200
    fields = KnowledgeGraphResponse.model_fields
    assert "total_note_count" in fields
    assert "filtered_note_count" in fields
    assert "visible_note_count" in fields
    print("FINAL FILTERED KNOWLEDGE GRAPH TEST PASSED")


if __name__ == "__main__":
    main()
