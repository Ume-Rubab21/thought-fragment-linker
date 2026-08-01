import os
import sys
from pathlib import Path

import pymupdf

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from mcp_server.local_file_server import WORKSPACE, read_local_text_file


def main() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    test_path = WORKSPACE / "pdf_import_test.pdf"

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text(
        (72, 90),
        "ThoughtLinker PDF import test. PostgreSQL pgvector supports semantic search.",
        fontsize=12,
    )
    document.save(test_path)
    document.close()

    try:
        result = read_local_text_file("pdf_import_test.pdf")
        assert result["extension"] == ".pdf"
        assert result["pages"] == 1
        assert "ThoughtLinker PDF import test" in result["content"]
        print("PDF pages:", result["pages"])
        print("OCR used:", result["ocr_used"])
        print("Imported characters:", result["characters"])
        print("PDF HYBRID TEXT/OCR IMPORT TEST PASSED")
    finally:
        test_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
