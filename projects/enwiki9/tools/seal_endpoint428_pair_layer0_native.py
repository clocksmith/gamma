#!/usr/bin/env python3
"""Seal native endpoint428 pair/layer-0 proof and counted economics."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


TARGET_SCORE = 109_500_000
BASE_FORECAST_SCORE = 109_557_404
TEN_M_CALIBRATION_FACTOR = 66.955334
EXPECTED_PREFIX_GAIN = 67
EXPECTED_DISJOINT_GAIN = 89
WRAPPER_HEADER_BYTES = 37


def artifact(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def require_identical(left: Path, right: Path, label: str) -> None:
    if left.read_bytes() != right.read_bytes():
        raise ValueError(f"{label} identity failed")


def require_clean_guard(path: Path) -> dict[str, Any]:
    guard = load_object(path)
    if not (
        guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib") == 0
    ):
        raise ValueError(f"guard is not clean and terminal: {path}")
    return guard


def calculate_economics(
    *,
    base_program_bytes: int,
    candidate_program_bytes: int,
    prefix_gain_bytes: int,
) -> dict[str, Any]:
    program_delta = candidate_program_bytes - base_program_bytes
    forecast = BASE_FORECAST_SCORE - prefix_gain_bytes * 1000 + program_delta
    debt_with_code = BASE_FORECAST_SCORE - TARGET_SCORE + program_delta
    required_10m_gain = math.ceil(debt_with_code / TEN_M_CALIBRATION_FACTOR)
    return {
        "target_score_bytes": TARGET_SCORE,
        "base_forecast_score_bytes": BASE_FORECAST_SCORE,
        "base_forecast_debt_bytes": BASE_FORECAST_SCORE - TARGET_SCORE,
        "base_program_bytes": base_program_bytes,
        "candidate_program_bytes": candidate_program_bytes,
        "incremental_program_bytes": program_delta,
        "prefix_gain_bytes": prefix_gain_bytes,
        "prefix_gain_bytes_per_1m": float(prefix_gain_bytes),
        "provisional_prefix_forecast_score_bytes": forecast,
        "provisional_prefix_forecast_margin_bytes": TARGET_SCORE - forecast,
        "ten_m_calibration_factor": TEN_M_CALIBRATION_FACTOR,
        "required_exact_10m_gain_bytes": required_10m_gain,
        "maximum_exact_10m_archive_bytes": 1_635_695 - required_10m_gain,
    }


def add_disjoint_economics(
    economics: dict[str, Any], *, disjoint_gain_bytes: int
) -> None:
    forecast = (
        BASE_FORECAST_SCORE
        - disjoint_gain_bytes * 1000
        + int(economics["incremental_program_bytes"])
    )
    economics.update(
        {
            "disjoint_gain_bytes_per_1m": float(disjoint_gain_bytes),
            "provisional_disjoint_forecast_score_bytes": forecast,
            "provisional_disjoint_forecast_margin_bytes": TARGET_SCORE - forecast,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shadow-receipt", type=Path, required=True)
    parser.add_argument("--shadow-p1", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-second", type=Path, required=True)
    parser.add_argument("--p1", type=Path, required=True)
    parser.add_argument("--p1-second", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--restored", type=Path, required=True)
    parser.add_argument("--encode-guard", type=Path, required=True)
    parser.add_argument("--decode-guard", type=Path, required=True)
    parser.add_argument("--determinism-guard", type=Path, required=True)
    parser.add_argument("--base-package-a", type=Path, required=True)
    parser.add_argument("--base-package-b", type=Path, required=True)
    parser.add_argument("--candidate-package-a", type=Path, required=True)
    parser.add_argument("--candidate-package-b", type=Path, required=True)
    parser.add_argument("--clean-program-a", type=Path, required=True)
    parser.add_argument("--clean-program-b", type=Path, required=True)
    parser.add_argument("--disjoint-input", type=Path, required=True)
    parser.add_argument("--disjoint-base-archive", type=Path, required=True)
    parser.add_argument("--disjoint-candidate-archive", type=Path, required=True)
    parser.add_argument("--disjoint-base-guard", type=Path, required=True)
    parser.add_argument("--disjoint-candidate-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    shadow = load_object(args.shadow_receipt)
    if shadow.get("schema") != "compact_layer0_online_mixer_receipt_v1":
        raise ValueError("unexpected shadow receipt schema")
    if shadow.get("exact_replay", {}).get("full", {}).get("saved_bytes") != EXPECTED_PREFIX_GAIN:
        raise ValueError("shadow prefix gain changed")

    for left, right, label in (
        (args.archive, args.archive_second, "archive"),
        (args.p1, args.p1_second, "native P1"),
        (args.p1, args.shadow_p1, "native/shadow P1"),
        (args.input, args.restored, "roundtrip"),
        (args.base_package_a, args.base_package_b, "base source package"),
        (
            args.candidate_package_a,
            args.candidate_package_b,
            "candidate source package",
        ),
        (args.clean_program_a, args.clean_program_b, "clean program"),
    ):
        require_identical(left, right, label)

    guards = {
        "encode": require_clean_guard(args.encode_guard),
        "decode": require_clean_guard(args.decode_guard),
        "determinism": require_clean_guard(args.determinism_guard),
        "disjoint_base": require_clean_guard(args.disjoint_base_guard),
        "disjoint_candidate": require_clean_guard(args.disjoint_candidate_guard),
    }
    base_archive = artifact(args.base_archive)
    candidate_archive = artifact(args.archive)
    prefix_gain = base_archive["bytes"] - candidate_archive["bytes"]
    if prefix_gain != EXPECTED_PREFIX_GAIN:
        raise ValueError("native prefix archive gain changed")
    shadow_payload = shadow["exact_replay"]["candidate_payload_artifact"]
    if candidate_archive["bytes"] - WRAPPER_HEADER_BYTES != shadow_payload["bytes"]:
        raise ValueError("native archive payload size differs from shadow replay")

    disjoint_base = artifact(args.disjoint_base_archive)
    disjoint_candidate = artifact(args.disjoint_candidate_archive)
    disjoint_gain = disjoint_base["bytes"] - disjoint_candidate["bytes"]
    if disjoint_gain != EXPECTED_DISJOINT_GAIN:
        raise ValueError("disjoint archive gain changed")

    economics = calculate_economics(
        base_program_bytes=args.base_package_a.stat().st_size,
        candidate_program_bytes=args.candidate_package_a.stat().st_size,
        prefix_gain_bytes=prefix_gain,
    )
    add_disjoint_economics(economics, disjoint_gain_bytes=disjoint_gain)
    if economics["incremental_program_bytes"] < 0:
        raise ValueError("candidate program delta is unexpectedly negative")
    if economics["provisional_prefix_forecast_margin_bytes"] <= 0:
        raise ValueError("native prefix forecast is not target-closing")

    receipt = {
        "schema": "endpoint428_pair_layer0_native_receipt_v1",
        "evidence_level": "constructive_prefix_with_disjoint_archive_transfer",
        "claim_boundary": (
            "Exact native 1M archive, roundtrip, deterministic clean-build replay, "
            "counted source delta, and cold-reset offset-500M archive transfer. The "
            "score projection is provisional; exact 10M economics and full 1G proof "
            "remain required."
        ),
        "scope": {
            "prefix_bytes": args.input.stat().st_size,
            "disjoint_bytes": args.disjoint_input.stat().st_size,
            "disjoint_offset_bytes": 500_000_000,
        },
        "identity": {
            "roundtrip_ok": True,
            "determinism_ok": True,
            "native_shadow_p1_identity": True,
            "source_package_determinism": True,
            "clean_program_determinism": True,
        },
        "prefix": {
            "base_archive_bytes": base_archive["bytes"],
            "candidate_archive_bytes": candidate_archive["bytes"],
            "saved_bytes": prefix_gain,
        },
        "disjoint": {
            "base_archive_bytes": disjoint_base["bytes"],
            "candidate_archive_bytes": disjoint_candidate["bytes"],
            "saved_bytes": disjoint_gain,
            "saved_bytes_per_1m": float(disjoint_gain),
        },
        "economics": economics,
        "resources": {
            name: {
                "max_sampled_single_rss_kib": guard["max_sampled_single_rss_kib"],
                "max_sampled_tree_rss_kib": guard["max_sampled_tree_rss_kib"],
                "official_decimal_over_limit_kib": 0,
            }
            for name, guard in guards.items()
        },
        "artifacts": {
            "shadow_receipt": artifact(args.shadow_receipt),
            "shadow_p1": artifact(args.shadow_p1),
            "base_archive": base_archive,
            "archive": candidate_archive,
            "archive_second": artifact(args.archive_second),
            "p1": artifact(args.p1),
            "p1_second": artifact(args.p1_second),
            "input": artifact(args.input),
            "restored": artifact(args.restored),
            "base_package_a": artifact(args.base_package_a),
            "base_package_b": artifact(args.base_package_b),
            "candidate_package_a": artifact(args.candidate_package_a),
            "candidate_package_b": artifact(args.candidate_package_b),
            "clean_program_a": artifact(args.clean_program_a),
            "clean_program_b": artifact(args.clean_program_b),
            "disjoint_input": artifact(args.disjoint_input),
            "disjoint_base_archive": disjoint_base,
            "disjoint_candidate_archive": disjoint_candidate,
            "encode_guard": artifact(args.encode_guard),
            "decode_guard": artifact(args.decode_guard),
            "determinism_guard": artifact(args.determinism_guard),
            "disjoint_base_guard": artifact(args.disjoint_base_guard),
            "disjoint_candidate_guard": artifact(args.disjoint_candidate_guard),
        },
        "verdict": "promote_frozen_candidate_to_exact_10m_economics_gate",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
