from bleach.sanitizer import Cleaner


ALLOWED_TAGS = [
    "p",
    "br",
    "div",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "strike",
    "h1",
    "h2",
    "h3",
    "ul",
    "ol",
    "li",
    "blockquote",
    "a",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
}

cleaner = Cleaner(
    tags=ALLOWED_TAGS,
    attributes=ALLOWED_ATTRIBUTES,
    protocols=["http", "https", "mailto"],
    strip=True,
    strip_comments=True,
)


def sanitize_rich_text(value: str | None) -> str:
    """Return safe rich-text HTML before writing it to PostgreSQL."""
    return cleaner.clean(value or "")