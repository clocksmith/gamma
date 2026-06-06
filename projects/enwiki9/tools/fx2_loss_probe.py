#!/usr/bin/env python3
"""Build and run a reproducible fx2-cmix coder-side loss ledger probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shlex
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FX2_DIR = ROOT / "external" / "fx2-cmix"
DATA_DEFAULT = ROOT / "data" / "enwik9"
OUT_DEFAULT = ROOT / "results" / "fx2_loss_profile"
DICT_DEFAULT = FX2_DIR / "dictionary" / "english.dic"


def run_logged(
    cmd: list[str],
    cwd: pathlib.Path,
    stdout_path: pathlib.Path,
    stderr_path: pathlib.Path,
) -> None:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    if stdout_path == stderr_path:
        with stdout_path.open("wb") as stdout:
            proc = subprocess.run(
                cmd, cwd=cwd, stdout=stdout, stderr=subprocess.STDOUT
            )
    else:
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            proc = subprocess.run(cmd, cwd=cwd, stdout=stdout, stderr=stderr)
    if proc.returncode:
        rendered = " ".join(shlex.quote(part) for part in cmd)
        raise SystemExit(f"command failed ({proc.returncode}): {rendered}")


def run_capture(cmd: list[str], cwd: pathlib.Path) -> bytes:
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        rendered = " ".join(shlex.quote(part) for part in cmd)
        sys.stderr.buffer.write(proc.stderr)
        raise SystemExit(f"command failed ({proc.returncode}): {rendered}")
    return proc.stdout


def write_prefix(data_path: pathlib.Path, limit: int, output: pathlib.Path) -> bytes:
    with data_path.open("rb") as f:
        raw = f.read(limit)
    if len(raw) != limit:
        raise SystemExit(f"requested {limit} bytes, got {len(raw)} from {data_path}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    return raw


def build_flags(args: argparse.Namespace) -> list[str]:
    flags = [
        f"-DSEED={args.seed}",
        f"-DUPDATE_LIMIT={args.update_limit}",
        "-DFX2_STRUCT_TOP_MIXER",
        f"-DFX2_STRUCT_TOP_MIXER_WEIGHT={args.struct_top_weight}",
        f"-DFX2_STRUCT_TOP_MIXER_CONTEXT={args.struct_top_context}",
        "-DFX2_LOSS_PROFILE",
        "-DFX2_LOSS_PROFILE_FROM_CODER",
        "-DFX2_LOSS_LEDGER",
        f"-DFX2_LOSS_LEDGER_MAX_ROWS={args.max_rows}",
        f"-DFX2_LOSS_LEDGER_MIN_QBITS={args.min_qbits}",
        f"-DFX2_LOSS_LEDGER_MIN_GAP_QBITS={args.min_gap_qbits}",
        f"-DFX2_LOSS_LEDGER_POS_STRIDE={args.stride}",
    ]
    for define in args.define:
        flags.append(define if define.startswith("-D") else f"-D{define}")
    return flags


def build_fx2(args: argparse.Namespace, flags: list[str], build_log: pathlib.Path) -> None:
    cmd = [
        "make",
        "-f",
        "makefile",
        f"CC={args.compiler}",
        "STRIP_FLAG=",
        f"CFLAGS_DEFINES={' '.join(flags)}",
        "cmix",
    ]
    run_logged(cmd, FX2_DIR, build_log, build_log)


def summarize(
    label: str,
    raw_path: pathlib.Path,
    comp_path: pathlib.Path,
    stderr_path: pathlib.Path,
    args: argparse.Namespace,
) -> dict[str, object]:
    summary_path = args.out_dir / f"{label}_sample_summary.json"
    run_capture(
        [
            sys.executable,
            str(ROOT / "tools" / "fx2_loss_sample_summary.py"),
            str(stderr_path),
            "--output",
            str(summary_path),
            "--sample-stride",
            str(args.stride),
            "--top",
            str(args.top),
            "--top-windows",
            str(args.top_windows),
        ],
        ROOT,
    )

    manifest: dict[str, object] = {
        "label": label,
        "raw": str(raw_path),
        "compressed": str(comp_path),
        "stderr_log": str(stderr_path),
        "sample_summary": str(summary_path),
        "raw_size": raw_path.stat().st_size,
        "compressed_size": comp_path.stat().st_size,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "compressed_sha256": hashlib.sha256(comp_path.read_bytes()).hexdigest(),
        "sample_stride": args.stride,
    }

    if args.required_bytes or args.scope_bytes:
        arbitrage_path = args.out_dir / f"{label}_arbitrage.json"
        cmd = [
            sys.executable,
            str(ROOT / "tools" / "fx2_arbitrage_report.py"),
            str(stderr_path),
            "--output",
            str(arbitrage_path),
            "--sample-stride",
            str(args.stride),
        ]
        if args.required_bytes:
            cmd += ["--required-bytes", str(args.required_bytes)]
        if args.scope_bytes:
            cmd += ["--scope-bytes", str(args.scope_bytes)]
        run_capture(cmd, ROOT)
        manifest["arbitrage_report"] = str(arbitrage_path)

    if args.rdo:
        rdo_path = args.out_dir / f"{label}_rdo_feasibility.json"
        run_capture(
            [
                sys.executable,
                str(ROOT / "tools" / "fx2_rdo_feasibility.py"),
                str(stderr_path),
                "--data",
                str(raw_path),
                "--output",
                str(rdo_path),
                "--min-match",
                str(args.rdo_min_match),
                "--max-match",
                str(args.rdo_max_match),
                "--copy-cost-bits",
                str(args.rdo_copy_cost_bits),
            ],
            ROOT,
        )
        manifest["rdo_feasibility"] = str(rdo_path)

    return manifest


def verify_roundtrip(
    raw: bytes,
    comp_path: pathlib.Path,
    restored_path: pathlib.Path,
    stdout_path: pathlib.Path,
    stderr_path: pathlib.Path,
    dictionary: pathlib.Path | None,
) -> dict[str, object]:
    cmd = [str(FX2_DIR / "cmix"), "-d"]
    if dictionary is not None:
        cmd.append(str(dictionary))
    cmd += [str(comp_path), str(restored_path)]
    run_logged(
        cmd,
        FX2_DIR,
        stdout_path,
        stderr_path,
    )
    restored = restored_path.read_bytes()
    ok = restored == raw
    return {
        "ok": ok,
        "restored": str(restored_path),
        "restored_size": len(restored),
        "restored_sha256": hashlib.sha256(restored).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    ap.add_argument("--dictionary", type=pathlib.Path)
    ap.add_argument("--use-default-dictionary", action="store_true")
    ap.add_argument("--limit", type=int, required=True)
    ap.add_argument("--out-dir", type=pathlib.Path, default=OUT_DEFAULT)
    ap.add_argument("--compiler", default="g++")
    ap.add_argument("--seed", type=int, default=923)
    ap.add_argument("--update-limit", type=int, default=3000)
    ap.add_argument("--struct-top-weight", type=int, default=16)
    ap.add_argument("--struct-top-context", type=int, default=6)
    ap.add_argument("--max-rows", type=int, default=120000)
    ap.add_argument("--min-qbits", type=int, default=1536)
    ap.add_argument("--min-gap-qbits", type=int, default=1024)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--define", action="append", default=[])
    ap.add_argument("--scope-bytes", type=int, default=0)
    ap.add_argument("--required-bytes", type=float, default=0.0)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--top-windows", type=int, default=12)
    ap.add_argument("--rdo", action="store_true")
    ap.add_argument("--rdo-min-match", type=int, default=8)
    ap.add_argument("--rdo-max-match", type=int, default=512)
    ap.add_argument("--rdo-copy-cost-bits", type=float, default=32.0)
    ap.add_argument("--verify-roundtrip", action="store_true")
    args = ap.parse_args()

    if not args.data.exists():
        raise SystemExit(f"missing data: {args.data}")
    if not FX2_DIR.exists():
        raise SystemExit(f"missing fx2-cmix checkout: {FX2_DIR}")
    dictionary = args.dictionary
    if args.use_default_dictionary:
        dictionary = DICT_DEFAULT
    if dictionary is not None and not dictionary.exists():
        raise SystemExit(f"missing dictionary: {dictionary}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    label = args.label
    raw_path = args.out_dir / f"{label}.raw"
    comp_path = args.out_dir / f"{label}.comp"
    stdout_path = args.out_dir / f"{label}_stdout.log"
    stderr_path = args.out_dir / f"{label}_stderr.log"
    build_log = args.out_dir / f"build_{label}.log"
    manifest_path = args.out_dir / f"{label}_manifest.json"
    restored_path = args.out_dir / f"{label}.restored"
    decode_stdout_path = args.out_dir / f"{label}_decode_stdout.log"
    decode_stderr_path = args.out_dir / f"{label}_decode_stderr.log"

    raw = write_prefix(args.data, args.limit, raw_path)
    flags = build_flags(args)
    build_fx2(args, flags, build_log)
    encode_cmd = [str(FX2_DIR / "cmix"), "-c"]
    if dictionary is not None:
        encode_cmd.append(str(dictionary))
    encode_cmd += [str(raw_path), str(comp_path)]
    run_logged(
        encode_cmd,
        FX2_DIR,
        stdout_path,
        stderr_path,
    )

    manifest = summarize(label, raw_path, comp_path, stderr_path, args)
    roundtrip_ok = True
    if args.verify_roundtrip:
        roundtrip = verify_roundtrip(
            raw,
            comp_path,
            restored_path,
            decode_stdout_path,
            decode_stderr_path,
            dictionary,
        )
        manifest["roundtrip"] = roundtrip
        roundtrip_ok = bool(roundtrip["ok"])
    manifest.update(
        {
            "build_log": str(build_log),
            "stdout_log": str(stdout_path),
            "build_flags": flags,
            "compiler": args.compiler,
            "data_path": str(args.data),
            "dictionary": str(dictionary) if dictionary is not None else None,
            "limit": args.limit,
            "input_sha256": hashlib.sha256(raw).hexdigest(),
        }
    )
    payload = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_path.write_text(payload + "\n")
    print(payload)
    return 0 if roundtrip_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
