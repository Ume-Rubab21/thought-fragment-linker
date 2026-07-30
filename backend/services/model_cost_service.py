from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)


ONE_MILLION_TOKENS = Decimal("1000000")
COST_PRECISION = Decimal("0.00000001")


class ModelCostConfigurationError(
    RuntimeError
):
    """Raised when model pricing configuration is invalid."""


@dataclass(frozen=True)
class ModelTokenRates:
    """
    Model prices expressed in USD per one million tokens.

    Rates are configurable through environment variables because model
    provider prices may change over time.
    """

    input_per_million_usd: Decimal
    output_per_million_usd: Decimal


@dataclass(frozen=True)
class ModelCostEstimate:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    input_cost_usd: Decimal
    output_cost_usd: Decimal
    total_cost_usd: Decimal


def read_decimal_environment_value(
    name: str,
    *,
    default: str = "0",
) -> Decimal:
    raw_value = os.getenv(
        name,
        default,
    ).strip()

    try:
        value = Decimal(raw_value)

    except InvalidOperation as error:
        raise ModelCostConfigurationError(
            f"{name} must contain a valid decimal number."
        ) from error

    if value < 0:
        raise ModelCostConfigurationError(
            f"{name} cannot be negative."
        )

    return value


def get_model_token_rates(
    *,
    model_tier: str,
) -> ModelTokenRates:
    """
    Read pricing from environment variables.

    Supported variables:

        SMALL_MODEL_INPUT_COST_PER_MILLION_USD
        SMALL_MODEL_OUTPUT_COST_PER_MILLION_USD

        LARGE_MODEL_INPUT_COST_PER_MILLION_USD
        LARGE_MODEL_OUTPUT_COST_PER_MILLION_USD

    Defaults are zero so the application never invents provider pricing.
    Add the real configured prices for the models used by the project.
    """

    normalized_tier = (
        model_tier.strip().lower()
    )

    if normalized_tier == "small":
        return ModelTokenRates(
            input_per_million_usd=(
                read_decimal_environment_value(
                    "SMALL_MODEL_INPUT_COST_PER_MILLION_USD"
                )
            ),
            output_per_million_usd=(
                read_decimal_environment_value(
                    "SMALL_MODEL_OUTPUT_COST_PER_MILLION_USD"
                )
            ),
        )

    if normalized_tier == "large":
        return ModelTokenRates(
            input_per_million_usd=(
                read_decimal_environment_value(
                    "LARGE_MODEL_INPUT_COST_PER_MILLION_USD"
                )
            ),
            output_per_million_usd=(
                read_decimal_environment_value(
                    "LARGE_MODEL_OUTPUT_COST_PER_MILLION_USD"
                )
            ),
        )

    raise ModelCostConfigurationError(
        "model_tier must be either 'small' or 'large'."
    )


def validate_token_count(
    value: int,
    *,
    field_name: str,
) -> int:
    try:
        token_count = int(value)

    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{field_name} must be an integer."
        ) from error

    if token_count < 0:
        raise ValueError(
            f"{field_name} cannot be negative."
        )

    return token_count


def calculate_token_cost(
    *,
    token_count: int,
    rate_per_million_usd: Decimal,
) -> Decimal:
    """
    Calculate the USD cost for one token category.
    """

    return (
        Decimal(token_count)
        * rate_per_million_usd
        / ONE_MILLION_TOKENS
    ).quantize(
        COST_PRECISION,
        rounding=ROUND_HALF_UP,
    )


def estimate_model_call_cost(
    *,
    model_tier: str,
    prompt_tokens: int,
    completion_tokens: int,
    rates: ModelTokenRates | None = None,
) -> ModelCostEstimate:
    """
    Calculate estimated model cost using input and output token prices.
    """

    safe_prompt_tokens = validate_token_count(
        prompt_tokens,
        field_name="prompt_tokens",
    )

    safe_completion_tokens = (
        validate_token_count(
            completion_tokens,
            field_name="completion_tokens",
        )
    )

    active_rates = (
        rates
        or get_model_token_rates(
            model_tier=model_tier,
        )
    )

    input_cost = calculate_token_cost(
        token_count=safe_prompt_tokens,
        rate_per_million_usd=(
            active_rates.input_per_million_usd
        ),
    )

    output_cost = calculate_token_cost(
        token_count=safe_completion_tokens,
        rate_per_million_usd=(
            active_rates.output_per_million_usd
        ),
    )

    total_cost = (
        input_cost + output_cost
    ).quantize(
        COST_PRECISION,
        rounding=ROUND_HALF_UP,
    )

    return ModelCostEstimate(
        prompt_tokens=safe_prompt_tokens,
        completion_tokens=(
            safe_completion_tokens
        ),
        total_tokens=(
            safe_prompt_tokens
            + safe_completion_tokens
        ),
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        total_cost_usd=total_cost,
    )