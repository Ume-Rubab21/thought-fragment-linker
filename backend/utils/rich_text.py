from html.parser import HTMLParser

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


class _PlainTextParser(HTMLParser):
    """Convert rich-text HTML into readable plain text."""

    BLOCK_TAGS = {
        "p",
        "div",
        "br",
        "li",
        "h1",
        "h2",
        "h3",
        "blockquote",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag in self.BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def get_text(self) -> str:
        return " ".join(
            "".join(self.parts).split()
        )


def sanitize_rich_text(value: str | None) -> str:
    """Return safe rich-text HTML before saving it."""
    return cleaner.clean(value or "")


def rich_text_to_plain_text(
    value: str | None,
) -> str:
    """Convert rich-text HTML into text for embeddings."""
    parser = _PlainTextParser()
    parser.feed(value or "")
    parser.close()

    return parser.get_text()