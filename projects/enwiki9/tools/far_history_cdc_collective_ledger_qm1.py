#!/usr/bin/env python3
"""Measure the collective entropy of QM0's full-1G far-history copy ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import struct
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "far_history_cdc_collective_ledger_qm1_v1"


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def count_ulebs(payload: bytes) -> int:
    count = 0
    for byte in payload:
        if byte & 128 == 0:
            count += 1
    return count


def validate_ledger(payload: bytes) -> dict[str, int | bool]:
    if len(payload) < 40 or payload[:8] != b"FHCLQ1\0\0":
        raise ValueError("bad ledger header")
    records, gap_size, distance_size, length_size = struct.unpack_from("<QQQQ", payload, 8)
    if 40 + gap_size + distance_size + length_size != len(payload):
        raise ValueError("ledger component lengths do not cover payload")
    gap_end = 40 + gap_size
    distance_end = gap_end + distance_size
    counts = (
        count_ulebs(payload[40:gap_end]),
        count_ulebs(payload[gap_end:distance_end]),
        count_ulebs(payload[distance_end:]),
    )
    return {
        "records": records,
        "gap_stream_bytes": gap_size,
        "distance_stream_bytes": distance_size,
        "length_stream_bytes": length_size,
        "component_record_counts_equal_header": counts == (records, records, records),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/enwik9")
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    source = ROOT / "tools/far_history_cdc_collective_ledger_qm1.cpp"
    binary = args.output_dir / "far_history_cdc_collective_ledger_qm1"
    build = subprocess.run(
        ["g++", "-O3", "-DNDEBUG", "-std=c++17", str(source), "-o", str(binary)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    (args.output_dir / "build.log").write_text(build.stdout)
    if build.returncode:
        raise RuntimeError(f"scanner build failed with status {build.returncode}")

    scans: list[dict[str, object]] = []
    ledger_paths: list[Path] = []
    for suffix in ("a", "b"):
        ledger_path = args.output_dir / f"ledger_{suffix}.bin"
        completed = subprocess.run(
            [str(binary), str(args.input), str(ledger_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        (args.output_dir / f"scan_{suffix}.stderr.log").write_text(completed.stderr)
        (args.output_dir / f"scan_{suffix}.json").write_text(completed.stdout)
        if completed.returncode:
            raise RuntimeError(f"scanner {suffix} failed with status {completed.returncode}")
        scans.append(json.loads(completed.stdout))
        ledger_paths.append(ledger_path)

    ledgers = [path.read_bytes() for path in ledger_paths]
    validations = [validate_ledger(payload) for payload in ledgers]
    scan_deterministic = scans[0] == scans[1]
    ledger_deterministic = ledgers[0] == ledgers[1]
    validation_deterministic = validations[0] == validations[1]
    ledger_compressed = lzma.compress(ledgers[0], preset=9 | lzma.PRESET_EXTREME)
    ledger_repeat_compressed = lzma.compress(ledgers[1], preset=9 | lzma.PRESET_EXTREME)
    compressed_path = args.output_dir / "ledger.lzma"
    compressed_path.write_bytes(ledger_compressed)

    source_paths = [
        Path(__file__),
        source,
        ROOT / "docs/far_history_cdc_collective_ledger_qm1_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    ]
    source_blob = b"".join(path.name.encode() + b"\0" + path.read_bytes() for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    package_path = args.output_dir / "source_package.lzma"
    package_path.write_bytes(source_package)

    scan = scans[0]
    gross = float(scan["average_rate_equivalent_gross_bytes"])
    net = gross - len(ledger_compressed) - len(source_package)
    split_copied = [int(value) for value in scan["split_copied_bytes"]]
    failed: list[str] = []
    if net < 5_000_000:
        failed.append("average_rate_equivalent_net_below_5000000")
    if any(value <= 0 for value in split_copied):
        failed.append("corpus_third_without_selected_copy")
    if not scan_deterministic:
        failed.append("repeat_scan_summary_mismatch")
    if not ledger_deterministic:
        failed.append("repeat_ledger_mismatch")
    if ledger_compressed != ledger_repeat_compressed:
        failed.append("repeat_compressed_ledger_mismatch")
    if not validation_deterministic or not bool(validations[0]["component_record_counts_equal_header"]):
        failed.append("ledger_parse_validation_failed")
    for field in (
        "selected_sources_strictly_prior",
        "selected_sources_fully_closed",
        "selected_anchors_exactly_verified",
    ):
        if not bool(scan[field]):
            failed.append(f"proof_failed_{field}")

    decision = {
        "schema": "enwiki9_far_history_cdc_collective_ledger_qm1_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "full_corpus_representation_ceiling_zero_credit",
        "verdict": "authorize_paid_residual_integration" if not failed else "retire_collective_far_history_ledger",
        "inputs": {
            "input": artifact(args.input),
            "scanner_source": artifact(source),
            "scanner_binary": artifact(binary),
            "parent_decision": artifact(ROOT / "results/far_history_cdc_copy_qm0_v1/decision.json"),
        },
        "scan": scan,
        "ledger": {
            **validations[0],
            "raw_bytes": len(ledgers[0]),
            "compressed_bytes": len(ledger_compressed),
            "compression_ratio": len(ledger_compressed) / len(ledgers[0]),
        },
        "accounting": {
            "average_rate_equivalent_gross_bytes": gross,
            "compressed_ledger_bytes": len(ledger_compressed),
            "compressed_source_package_bytes": len(source_package),
            "average_rate_equivalent_net_after_ledger_and_source_bytes": net,
            "current_forecast_score_bytes": 109_389_323,
            "current_target_bytes": 105_000_000,
            "current_debt_bytes": 4_389_323,
            "promotion_floor_bytes": 5_000_000,
            "score_credit_bytes": 0,
        },
        "proof": {
            "scan_summary_deterministic": scan_deterministic,
            "raw_ledger_deterministic": ledger_deterministic,
            "compressed_ledger_deterministic": ledger_compressed == ledger_repeat_compressed,
            "ledger_parse_valid": bool(validations[0]["component_record_counts_equal_header"]),
            "prior_source_only": bool(scan["selected_sources_strictly_prior"]),
            "fully_closed_sources": bool(scan["selected_sources_fully_closed"]),
            "all_selected_anchors_exact": bool(scan["selected_anchors_exactly_verified"]),
        },
        "artifacts": {
            "ledger_raw": artifact(ledger_paths[0]),
            "ledger_compressed": artifact(compressed_path),
            "source_package": artifact(package_path),
        },
        "failed_conditions": failed,
        "claim_boundary": "Full-corpus collective-ledger entropy gate only. It charges exact target gaps, distances, and lengths, but residual payload savings use the current archive-average proxy. It is not an Endpoint428 replay, native codec, source-bound forecast, official score, or runtime result.",
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
