"""
Similarity thresholds calibrated for:

sentence-transformers/all-MiniLM-L6-v2

LOW:
    Scores below this value are treated as a new topic.

LOW to HIGH:
    Scores inside this range are ambiguous and can be
    escalated to the large reasoning model.

HIGH:
    Scores above this value are treated as clearly related.

These values were selected using the Day 6 calibration corpus:
- PostgreSQL/search cluster
- React/frontend cluster
- AI/embedding cluster
- Near-duplicate notes
- Unrelated notes
"""

SIMILARITY_LOW = 0.45
SIMILARITY_HIGH = 0.65


ROUTE_NEW_TOPIC = "new_topic"
ROUTE_AMBIGUOUS = "ambiguous"
ROUTE_CLEARLY_RELATED = "clearly_related"


def classify_similarity(similarity: float) -> str:
    """
    Classify one cosine-similarity score.

    Rules required by the PRD:

    score < LOW:
        New topic. No large-model escalation.

    LOW <= score <= HIGH:
        Ambiguous. Escalate to the reasoning model.

    score > HIGH:
        Clearly related. No large-model escalation.
    """
    if similarity < SIMILARITY_LOW:
        return ROUTE_NEW_TOPIC

    if similarity <= SIMILARITY_HIGH:
        return ROUTE_AMBIGUOUS

    return ROUTE_CLEARLY_RELATED