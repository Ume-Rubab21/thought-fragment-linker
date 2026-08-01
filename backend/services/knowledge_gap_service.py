from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class KnowledgeGapInsight:
    title: str
    description: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


TOPIC_RULES: tuple[dict[str, object], ...] = (
    {
        "triggers": {"semantic", "search", "pgvector", "embedding", "similarity"},
        "gaps": (
            (
                {"evaluation", "precision", "recall", "benchmark"},
                "Search evaluation",
                "Add a plan for measuring retrieval quality with test queries and relevance metrics.",
            ),
            (
                {"index", "hnsw", "ivfflat", "performance"},
                "Vector-index strategy",
                "Explain which vector index to use and how it affects speed, recall, and maintenance.",
            ),
            (
                {"refresh", "update", "re-embed", "consistency"},
                "Embedding lifecycle",
                "Describe when embeddings are regenerated after a note changes and how stale vectors are handled.",
            ),
        ),
    },
    {
        "triggers": {"reasoning", "confidence", "routing", "large model", "human review"},
        "gaps": (
            (
                {"calibration", "threshold", "confidence calibration"},
                "Confidence calibration",
                "Define how confidence scores are calibrated and which thresholds trigger human review.",
            ),
            (
                {"fallback", "failure", "retry", "guardrail"},
                "Reasoning fallback",
                "Document what happens when reasoning output is invalid, unavailable, or rejected by guardrails.",
            ),
            (
                {"feedback", "correction", "learning"},
                "Human-feedback loop",
                "Capture accepted, edited, and rejected decisions so routing quality can be evaluated later.",
            ),
        ),
    },
    {
        "triggers": {"fastapi", "backend", "api", "database", "pipeline"},
        "gaps": (
            (
                {"test", "testing", "integration"},
                "Integration testing",
                "Add an end-to-end test that verifies the complete request, processing, and persistence flow.",
            ),
            (
                {"logging", "metrics", "observability", "latency"},
                "Operational visibility",
                "Track failures, latency, retries, and routing decisions so production issues can be diagnosed.",
            ),
        ),
    },
)


def detect_knowledge_gaps(
    raw_text: str,
    *,
    limit: int = 3,
) -> list[KnowledgeGapInsight]:
    """Return deterministic, inspectable gap suggestions without another AI call."""
    normalized = " ".join(raw_text.lower().replace("-", " ").split())
    words = set(normalized.split())
    results: list[KnowledgeGapInsight] = []
    seen_titles: set[str] = set()

    for rule in TOPIC_RULES:
        triggers = rule["triggers"]
        if not any(trigger in normalized or trigger in words for trigger in triggers):
            continue

        for present_terms, title, description in rule["gaps"]:
            if any(term in normalized for term in present_terms):
                continue
            if title in seen_titles:
                continue

            seen_titles.add(title)
            results.append(
                KnowledgeGapInsight(
                    title=title,
                    description=description,
                    evidence="Suggested because the Brain Dump discusses related concepts but does not cover this area.",
                )
            )

            if len(results) >= max(0, min(limit, 5)):
                return results

    return results
