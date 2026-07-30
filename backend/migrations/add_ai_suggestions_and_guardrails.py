"""
Create the ai_suggestions and guardrail_events tables.

Run from the backend folder:

    python migrations/add_ai_suggestions_and_guardrails.py
"""

import sys
from pathlib import Path

from sqlalchemy import text


BACKEND_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from database import engine  # noqa: E402


def run() -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS ai_suggestions (
            id UUID PRIMARY KEY,

            user_id UUID NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,

            brain_dump_id UUID NOT NULL
                REFERENCES braindumps(id)
                ON DELETE CASCADE,

            suggested_title VARCHAR(120) NOT NULL,

            summary TEXT NOT NULL,

            tags JSONB NOT NULL
                DEFAULT '[]'::jsonb,

            keywords JSONB NOT NULL
                DEFAULT '[]'::jsonb,

            related_note_ids JSONB NOT NULL
                DEFAULT '[]'::jsonb,

            model_name VARCHAR(120) NOT NULL,

            prompt_tokens INTEGER NOT NULL
                DEFAULT 0,

            completion_tokens INTEGER NOT NULL
                DEFAULT 0,

            total_tokens INTEGER NOT NULL
                DEFAULT 0,

            attempts INTEGER NOT NULL
                DEFAULT 1,

            retry_count INTEGER NOT NULL
                DEFAULT 0,

            status VARCHAR(30) NOT NULL
                DEFAULT 'pending',

            created_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT ck_ai_suggestions_status
                CHECK (
                    status IN (
                        'pending',
                        'accepted',
                        'rejected',
                        'applied'
                    )
                ),

            CONSTRAINT ck_ai_suggestions_prompt_tokens
                CHECK (prompt_tokens >= 0),

            CONSTRAINT ck_ai_suggestions_completion_tokens
                CHECK (completion_tokens >= 0),

            CONSTRAINT ck_ai_suggestions_total_tokens
                CHECK (total_tokens >= 0),

            CONSTRAINT ck_ai_suggestions_attempts
                CHECK (attempts >= 1),

            CONSTRAINT ck_ai_suggestions_retry_count
                CHECK (retry_count >= 0),

            CONSTRAINT uq_ai_suggestions_brain_dump
                UNIQUE (brain_dump_id)
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_ai_suggestions_user_id
        ON ai_suggestions (user_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_ai_suggestions_brain_dump_id
        ON ai_suggestions (brain_dump_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_ai_suggestions_status
        ON ai_suggestions (status)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_ai_suggestions_user_created_at
        ON ai_suggestions (
            user_id,
            created_at DESC
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS guardrail_events (
            id UUID PRIMARY KEY,

            user_id UUID NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,

            brain_dump_id UUID NOT NULL
                REFERENCES braindumps(id)
                ON DELETE CASCADE,

            attempt_number INTEGER NOT NULL,

            failure_category VARCHAR(80) NOT NULL,

            failure_reason TEXT NOT NULL,

            raw_model_response TEXT NULL,

            failure_metadata JSONB NOT NULL
                DEFAULT '{}'::jsonb,

            model_name VARCHAR(120) NULL,

            prompt_tokens INTEGER NOT NULL
                DEFAULT 0,

            completion_tokens INTEGER NOT NULL
                DEFAULT 0,

            total_tokens INTEGER NOT NULL
                DEFAULT 0,

            created_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT ck_guardrail_attempt_number
                CHECK (attempt_number >= 1),

            CONSTRAINT ck_guardrail_prompt_tokens
                CHECK (prompt_tokens >= 0),

            CONSTRAINT ck_guardrail_completion_tokens
                CHECK (completion_tokens >= 0),

            CONSTRAINT ck_guardrail_total_tokens
                CHECK (total_tokens >= 0)
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_guardrail_events_user_id
        ON guardrail_events (user_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_guardrail_events_brain_dump_id
        ON guardrail_events (brain_dump_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_guardrail_events_failure_category
        ON guardrail_events (failure_category)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_guardrail_events_brain_dump_attempt
        ON guardrail_events (
            brain_dump_id,
            attempt_number
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
        ix_guardrail_events_user_created_at
        ON guardrail_events (
            user_id,
            created_at DESC
        )
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(
                text(statement)
            )

    print(
        "AI suggestion and guardrail migration "
        "completed successfully."
    )

    print(
        "Created ai_suggestions and "
        "guardrail_events tables."
    )


if __name__ == "__main__":
    run()