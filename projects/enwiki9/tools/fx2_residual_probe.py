#!/usr/bin/env python3
"""Run the certificate-first fx2 residual APM probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shlex
import subprocess
import sys
from contextlib import ExitStack
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
FX2_DIR = ROOT / "external" / "fx2-cmix"
DATA_DEFAULT = ROOT / "data" / "enwik9"
DICT_DEFAULT = FX2_DIR / "dictionary" / "english.dic"
OUT_DEFAULT = ROOT / "results" / "fx2_residual_probe"


def run(cmd: list[str], cwd: pathlib.Path, stdout: pathlib.Path | None = None,
        stderr: pathlib.Path | None = None) -> None:
    if stdout:
        stdout.parent.mkdir(parents=True, exist_ok=True)
    if stderr:
        stderr.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        out = stack.enter_context(stdout.open("wb")) if stdout else subprocess.DEVNULL
        if stderr is not None and stdout is not None and stderr == stdout:
            err: int | Any = subprocess.STDOUT
        else:
            err = stack.enter_context(stderr.open("wb")) if stderr else subprocess.DEVNULL
        proc = subprocess.run(cmd, cwd=cwd, stdout=out, stderr=err)
    if proc.returncode:
        rendered = " ".join(shlex.quote(part) for part in cmd)
        raise SystemExit(f"command failed ({proc.returncode}): {rendered}")


def capture(cmd: list[str], cwd: pathlib.Path) -> bytes:
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        sys.stderr.buffer.write(proc.stderr)
        rendered = " ".join(shlex.quote(part) for part in cmd)
        raise SystemExit(f"command failed ({proc.returncode}): {rendered}")
    return proc.stdout


def write_prefix(data_path: pathlib.Path, limit: int, output: pathlib.Path) -> bytes:
    with data_path.open("rb") as f:
        raw = f.read(limit)
    if len(raw) != limit:
        raise SystemExit(f"requested {limit} bytes, got {len(raw)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    return raw


def build_fx2(args: argparse.Namespace, build_log: pathlib.Path) -> list[str]:
    flags = [
        f"-DSEED={args.seed}",
        f"-DUPDATE_LIMIT={args.update_limit}",
        f"-DFX2_STRUCT_SIDECAR={args.struct_sidecar}",
        f"-DFX2_WRT_OBSERVATION={int(args.wrt_observation)}",
        "-DFX2_RESIDUAL_LOG=1",
        f"-DFX2_RESIDUAL_LOG_STRIDE={args.residual_stride}",
        f"-DFX2_RESIDUAL_LOG_MAX_ROWS={args.max_rows}",
    ]
    for define in args.define:
        flags.append(define if define.startswith("-D") else f"-D{define}")
    run(
        [
            "make",
            "-f",
            "makefile",
            f"CC={args.compiler}",
            "STRIP_FLAG=",
            f"CFLAGS_DEFINES={' '.join(flags)}",
            "clean",
            "cmix",
        ],
        cwd=FX2_DIR,
        stdout=build_log,
        stderr=build_log,
    )
    return flags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    ap.add_argument("--dictionary", type=pathlib.Path, default=DICT_DEFAULT)
    ap.add_argument("--limit", type=int, required=True)
    ap.add_argument("--out-dir", type=pathlib.Path, default=OUT_DEFAULT)
    ap.add_argument("--compiler", default="g++")
    ap.add_argument("--seed", type=int, default=923)
    ap.add_argument("--update-limit", type=int, default=3000)
    ap.add_argument("--struct-sidecar", type=int, choices=(0, 1, 2, 3, 4), default=1)
    ap.add_argument("--wrt-observation", action="store_true")
    ap.add_argument("--trace-only", action="store_true")
    ap.add_argument("--residual-stride", type=int, default=1)
    ap.add_argument("--max-rows", type=int, default=0)
    ap.add_argument("--define", action="append", default=[])
    ap.add_argument("--key", default="p_bucket,bit_pos,field,mode")
    ap.add_argument("--p-buckets", type=int, default=32)
    ap.add_argument("--blend-ppm", type=int, default=125000)
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--train-bytes", type=int, default=0)
    ap.add_argument("--scope-bytes", type=int, default=1_000_000_000)
    ap.add_argument("--baseline-score", type=int, default=110_181_114)
    ap.add_argument("--target-score", type=int, default=109_000_000)
    ap.add_argument("--patch-bytes", type=int, default=0)
    ap.add_argument("--table-bits", type=int, default=0)
    ap.add_argument("--gate-split", choices=["train", "test", "all"], default="all")
    ap.add_argument("--full-coverage", action="store_true")
    ap.add_argument("--manifold-search", action="store_true")
    ap.add_argument("--manifold-trials", type=int, default=16)
    ap.add_argument("--manifold-max-rows", type=int, default=0)
    ap.add_argument("--manifold-train-bytes", type=int)
    args = ap.parse_args()

    if args.limit <= 0:
        raise SystemExit("--limit must be positive")
    args.data = args.data.resolve()
    args.dictionary = args.dictionary.resolve()
    args.out_dir = args.out_dir.resolve()
    if not args.data.exists():
        raise SystemExit(f"missing data: {args.data}")
    if not args.dictionary.exists():
        raise SystemExit(f"missing dictionary: {args.dictionary}")

    run_dir = args.out_dir / args.label
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_path = run_dir / "input.raw"
    comp_path = run_dir / "output.cmix"
    stdout_log = run_dir / "stdout.log"
    stderr_log = run_dir / "stderr.log"
    build_log = run_dir / "build.log"
    scored_rows = run_dir / "residual_scored.jsonl"
    score_summary = run_dir / "residual_score_summary.json"
    cert_path = run_dir / "residual_gain_certificate.json"
    manifold_path = run_dir / "manifold_outer_sse_search.json"
    manifest_path = run_dir / "manifest.json"

    raw = write_prefix(args.data, args.limit, raw_path)
    flags = build_fx2(args, build_log)
    run(
        [
            str(FX2_DIR / "cmix"),
            "-c",
            str(args.dictionary),
            str(raw_path),
            str(comp_path),
        ],
        cwd=FX2_DIR,
        stdout=stdout_log,
        stderr=stderr_log,
    )
    if not args.trace_only:
        capture(
            [
                sys.executable,
                str(ROOT / "tools" / "fx2_residual_apm_score.py"),
                str(stderr_log),
                "--output",
                str(scored_rows),
                "--summary",
                str(score_summary),
                "--key",
                args.key,
                "--p-buckets",
                str(args.p_buckets),
                "--alpha",
                str(args.alpha),
                "--blend-ppm",
                str(args.blend_ppm),
                "--train-bytes",
                str(args.train_bytes),
            ],
            cwd=ROOT,
        )
        capture(
            [
                sys.executable,
                str(ROOT / "tools" / "fx2_residual_gain_certificate.py"),
                str(scored_rows),
                "--output",
                str(cert_path),
                "--baseline-score",
                str(args.baseline_score),
                "--target-score",
                str(args.target_score),
                "--scope-bytes",
                str(args.scope_bytes),
                "--patch-bytes",
                str(args.patch_bytes),
                "--table-bits",
                str(args.table_bits),
                "--gate-split",
                args.gate_split,
            ]
            + (["--full-coverage"] if args.full_coverage else []),
            cwd=ROOT,
        )
    if args.manifold_search and not args.trace_only:
        manifold_train_bytes = (
            args.manifold_train_bytes
            if args.manifold_train_bytes is not None
            else args.train_bytes
        )
        capture(
            [
                sys.executable,
                str(ROOT / "tools" / "fx2_manifold_outer_sse_search.py"),
                str(stderr_log),
                "--output",
                str(manifold_path),
                "--trials",
                str(args.manifold_trials),
                "--train-bytes",
                str(manifold_train_bytes),
                "--max-rows",
                str(args.manifold_max_rows),
            ],
            cwd=ROOT,
        )

    cert = json.loads(cert_path.read_text()) if not args.trace_only else None
    summary = json.loads(score_summary.read_text()) if not args.trace_only else None
    manifest = {
        "label": args.label,
        "limit": args.limit,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "compressed_size": comp_path.stat().st_size,
        "trace_only": args.trace_only,
        "build_flags": flags,
        "logs": {
            "stdout": str(stdout_log),
            "stderr": str(stderr_log),
            "scored_rows": str(scored_rows) if not args.trace_only else None,
            "score_summary": str(score_summary) if not args.trace_only else None,
            "certificate": str(cert_path) if not args.trace_only else None,
            "manifold_search": str(manifold_path) if args.manifold_search else None,
        },
        "score_summary": summary,
        "certificate_gate": cert["gate"] if cert else None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
