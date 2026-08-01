from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

router = BACKEND / "routers" / "brain_dumps.py"
schema = BACKEND / "schemas" / "brain_dump.py"
brain_ui = FRONTEND / "src" / "pages" / "BrainDump.jsx"
ai_ui = FRONTEND / "src" / "pages" / "AISuggestions.jsx"


def backup(path: Path) -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = path.with_suffix(path.suffix + f".backup_{stamp}")
    shutil.copy2(path, target)
    print(f"Backup: {target}")


def patch_router() -> None:
    text = router.read_text(encoding="utf-8")
    if "suggested_content=suggestion.suggested_content" in text:
        print("brain_dumps.py already fixed")
        return

    old = """        suggested_title=suggestion.suggested_title,
        summary=suggestion.summary,
        tags=list(suggestion.tags or []),
"""
    new = """        suggested_title=suggestion.suggested_title,
        summary=suggestion.summary,
        suggested_content=suggestion.suggested_content,
        tags=list(suggestion.tags or []),
"""
    if old not in text:
        raise RuntimeError("Expected suggestion response block was not found in brain_dumps.py")

    backup(router)
    router.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"Patched: {router}")


def patch_schema() -> None:
    text = schema.read_text(encoding="utf-8")
    match = re.search(
        r"class\s+BrainDumpSuggestionResponse\s*\([^)]*\)\s*:\s*(.*?)(?=\nclass\s+|\Z)",
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise RuntimeError("BrainDumpSuggestionResponse was not found in schemas/brain_dump.py")

    block = match.group(0)
    if re.search(r"^\s+suggested_content\s*:", block, flags=re.MULTILINE):
        print("brain_dump.py schema already fixed")
        return

    patched_block, count = re.subn(
        r"(^\s+summary\s*:\s*[^\n]+\n)",
        r"\1    suggested_content: str\n",
        block,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError("summary field was not found in BrainDumpSuggestionResponse")

    backup(schema)
    schema.write_text(
        text[:match.start()] + patched_block + text[match.end():],
        encoding="utf-8",
    )
    print(f"Patched: {schema}")


def patch_brain_ui() -> None:
    text = brain_ui.read_text(encoding="utf-8")
    changed = False

    old = """    setSuggestion(response)
    setTitle(response.suggested_title || '')
    setBody(response.suggested_content || text.trim())
    setTagInput(
"""
    new = """    if (!response.suggested_content?.trim()) {
      throw new Error(
        'The backend suggestion response is missing AI-suggested content.',
      )
    }

    setSuggestion(response)
    setTitle(response.suggested_title || '')
    setBody(response.suggested_content)
    setTagInput(
"""
    if old in text:
        text = text.replace(old, new, 1)
        changed = True

    old_change = """              onChange={(event) =>
                setText(event.target.value)
              }
"""
    new_change = """              onChange={(event) => {
                setText(event.target.value)
                setToolUsage(null)
                setGenerationFailed(false)
              }}
"""
    if old_change in text:
        text = text.replace(old_change, new_change, 1)
        changed = True

    if changed:
        backup(brain_ui)
        brain_ui.write_text(text, encoding="utf-8")
        print(f"Patched: {brain_ui}")
    else:
        print("BrainDump.jsx already fixed or uses a different layout")


def patch_ai_ui() -> None:
    if not ai_ui.exists():
        return
    text = ai_ui.read_text(encoding="utf-8")
    old = "      setBody(response.brain_dump_text || '')"
    new = "      setBody(response.suggested_content || response.brain_dump_text || '')"
    if old in text:
        backup(ai_ui)
        ai_ui.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"Patched: {ai_ui}")


def main() -> None:
    for path in (router, schema, brain_ui):
        if not path.exists():
            raise FileNotFoundError(path)

    patch_router()
    patch_schema()
    patch_brain_ui()
    patch_ai_ui()
    print("\nFINAL SUGGESTED CONTENT FIX APPLIED SUCCESSFULLY")


if __name__ == "__main__":
    main()
