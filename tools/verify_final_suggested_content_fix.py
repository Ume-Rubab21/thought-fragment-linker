from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from schemas.brain_dump import BrainDumpSuggestionResponse

assert "suggested_content" in BrainDumpSuggestionResponse.model_fields

router = (BACKEND / "routers" / "brain_dumps.py").read_text(encoding="utf-8")
assert "suggested_content=suggestion.suggested_content" in router

ui = (ROOT / "frontend" / "src" / "pages" / "BrainDump.jsx").read_text(encoding="utf-8")
assert "setBody(response.suggested_content)" in ui
assert "response.suggested_content || text.trim()" not in ui

print("FINAL SUGGESTED CONTENT API/UI TEST PASSED")
