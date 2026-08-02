from pathlib import Path

root = Path(__file__).resolve().parent
jsx = (root / "frontend/src/pages/KnowledgeGraph.jsx").read_text(encoding="utf-8")
css = (root / "frontend/src/pages/KnowledgeGraph.css").read_text(encoding="utf-8")

assert "function splitLabel" in jsx
assert "const showLabel = true" in jsx
assert "labelLines.map" in jsx
assert "<tspan" in jsx
assert "knowledge-node__label is-${node.kind}" in jsx
assert ".knowledge-node__label.is-tag" in css
assert "font-size: 9px" in css

print("FINAL LABELED FILTERED KNOWLEDGE GRAPH FILE TEST PASSED")
