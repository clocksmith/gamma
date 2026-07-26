#!/usr/bin/env python3
"""Seal source equivalence and package economics for the 200x2 frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASELINE_FORECAST_SCORE = 110_181_114
BASELINE_PROGRAM_BYTES = 183_008
TARGET_SCORE = 108_000_000
EXPECTED_1M_GAIN = 1_149


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
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


def package_economics(package_bytes: int) -> dict[str, int | float]:
    counted_program = package_bytes + 3
    incremental_program = counted_program - BASELINE_PROGRAM_BYTES
    projected_gross = EXPECTED_1M_GAIN * 1_000
    forecast = BASELINE_FORECAST_SCORE - projected_gross + incremental_program + 1
    required_gross = (
        BASELINE_FORECAST_SCORE - TARGET_SCORE + incremental_program + 1
    )
    return {
        "source_package_bytes": package_bytes,
        "option_bytes": 3,
        "counted_program_bytes": counted_program,
        "incremental_program_bytes": incremental_program,
        "first_1m_gross_saved_bytes": EXPECTED_1M_GAIN,
        "linear_projected_1g_gross_saved_bytes": projected_gross,
        "linear_projected_score_bytes": forecast,
        "linear_projected_target_margin_bytes": TARGET_SCORE - forecast,
        "required_gross_saved_bytes_at_1g": required_gross,
        "required_gross_saved_bytes_per_1m": required_gross / 1_000,
    }


def clean_guard(guard: dict[str, Any]) -> bool:
    return bool(
        guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib", 0) == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discovery-receipt", type=Path, required=True)
    parser.add_argument("--speed-250k-receipt", type=Path, required=True)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--source-archive-250k", type=Path, required=True)
    parser.add_argument("--source-guard-250k", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    for path in (
        args.discovery_receipt,
        args.speed_250k_receipt,
        args.source_package_receipt,
        args.source_archive_250k,
        args.source_guard_250k,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    discovery = load_object(args.discovery_receipt)
    speed = load_object(args.speed_250k_receipt)
    package = load_object(args.source_package_receipt)
    guard = load_object(args.source_guard_250k)
    if discovery.get("schema") != "fx2_cmix21_geometry_nopaq_constructive_v1":
        raise RuntimeError("unexpected 200x2 discovery schema")
    if discovery.get("candidate_1m", {}).get("gross_saved_bytes") != EXPECTED_1M_GAIN:
        raise RuntimeError("unexpected 200x2 first-1M gain")
    if speed.get("scope_raw_bytes") != 250_000 or speed.get("clean_guard") is not True:
        raise RuntimeError("speed reference is not a clean exact 250K screen")
    if package.get("schema") != "reproducible_source_shar_package_v1":
        raise RuntimeError("unexpected source package schema")
    if package.get("proof", {}).get("clean_build_complete") is not True:
        raise RuntimeError("source package clean-build proof is incomplete")
    if not clean_guard(guard):
        raise RuntimeError("source-equivalence guard is not clean")
    source_archive = artifact(args.source_archive_250k)
    reference_archive = speed["archive"]
    archive_identity = all(
        source_archive[key] == reference_archive[key] for key in ("bytes", "sha256")
    )
    package_binary = package["artifacts"]["clean_backend_a"]
    source_command = guard.get("command", [])
    if not source_command:
        raise RuntimeError("guard did not preserve the source command")
    source_binary = artifact(Path(source_command[0]))
    if any(source_binary[key] != package_binary[key] for key in ("bytes", "sha256")):
        raise RuntimeError("guarded source binary differs from the package build")

    economics = package_economics(package["artifacts"]["zip_a"]["bytes"])
    if archive_identity:
        verdict = "source_equivalence_passed_authorizes_reset_disjoint_screen"
        next_action = (
            "run the unchanged source-built 200x2 backend on the frozen offset-500M "
            "geometry reset slice and compare with the exact FX2 archive"
        )
    else:
        verdict = "source_equivalence_failed_requires_own_1m_screen"
        next_action = (
            "do not inherit the discovery gain; measure the source-built backend at 1M "
            "before any disjoint or forecast claim"
        )

    receipt = {
        "schema": "fx2_cmix21_lstm200_source_frontier_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "constructive_1m_discovery_plus_source_250k_equivalence_screen",
        "artifacts": {
            "discovery_receipt": artifact(args.discovery_receipt),
            "speed_250k_receipt": artifact(args.speed_250k_receipt),
            "source_package_receipt": artifact(args.source_package_receipt),
            "source_archive_250k": source_archive,
            "source_guard_250k": artifact(args.source_guard_250k),
            "source_binary": source_binary,
            "reference_archive_250k": reference_archive,
        },
        "proof": {
            "source_guard_clean": True,
            "source_package_clean_build_complete": True,
            "source_binary_matches_package": True,
            "source_archive_matches_discovery_backend_250k": archive_identity,
        },
        "economics": economics if archive_identity else None,
        "decision": {
            "verdict": verdict,
            "reset_disjoint_screen_authorized": archive_identity,
            "larger_prize_gate_authorized": False,
            "promotion_authorized": False,
            "next_action": next_action,
        },
        "claim_boundary": (
            "The linear score is a first-1M forecast and source equivalence is measured "
            "only through 250K. A frozen disjoint screen, cumulative scaling, exact wrapper "
            "replay, runtime, and full-corpus official accounting remain required."
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
