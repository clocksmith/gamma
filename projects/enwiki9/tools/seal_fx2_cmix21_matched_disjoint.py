#!/usr/bin/env python3
"""Seal the frozen disjoint 96x2/full-CMIX matched endpoint decision."""

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
TARGET_SCORE_BYTES = 108_000_000
BASE_TAIL_GAIN_BYTES_PER_1M = 509.8
EXPECTED_WEIGHT_PPM = 625_000
ARCHIVE_MARKER_BYTES = 1
OPTION_BYTES = 3


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


def guarded_binary(guard: dict[str, Any]) -> Path:
    command = guard.get("command", [])
    if not isinstance(command, list) or not command:
        raise RuntimeError("guard does not preserve a command")
    index = 0
    if command[0] == "env":
        index = 1
        while index < len(command) and "=" in command[index]:
            index += 1
    if index >= len(command):
        raise RuntimeError("guard command does not contain an executable")
    path = Path(command[index])
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def economics(package_bytes: int, blend_rate: float) -> dict[str, int | float]:
    counted_program = package_bytes + OPTION_BYTES
    incremental_program = counted_program - BASELINE_PROGRAM_BYTES
    base_forecast = round(
        BASELINE_FORECAST_SCORE_BYTES
        - BASE_TAIL_GAIN_BYTES_PER_1M * 1000
        + incremental_program
        + ARCHIVE_MARKER_BYTES
    )
    debt = base_forecast - TARGET_SCORE_BYTES
    projected_blend_gain = round(blend_rate * 1000)
    score_before_integration = base_forecast - projected_blend_gain
    return {
        "source_package_bytes": package_bytes,
        "option_bytes": OPTION_BYTES,
        "counted_base_program_bytes": counted_program,
        "incremental_base_program_bytes": incremental_program,
        "base_tail_gain_bytes_per_1m": BASE_TAIL_GAIN_BYTES_PER_1M,
        "base_forecast_score_bytes": base_forecast,
        "base_forecast_debt_bytes": debt,
        "required_blend_gain_bytes_per_1m_before_integration": debt / 1000,
        "disjoint_blend_gain_bytes_per_1m": blend_rate,
        "linear_projected_blend_gain_bytes": projected_blend_gain,
        "linear_projected_score_before_integration_bytes": score_before_integration,
        "maximum_integration_bytes_at_target": TARGET_SCORE_BYTES
        - score_before_integration,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-receipt", type=Path, required=True)
    parser.add_argument("--opening-receipt", type=Path, required=True)
    parser.add_argument("--disjoint-screen", type=Path, required=True)
    parser.add_argument("--store-guard", type=Path, required=True)
    parser.add_argument("--base-guard", type=Path, required=True)
    parser.add_argument("--teacher-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    package = load_object(args.package_receipt)
    opening = load_object(args.opening_receipt)
    screen = load_object(args.disjoint_screen)
    guards = {
        "store": load_object(args.store_guard),
        "base": load_object(args.base_guard),
        "teacher": load_object(args.teacher_guard),
    }
    if package.get("schema") != "reproducible_source_shar_package_v1":
        raise RuntimeError("unexpected source-package receipt schema")
    if package.get("proof", {}).get("proof_complete") is not True:
        raise RuntimeError("source-package proof is incomplete")
    if opening.get("schema") != "fx2_cmix21_nested_endpoint_screen_v1":
        raise RuntimeError("unexpected opening matched-screen schema")
    selected = opening.get("selected", {})
    if (
        selected.get("kind") != "fixed_blend"
        or selected.get("weight_ppm") != EXPECTED_WEIGHT_PPM
        or opening.get("exact_cmix_replay", {}).get("decoder_replay_ok") is not True
    ):
        raise RuntimeError("opening receipt does not freeze the expected blend")
    if screen.get("schema") != "fx2_cmix21_nested_endpoint_screen_v1":
        raise RuntimeError("unexpected disjoint matched-screen schema")
    if screen.get("mode") != "frozen_confirmation":
        raise RuntimeError("disjoint screen was not frozen confirmation")
    disjoint_selected = screen.get("selected", {})
    if (
        disjoint_selected.get("kind") != "fixed_blend"
        or disjoint_selected.get("weight_ppm") != EXPECTED_WEIGHT_PPM
    ):
        raise RuntimeError("disjoint screen changed the frozen blend")
    if not all(clean_guard(guard) for guard in guards.values()):
        raise RuntimeError("one or more matched disjoint guards are not clean")
    trace = screen.get("trace", {})
    base = screen.get("base", {})
    replay = screen.get("exact_cmix_replay", {})
    if trace.get("wrt_truth_stream_identity") is not True:
        raise RuntimeError("disjoint WRT truth identity failed")
    if base.get("reference_archive_identity") is not True:
        raise RuntimeError("observation changed the base archive")
    if base.get("archive_payload_identity") is not True:
        raise RuntimeError("base probability replay changed the payload")
    if replay.get("decoder_replay_ok") is not True:
        raise RuntimeError("candidate decoder replay failed")

    package_bytes = package["artifacts"]["zip_a"]["bytes"]
    full_rate = float(replay["full_saved_bytes_per_1m_raw"])
    accounting = economics(package_bytes, full_rate)
    regression_free = replay.get("holdout_block_regressions") == 0
    clears_debt = accounting["maximum_integration_bytes_at_target"] > 0
    if clears_debt and regression_free:
        verdict = "disjoint_gross_pass_requires_counted_shared_state_integration"
        next_action = (
            "integrate the frozen fixed blend in one process, measure shared-state RSS, "
            "package the added source, and require exact native archive transfer"
        )
        integration_authorized = True
    else:
        verdict = "retire_fixed_full_cmix_blend_insufficient_disjoint_economics"
        next_action = (
            "preserve the matched receipts and construct a genuinely new WRT-native "
            "endpoint; do not optimize this selector or launch a larger unchanged gate"
        )
        integration_authorized = False

    trace_path = Path(trace["path"])
    store_path = Path(trace["wrt_store_path"])
    teacher_p1_path = Path(trace["external_endpoint_path"])
    base_archive_path = Path(base["archive_path"])
    candidate_payload_path = Path(replay["candidate_payload_path"])
    base_guard_command = guards["base"]["command"]
    teacher_guard_command = guards["teacher"]["command"]
    base_p1_path = Path(
        next(
            value.split("=", 1)[1]
            for value in base_guard_command
            if value.startswith("CMIX_P1_TRACE=")
        )
    )
    teacher_archive_path = Path(teacher_guard_command[-1])

    receipt = {
        "schema": "fx2_cmix21_matched_disjoint_terminal_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "frozen_same_store_offset500m_exact_shadow_replay",
        "artifacts": {
            "package_receipt": artifact(args.package_receipt),
            "opening_receipt": artifact(args.opening_receipt),
            "disjoint_screen": artifact(args.disjoint_screen),
            "store_guard": artifact(args.store_guard),
            "base_guard": artifact(args.base_guard),
            "teacher_guard": artifact(args.teacher_guard),
            "minimal_base_trace": artifact(trace_path),
            "wrt_store": artifact(store_path),
            "base_probability_trace": artifact(base_p1_path),
            "teacher_probability_trace": artifact(teacher_p1_path),
            "base_binary": artifact(guarded_binary(guards["base"])),
            "teacher_binary": artifact(guarded_binary(guards["teacher"])),
            "base_archive": artifact(base_archive_path),
            "teacher_archive": artifact(teacher_archive_path),
            "candidate_payload": artifact(candidate_payload_path),
        },
        "proof": {
            "frozen_weight_ppm": EXPECTED_WEIGHT_PPM,
            "same_wrt_truth_stream": True,
            "base_archive_identity": True,
            "base_probability_payload_identity": True,
            "candidate_decoder_replay_ok": True,
            "guards_clean": True,
            "holdout_block_regressions": replay.get("holdout_block_regressions"),
            "largest_holdout_block_regression_bytes": replay.get(
                "largest_holdout_block_regression_bytes"
            ),
        },
        "metrics": {
            "opening_full_saved_bytes_per_1m": opening["exact_cmix_replay"][
                "full_saved_bytes_per_1m_raw"
            ],
            "disjoint_full_saved_bytes": replay["full_saved_bytes"],
            "disjoint_full_saved_bytes_per_1m": full_rate,
            "disjoint_holdout_saved_bytes": replay["holdout_saved_bytes"],
            "disjoint_holdout_saved_bytes_per_1m": replay[
                "holdout_saved_bytes_per_proportional_1m_raw"
            ],
        },
        "economics": accounting,
        "decision": {
            "verdict": verdict,
            "native_shared_state_integration_authorized": integration_authorized,
            "larger_prize_gate_authorized": False,
            "promotion_authorized": False,
            "next_action": next_action,
        },
        "claim_boundary": (
            "This receipt is frozen disjoint exact-shadow and range-coder replay "
            "evidence. Native shared-state integration, complete added source cost, "
            "roundtrip, determinism, cumulative scaling, runtime, and official 1G "
            "accounting remain unproven."
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
