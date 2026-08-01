import os
import shutil
from pathlib import Path
from typing import Any

import pymupdf
import pytesseract
from PIL import Image
from mcp.server.fastmcp import FastMCP


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = BACKEND_DIR / "mcp_workspace" / "imports"
WORKSPACE = Path(
    os.getenv("THOUGHTLINKER_MCP_WORKSPACE", str(DEFAULT_WORKSPACE))
).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}
MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_PDF_PAGES = 100
MAX_EXTRACTED_CHARACTERS = 200_000
OCR_DPI = 300
MIN_NATIVE_TEXT_CHARACTERS = 40

mcp = FastMCP("ThoughtLinker Local File Server")


def _configure_tesseract() -> str | None:
    configured = os.getenv("TESSERACT_CMD", "").strip()
    if configured:
        candidate = Path(configured)
        if candidate.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return str(candidate)

    discovered = shutil.which("tesseract")
    if discovered:
        pytesseract.pytesseract.tesseract_cmd = discovered
        return discovered

    common_windows_paths = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    for candidate in common_windows_paths:
        if candidate.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return str(candidate)

    return None


TESSERACT_EXECUTABLE = _configure_tesseract()


def resolve_safe_file(relative_path: str) -> Path:
    candidate = (WORKSPACE / relative_path).resolve()
    try:
        candidate.relative_to(WORKSPACE)
    except ValueError as error:
        raise ValueError("The requested file is outside the MCP workspace.") from error

    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Only .txt, .md, and .pdf files are supported.")
    if not candidate.is_file():
        raise FileNotFoundError("The requested file does not exist.")
    if candidate.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("The file exceeds the 15 MB import limit.")
    return candidate


def _normalize_text(value: str) -> str:
    lines = [line.rstrip() for line in value.replace("\x00", "").splitlines()]
    compact: list[str] = []
    blank = False
    for line in lines:
        if line.strip():
            compact.append(line)
            blank = False
        elif not blank:
            compact.append("")
            blank = True
    return "\n".join(compact).strip()


def _append_unique(chunks: list[str], candidate: str) -> None:
    normalized = _normalize_text(candidate)
    if not normalized:
        return
    lowered = normalized.lower()
    for existing in chunks:
        existing_lower = existing.lower()
        if lowered == existing_lower or lowered in existing_lower:
            return
    chunks.append(normalized)


def _pixmap_to_pillow(pixmap: pymupdf.Pixmap) -> Image.Image:
    mode = "RGBA" if pixmap.alpha else "RGB"
    return Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)


def _ocr_pixmap(pixmap: pymupdf.Pixmap, language: str) -> str:
    if not TESSERACT_EXECUTABLE:
        raise RuntimeError(
            "Tesseract OCR is not installed or could not be found. "
            "Install Tesseract and add it to PATH, or set TESSERACT_CMD."
        )
    image = _pixmap_to_pillow(pixmap)
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        image = background
    return pytesseract.image_to_string(image, lang=language)


