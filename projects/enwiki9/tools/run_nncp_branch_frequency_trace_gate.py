#!/usr/bin/env python3
"""Run an archive-neutral Compact5 NNCP branch-frequency trace gate."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import time

from materialize_nncp_branch_frequency_observer import materialize


CFLAGS = (
    "-O3 -Wall -Wpointer-arith -fno-math-errno -fno-trapping-math "
    "-MMD -Wno-format-truncation "
    '-DCONFIG_VERSION=\\"2024-06-05\\" -DLIBNC_CONFIG_FULL'
)
PROFILE_ARGUMENTS = [
    "--profile",
    "enwik9",
    "--batch_size",
    "1",
    "-T",
    "4",
    "--n_layer",
    "5",
    "--d_model",
    "256",
    "--d_inner",
    "768",
    "--preprocess",
    "16384,512",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def timed_run(
    command: list[str],
    environment: dict[str, str],
) -> float:
    start = time.monotonic()
    subprocess.run(
        command,
        check=True,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return time.monotonic() - start


def load_verifier(path: Path):
    spec = importlib.util.spec_from_file_location("branch_trace_verifier", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("could not load branch trace verifier")
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--limit", required=True, type=int)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    if args.limit <= 0:
        raise ValueError("limit must be positive")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_data = args.input.read_bytes()[: args.limit]
    if len(source_data) != args.limit:
        raise ValueError("input is shorter than requested limit")

    with tempfile.TemporaryDirectory(prefix="nncp-branch-gate-") as td:
        root = Path(td)
        with tarfile.open(args.source_package, "r:xz") as archive:
            archive.extractall(root)
        patch = root / "branch_trace.patch"
        materialize(root / "cp_utils.c", patch)
        build_start = time.monotonic()
        subprocess.run(
            ["make", "-C", str(root), "-j2", f"CFLAGS={CFLAGS}"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        build_seconds = time.monotonic() - build_start

        binary = root / "nncp"
        library = root / "libnc.so"
        source = root / "input"
        source.write_bytes(source_data)
        trace_off = args.output_dir / "trace_off.nncp"
        trace_on = args.output_dir / "trace_on.nncp"
        trace = args.output_dir / "branch_frequency_trace.bin"
        decoded = root / "decoded"

        environment = os.environ.copy()
        prior = environment.get("LD_LIBRARY_PATH")
        environment["LD_LIBRARY_PATH"] = (
            str(root) if not prior else f"{root}:{prior}"
        )
        command_prefix = [str(binary), *PROFILE_ARGUMENTS, "c", str(source)]
        off_environment = environment.copy()
        off_environment.pop("NNCP_BRANCH_TRACE", None)
        trace_off_seconds = timed_run(
            [*command_prefix, str(trace_off)], off_environment
        )
        on_environment = environment.copy()
        on_environment["NNCP_BRANCH_TRACE"] = str(trace)
        trace_on_seconds = timed_run(
            [*command_prefix, str(trace_on)], on_environment
        )

        off = trace_off.read_bytes()
        on = trace_on.read_bytes()
        if off != on:
            raise ValueError("trace-on and trace-off archives differ")
        decode_seconds = timed_run(
            [str(binary), "d", str(trace_on), str(decoded)], off_environment
        )
        decoded_data = decoded.read_bytes()
        if decoded_data != source_data:
            raise ValueError("instrumented NNCP roundtrip failed")

        verifier_path = Path(__file__).with_name(
            "verify_nncp_branch_frequency_trace.py"
        )
        verifier = load_verifier(verifier_path)
        raw_trace = trace.read_bytes()
        if len(raw_trace) < verifier.HEADER.size:
            raise ValueError("trace is truncated")
        magic, symbol_count, branch_count = verifier.HEADER.unpack_from(raw_trace)
        if magic != verifier.MAGIC:
            raise ValueError("trace magic mismatch")

        verification_receipt = args.output_dir / "trace_verification.json"
        subprocess.run(
            [
                "python3",
                str(verifier_path),
                "--trace",
                str(trace),
                "--receipt",
                str(verification_receipt),
                "--trace-on-archive",
                str(trace_on),
                "--trace-off-archive",
                str(trace_off),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )

        receipt = {
            "archive": {
                "bytes": len(on),
                "sha256": sha256(on),
                "trace_identity": True,
            },
            "binary": {
                "bytes": binary.stat().st_size,
                "sha256": sha256(binary.read_bytes()),
            },
            "branch_count": branch_count,
            "build_seconds": build_seconds,
            "claim_boundary": (
                "Archive-neutral bounded branch-frequency teacher trace only. "
                "No student, full score, or Hutter credit is established."
            ),
            "input": {
                "bytes": len(source_data),
                "sha256": sha256(source_data),
            },
            "library": {
                "bytes": library.stat().st_size,
                "sha256": sha256(library.read_bytes()),
            },
            "roundtrip_ok": True,
            "schema": "nncp_branch_frequency_trace_gate_v1",
            "score_credit_bytes": 0,
            "source_package": {
                "bytes": args.source_package.stat().st_size,
                "sha256": sha256(args.source_package.read_bytes()),
            },
            "symbol_count": symbol_count,
            "timing_seconds": {
                "decode": decode_seconds,
                "trace_off": trace_off_seconds,
                "trace_on": trace_on_seconds,
            },
            "trace": {
                "bytes": len(raw_trace),
                "sha256": sha256(raw_trace),
            },
            "verifier_receipt": str(verification_receipt),
        }
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
