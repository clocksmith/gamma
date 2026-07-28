#!/usr/bin/env python3
"""Produce an archive-identical endpoint428 P1 trace and WRT store."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def run_to_logs(command: list[str], stdout_path: Path, stderr_path: Path) -> None:
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        subprocess.run(command, stdout=stdout, stderr=stderr, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wrapper", required=True, type=Path)
    parser.add_argument("--backend", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--raw-input", required=True, type=Path)
    parser.add_argument("--reference-archive", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--rss-guard",
        type=Path,
        default=Path(__file__).with_name("run_with_rss_guard.py"),
    )
    parser.add_argument("--limit-kib", type=int, default=10_485_760)
    parser.add_argument("--official-decimal-limit-kib", type=int, default=9_765_625)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required = (
        args.wrapper,
        args.backend,
        args.dictionary,
        args.raw_input,
        args.reference_archive,
        args.rss_guard,
    )
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing required artifact: {path}")
    if args.raw_input.stat().st_size != 10_000_000:
        raise SystemExit("raw input must be exactly 10,000,000 bytes")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=False)
    wrt_store = output_dir / "wrt_store.bin"
    trace = output_dir / "native.p1"
    archive = output_dir / "archive.bin"
    store_stdout = output_dir / "store_stdout.log"
    store_stderr = output_dir / "store_stderr.log"
    encode_stdout = output_dir / "encode_stdout.log"
    encode_stderr = output_dir / "encode_stderr.log"
    guard = output_dir / "encode_guard.json"
    decision_path = output_dir / "decision.json"

    run_to_logs(
        [
            str(args.backend),
            "-s",
            str(args.dictionary),
            str(args.raw_input),
            str(wrt_store),
        ],
        store_stdout,
        store_stderr,
    )

    shell_command = (
        'CMIX_P1_TRACE="$1" exec "$2" c "$3" "$4" >"$5" 2>"$6"'
    )
    guard_command = [
        sys.executable,
        str(args.rss_guard),
        "--limit-kib",
        str(args.limit_kib),
        "--limit-mode",
        "max_single",
        "--official-decimal-limit-kib",
        str(args.official_decimal_limit_kib),
        "--guard-json",
        str(guard),
        "--label",
        "endpoint428_pair_layer0_online_native_trace_10m_v1",
        "--",
        "bash",
        "-c",
        shell_command,
        "_",
        str(trace),
        str(args.wrapper),
        str(args.raw_input),
        str(archive),
        str(encode_stdout),
        str(encode_stderr),
    ]
    subprocess.run(guard_command, check=True)

    guard_data = json.loads(guard.read_text(encoding="utf-8"))
    archive_identity = (
        archive.stat().st_size == args.reference_archive.stat().st_size
        and sha256(archive) == sha256(args.reference_archive)
    )
    guard_clean = (
        guard_data.get("returncode") == 0
        and not guard_data.get("rss_guard_exceeded", False)
        and int(guard_data.get("official_decimal_over_limit_kib", 1)) == 0
    )
    trace_nonempty = trace.stat().st_size > 16
    store_nonempty = wrt_store.stat().st_size > 10
    passed = archive_identity and guard_clean and trace_nonempty and store_nonempty

    decision = {
        "schema": "gamma.endpoint428_p1_trace_gate.v1",
        "candidate": "janus_paid_residual_mdl_q0_v1",
        "purpose": "zero_credit_trace_infrastructure",
        "scope_raw_bytes": 10_000_000,
        "artifacts": {
            "raw_input": artifact(args.raw_input),
            "wrapper": artifact(args.wrapper),
            "backend": artifact(args.backend),
            "dictionary": artifact(args.dictionary),
            "reference_archive": artifact(args.reference_archive),
            "trace_archive": artifact(archive),
            "p1_trace": artifact(trace),
            "wrt_store": artifact(wrt_store),
            "memory_guard": artifact(guard),
        },
        "proof": {
            "archive_identity": archive_identity,
            "guard_clean": guard_clean,
            "trace_nonempty": trace_nonempty,
            "wrt_store_nonempty": store_nonempty,
            "passed": passed,
        },
        "decision": {
            "verdict": "AUTHORIZED_JANUS_10M" if passed else "INVALID_TRACE",
            "score_credit_bytes": 0,
            "native_integration_authorized": False,
            "larger_gate_authorized": False,
        },
    }
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
