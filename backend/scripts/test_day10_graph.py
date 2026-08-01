from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.brain_dump_graph import describe_brain_dump_graph
from services.knowledge_gap_service import detect_knowledge_gaps


def main() -> None:
    graph = describe_brain_dump_graph()
    expected_nodes = {
        "load",
        "mark_processing",
        "normalize",
        "route_and_generate",
        "detect_gaps",
        "mark_ready",
    }
    assert expected_nodes.issubset(set(graph["nodes"]))

    gaps = detect_knowledge_gaps(
        "PostgreSQL pgvector semantic search stores embeddings and ranks similar notes."
    )
    assert gaps, "Expected at least one knowledge-gap insight."
    assert all(gap.title and gap.description for gap in gaps)

    print(f"Graph engine: {graph['engine']}")
    print("Graph nodes:", " -> ".join(graph["nodes"]))
    print("Gap insights:", ", ".join(gap.title for gap in gaps))
    print("DAY 10 LANGGRAPH AND GAP DETECTION TEST PASSED")


if __name__ == "__main__":
    main()
