"""
Create the model_calls table.

Run from the backend directory:

    python migrations/add_model_calls.py
"""

import sys
from pathlib import Path

from sqlalchemy import text


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIRECTORY),
    )


from database import engine  # noqa: E402


def run() -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS model_calls (
            id UUID PRIMARY KEY,

            user_id UUID NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,

            brain_dump_id UUID
                REFERENCES braindumps(id)
                ON DELETE CASCADE,

            provider VARCHAR(50) NOT NULL,

            model_name VARCHAR(150) NOT NULL,

            model_tier VARCHAR(20) NOT NULL,

            call_purpose VARCHAR(80) NOT NULL
                DEFAULT 'brain-dump-suggestion',

            routing_decision VARCHAR(40) NOT NULL,

            routing_reason VARCHAR(500) NOT NULL,

            highest_similarity DOUBLE PRECISION,

            low_threshold DOUBLE PRECISION,

            high_threshold DOUBLE PRECISION,

            prompt_tokens INTEGER NOT NULL DEFAULT 0,

            completion_tokens INTEGER NOT NULL DEFAULT 0,

            total_tokens INTEGER NOT NULL DEFAULT 0,

            latency_ms INTEGER NOT NULL DEFAULT 0,

            estimated_cost_usd DOUBLE PRECISION
                NOT NULL DEFAULT 0,

            success BOOLEAN NOT NULL DEFAULT TRUE,

            error_message TEXT,

            created_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT ck_model_calls_similarity_range
                CHECK (
                    highest_similarity IS NULL
                    OR (
                        highest_similarity >= 0
                        AND highest_similarity <= 1
                    )
                ),

            CONSTRAINT ck_model_calls_low_threshold_range
                CHECK (
                    low_threshold IS NULL
                    OR (
                        low_threshold >= 0
                        AND low_threshold <= 1
                    )
                ),

            CONSTRAINT ck_model_calls_high_threshold_range
                CHECK (
                    high_threshold IS NULL
                    OR (
                        high_threshold >= 0
                        AND high_threshold <= 1
                    )
                ),

            CONSTRAINT ck_model_calls_threshold_order
                CHECK (
                    low_threshold IS NULL
                    OR high_threshold IS NULL
                    OR low_threshold <= high_threshold
                ),

            CONSTRAINT ck_model_calls_prompt_tokens_non_negative
                CHECK (
                    prompt_tokens >= 0
                ),

            CONSTRAINT ck_model_calls_completion_tokens_non_negative
                CHECK (
                    completion_tokens >= 0
                ),

            CONSTRAINT ck_model_calls_total_tokens_non_negative
                CHECK (
                    total_tokens >= 0
                ),

            CONSTRAINT ck_model_calls_latency_non_negative
                CHECK (
                    latency_ms >= 0
                ),

            CONSTRAINT ck_model_calls_cost_non_negative
                CHECK (
                    estimated_cost_usd >= 0
                )
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_model_calls_user_id
        ON model_calls (
            user_id
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_model_calls_brain_dump_id
        ON model_calls (
            brain_dump_id
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_model_calls_created_at
        ON model_calls (
            created_at
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_model_calls_user_created_at
        ON model_calls (
            user_id,
            created_at
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_model_calls_routing_decision
        ON model_calls (
            routing_decision
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_model_calls_model_tier
        ON model_calls (
            model_tier
        )
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(
                text(statement)
            )

    print(
        "Model calls migration completed successfully."
    )
    print(
        "Created model_calls table and indexes."
    )


if __name__ == "__main__":
    run()