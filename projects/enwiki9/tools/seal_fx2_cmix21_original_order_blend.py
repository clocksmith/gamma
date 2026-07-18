#!/usr/bin/env python3
"""Seal the frozen exact-FX2/compact-200 original-order blend decision."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASELINE_FORECAST_SCORE_BYTES = 110_181_114
BASELINE_PROGRAM_BYTES = 183_008
TARGET_SCORE_BYTES = 109_500_000
ARCHIVE_MARKER_BYTES = 1
OPTION_BYTES = 3
EXPECTED_WEIGHT_PPM = 750_000
OPENING_SCOPE_BYTES = 1_000_000
CONFIRMATION_SCOPE_BYTES = 10_000_000
MAX_HOLDOUT_REGRESSION_BLOCKS = 2
MAX_LARGEST_HOLDOUT_REGRESSION_BYTES = 32
MAX_TOTAL_HOLDOUT_REGRESSION_BYTES = 64


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def clean_guard(guard: dict[str, Any]) -> bool:
    return bool(
        guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib", 0) == 0
    )


def guard_binary_path(guard: dict[str, Any]) -> Path:
    command = guard.get("command")
    if not isinstance(command, list) or not command:
        raise RuntimeError("guard lacks a command")
    index = 0
    if Path(str(command[0])).name == "env":
        index = 1
        while index < len(command) and "=" in str(command[index]):
            index += 1
    if index >= len(command) or not isinstance(command[index], str):
        raise RuntimeError("guard lacks a codec binary")
    return Path(command[index]).resolve()


def guard_env_path(guard: dict[str, Any], name: str) -> Path:
    command = guard.get("command")
    if not isinstance(command, list) or not command:
        raise RuntimeError("guard lacks a command")
    if Path(str(command[0])).name != "env":
        raise RuntimeError(f"guard command lacks required {name} assignment")
    for token in command[1:]:
        text = str(token)
        if "=" not in text:
            break
        key, value = text.split("=", 1)
        if key == name and value:
            return Path(value).resolve()
    raise RuntimeError(f"guard command lacks required {name} assignment")


def within_regression_budget(replay: dict[str, Any]) -> bool:
    return bool(
        replay.get("holdout_block_regressions", 1 << 30)
        <= MAX_HOLDOUT_REGRESSION_BLOCKS
        and replay.get("largest_holdout_block_regression_bytes", 1 << 30)
        <= MAX_LARGEST_HOLDOUT_REGRESSION_BYTES
        and replay.get("total_holdout_block_regression_bytes", 1 << 30)
        <= MAX_TOTAL_HOLDOUT_REGRESSION_BYTES
    )


def calculate_economics(
    *,
    original_archive_bytes: int,
    geometry_archive_bytes: int,
    compact_package_bytes: int,
    blend_rate_bytes_per_1m: float,
) -> dict[str, int | float]:
    order_penalty_rate = (
        original_archive_bytes - geometry_archive_bytes
    ) * 1_000_000 / CONFIRMATION_SCOPE_BYTES
    forecast_debt = BASELINE_FORECAST_SCORE_BYTES - TARGET_SCORE_BYTES
    compact_program_bytes = compact_package_bytes + OPTION_BYTES
    incremental_compact_program_bytes = compact_program_bytes - BASELINE_PROGRAM_BYTES
    required_rate_if_compact_package = (
        forecast_debt
        + order_penalty_rate * 1000
        + incremental_compact_program_bytes
        + ARCHIVE_MARKER_BYTES
    ) / 1000
    projected_blend_gain = round(blend_rate_bytes_per_1m * 1000)
    projected_order_penalty = round(order_penalty_rate * 1000)
    maximum_combined_program_bytes = (
        TARGET_SCORE_BYTES
        - BASELINE_FORECAST_SCORE_BYTES
        + BASELINE_PROGRAM_BYTES
        - projected_order_penalty
        + projected_blend_gain
        - ARCHIVE_MARKER_BYTES
    )
    return {
        "baseline_forecast_score_bytes": BASELINE_FORECAST_SCORE_BYTES,
        "baseline_program_bytes": BASELINE_PROGRAM_BYTES,
        "target_score_bytes": TARGET_SCORE_BYTES,
        "forecast_debt_bytes": forecast_debt,
        "original_archive_bytes_10m": original_archive_bytes,
        "geometry_title_archive_bytes_10m": geometry_archive_bytes,
        "original_order_penalty_bytes_10m": (
            original_archive_bytes - geometry_archive_bytes
        ),
        "original_order_penalty_bytes_per_1m": order_penalty_rate,
        "compact_source_package_bytes": compact_package_bytes,
        "compact_option_bytes": OPTION_BYTES,
        "compact_program_bytes": compact_program_bytes,
        "incremental_compact_program_bytes": incremental_compact_program_bytes,
        "required_blend_rate_if_combined_package_matches_compact_bytes_per_1m": (
            required_rate_if_compact_package
        ),
        "observed_blend_rate_bytes_per_1m": blend_rate_bytes_per_1m,
        "projected_blend_gain_bytes": projected_blend_gain,
        "projected_original_order_penalty_bytes": projected_order_penalty,
        "maximum_combined_program_bytes_at_target": maximum_combined_program_bytes,
        "headroom_over_compact_program_bytes": (
            maximum_combined_program_bytes - compact_program_bytes
        ),
    }


def require_screen(
    screen: dict[str, Any], *, scope: int, frozen: bool
) -> dict[str, Any]:
    if screen.get("schema") != "fx2_cmix21_nested_endpoint_screen_v1":
        raise RuntimeError("unexpected matched-screen schema")
    if screen.get("scope_raw_bytes") != scope:
        raise RuntimeError("matched screen has the wrong scope")
    expected_mode = "frozen_confirmation" if frozen else "discovery_selection"
    if screen.get("mode") != expected_mode:
        raise RuntimeError("matched screen has the wrong selection mode")
    selected = screen.get("selected", {})
    if (
        selected.get("kind") != "fixed_blend"
        or selected.get("weight_ppm") != EXPECTED_WEIGHT_PPM
        or selected.get("endpoint_name") != "compact200_original_post_sse"
    ):
        raise RuntimeError("matched screen changed the frozen endpoint or weight")
    trace = screen.get("trace", {})
    base = screen.get("base", {})
    replay = screen.get("exact_cmix_replay", {})
    if trace.get("wrt_truth_stream_identity") is not True:
        raise RuntimeError("WRT truth identity failed")
    if base.get("name") != "exact_fx2_original_order":
        raise RuntimeError("matched screen uses the wrong base")
    if base.get("reference_archive_identity") is not True:
        raise RuntimeError("observation changed the exact FX2 archive")
    if base.get("archive_payload_identity") is not True:
        raise RuntimeError("base probability replay changed the FX2 payload")
    if replay.get("decoder_replay_ok") is not True:
        raise RuntimeError("candidate decoder replay failed")
    return replay


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact-package-receipt", type=Path, required=True)
    parser.add_argument("--opening-screen", type=Path, required=True)
    parser.add_argument("--confirmation-screen", type=Path, required=True)
    parser.add_argument("--original-fx2-receipt", type=Path, required=True)
    parser.add_argument("--geometry-fx2-receipt", type=Path, required=True)
    parser.add_argument("--compact-trace-guard", type=Path, required=True)
    parser.add_argument("--trace-identity-archive", type=Path, required=True)
    parser.add_argument("--trace-identity-reference", type=Path, required=True)
    parser.add_argument("--trace-identity-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    package = load_object(args.compact_package_receipt)
    opening = load_object(args.opening_screen)
    confirmation = load_object(args.confirmation_screen)
    original = load_object(args.original_fx2_receipt)
    geometry = load_object(args.geometry_fx2_receipt)
    compact_guard = load_object(args.compact_trace_guard)
    identity_guard = load_object(args.trace_identity_guard)
    if package.get("schema") != "reproducible_source_shar_package_v1":
        raise RuntimeError("unexpected compact source-package schema")
    if package.get("proof", {}).get("proof_complete") is not True:
        raise RuntimeError("compact source-package proof is incomplete")
    opening_replay = require_screen(
        opening, scope=OPENING_SCOPE_BYTES, frozen=False
    )
    confirmation_replay = require_screen(
        confirmation, scope=CONFIRMATION_SCOPE_BYTES, frozen=True
    )
    if not clean_guard(compact_guard) or not clean_guard(identity_guard):
        raise RuntimeError("one or more compact trace guards are not clean")
    compact_trace_binary = guard_binary_path(compact_guard)
    identity_trace_binary = guard_binary_path(identity_guard)
    if compact_trace_binary != identity_trace_binary:
        raise RuntimeError(
            "the cumulative trace and arithmetic-neutrality gate use different binaries"
        )
    identity_archive = artifact(args.trace_identity_archive)
    identity_reference = artifact(args.trace_identity_reference)
    if any(
        identity_archive[key] != identity_reference[key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("trace instrumentation changed the compact archive")

    original_archive = artifact(Path(original["archive"]["path"]))
    original_store = artifact(Path(original["wrt_store"]["path"]))
    confirmation_trace = confirmation["trace"]
    confirmation_base = confirmation["base"]
    if any(
        original_archive[key] != original["archive"][key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("original FX2 archive changed")
    if any(
        original_store[key] != original["wrt_store"][key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("original WRT store changed")
    if artifact(Path(confirmation_trace["wrt_store_path"]))["sha256"] != (
        original_store["sha256"]
    ):
        raise RuntimeError("confirmation screen uses a different WRT store")
    if artifact(Path(confirmation_base["archive_path"]))["sha256"] != (
        original_archive["sha256"]
    ):
        raise RuntimeError("confirmation screen uses a different FX2 archive")

    geometry_archive = artifact(Path(geometry["archive"]["path"]))
    if any(
        geometry_archive[key] != geometry["archive"][key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("geometry-title FX2 archive changed")
    package_bytes = int(package["artifacts"]["zip_a"]["bytes"])
    full_rate = float(confirmation_replay["full_saved_bytes_per_1m_raw"])
    holdout_rate = float(
        confirmation_replay["holdout_saved_bytes_per_proportional_1m_raw"]
    )
    accounting = calculate_economics(
        original_archive_bytes=original_archive["bytes"],
        geometry_archive_bytes=geometry_archive["bytes"],
        compact_package_bytes=package_bytes,
        blend_rate_bytes_per_1m=full_rate,
    )
    required_rate = float(
        accounting[
            "required_blend_rate_if_combined_package_matches_compact_bytes_per_1m"
        ]
    )
    regression_budget_ok = within_regression_budget(confirmation_replay)
    clears_optimistic_floor = full_rate >= required_rate
    holdout_clears_optimistic_floor = holdout_rate >= required_rate
    if (
        clears_optimistic_floor
        and holdout_clears_optimistic_floor
        and regression_budget_ok
    ):
        verdict = "cumulative_signal_pass_requires_combined_native_integration"
        integration_authorized = True
        next_action = (
            "integrate exact FX2 and the compact-200 endpoint in one shared-state "
            "process, then measure combined source bytes, decimal RSS, exact archive "
            "transfer, roundtrip, and determinism"
        )
    else:
        verdict = "retire_original_order_fixed_blend_insufficient_cumulative_margin"
        integration_authorized = False
        next_action = (
            "preserve the matched endpoint evidence and return to a new shared-state "
            "endpoint; do not run a larger unchanged original-order blend"
        )

    candidate_payload = Path(confirmation_replay["candidate_payload_path"])
    external_trace = Path(confirmation_trace["external_endpoint_path"])
    guarded_trace = guard_env_path(compact_guard, "CMIX_P1_TRACE")
    if guarded_trace != external_trace.resolve():
        raise RuntimeError("confirmation screen did not consume the guarded trace")
    compact_command = compact_guard.get("command")
    if not isinstance(compact_command, list) or len(compact_command) < 3:
        raise RuntimeError("compact trace guard lacks codec input and output paths")
    guarded_store = Path(str(compact_command[-2])).resolve()
    if guarded_store != Path(original_store["path"]).resolve():
        raise RuntimeError("compact trace guard used a different WRT store")
    compact_trace_archive = Path(str(compact_command[-1]))
    receipt = {
        "schema": "fx2_cmix21_original_order_blend_terminal_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "frozen_cumulative_10m_exact_shadow_range_replay",
        "artifacts": {
            "compact_package_receipt": artifact(args.compact_package_receipt),
            "opening_screen": artifact(args.opening_screen),
            "confirmation_screen": artifact(args.confirmation_screen),
            "original_fx2_receipt": artifact(args.original_fx2_receipt),
            "geometry_fx2_receipt": artifact(args.geometry_fx2_receipt),
            "compact_trace_guard": artifact(args.compact_trace_guard),
            "trace_identity_guard": artifact(args.trace_identity_guard),
            "trace_identity_archive": identity_archive,
            "trace_identity_reference": identity_reference,
            "instrumented_compact_binary": artifact(compact_trace_binary),
            "original_fx2_archive": original_archive,
            "geometry_fx2_archive": geometry_archive,
            "original_wrt_store": original_store,
            "minimal_base_trace": artifact(Path(confirmation_trace["path"])),
            "compact_probability_trace": artifact(external_trace),
            "compact_trace_archive": artifact(compact_trace_archive),
            "candidate_payload": artifact(candidate_payload),
        },
        "proof": {
            "frozen_weight_ppm": EXPECTED_WEIGHT_PPM,
            "opening_decoder_replay_ok": opening_replay["decoder_replay_ok"],
            "confirmation_decoder_replay_ok": confirmation_replay[
                "decoder_replay_ok"
            ],
            "same_wrt_truth_stream": True,
            "base_archive_identity": True,
            "base_probability_payload_identity": True,
            "trace_instrumentation_archive_identity": True,
            "compact_guards_clean": True,
            "holdout_block_regressions": confirmation_replay.get(
                "holdout_block_regressions"
            ),
            "largest_holdout_block_regression_bytes": confirmation_replay.get(
                "largest_holdout_block_regression_bytes"
            ),
            "total_holdout_block_regression_bytes": confirmation_replay.get(
                "total_holdout_block_regression_bytes"
            ),
            "regression_budget": {
                "max_regression_blocks": MAX_HOLDOUT_REGRESSION_BLOCKS,
                "max_largest_regression_bytes": (
                    MAX_LARGEST_HOLDOUT_REGRESSION_BYTES
                ),
                "max_total_regression_bytes": MAX_TOTAL_HOLDOUT_REGRESSION_BYTES,
                "passed": regression_budget_ok,
            },
        },
        "metrics": {
            "opening_full_saved_bytes_per_1m": opening_replay[
                "full_saved_bytes_per_1m_raw"
            ],
            "opening_holdout_saved_bytes_per_1m": opening_replay[
                "holdout_saved_bytes_per_proportional_1m_raw"
            ],
            "confirmation_full_saved_bytes": confirmation_replay["full_saved_bytes"],
            "confirmation_full_saved_bytes_per_1m": full_rate,
            "confirmation_holdout_saved_bytes": confirmation_replay[
                "holdout_saved_bytes"
            ],
            "confirmation_holdout_saved_bytes_per_1m": holdout_rate,
        },
        "economics": accounting,
        "decision": {
            "verdict": verdict,
            "clears_optimistic_compact_package_floor": clears_optimistic_floor,
            "holdout_clears_optimistic_compact_package_floor": (
                holdout_clears_optimistic_floor
            ),
            "combined_native_integration_authorized": integration_authorized,
            "larger_prize_gate_authorized": False,
            "promotion_authorized": False,
            "next_action": next_action,
        },
        "claim_boundary": (
            "This receipt measures a frozen blend of two separately evolved "
            "probability streams. The compact-only package size is an optimistic "
            "integration floor, not counted combined-program evidence. A 10.95 percent "
            "claim still requires one native decoder-replayable process, combined source "
            "and state accounting, roundtrip, determinism, runtime, and official 1G proof."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
