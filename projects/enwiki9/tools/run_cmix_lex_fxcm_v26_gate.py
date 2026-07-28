#!/usr/bin/env python3
"""Run the bounded public cmix-lex predictor transfer gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


PINNED_COMMIT = "370e698f7ea62168cc64326ff97950c3dc212691"
GAMMA_PARENT_ARCHIVE_BYTES = 45_178
PROMOTION_CEILING_BYTES = 44_678
GUARD_KIB = 10_485_760
OFFICIAL_DECIMAL_LIMIT_KIB = 9_765_625
LOCAL_CLANG_ROOT = Path(
    "/home/x/enwiki9-nonproof/toolchains/clang17/root"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def write_prefix(source: Path, destination: Path, limit: int) -> None:
    remaining = limit
    with source.open("rb") as src, destination.open("wb") as dst:
        while remaining:
            chunk = src.read(min(1 << 20, remaining))
            if not chunk:
                raise EOFError(f"input ended before {limit} bytes")
            dst.write(chunk)
            remaining -= len(chunk)


def run_guarded(
    guard_tool: Path,
    command: list[str],
    guard_path: Path,
    log_path: Path,
    label: str,
) -> float:
    started = time.monotonic()
    with log_path.open("wb") as log:
        subprocess.run(
            [
                "python3",
                str(guard_tool),
                "--limit-kib",
                str(GUARD_KIB),
                "--limit-mode",
                "max_single",
                "--official-decimal-limit-kib",
                str(OFFICIAL_DECIMAL_LIMIT_KIB),
                "--sample-interval",
                "1",
                "--guard-json",
                str(guard_path),
                "--label",
                label,
                "--",
                *command,
            ],
            check=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    return time.monotonic() - started


def write_decision(path: Path, decision: dict) -> None:
    path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=250_000)
    parser.add_argument("--result-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.limit != 250_000:
        raise ValueError("the frozen gate requires exactly 250000 raw bytes")

    project = Path(__file__).resolve().parents[1]
    guard_tool = project / "tools" / "run_with_rss_guard.py"
    args.result_dir.mkdir(parents=True, exist_ok=True)

    source_commit = subprocess.check_output(
        ["git", "-C", str(args.source), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if source_commit != PINNED_COMMIT:
        raise ValueError(
            f"cmix-lex source commit {source_commit} != {PINNED_COMMIT}"
        )

    prefix = args.result_dir / "input.raw"
    archive1 = args.result_dir / "archive.first.bin"
    archive2 = args.result_dir / "archive.second.bin"
    decoded = args.result_dir / "decoded.raw"
    write_prefix(args.input, prefix, args.limit)

    with tempfile.TemporaryDirectory(prefix="cmix-lex-v26-gate-") as td:
        build = Path(td) / "cmix-lex"
        shutil.copytree(
            args.source,
            build,
            ignore=shutil.ignore_patterns(".git", "run", "pgo_data", "*.o", "cmix"),
        )
        build_started = time.monotonic()
        local_compiler = LOCAL_CLANG_ROOT / "usr/lib/llvm-17/bin/clang++"
        compiler = (
            shutil.which("clang++-17")
            or (
                str(local_compiler)
                if local_compiler.is_file()
                else None
            )
            or shutil.which("clang++")
        )
        if compiler is None:
            raise FileNotFoundError("clang++-17 or clang++ is required")
        build_env = os.environ.copy()
        local_library = (
            LOCAL_CLANG_ROOT / "usr/lib/x86_64-linux-gnu"
        )
        if compiler == str(local_compiler):
            prior = build_env.get("LD_LIBRARY_PATH")
            build_env["LD_LIBRARY_PATH"] = (
                str(local_library)
                if not prior
                else f"{local_library}:{prior}"
            )
        subprocess.run(
            [
                "make",
                "-C",
                str(build),
                "-j2",
                f"CC={compiler}",
                "LFLAGS=-m64 -Wl,--gc-sections -std=c++17",
                "cmix",
            ],
            check=True,
            stdout=(args.result_dir / "build.log").open("wb"),
            stderr=subprocess.STDOUT,
            env=build_env,
        )
        build_seconds = time.monotonic() - build_started
        binary = build / "cmix"
        dictionary = build / "dictionary" / "english.dic"

        encode1_seconds = run_guarded(
            guard_tool,
            [
                str(binary),
                "-c",
                str(dictionary),
                str(prefix),
                str(archive1),
            ],
            args.result_dir / "encode.first.guard.json",
            args.result_dir / "encode.first.log",
            "cmix_lex_fxcm_v26_250k_first",
        )
        archive_bytes = archive1.stat().st_size
        gain_bytes = GAMMA_PARENT_ARCHIVE_BYTES - archive_bytes
        decision = {
            "schema": "cmix_lex_fxcm_v26_transfer_gate_v1",
            "status": (
                "PASS_FIRST_ARCHIVE_CEILING"
                if archive_bytes <= PROMOTION_CEILING_BYTES
                else "FAIL_FIRST_ARCHIVE_CEILING"
            ),
            "score_credit_bytes": 0,
            "claim_boundary": (
                "External same-prefix predictor-stack falsification only. "
                "No native Gamma integration or score credit."
            ),
            "source": {
                "path": str(args.source),
                "commit": source_commit,
            },
            "input": {
                "bytes": prefix.stat().st_size,
                "sha256": sha256(prefix),
            },
            "gamma_parent_archive_bytes": GAMMA_PARENT_ARCHIVE_BYTES,
            "promotion_ceiling_bytes": PROMOTION_CEILING_BYTES,
            "archive": {
                "bytes": archive_bytes,
                "sha256": sha256(archive1),
            },
            "gain_bytes": gain_bytes,
            "gain_bytes_per_million": gain_bytes * 4,
            "build_seconds": build_seconds,
            "first_encode_seconds": encode1_seconds,
            "roundtrip_ok": None,
            "determinism_ok": None,
        }
        if archive_bytes > PROMOTION_CEILING_BYTES:
            decision["next_action"] = (
                "reject unchanged fxcm_v26 predictor-stack transfer; "
                "skip native port"
            )
            write_decision(args.result_dir / "decision.json", decision)
            return 0

        decode_seconds = run_guarded(
            guard_tool,
            [
                str(binary),
                "-d",
                str(dictionary),
                str(archive1),
                str(decoded),
            ],
            args.result_dir / "decode.guard.json",
            args.result_dir / "decode.log",
            "cmix_lex_fxcm_v26_250k_decode",
        )
        encode2_seconds = run_guarded(
            guard_tool,
            [
                str(binary),
                "-c",
                str(dictionary),
                str(prefix),
                str(archive2),
            ],
            args.result_dir / "encode.second.guard.json",
            args.result_dir / "encode.second.log",
            "cmix_lex_fxcm_v26_250k_second",
        )
        roundtrip = (
            decoded.stat().st_size == prefix.stat().st_size
            and sha256(decoded) == sha256(prefix)
        )
        deterministic = (
            archive2.stat().st_size == archive1.stat().st_size
            and sha256(archive2) == sha256(archive1)
        )
        decision.update(
            {
                "status": (
                    "PASS"
                    if roundtrip and deterministic
                    else "FAIL_EXACTNESS"
                ),
                "roundtrip_ok": roundtrip,
                "determinism_ok": deterministic,
                "decoded": {
                    "bytes": decoded.stat().st_size,
                    "sha256": sha256(decoded),
                },
                "second_archive": {
                    "bytes": archive2.stat().st_size,
                    "sha256": sha256(archive2),
                },
                "decode_seconds": decode_seconds,
                "second_encode_seconds": encode2_seconds,
                "next_action": (
                    "authorize native fxcm_v26 port"
                    if roundtrip and deterministic
                    else "reject invalid external comparator"
                ),
            }
        )
        write_decision(args.result_dir / "decision.json", decision)
        return 0 if roundtrip and deterministic else 1


if __name__ == "__main__":
    raise SystemExit(main())
