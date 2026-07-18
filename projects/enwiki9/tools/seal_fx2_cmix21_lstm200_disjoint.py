#!/usr/bin/env python3
"""Seal the offset-500M reset-slice decision for the source-built 200x2 codec."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_SCOPE_BYTES = 1_000_000


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


def summarize(
    *, baseline_archive_bytes: int, candidate_archive_bytes: int, required_rate: float
) -> dict[str, int | float | bool]:
    gain = baseline_archive_bytes - candidate_archive_bytes
    return {
        "baseline_archive_bytes": baseline_archive_bytes,
        "candidate_archive_bytes": candidate_archive_bytes,
        "gross_saved_bytes": gain,
        "gross_saved_bytes_per_1m": float(gain),
        "required_gross_saved_bytes_per_1m": required_rate,
        "margin_over_required_rate_bytes_per_1m": gain - required_rate,
        "clears_required_rate": gain >= required_rate,
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
    parser.add_argument("--frontier-receipt", type=Path, required=True)
    parser.add_argument("--baseline-receipt", type=Path, required=True)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    parser.add_argument("--candidate-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    for path in (
        args.frontier_receipt,
        args.baseline_receipt,
        args.candidate_archive,
        args.candidate_guard,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    frontier = load_object(args.frontier_receipt)
    baseline = load_object(args.baseline_receipt)
    guard = load_object(args.candidate_guard)
    if frontier.get("schema") != "fx2_cmix21_lstm200_source_frontier_v1":
        raise RuntimeError("unexpected 200x2 frontier schema")
    if frontier.get("decision", {}).get("reset_disjoint_screen_authorized") is not True:
        raise RuntimeError("frontier did not authorize the reset disjoint screen")
    if baseline.get("scope_raw_bytes") != EXPECTED_SCOPE_BYTES:
        raise RuntimeError("baseline receipt is not exact 1M")
    if baseline.get("input", {}).get("bytes") != EXPECTED_SCOPE_BYTES:
        raise RuntimeError("baseline input is not exact 1M")
    observed_input = artifact(Path(baseline["input"]["path"]))
    if any(observed_input[key] != baseline["input"][key] for key in ("bytes", "sha256")):
        raise RuntimeError("frozen disjoint input changed")
    if not clean_guard(guard):
        raise RuntimeError("candidate disjoint guard is not clean")
    command = guard.get("command", [])
    if len(command) < 5:
        raise RuntimeError("candidate guard did not preserve the codec command")
    guarded_binary = artifact(Path(command[0]))
    if any(
        guarded_binary[key] != frontier["artifacts"]["source_binary"][key]
        for key in ("bytes", "sha256")
    ):
        raise RuntimeError("disjoint run used a different source backend")
    guarded_input = artifact(Path(command[-2]))
    if any(guarded_input[key] != observed_input[key] for key in ("bytes", "sha256")):
        raise RuntimeError("disjoint run used a different input")

    required_rate = frontier["economics"]["required_gross_saved_bytes_per_1m"]
    metrics = summarize(
        baseline_archive_bytes=baseline["baseline"]["artifact"]["bytes"],
        candidate_archive_bytes=args.candidate_archive.stat().st_size,
        required_rate=required_rate,
    )
    if metrics["clears_required_rate"]:
        verdict = "disjoint_target_rate_pass_requires_replay_and_cumulative_gate"
        next_action = (
            "run exact source-wrapper roundtrip and determinism on this slice, then require "
            "a cumulative geometry-title gate before any full-corpus promotion"
        )
        replay_authorized = True
    else:
        verdict = "retire_lstm200_prefix_gain_not_disjoint_target_rate"
        next_action = (
            "preserve the capacity receipt; do not decode or run a larger unchanged 200x2 "
            "gate, and return to a genuinely new causal endpoint"
        )
        replay_authorized = False

    receipt = {
        "schema": "fx2_cmix21_lstm200_disjoint_terminal_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "exact_guarded_offset500m_reset_1m_archive_screen",
        "artifacts": {
            "frontier_receipt": artifact(args.frontier_receipt),
            "baseline_receipt": artifact(args.baseline_receipt),
            "candidate_archive": artifact(args.candidate_archive),
            "candidate_guard": artifact(args.candidate_guard),
            "input": observed_input,
            "binary": guarded_binary,
            "baseline_archive": baseline["baseline"]["artifact"],
        },
        "metrics": {
            "first_1m_gross_saved_bytes": frontier["economics"][
                "first_1m_gross_saved_bytes"
            ],
            **metrics,
        },
        "proof": {
            "guard_clean": True,
            "input_matches_frozen_reset_slice": True,
            "binary_matches_source_package_frontier": True,
            "roundtrip_ok": None,
            "determinism_ok": None,
        },
        "decision": {
            "verdict": verdict,
            "replay_authorized": replay_authorized,
            "larger_prize_gate_authorized": False,
            "promotion_authorized": False,
            "next_action": next_action,
        },
        "claim_boundary": (
            "This is a reset-slice archive screen, not continuous full-corpus scaling. "
            "A positive result would still require wrapper replay, cumulative evidence, "
            "runtime qualification, and full official accounting."
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