def _extract_pdf(path: Path) -> dict[str, Any]:
    language = os.getenv("THOUGHTLINKER_OCR_LANG", "eng")
    page_results: list[str] = []
    warnings: list[str] = []
    ocr_pages: list[int] = []
    image_regions_ocrd = 0

    try:
        document = pymupdf.open(path)
    except Exception as error:
        raise ValueError(f"The PDF could not be opened: {error}") from error

    try:
        if document.is_encrypted and not document.authenticate(""):
            raise ValueError("Password-protected PDFs are not supported.")
        if document.page_count == 0:
            raise ValueError("The PDF does not contain any pages.")
        if document.page_count > MAX_PDF_PAGES:
            raise ValueError(
                f"The PDF has {document.page_count} pages; the current limit is {MAX_PDF_PAGES}."
            )

        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            native_text = _normalize_text(page.get_text("text", sort=True))
            chunks: list[str] = []
            _append_unique(chunks, native_text)

            # OCR the full page when it is scanned or contains almost no embedded text.
            if len(native_text) < MIN_NATIVE_TEXT_CHARACTERS:
                if TESSERACT_EXECUTABLE:
                    matrix = pymupdf.Matrix(OCR_DPI / 72, OCR_DPI / 72)
                    full_page_pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                    _append_unique(chunks, _ocr_pixmap(full_page_pixmap, language))
                    ocr_pages.append(page_index + 1)
                else:
                    warnings.append(
                        f"Page {page_index + 1} appears scanned, but Tesseract OCR is unavailable."
                    )
            else:
                # On mixed pages, OCR image regions so text embedded in screenshots,
                # scanned diagrams, and pictures is not silently ignored.
                raw_dict = page.get_text("dict")
                for block in raw_dict.get("blocks", []):
                    if block.get("type") != 1:
                        continue
                    bbox = block.get("bbox")
                    if not bbox:
                        continue
                    rect = pymupdf.Rect(bbox)
                    if rect.width < 40 or rect.height < 25:
                        continue
                    if not TESSERACT_EXECUTABLE:
                        if not any("image text" in warning.lower() for warning in warnings):
                            warnings.append(
                                "The PDF contains images, but Tesseract OCR is unavailable; "
                                "text inside those images may be missing."
                            )
                        continue
                    matrix = pymupdf.Matrix(OCR_DPI / 72, OCR_DPI / 72)
                    pixmap = page.get_pixmap(matrix=matrix, clip=rect, alpha=False)
                    image_text = _ocr_pixmap(pixmap, language)
                    before = len(chunks)
                    _append_unique(chunks, image_text)
                    if len(chunks) > before:
                        image_regions_ocrd += 1

            page_text = "\n\n".join(chunks).strip()
            if not page_text:
                page_text = "[No readable text was extracted from this page.]"
            page_results.append(f"--- Page {page_index + 1} ---\n{page_text}")

        content = "\n\n".join(page_results).strip()
        if not content or all("No readable text" in item for item in page_results):
            raise ValueError(
                "No readable text could be extracted. Install Tesseract OCR for scanned PDFs."
            )
        if len(content) > MAX_EXTRACTED_CHARACTERS:
            content = content[:MAX_EXTRACTED_CHARACTERS]
            warnings.append(
                f"Extracted content was truncated to {MAX_EXTRACTED_CHARACTERS:,} characters."
            )

        return {
            "content": content,
            "pages": document.page_count,
            "ocr_used": bool(ocr_pages or image_regions_ocrd),
            "ocr_pages": ocr_pages,
            "image_regions_ocrd": image_regions_ocrd,
            "warnings": warnings,
        }
    finally:
        document.close()


@mcp.tool()
def read_local_text_file(relative_path: str) -> dict[str, Any]:
    """Read a local TXT, Markdown, or PDF file; OCR scanned PDF pages and image text."""
    path = resolve_safe_file(relative_path)

    if path.suffix.lower() == ".pdf":
        result = _extract_pdf(path)
        content = result["content"]
        extra = {
            "pages": result["pages"],
            "ocr_used": result["ocr_used"],
            "ocr_pages": result["ocr_pages"],
            "image_regions_ocrd": result["image_regions_ocrd"],
            "warnings": result["warnings"],
        }
    else:
        try:
            content = _normalize_text(path.read_text(encoding="utf-8-sig"))
        except UnicodeDecodeError as error:
            raise ValueError("The imported text file must use UTF-8 encoding.") from error
        extra = {
            "pages": None,
            "ocr_used": False,
            "ocr_pages": [],
            "image_regions_ocrd": 0,
            "warnings": [],
        }

    if not content:
        raise ValueError("The imported file is empty or contains no readable text.")

    return {
        "tool": "read_local_text_file",
        "file_name": path.name,
        "extension": path.suffix.lower(),
        "characters": len(content),
        "content": content,
        **extra,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
