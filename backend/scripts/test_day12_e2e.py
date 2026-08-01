from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def assert_files() -> None:
    required = [
        BACKEND_DIR / "routers" / "knowledge_graph.py",
        BACKEND_DIR / "schemas" / "knowledge_graph.py",
        BACKEND_DIR / "core" / "production.py",
        PROJECT_ROOT / "frontend" / "src" / "pages" / "KnowledgeGraph.jsx",
        PROJECT_ROOT / "frontend" / "vercel.json",
        BACKEND_DIR / "Dockerfile",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing Day 12 files: {missing}"


def verify_imports() -> None:
    from main import app
    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/health/ready" in paths
    assert "/knowledge-graph" in paths


def live_health_check() -> None:
    base_url = os.getenv("DAY12_LIVE_BACKEND_URL", "").rstrip("/")
    if not base_url:
        print("Live check skipped: set DAY12_LIVE_BACKEND_URL after deployment.")
        return
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert payload.get("status") == "ok"
    except urllib.error.URLError as error:
        raise AssertionError(f"Live backend health check failed: {error}") from error
    print(f"Live backend healthy: {base_url}")


def main() -> None:
    assert_files()
    verify_imports()
    live_health_check()
    print("DAY 12 HARDENING, GRAPH AND E2E TEST PASSED")


if __name__ == "__main__":
    main()
