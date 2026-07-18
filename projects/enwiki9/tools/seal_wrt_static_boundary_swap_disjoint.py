#!/usr/bin/env python3
"""Seal an untouched reset-slice WRT boundary-swap archive comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib


EXPECTED_SCOPE_BYTES = 1_000_000


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: pathlib.Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def clean_guard(receipt: dict[str, object]) -> bool:
    return bool(
        receipt.get("status") == "complete"
        and receipt.get("returncode") == 0
        and receipt.get("rss_guard_exceeded") is False
        and receipt.get("official_decimal_over_limit_kib", 0) == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-receipt", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-archive", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-guard", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-dictionary", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    baseline = json.loads(args.baseline_receipt.read_text())
    guard = json.loads(args.candidate_guard.read_text())
    if baseline.get("scope_raw_bytes") != EXPECTED_SCOPE_BYTES:
        raise ValueError("baseline is not exact 1M")
    if baseline.get("clean_guard") is not True:
        raise ValueError("baseline guard is not clean")
    baseline_archive = pathlib.Path(baseline["archive"]["path"])
    baseline_input = pathlib.Path(baseline["input"]["path"])
    baseline_binary = pathlib.Path(baseline["binary"]["path"])
    for entry, path in (
        (baseline["archive"], baseline_archive),
        (baseline["input"], baseline_input),
        (baseline["binary"], baseline_binary),
    ):
        observed = artifact(path)
        if observed["bytes"] != entry["bytes"] or observed["sha256"] != entry["sha256"]:
            raise ValueError(f"baseline artifact drift: {path}")
    command = guard.get("command")
    if not isinstance(command, list) or len(command) < 5:
        raise ValueError("candidate guard lacks the codec command")
    if pathlib.Path(command[0]).resolve() != baseline_binary.resolve():
        raise ValueError("candidate and baseline binaries differ")
    if pathlib.Path(command[-2]).resolve() != baseline_input.resolve():
        raise ValueError("candidate and baseline inputs differ")
    if pathlib.Path(command[-3]).resolve() != args.candidate_dictionary.resolve():
        raise ValueError("candidate guard dictionary differs")
    if pathlib.Path(command[-1]).resolve() != args.candidate_archive.resolve():
        raise ValueError("candidate guard archive differs")

    guard_clean = clean_guard(guard)
    archive_saved = baseline_archive.stat().st_size - args.candidate_archive.stat().st_size
    receipt = {
        "schema": "wrt_static_boundary_swap_disjoint_v1",
        "evidence_level": "exact_guarded_reset_disjoint_1m_archive_screen",
        "scope_raw_bytes": EXPECTED_SCOPE_BYTES,
        "artifacts": {
            "baseline_receipt": artifact(args.baseline_receipt),
            "baseline_archive": artifact(baseline_archive),
            "candidate_archive": artifact(args.candidate_archive),
            "candidate_guard": artifact(args.candidate_guard),
            "input": artifact(baseline_input),
            "binary": artifact(baseline_binary),
            "candidate_dictionary": artifact(args.candidate_dictionary),
        },
        "metrics": {
            "baseline_archive_bytes": baseline_archive.stat().st_size,
            "candidate_archive_bytes": args.candidate_archive.stat().st_size,
            "archive_saved_bytes": archive_saved,
            "archive_saved_bytes_per_1m": float(archive_saved),
        },
        "proof": {
            "candidate_guard_clean": guard_clean,
            "matched_binary": True,
            "matched_input": True,
            "frozen_dictionary": True,
        },
        "decision": {
            "verdict": (
                "disjoint_static_boundary_swap_nonnegative"
                if guard_clean and archive_saved >= 0
                else "disjoint_static_boundary_swap_regressed"
            ),
            "supports_generalization": guard_clean and archive_saved >= 0,
            "promotion_authorized": False,
            "larger_gate_authorized": False,
        },
        "claim_boundary": (
            "This receipt measures only an exact reset 1M archive delta against the "
            "matched 112+80 endpoint. It does not prove cumulative-state scaling, "
            "roundtrip, determinism, runtime eligibility, or a full-corpus score."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if guard_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
