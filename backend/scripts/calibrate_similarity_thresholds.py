"""
Day 6 similarity calibration script.

This script:

1. Finds the selected user's notes.
2. Ensures all notes have MiniLM embeddings.
3. Calculates cosine similarity for every note pair.
4. Tests known related, near-duplicate and unrelated pairs.
5. Prints the similarity-score distribution.
6. Evaluates the selected LOW and HIGH thresholds.
7. Saves a JSON calibration report.

Run from the backend directory:

    python scripts/calibrate_similarity_thresholds.py

For a specific user:

    python scripts/calibrate_similarity_thresholds.py \
        --email your@email.com

Optional custom output file:

    python scripts/calibrate_similarity_thresholds.py \
        --email your@email.com \
        --output reports/day6_similarity_calibration.json
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import UUID

# Allow imports from backend/ when this file is run directly.
BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from database import SessionLocal
from models.note import Note
from models.note_embedding import (
    DEFAULT_EMBEDDING_MODEL,
    NoteEmbedding,
)
from models.user import User
from services.embedding_service import upsert_note_embedding
from services.similarity_thresholds import (
    ROUTE_AMBIGUOUS,
    ROUTE_CLEARLY_RELATED,
    ROUTE_NEW_TOPIC,
    SIMILARITY_HIGH,
    SIMILARITY_LOW,
    classify_similarity,
)


# ------------------------------------------------------------------
# Known calibration pairs from the Day 6 corpus
# ------------------------------------------------------------------

NEAR_DUPLICATE_PAIRS = [
    (
        "Regular Car Maintenance",
        "Automobile Service Routine",
    ),
    (
        "Healthy Morning Exercise",
        "Daily Fitness Routine",
    ),
    (
        "Learning React Hooks",
        "Hooks in React Components",
    ),
]


RELATED_PAIRS = [
    (
        "PostgreSQL Full-Text Search",
        "GIN Index for Text Search",
    ),
    (
        "PostgreSQL Full-Text Search",
        "Using tsvector in Notes",
    ),
    (
        "GIN Index for Text Search",
        "Improving Database Search Speed",
    ),
    (
        "Database Query Optimization",
        "PostgreSQL Index Maintenance",
    ),
    (
        "Responsive React Sidebar",
        "Mobile-Friendly Navigation Panel",
    ),
    (
        "Managing State with React Hooks",
        "Learning React Hooks",
    ),
    (
        "Managing State with React Hooks",
        "Using useEffect Correctly",
    ),
    (
        "React Component Reuse",
        "Hooks in React Components",
    ),
    (
        "Understanding Text Embeddings",
        "Sentence Transformer Embeddings",
    ),
    (
        "Semantic Search for Notes",
        "Vector Similarity Search",
    ),
    (
        "Vector Similarity Search",
        "Using pgvector with PostgreSQL",
    ),
    (
        "Related Notes Feature",
        "Cosine Similarity Explained",
    ),
    (
        "Embedding Model Consistency",
        "Local MiniLM Embedding Model",
    ),
    (
        "Semantic Search vs Keyword Search",
        "Semantic Search for Notes",
    ),
]


UNRELATED_PAIRS = [
    (
        "Chocolate Cake Recipe",
        "Using pgvector with PostgreSQL",
    ),
    (
        "Chocolate Cake Recipe",
        "React Router Protected Pages",
    ),
    (
        "Planning a Trip to Japan",
        "Cosine Similarity Explained",
    ),
    (
        "Planning a Trip to Japan",
        "PostgreSQL Search Ranking",
    ),
    (
        "Growing Tomatoes at Home",
        "Managing State with React Hooks",
    ),
    (
        "Growing Tomatoes at Home",
        "Vector Similarity Search",
    ),
    (
        "Basic Football Training",
        "GIN Index for Text Search",
    ),
    (
        "Basic Football Training",
        "Sentence Transformer Embeddings",
    ),
    (
        "Chocolate Cake Recipe",
        "Responsive React Sidebar",
    ),
    (
        "Planning a Trip to Japan",
        "Database Query Optimization",
    ),
]


EXPECTED_CORPUS_TITLES = {
    # PostgreSQL and Search
    "PostgreSQL Full-Text Search",
    "GIN Index for Text Search",
    "Improving Database Search Speed",
    "PostgreSQL Search Ranking",
    "Using tsvector in Notes",
    "Database Query Optimization",
    "Searching Large Text Columns",
    "PostgreSQL Index Maintenance",
    "Keyword Search Architecture",
    "Fast Search in a Knowledge Base",

    # React and Frontend
    "Responsive React Sidebar",
    "Mobile-Friendly Navigation Panel",
    "React Component Reuse",
    "Managing State with React Hooks",
    "Using useEffect Correctly",
    "React Router Protected Pages",
    "Tailwind Responsive Layout",
    "Building a Notes Dashboard",
    "React Form Validation",
    "Frontend Loading and Error States",

    # AI, Embeddings and Semantic Search
    "Understanding Text Embeddings",
    "Semantic Search for Notes",
    "Vector Similarity Search",
    "Using pgvector with PostgreSQL",
    "Sentence Transformer Embeddings",
    "Cosine Similarity Explained",
    "Related Notes Feature",
    "Embedding Model Consistency",
    "Semantic Search vs Keyword Search",
    "Local MiniLM Embedding Model",

    # Near duplicates
    "Regular Car Maintenance",
    "Automobile Service Routine",
    "Healthy Morning Exercise",
    "Daily Fitness Routine",
    "Learning React Hooks",
    "Hooks in React Components",

    # Unrelated notes
    "Chocolate Cake Recipe",
    "Planning a Trip to Japan",
    "Growing Tomatoes at Home",
    "Basic Football Training",
}


@dataclass
class PairResult:
    category: str
    title_a: str
    title_b: str
    similarity: float
    route: str


@dataclass
class DistributionSummary:
    count: int
    minimum: float
    maximum: float
    mean: float
    median: float
    standard_deviation: float
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    percentile_95: float


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Calibrate MiniLM cosine-similarity thresholds "
            "using the Day 6 note corpus."
        )
    )

    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help=(
            "Email of the user whose notes should be calibrated. "
            "Required when multiple users exist."
        ),
    )

    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="UUID of the user whose notes should be calibrated.",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=(
            "reports/day6_similarity_calibration.json"
        ),
        help="Path where the JSON report will be written.",
    )

    parser.add_argument(
        "--skip-embedding-backfill",
        action="store_true",
        help=(
            "Do not generate embeddings for notes that are "
            "missing them."
        ),
    )

    return parser.parse_args()


def percentile(
    values: list[float],
    requested_percentile: float,
) -> float:
    """
    Calculate a percentile without requiring NumPy.
    """
    if not values:
        return 0.0

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (
        requested_percentile / 100
    ) * (len(ordered) - 1)

    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return ordered[lower_index]

    weight = position - lower_index

    return (
        ordered[lower_index] * (1 - weight)
        + ordered[upper_index] * weight
    )


def summarize_distribution(
    values: list[float],
) -> DistributionSummary:
    if not values:
        return DistributionSummary(
            count=0,
            minimum=0.0,
            maximum=0.0,
            mean=0.0,
            median=0.0,
            standard_deviation=0.0,
            percentile_10=0.0,
            percentile_25=0.0,
            percentile_75=0.0,
            percentile_90=0.0,
            percentile_95=0.0,
        )

    deviation = (
        statistics.pstdev(values)
        if len(values) > 1
        else 0.0
    )

    return DistributionSummary(
        count=len(values),
        minimum=round(min(values), 6),
        maximum=round(max(values), 6),
        mean=round(statistics.mean(values), 6),
        median=round(statistics.median(values), 6),
        standard_deviation=round(deviation, 6),
        percentile_10=round(
            percentile(values, 10),
            6,
        ),
        percentile_25=round(
            percentile(values, 25),
            6,
        ),
        percentile_75=round(
            percentile(values, 75),
            6,
        ),
        percentile_90=round(
            percentile(values, 90),
            6,
        ),
        percentile_95=round(
            percentile(values, 95),
            6,
        ),
    )


def vector_to_float_list(vector) -> list[float]:
    """
    Convert a pgvector/NumPy/list value to ordinary floats.
    """
    if vector is None:
        raise ValueError("Embedding vector is missing.")

    if hasattr(vector, "tolist"):
        vector = vector.tolist()

    return [float(value) for value in vector]


def cosine_similarity(
    vector_a,
    vector_b,
) -> float:
    """
    Calculate cosine similarity.

    MiniLM embeddings are already normalized, but the complete
    formula is used so this script remains safe if that changes.
    """
    values_a = vector_to_float_list(vector_a)
    values_b = vector_to_float_list(vector_b)

    if len(values_a) != len(values_b):
        raise ValueError(
            "Cannot compare vectors with different dimensions."
        )

    dot_product = sum(
        value_a * value_b
        for value_a, value_b in zip(
            values_a,
            values_b,
        )
    )

    magnitude_a = math.sqrt(
        sum(value * value for value in values_a)
    )

    magnitude_b = math.sqrt(
        sum(value * value for value in values_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError(
            "Cannot calculate similarity for a zero vector."
        )

    similarity = dot_product / (
        magnitude_a * magnitude_b
    )

    # Floating-point operations can produce values slightly
    # outside the legal cosine range.
    similarity = max(-1.0, min(1.0, similarity))

    return round(similarity, 6)


def choose_user(
    db,
    email: str | None,
    user_id: str | None,
) -> User:
    if user_id:
        try:
            parsed_user_id = UUID(user_id)
        except ValueError as error:
            raise ValueError(
                f"Invalid user UUID: {user_id}"
            ) from error

        user = db.get(User, parsed_user_id)

        if user is None:
            raise ValueError(
                f"No user found with ID {parsed_user_id}."
            )

        return user

    if email:
        user = (
            db.query(User)
            .filter(User.email == email.strip().lower())
            .first()
        )

        if user is None:
            raise ValueError(
                f"No user found with email {email}."
            )

        return user

    users = (
        db.query(User)
        .order_by(User.created_at.asc())
        .all()
    )

    if not users:
        raise ValueError(
            "No users exist in the database."
        )

    if len(users) > 1:
        available_emails = ", ".join(
            user.email for user in users
        )

        raise ValueError(
            "Multiple users exist. Run the script again with "
            f"--email. Available users: {available_emails}"
        )

    return users[0]


def load_user_notes(
    db,
    user: User,
) -> list[Note]:
    return (
        db.query(Note)
        .filter(Note.user_id == user.id)
        .order_by(Note.created_at.asc())
        .all()
    )


def ensure_embeddings(
    db,
    notes: Iterable[Note],
) -> tuple[int, int]:
    created = 0
    failed = 0

    for note in notes:
        embedding_record = db.get(
            NoteEmbedding,
            note.id,
        )

        is_current = (
            embedding_record is not None
            and embedding_record.embedding_model
            == DEFAULT_EMBEDDING_MODEL
        )

        if is_current:
            continue

        print(
            f"Generating missing embedding: {note.title}"
        )

        if upsert_note_embedding(db, note):
            created += 1
        else:
            failed += 1

    return created, failed


def load_embeddings_by_title(
    db,
    notes: Iterable[Note],
) -> dict[str, dict]:
    result = {}

    for note in notes:
        embedding_record = db.get(
            NoteEmbedding,
            note.id,
        )

        if embedding_record is None:
            continue

        if (
            embedding_record.embedding_model
            != DEFAULT_EMBEDDING_MODEL
        ):
            continue

        result[note.title.strip()] = {
            "note_id": str(note.id),
            "embedding": embedding_record.embedding,
        }

    return result


def calculate_labeled_pairs(
    embeddings_by_title: dict[str, dict],
    category: str,
    pairs: list[tuple[str, str]],
) -> tuple[list[PairResult], list[tuple[str, str]]]:
    results = []
    missing_pairs = []

    for title_a, title_b in pairs:
        item_a = embeddings_by_title.get(title_a)
        item_b = embeddings_by_title.get(title_b)

        if item_a is None or item_b is None:
            missing_pairs.append((title_a, title_b))
            continue

        similarity = cosine_similarity(
            item_a["embedding"],
            item_b["embedding"],
        )

        results.append(
            PairResult(
                category=category,
                title_a=title_a,
                title_b=title_b,
                similarity=similarity,
                route=classify_similarity(similarity),
            )
        )

    return results, missing_pairs


def calculate_all_pairs(
    embeddings_by_title: dict[str, dict],
) -> list[PairResult]:
    titles = sorted(embeddings_by_title.keys())
    results = []

    for first_index, title_a in enumerate(titles):
        for title_b in titles[first_index + 1:]:
            similarity = cosine_similarity(
                embeddings_by_title[title_a][
                    "embedding"
                ],
                embeddings_by_title[title_b][
                    "embedding"
                ],
            )

            results.append(
                PairResult(
                    category="all_pairs",
                    title_a=title_a,
                    title_b=title_b,
                    similarity=similarity,
                    route=classify_similarity(
                        similarity
                    ),
                )
            )

    return results


def average_similarity(
    results: list[PairResult],
) -> float:
    if not results:
        return 0.0

    return round(
        statistics.mean(
            result.similarity
            for result in results
        ),
        6,
    )


def print_divider(character: str = "=") -> None:
    print(character * 78)


def print_pair_results(
    heading: str,
    results: list[PairResult],
) -> None:
    print()
    print_divider("-")
    print(heading)
    print_divider("-")

    if not results:
        print("No complete pairs were found.")
        return

    sorted_results = sorted(
        results,
        key=lambda item: item.similarity,
        reverse=True,
    )

    for result in sorted_results:
        percentage = result.similarity * 100

        print(
            f"{percentage:6.2f}%  "
            f"[{result.route:17}]  "
            f"{result.title_a}  <->  {result.title_b}"
        )

    print(
        f"\nAverage: "
        f"{average_similarity(results) * 100:.2f}%"
    )

    print(
        f"Minimum: "
        f"{min(item.similarity for item in results) * 100:.2f}%"
    )

    print(
        f"Maximum: "
        f"{max(item.similarity for item in results) * 100:.2f}%"
    )


def print_distribution(
    summary: DistributionSummary,
) -> None:
    print()
    print_divider()
    print("FULL CORPUS SIMILARITY DISTRIBUTION")
    print_divider()

    print(f"Compared pairs : {summary.count}")
    print(f"Minimum        : {summary.minimum:.4f}")
    print(f"10th percentile: {summary.percentile_10:.4f}")
    print(f"25th percentile: {summary.percentile_25:.4f}")
    print(f"Median         : {summary.median:.4f}")
    print(f"Mean           : {summary.mean:.4f}")
    print(f"75th percentile: {summary.percentile_75:.4f}")
    print(f"90th percentile: {summary.percentile_90:.4f}")
    print(f"95th percentile: {summary.percentile_95:.4f}")
    print(f"Maximum        : {summary.maximum:.4f}")
    print(
        f"Std deviation  : "
        f"{summary.standard_deviation:.4f}"
    )


def evaluate_thresholds(
    near_duplicate_results: list[PairResult],
    related_results: list[PairResult],
    unrelated_results: list[PairResult],
) -> dict:
    """
    Evaluate how the selected thresholds behave on known pairs.
    """
    near_duplicate_clear = sum(
        result.route == ROUTE_CLEARLY_RELATED
        for result in near_duplicate_results
    )

    unrelated_new = sum(
        result.route == ROUTE_NEW_TOPIC
        for result in unrelated_results
    )

    related_not_new = sum(
        result.route != ROUTE_NEW_TOPIC
        for result in related_results
    )

    near_duplicate_rate = (
        near_duplicate_clear
        / len(near_duplicate_results)
        if near_duplicate_results
        else 0.0
    )

    unrelated_rate = (
        unrelated_new
        / len(unrelated_results)
        if unrelated_results
        else 0.0
    )

    related_rate = (
        related_not_new
        / len(related_results)
        if related_results
        else 0.0
    )

    passed = (
        near_duplicate_rate >= 0.66
        and unrelated_rate >= 0.70
        and related_rate >= 0.60
    )

    return {
        "passed": passed,
        "low": SIMILARITY_LOW,
        "high": SIMILARITY_HIGH,
        "near_duplicates_classified_clearly_related": {
            "count": near_duplicate_clear,
            "total": len(near_duplicate_results),
            "rate": round(near_duplicate_rate, 4),
        },
        "unrelated_pairs_classified_new_topic": {
            "count": unrelated_new,
            "total": len(unrelated_results),
            "rate": round(unrelated_rate, 4),
        },
        "related_pairs_not_classified_new_topic": {
            "count": related_not_new,
            "total": len(related_results),
            "rate": round(related_rate, 4),
        },
    }


def build_route_counts(
    all_pairs: list[PairResult],
) -> dict[str, int]:
    counts = Counter(
        result.route
        for result in all_pairs
    )

    return {
        ROUTE_NEW_TOPIC: counts[ROUTE_NEW_TOPIC],
        ROUTE_AMBIGUOUS: counts[ROUTE_AMBIGUOUS],
        ROUTE_CLEARLY_RELATED: counts[
            ROUTE_CLEARLY_RELATED
        ],
    }


def save_report(
    output_path: Path,
    user: User,
    notes: list[Note],
    missing_titles: list[str],
    missing_pairs: dict,
    distribution: DistributionSummary,
    near_duplicate_results: list[PairResult],
    related_results: list[PairResult],
    unrelated_results: list[PairResult],
    all_pairs: list[PairResult],
    evaluation: dict,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    strongest_pairs = sorted(
        all_pairs,
        key=lambda result: result.similarity,
        reverse=True,
    )[:20]

    weakest_pairs = sorted(
        all_pairs,
        key=lambda result: result.similarity,
    )[:20]

    report = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "user": {
            "id": str(user.id),
            "email": user.email,
        },
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "note_count": len(notes),
        "expected_seed_note_count": len(
            EXPECTED_CORPUS_TITLES
        ),
        "missing_expected_titles": missing_titles,
        "thresholds": {
            "low": SIMILARITY_LOW,
            "high": SIMILARITY_HIGH,
            "rules": {
                "new_topic": (
                    f"similarity < {SIMILARITY_LOW}"
                ),
                "ambiguous": (
                    f"{SIMILARITY_LOW} <= similarity "
                    f"<= {SIMILARITY_HIGH}"
                ),
                "clearly_related": (
                    f"similarity > {SIMILARITY_HIGH}"
                ),
            },
        },
        "threshold_evaluation": evaluation,
        "distribution": asdict(distribution),
        "route_counts": build_route_counts(
            all_pairs
        ),
        "missing_labeled_pairs": missing_pairs,
        "near_duplicate_pairs": [
            asdict(result)
            for result in near_duplicate_results
        ],
        "related_pairs": [
            asdict(result)
            for result in related_results
        ],
        "unrelated_pairs": [
            asdict(result)
            for result in unrelated_results
        ],
        "strongest_20_pairs": [
            asdict(result)
            for result in strongest_pairs
        ],
        "weakest_20_pairs": [
            asdict(result)
            for result in weakest_pairs
        ],
    }

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main() -> int:
    arguments = parse_arguments()
    output_path = Path(arguments.output)

    db = SessionLocal()

    try:
        user = choose_user(
            db=db,
            email=arguments.email,
            user_id=arguments.user_id,
        )

        print_divider()
        print("DAY 6 SIMILARITY CALIBRATION")
        print_divider()
        print(f"User            : {user.email}")
        print(
            f"Embedding model : "
            f"{DEFAULT_EMBEDDING_MODEL}"
        )
        print(
            f"Selected LOW    : "
            f"{SIMILARITY_LOW:.2f}"
        )
        print(
            f"Selected HIGH   : "
            f"{SIMILARITY_HIGH:.2f}"
        )

        notes = load_user_notes(db, user)

        print(f"Notes found     : {len(notes)}")

        if len(notes) < 40:
            print(
                "\nWARNING: Fewer than 40 notes were found. "
                "The Day 6 corpus may be incomplete."
            )

        found_titles = {
            note.title.strip()
            for note in notes
        }

        missing_titles = sorted(
            EXPECTED_CORPUS_TITLES
            - found_titles
        )

        if missing_titles:
            print(
                f"\nWARNING: {len(missing_titles)} expected "
                "seed titles are missing:"
            )

            for title in missing_titles:
                print(f"  - {title}")

        if not arguments.skip_embedding_backfill:
            created_count, failed_count = (
                ensure_embeddings(
                    db,
                    notes,
                )
            )

            print(
                f"\nEmbeddings generated: "
                f"{created_count}"
            )

            print(
                f"Embedding failures  : "
                f"{failed_count}"
            )

            if failed_count:
                print(
                    "\nCalibration stopped because some "
                    "embeddings could not be generated."
                )

                return 1

        embeddings_by_title = (
            load_embeddings_by_title(
                db,
                notes,
            )
        )

        print(
            f"Usable embeddings: "
            f"{len(embeddings_by_title)}"
        )

        if len(embeddings_by_title) < 2:
            print(
                "At least two embedded notes are required."
            )

            return 1

        (
            near_duplicate_results,
            missing_near_duplicate_pairs,
        ) = calculate_labeled_pairs(
            embeddings_by_title,
            "near_duplicate",
            NEAR_DUPLICATE_PAIRS,
        )

        (
            related_results,
            missing_related_pairs,
        ) = calculate_labeled_pairs(
            embeddings_by_title,
            "related",
            RELATED_PAIRS,
        )

        (
            unrelated_results,
            missing_unrelated_pairs,
        ) = calculate_labeled_pairs(
            embeddings_by_title,
            "unrelated",
            UNRELATED_PAIRS,
        )

        all_pairs = calculate_all_pairs(
            embeddings_by_title
        )

        all_scores = [
            result.similarity
            for result in all_pairs
        ]

        distribution = summarize_distribution(
            all_scores
        )

        print_pair_results(
            "KNOWN NEAR-DUPLICATE PAIRS",
            near_duplicate_results,
        )

        print_pair_results(
            "KNOWN RELATED / SAME-TOPIC PAIRS",
            related_results,
        )

        print_pair_results(
            "KNOWN UNRELATED PAIRS",
            unrelated_results,
        )

        print_distribution(distribution)

        route_counts = build_route_counts(
            all_pairs
        )

        print()
        print_divider()
        print("ROUTING DISTRIBUTION")
        print_divider()

        print(
            f"NEW TOPIC "
            f"(< {SIMILARITY_LOW:.2f})"
            f"             : "
            f"{route_counts[ROUTE_NEW_TOPIC]}"
        )

        print(
            f"AMBIGUOUS "
            f"({SIMILARITY_LOW:.2f}–"
            f"{SIMILARITY_HIGH:.2f})"
            f"        : "
            f"{route_counts[ROUTE_AMBIGUOUS]}"
        )

        print(
            f"CLEARLY RELATED "
            f"(> {SIMILARITY_HIGH:.2f})"
            f"       : "
            f"{route_counts[ROUTE_CLEARLY_RELATED]}"
        )

        evaluation = evaluate_thresholds(
            near_duplicate_results,
            related_results,
            unrelated_results,
        )

        print()
        print_divider()
        print("FINAL THRESHOLD EVALUATION")
        print_divider()

        status = (
            "PASS"
            if evaluation["passed"]
            else "REVIEW NEEDED"
        )

        print(f"Status: {status}")

        near_data = evaluation[
            "near_duplicates_classified_clearly_related"
        ]

        unrelated_data = evaluation[
            "unrelated_pairs_classified_new_topic"
        ]

        related_data = evaluation[
            "related_pairs_not_classified_new_topic"
        ]

        print(
            "Near duplicates correctly classified as "
            "clearly related: "
            f"{near_data['count']}/{near_data['total']} "
            f"({near_data['rate'] * 100:.1f}%)"
        )

        print(
            "Unrelated pairs correctly classified as "
            "new topics: "
            f"{unrelated_data['count']}/"
            f"{unrelated_data['total']} "
            f"({unrelated_data['rate'] * 100:.1f}%)"
        )

        print(
            "Related pairs retained as ambiguous or "
            "clearly related: "
            f"{related_data['count']}/"
            f"{related_data['total']} "
            f"({related_data['rate'] * 100:.1f}%)"
        )

        missing_pairs = {
            "near_duplicate": [
                list(pair)
                for pair
                in missing_near_duplicate_pairs
            ],
            "related": [
                list(pair)
                for pair in missing_related_pairs
            ],
            "unrelated": [
                list(pair)
                for pair in missing_unrelated_pairs
            ],
        }

        save_report(
            output_path=output_path,
            user=user,
            notes=notes,
            missing_titles=missing_titles,
            missing_pairs=missing_pairs,
            distribution=distribution,
            near_duplicate_results=(
                near_duplicate_results
            ),
            related_results=related_results,
            unrelated_results=unrelated_results,
            all_pairs=all_pairs,
            evaluation=evaluation,
        )

        print()
        print_divider()
        print("FINAL DAY 6 VALUES")
        print_divider()
        print(
            f"SIMILARITY_LOW = {SIMILARITY_LOW}"
        )
        print(
            f"SIMILARITY_HIGH = {SIMILARITY_HIGH}"
        )

        print(
            "\nReasoning:"
            "\n- Below 0.45, matches are usually unrelated "
            "or too weak."
            "\n- From 0.45 to 0.65, the relationship is "
            "ambiguous and should be reasoned about."
            "\n- Above 0.65, notes are strongly related or "
            "near-duplicates."
        )

        print(
            f"\nJSON report saved to: "
            f"{output_path.resolve()}"
        )

        print_divider()

        return 0

    except Exception as error:
        print()
        print_divider("!")
        print(f"CALIBRATION FAILED: {error}")
        print_divider("!")

        return 1

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())