#!/usr/bin/env python3
"""Seal matched prefix identity and runtime evidence for a backend optimization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REFERENCE_TAIL_FORECAST_SCORE = 109_498_879
TARGET_SCORE = 109_500_000


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


def verify_screen(receipt: dict[str, Any], expected_scope: int) -> None:
    if receipt.get("schema") != "fx2_cmix21_backend_identity_runtime_screen_v1":
        raise RuntimeError("unexpected backend screen schema")
    if receipt.get("scope_bytes") != expected_scope:
        raise RuntimeError(f"backend screen is not exact {expected_scope} bytes")
    metrics = receipt.get("metrics", {})
    if metrics.get("all_guards_clean") is not True:
        raise RuntimeError("backend screen has a failed guard")
    if metrics.get("archive_identity") is not True:
        raise RuntimeError("backend screen did not preserve the archive")
    if len(receipt.get("runs", [])) != 4:
        raise RuntimeError("backend screen does not contain four alternating runs")
    for run in receipt["runs"]:
        for key in ("archive", "guard"):
            observed = artifact(Path(run[key]["path"]))
            if any(observed[field] != run[key][field] for field in ("bytes", "sha256")):
                raise RuntimeError(f"backend screen artifact changed: {run[key]['path']}")


def package_metrics(
    *, reference_package_bytes: int, candidate_package_bytes: int
) -> dict[str, int]:
    delta = candidate_package_bytes - reference_package_bytes
    forecast = REFERENCE_TAIL_FORECAST_SCORE + delta
    return {
        "reference_source_package_bytes": reference_package_bytes,
        "candidate_source_package_bytes": candidate_package_bytes,
        "candidate_source_package_delta_bytes": delta,
        "candidate_tail_forecast_score_bytes": forecast,
        "candidate_tail_forecast_margin_bytes": TARGET_SCORE - forecast,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity-receipt", type=Path, required=True)
    parser.add_argument("--runtime-receipt", type=Path, required=True)
    parser.add_argument("--reference-source", type=Path, required=True)
    parser.add_argument("--candidate-source", type=Path, required=True)
    parser.add_argument("--reference-package-receipt", type=Path, required=True)
    parser.add_argument("--candidate-package-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    for path in (
        args.identity_receipt,
        args.runtime_receipt,
        args.reference_source,
        args.candidate_source,
        args.reference_package_receipt,
        args.candidate_package_receipt,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    identity = load_object(args.identity_receipt)
    runtime = load_object(args.runtime_receipt)
    verify_screen(identity, 1_000)
    verify_screen(runtime, 250_000)
    for key in ("reference_binary", "candidate_binary", "dictionary"):
        if identity["artifacts"][key]["sha256"] != runtime["artifacts"][key]["sha256"]:
            raise RuntimeError(f"identity and runtime screens differ at {key}")
    reduction = runtime["metrics"]["candidate_runtime_reduction_fraction"]
    if reduction <= 0:
        raise RuntimeError("candidate has no matched median runtime reduction")
    if args.reference_source.read_bytes() == args.candidate_source.read_bytes():
        raise RuntimeError("candidate source is unchanged")
    reference_package = load_object(args.reference_package_receipt)
    candidate_package = load_object(args.candidate_package_receipt)
    for name, package in (
        ("reference", reference_package),
        ("candidate", candidate_package),
    ):
        if package.get("schema") != "reproducible_source_shar_package_v1":
            raise RuntimeError(f"unexpected {name} package receipt schema")
        if package.get("proof", {}).get("proof_complete") is not True:
            raise RuntimeError(f"{name} source reconstruction did not pass")
        if package.get("proof", {}).get("clean_build_complete") is not True:
            raise RuntimeError(f"{name} clean-build proof did not pass")
        require_binary = package["artifacts"]["clean_backend_a"]
        expected_binary = runtime["artifacts"][f"{name}_binary"]
        if any(require_binary[key] != expected_binary[key] for key in ("bytes", "sha256")):
            raise RuntimeError(f"{name} package builds a different backend")
    packages = package_metrics(
        reference_package_bytes=reference_package["artifacts"]["zip_a"]["bytes"],
        candidate_package_bytes=candidate_package["artifacts"]["zip_a"]["bytes"],
    )

    receipt = {
        "schema": "fx2_cmix21_backend_identity_runtime_terminal_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "matched_guarded_1k_and_250k_archive_identity_runtime_screen",
        "mechanism": (
            "compute Adam learning-rate and bias-correction scalars once per recurrent "
            "gate update and reuse them for every row, gamma, and beta update"
        ),
        "artifacts": {
            "identity_receipt": artifact(args.identity_receipt),
            "runtime_receipt": artifact(args.runtime_receipt),
            "reference_source": artifact(args.reference_source),
            "candidate_source": artifact(args.candidate_source),
            "reference_package_receipt": artifact(args.reference_package_receipt),
            "candidate_package_receipt": artifact(args.candidate_package_receipt),
            "reference_binary": runtime["artifacts"]["reference_binary"],
            "candidate_binary": runtime["artifacts"]["candidate_binary"],
        },
        "proof": {
            "identity_1k": True,
            "identity_250k": True,
            "alternating_runs_per_scope": 4,
            "all_guards_clean": True,
            "candidate_source_differs": True,
        },
        "metrics": {
            "reference_median_elapsed_s_250k": runtime["metrics"][
                "reference_median_elapsed_s"
            ],
            "candidate_median_elapsed_s_250k": runtime["metrics"][
                "candidate_median_elapsed_s"
            ],
            "candidate_over_reference_runtime_ratio_250k": runtime["metrics"][
                "candidate_over_reference_runtime_ratio"
            ],
            "candidate_runtime_reduction_fraction_250k": reduction,
            "archive_bytes_250k": runtime["metrics"]["archive_size_values"][0],
            "max_sampled_single_rss_kib": max(
                run["guard_result"]["max_sampled_single_rss_kib"]
                for run in runtime["runs"]
            ),
            **packages,
        },
        "decision": {
            "verdict": "accept_bit_identical_runtime_optimization_for_descendants",
            "source_package_cost_required": False,
            "promotion_authorized": False,
            "larger_prize_gate_authorized": False,
            "unchanged_112_plus80_remains_retired": True,
            "next_action": (
                "reuse the measured optimization only when a new compression mechanism "
                "independently earns a larger gate"
            ),
        },
        "claim_boundary": (
            "The optimization preserves the measured 1K and 250K archives and reduces "
            "matched median runtime at 250K. Its source package adds 65 bytes and moves "
            "the same tail forecast to 109498944, but it does not save compressed bytes, "
            "establish full-corpus runtime, or authorize the retired codec for promotion."
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
