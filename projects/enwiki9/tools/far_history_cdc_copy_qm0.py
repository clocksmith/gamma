#!/usr/bin/env python3
"""Build, repeat, and seal the full-1G far-history CDC copy ceiling."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "far_history_cdc_copy_qm0_v1"


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/enwik9")
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    source = ROOT / "tools/far_history_cdc_copy_qm0.cpp"
    binary = args.output_dir / "far_history_cdc_copy_qm0"
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
    for suffix in ("a", "b"):
        completed = subprocess.run(
            [str(binary), str(args.input)],
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

    deterministic = scans[0] == scans[1]
    scan = scans[0]
    source_paths = [
        Path(__file__),
        source,
        ROOT / "docs/far_history_cdc_copy_qm0_plan.md",
        ROOT / "programs/far_history_cdc_copy_qm0_v1/meta.json",
    ]
    source_blob = b"".join(path.name.encode("utf-8") + b"\0" + path.read_bytes() for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    package_path = args.output_dir / "source_package.lzma"
    package_path.write_bytes(source_package)

    net = float(scan["average_rate_equivalent_net_before_source"]) - len(source_package)
    copied = int(scan["copied_bytes"])
    split_copied = [int(value) for value in scan["split_copied_bytes"]]
    failed: list[str] = []
    if copied < 100_000_000:
        failed.append("copied_bytes_below_100000000")
    if net < 8_800_000:
        failed.append("average_rate_equivalent_net_below_8800000")
    if any(value <= 0 for value in split_copied):
        failed.append("corpus_third_without_selected_copy")
    if not deterministic:
        failed.append("repeat_scan_summary_mismatch")
    if not bool(scan["selected_sources_strictly_prior"]):
        failed.append("selected_source_not_strictly_prior")
    if not bool(scan["selected_sources_fully_closed"]):
        failed.append("selected_source_not_fully_closed")
    if not bool(scan["selected_anchors_exactly_verified"]):
        failed.append("selected_anchor_not_exactly_verified")

    decision = {
        "schema": "enwiki9_far_history_cdc_copy_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "full_corpus_representation_ceiling_zero_credit",
        "verdict": "authorize_paid_far_history_copy_stream" if not failed else "retire_far_history_cdc_copy",
        "inputs": {
            "input": artifact(args.input),
            "scanner_source": artifact(source),
            "scanner_binary": artifact(binary),
        },
        "scan": scan,
        "accounting": {
            "compressed_source_package_bytes": len(source_package),
            "average_rate_equivalent_net_after_source_bytes": net,
            "current_forecast_score_bytes": 109_389_323,
            "current_target_bytes": 105_000_000,
            "current_debt_bytes": 4_389_323,
            "score_credit_bytes": 0,
        },
        "proof": {
            "two_independent_hashes_per_anchor": True,
            "exact_memcmp_before_extension": True,
            "deterministic_repeat_summary": deterministic,
            "prior_source_only": bool(scan["selected_sources_strictly_prior"]),
            "fully_closed_sources": bool(scan["selected_sources_fully_closed"]),
            "all_selected_anchors_exact": bool(scan["selected_anchors_exactly_verified"]),
        },
        "artifacts": {
            "scan_a": artifact(args.output_dir / "scan_a.json"),
            "scan_b": artifact(args.output_dir / "scan_b.json"),
            "source_package": artifact(package_path),
        },
        "failed_conditions": failed,
        "claim_boundary": "Full-corpus raw-copy representation ceiling only. Average-rate-equivalent accounting is a target-bearing proxy, not an Endpoint428 P1 replay, native archive, source-bound forecast, official score, or runtime result.",
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

