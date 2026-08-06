from __future__ import annotations

import os
import uuid
from typing import Any, TypedDict

from sqlalchemy.orm import Session

from models.ai_suggestion import AISuggestion
from models.brain_dump import BrainDump
from services.knowledge_gap_service import detect_knowledge_gaps
from services.small_model_persistence import generate_and_store_suggestion

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # Plain-pipeline fallback remains supported.
    END = START = StateGraph = None


class LangGraphUnavailableError(RuntimeError):
    """Raised only when LangGraph cannot be imported or compiled."""


class BrainDumpGraphState(TypedDict, total=False):
    db: Session
    brain_dump_id: uuid.UUID
    brain_dump: BrainDump
    cleaned_text: str
    suggestion: AISuggestion
    knowledge_gaps: list[dict[str, str]]
    trace: list[str]


def _append_trace(state: BrainDumpGraphState, node: str) -> list[str]:
    return [*(state.get("trace") or []), node]


def _load_node(state: BrainDumpGraphState) -> dict[str, Any]:
    from services.brain_dump_pipeline import get_brain_dump

    brain_dump = get_brain_dump(
        db=state["db"],
        brain_dump_id=state["brain_dump_id"],
    )
    return {"brain_dump": brain_dump, "trace": _append_trace(state, "load")}


def _processing_node(state: BrainDumpGraphState) -> dict[str, Any]:
    from services.brain_dump_pipeline import mark_as_processing

    mark_as_processing(state["db"], state["brain_dump"])
    return {"trace": _append_trace(state, "mark_processing")}


def _normalize_node(state: BrainDumpGraphState) -> dict[str, Any]:
    from services.brain_dump_pipeline import normalize_brain_dump_text, save_normalized_text

    cleaned_text = normalize_brain_dump_text(state["brain_dump"].raw_text)
    save_normalized_text(state["db"], state["brain_dump"], cleaned_text)
    return {
        "cleaned_text": cleaned_text,
        "trace": _append_trace(state, "normalize"),
    }


def _suggestion_node(state: BrainDumpGraphState) -> dict[str, Any]:
    brain_dump = state["brain_dump"]
    fast_mode = os.getenv(
        "BRAIN_DUMP_FAST_MODE",
        "true",
    ).strip().lower() not in {"0", "false", "no", "off"}

    suggestion = generate_and_store_suggestion(
        db=state["db"],
        user_id=brain_dump.user_id,
        brain_dump_id=brain_dump.id,
        raw_text=state["cleaned_text"],
        # Similarity retrieval loads the local embedding model and can add
        # a long cold-start delay. In fast mode the suggestion is generated
        # immediately with the small-model route. Gap/relationship analysis
        # remains available through the separate endpoints after readiness.
        candidate_notes=[] if fast_mode else None,
    )
    return {
        "suggestion": suggestion,
        "trace": _append_trace(state, "route_and_generate"),
    }


def _gap_node(state: BrainDumpGraphState) -> dict[str, Any]:
    # Knowledge-gap detection is intentionally deferred. It is requested by
    # the frontend only after the suggestion is ready, so running it here
    # blocks readiness and then repeats the same work in /gaps.
    return {
        "knowledge_gaps": [],
        "trace": _append_trace(state, "detect_gaps"),
    }


def _ready_node(state: BrainDumpGraphState) -> dict[str, Any]:
    from services.brain_dump_pipeline import mark_as_ready

    mark_as_ready(state["db"], state["brain_dump"])
    return {"trace": _append_trace(state, "mark_ready")}


def _build_graph():
    if StateGraph is None:
        return None

    graph = StateGraph(BrainDumpGraphState)
    graph.add_node("load", _load_node)
    graph.add_node("mark_processing", _processing_node)
    graph.add_node("normalize", _normalize_node)
    graph.add_node("route_and_generate", _suggestion_node)
    graph.add_node("detect_gaps", _gap_node)
    graph.add_node("mark_ready", _ready_node)

    graph.add_edge(START, "load")
    graph.add_edge("load", "mark_processing")
    graph.add_edge("mark_processing", "normalize")
    graph.add_edge("normalize", "route_and_generate")
    graph.add_edge("route_and_generate", "detect_gaps")
    graph.add_edge("detect_gaps", "mark_ready")
    graph.add_edge("mark_ready", END)
    return graph.compile()


COMPILED_BRAIN_DUMP_GRAPH = _build_graph()


def run_brain_dump_graph(
    db: Session,
    brain_dump_id: uuid.UUID,
) -> tuple[BrainDump, AISuggestion]:
    if COMPILED_BRAIN_DUMP_GRAPH is None:
        raise LangGraphUnavailableError(
            "LangGraph is not installed; use the plain pipeline fallback."
        )

    result = COMPILED_BRAIN_DUMP_GRAPH.invoke(
        {
            "db": db,
            "brain_dump_id": brain_dump_id,
            "trace": [],
        }
    )
    return result["brain_dump"], result["suggestion"]


def describe_brain_dump_graph() -> dict[str, object]:
    nodes = [
        "load",
        "mark_processing",
        "normalize",
        "route_and_generate",
        "detect_gaps",
        "mark_ready",
    ]
    edges = [
        ["START", "load"],
        ["load", "mark_processing"],
        ["mark_processing", "normalize"],
        ["normalize", "route_and_generate"],
        ["route_and_generate", "detect_gaps"],
        ["detect_gaps", "mark_ready"],
        ["mark_ready", "END"],
    ]
    return {
        "engine": "langgraph" if COMPILED_BRAIN_DUMP_GRAPH is not None else "plain-pipeline",
        "available": COMPILED_BRAIN_DUMP_GRAPH is not None,
        "nodes": nodes,
        "edges": edges,
        "fallback": "The existing plain pipeline is used if LangGraph is unavailable.",
    }
