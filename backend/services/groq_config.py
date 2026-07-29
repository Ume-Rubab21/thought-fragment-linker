from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Locate backend/.env reliably, regardless of where the command is run.
BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIRECTORY / ".env"

load_dotenv(dotenv_path=ENV_FILE)


@dataclass(frozen=True)
class GroqSettings:
    api_key: str
    small_model: str
    temperature: float
    max_tokens: int


def get_groq_settings() -> GroqSettings:
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            f"GROQ_API_KEY is missing. Add it to: {ENV_FILE}"
        )

    small_model = os.getenv(
        "GROQ_SMALL_MODEL",
        "llama-3.1-8b-instant",
    ).strip()

    try:
        temperature = float(
            os.getenv(
                "GROQ_SMALL_MODEL_TEMPERATURE",
                "0.1",
            )
        )
    except ValueError as error:
        raise RuntimeError(
            "GROQ_SMALL_MODEL_TEMPERATURE must be a number."
        ) from error

    try:
        max_tokens = int(
            os.getenv(
                "GROQ_SMALL_MODEL_MAX_TOKENS",
                "500",
            )
        )
    except ValueError as error:
        raise RuntimeError(
            "GROQ_SMALL_MODEL_MAX_TOKENS must be an integer."
        ) from error

    return GroqSettings(
        api_key=api_key,
        small_model=small_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )