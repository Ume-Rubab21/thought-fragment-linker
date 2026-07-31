from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from schemas.small_model import SmallModelSuggestion
from services.model_routing_service import evaluate_model_route

assert evaluate_model_route(highest_similarity=0.2).model_tier == "small"
assert evaluate_model_route(highest_similarity=0.5).model_tier == "large"
assert evaluate_model_route(highest_similarity=0.8).model_tier == "small"
item = SmallModelSuggestion(
    suggested_title="Ambiguous semantic note", summary="This suggestion requires a reasoning decision.",
    tags=["semantic-search"], keywords=["semantic search"], related_note_ids=[],
    reasoning_decision="uncertain", reasoning="The idea overlaps existing notes but also introduces a distinct goal.",
    confidence_score=72,
)
assert item.confidence_score == 72
print("DAY 9 REASONING SCHEMA AND ROUTING TEST PASSED")
