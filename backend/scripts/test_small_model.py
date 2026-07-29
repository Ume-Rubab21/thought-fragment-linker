from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest import result


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))


from services.small_model_service import (
    SmallModelError,
    generate_small_model_suggestion,
)


DEFAULT_TEST_TEXT = """
I am building semantic search for my note application.
The backend uses PostgreSQL with pgvector, while MiniLM
creates embeddings for each note. I also want users to see
related notes based on cosine similarity.
""".strip()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test the ThoughtLinker Groq small model."
    )

    parser.add_argument(
        "--text",
        type=str,
        default=DEFAULT_TEST_TEXT,
        help="Brain Dump text to send to Groq.",
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    print("=" * 72)
    print("THOUGHTLINKER GROQ SMALL-MODEL TEST")
    print("=" * 72)

    try:
        result = generate_small_model_suggestion(
            arguments.text
        )
    except (ValueError, SmallModelError) as error:
        print(f"FAILED: {error}")
        return 1

    print(f"Model             : {result.model}")
    print(f"Prompt tokens     : {result.prompt_tokens}")
    print(f"Completion tokens : {result.completion_tokens}")
    print(f"Total tokens      : {result.total_tokens}")
    print(f"Attempts          : {result.attempts}")
    print(f"Retry count       : {result.retry_count}")

    print()
    print("STRUCTURED RESULT")
    print("-" * 72)

    print(
        result.suggestion.model_dump_json(
            indent=2
        )
    )

    print()
    print("=" * 72)
    print("GROUP 1 TEST PASSED")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())