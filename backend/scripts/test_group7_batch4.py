from __future__ import annotations

import argparse
import sys
from pathlib import Path


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]

if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIRECTORY),
    )


from database import SessionLocal
from models.user import User
from services.model_call_dashboard_service import (
    get_model_call_dashboard,
)


def print_pass(message: str) -> None:
    print(f"PASS {message}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the Group 7 routing dashboard "
            "for one user."
        )
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Email address of the user to test.",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == args.email)
            .first()
        )

        if user is None:
            raise RuntimeError(
                f"User not found: {args.email}"
            )

        dashboard = get_model_call_dashboard(
            db=db,
            user_id=user.id,
            limit=25,
        )

        summary = dashboard.summary

        print("=" * 72)
        print(
            "THOUGHTLINKER GROUP 7 BATCH 4 "
            "DASHBOARD TEST"
        )
        print("=" * 72)

        print(f"User email       : {user.email}")
        print(f"Total calls      : {summary.total_calls}")
        print(
            f"Successful calls : "
            f"{summary.successful_calls}"
        )
        print(
            f"Failed calls     : "
            f"{summary.failed_calls}"
        )
        print(
            f"Small calls      : "
            f"{summary.small_model_calls}"
        )
        print(
            f"Large calls      : "
            f"{summary.large_model_calls}"
        )
        print(
            f"Total tokens     : "
            f"{summary.total_tokens}"
        )
        print(
            f"Average latency  : "
            f"{summary.average_latency_ms} ms"
        )
        print(
            f"Actual cost      : "
            f"${summary.actual_cost_usd:.8f}"
        )
        print(
            f"All-large cost   : "
            f"${summary.estimated_all_large_cost_usd:.8f}"
        )
        print(
            f"Estimated saving : "
            f"${summary.estimated_savings_usd:.8f}"
        )
        print(
            f"Savings percent  : "
            f"{summary.savings_percentage:.2f}%"
        )

        print("-" * 72)

        assert (
            summary.total_calls
            == summary.successful_calls
            + summary.failed_calls
        )

        print_pass(
            "Successful and failed calls match total calls"
        )

        assert (
            summary.total_calls
            == summary.small_model_calls
            + summary.large_model_calls
        )

        print_pass(
            "Small and large calls match total calls"
        )

        assert summary.total_tokens >= 0

        print_pass(
            "Total token count is valid"
        )

        assert summary.total_latency_ms >= 0

        print_pass(
            "Total latency is valid"
        )

        assert summary.average_latency_ms >= 0

        print_pass(
            "Average latency is valid"
        )

        assert summary.actual_cost_usd >= 0

        print_pass(
            "Actual estimated cost is valid"
        )

        assert (
            summary.estimated_all_large_cost_usd
            >= 0
        )

        print_pass(
            "All-large estimated cost is valid"
        )

        assert summary.estimated_savings_usd >= 0

        print_pass(
            "Estimated savings value is valid"
        )

        assert 0 <= summary.savings_percentage <= 100

        print_pass(
            "Savings percentage is valid"
        )

        assert len(dashboard.calls) <= 25

        print_pass(
            "Dashboard call limit is respected"
        )

        for model_call in dashboard.calls:
            assert model_call.model_tier in {
                "small",
                "large",
            }

            assert model_call.prompt_tokens >= 0
            assert model_call.completion_tokens >= 0
            assert model_call.total_tokens >= 0
            assert model_call.latency_ms >= 0
            assert model_call.estimated_cost_usd >= 0

        print_pass(
            "Recent model-call records are valid"
        )

        if summary.total_calls == 0:
            print(
                "INFO No model calls are recorded yet. "
                "Process a Brain Dump and rerun this test."
            )
        else:
            print(
                "INFO Model-call records were found "
                "for this user."
            )

        print("-" * 72)
        print(
            "GROUP 7 BATCH 4 DASHBOARD TEST PASSED"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()