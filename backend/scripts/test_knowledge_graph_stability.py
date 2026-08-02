from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

router = (ROOT / 'routers' / 'knowledge_graph.py').read_text(encoding='utf-8')
ui = (ROOT.parent / 'frontend' / 'src' / 'pages' / 'KnowledgeGraph.jsx').read_text(encoding='utf-8')
css = (ROOT.parent / 'frontend' / 'src' / 'pages' / 'KnowledgeGraph.css').read_text(encoding='utf-8')

assert 'MAX_CANDIDATES = 100' in router
assert 'len(tag.notes)' not in router
assert 'knowledge-node__hit-area' in ui
assert 'knowledge-node__visible-circle' in ui
assert 'transform: scale' not in css
assert 'setHoveredId' not in ui
assert 'border: 1px solid #dfe8dc' in css
assert 'background: #fffef9' in css
assert '.knowledge-graph-neighbours button:focus-visible' in css
print('FAST STABLE KNOWLEDGE GRAPH TEST PASSED')
