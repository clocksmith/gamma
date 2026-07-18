from __future__ import annotations

from projects.enwiki9.tools.seal_fx2_cmix21_original_order_blend import (
    calculate_economics,
    guard_binary_path,
    guard_env_path,
    within_regression_budget,
)


def test_calculate_economics_charges_order_and_program() -> None:
    result = calculate_economics(
        original_archive_bytes=1_648_690,
        geometry_archive_bytes=1_643_626,
        compact_package_bytes=264_314,
        blend_rate_bytes_per_1m=1_345.0,
    )

    assert result["original_order_penalty_bytes_per_1m"] == 506.4
    assert result["incremental_compact_program_bytes"] == 81_309
    assert result[
        "required_blend_rate_if_combined_package_matches_compact_bytes_per_1m"
    ] == 1_268.824
    assert result["maximum_combined_program_bytes_at_target"] == 340_493
    assert result["headroom_over_compact_program_bytes"] == 76_176


def test_guard_binary_path_skips_env_assignments() -> None:
    guard = {
        "command": [
            "env",
            "CMIX_P1_TRACE=/tmp/trace.bin",
            "/tmp/cmix.bin",
            "-r",
            "/tmp/dic",
            "/tmp/in",
            "/tmp/out",
        ]
    }

    assert guard_binary_path(guard).as_posix() == "/tmp/cmix.bin"
    assert guard_env_path(guard, "CMIX_P1_TRACE").as_posix() == "/tmp/trace.bin"


def test_guard_helpers_accept_absolute_env_program() -> None:
    guard = {
        "command": [
            "/usr/bin/env",
            "CMIX_P1_TRACE=/tmp/trace.bin",
            "/tmp/cmix.bin",
            "-r",
            "/tmp/dic",
            "/tmp/in",
            "/tmp/out",
        ]
    }

    assert guard_binary_path(guard).as_posix() == "/tmp/cmix.bin"
    assert guard_env_path(guard, "CMIX_P1_TRACE").as_posix() == "/tmp/trace.bin"


def test_regression_budget_is_bounded_but_not_zero_only() -> None:
    assert within_regression_budget(
        {
            "holdout_block_regressions": 2,
            "largest_holdout_block_regression_bytes": 32,
            "total_holdout_block_regression_bytes": 64,
        }
    )
    assert not within_regression_budget(
        {
            "holdout_block_regressions": 3,
            "largest_holdout_block_regression_bytes": 1,
            "total_holdout_block_regression_bytes": 3,
        }
    )
    assert not within_regression_budget(
        {
            "holdout_block_regressions": 1,
            "largest_holdout_block_regression_bytes": 33,
            "total_holdout_block_regression_bytes": 33,
        }
    )
