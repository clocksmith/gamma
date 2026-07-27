#!/usr/bin/env python3
"""Run the exact ACS-PROVER XML-state endpoint calibration shadow."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CPP_SOURCE = Path(__file__).with_suffix(".cpp")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trace",
        type=Path,
        default=PROJECT_ROOT
        / "results/wrt_wiki_shell_v1/trace_1m_v1/residual_cache.tsv",
    )
    parser.add_argument(
        "--raw",
        type=Path,
        default=PROJECT_ROOT / "results/wrt_wiki_shell_v1/trace_1m_v1/input.raw",
    )
    parser.add_argument(
        "--wrt-stream",
        type=Path,
        default=PROJECT_ROOT
        / "results/wrt_wiki_shell_v1/trace_1m_v1/wrt_stream.bin",
    )
    parser.add_argument(
        "--baseline-archive",
        type=Path,
        default=PROJECT_ROOT
        / "results/wrt_wiki_shell_v1/trace_1m_v1/output.cmix",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT
        / "results/acs_prover_xml_state_endpoint_shadow_v1/receipt.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for path in (args.trace, args.raw, args.wrt_stream, args.baseline_archive):
        if not path.is_file():
            raise SystemExit(f"missing required input: {path}")

    expected_rows = args.wrt_stream.stat().st_size * 8
    with tempfile.TemporaryDirectory(prefix="acs-prover-shadow-") as directory:
        executable = Path(directory) / "shadow"
        subprocess.run(
            [
                "g++",
                "-O3",
                "-std=c++17",
                "-Wall",
                "-Wextra",
                "-pedantic",
                str(CPP_SOURCE),
                "-o",
                str(executable),
            ],
            check=True,
        )
        completed = subprocess.run(
            [
                str(executable),
                str(args.trace),
                str(args.raw),
                str(expected_rows),
            ],
            check=True,
            text=True,
            capture_output=True,
        )
    receipt = json.loads(completed.stdout)
    baseline_archive_bytes = args.baseline_archive.stat().st_size
    receipt["baseline_archive_bytes"] = baseline_archive_bytes
    receipt["baseline_matches_reference_archive"] = (
        receipt["all_baseline_bytes"] == baseline_archive_bytes
    )
    receipt["unmodeled_reference_artifact_delta_bytes"] = (
        baseline_archive_bytes - receipt["all_baseline_bytes"]
    )
    receipt["gate_valid"] = bool(
        receipt["rows"] == expected_rows
        and receipt["raw_bytes"] <= args.raw.stat().st_size
        and receipt["all_baseline_bytes"] > 0
    )
    receipt["score_credit_bytes"] = 0
    receipt["claim_boundary"] = (
        "Exact same-coder causal endpoint comparison on every logged decision. "
        "The native artifact delta is unmodeled, so this is not a constructive "
        "archive and receives no source-bound score credit."
    )
    receipt["inputs"] = {
        "trace": {
            "path": str(args.trace.relative_to(PROJECT_ROOT)),
            "bytes": args.trace.stat().st_size,
            "sha256": sha256(args.trace),
        },
        "raw": {
            "path": str(args.raw.relative_to(PROJECT_ROOT)),
            "bytes": args.raw.stat().st_size,
            "sha256": sha256(args.raw),
        },
        "wrt_stream": {
            "path": str(args.wrt_stream.relative_to(PROJECT_ROOT)),
            "bytes": args.wrt_stream.stat().st_size,
            "sha256": sha256(args.wrt_stream),
        },
        "baseline_archive": {
            "path": str(args.baseline_archive.relative_to(PROJECT_ROOT)),
            "bytes": baseline_archive_bytes,
            "sha256": sha256(args.baseline_archive),
        },
    }
    receipt["implementation"] = {
        "cpp_source": str(CPP_SOURCE.relative_to(PROJECT_ROOT)),
        "cpp_source_bytes": CPP_SOURCE.stat().st_size,
        "cpp_source_sha256": sha256(CPP_SOURCE),
        "wrapper": str(Path(__file__).resolve().relative_to(PROJECT_ROOT)),
        "wrapper_bytes": Path(__file__).stat().st_size,
        "wrapper_sha256": sha256(Path(__file__).resolve()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = {
        "decision": receipt["decision"],
        "gate_valid": receipt["gate_valid"],
        "holdout_incremental_state_saved_bytes": receipt[
            "holdout_incremental_state_saved_bytes"
        ],
        "holdout_saved_bytes": receipt["holdout_saved_bytes"],
        "holdout_saved_bytes_per_million": receipt[
            "holdout_saved_bytes_per_million"
        ],
        "output": str(args.output),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if receipt["gate_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
