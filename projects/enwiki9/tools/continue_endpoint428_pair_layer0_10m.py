#!/usr/bin/env python3
"""Finish endpoint428 pair/layer-0 10M proof only after economics passes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


TERMINAL_GUARD_STATES = {"complete", "failed", "terminated"}


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def wait_for_terminal_guard(path: Path, poll_seconds: float) -> dict[str, Any]:
    while True:
        guard = load_object(path)
        if guard.get("status") in TERMINAL_GUARD_STATES:
            return guard
        time.sleep(poll_seconds)


def require_absent(paths: list[Path]) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise RuntimeError(f"refusing to overwrite proof artifacts: {existing}")


def guard_command(
    *,
    run_guard: Path,
    guard_json: Path,
    label: str,
    wrapper: Path,
    mode: str,
    source: Path,
    target: Path,
    stdout_log: Path,
    stderr_log: Path,
) -> list[str]:
    return [
        sys.executable,
        str(run_guard),
        "--limit-kib",
        "10485760",
        "--limit-mode",
        "max_single",
        "--official-decimal-limit-kib",
        "9765625",
        "--sample-interval",
        "1",
        "--guard-json",
        str(guard_json),
        "--label",
        label,
        "--",
        "bash",
        "-c",
        f'exec "$1" {mode} "$2" "$3" >"$4" 2>"$5"',
        "_",
        str(wrapper),
        str(source),
        str(target),
        str(stdout_log),
        str(stderr_log),
    ]


def sealer_command(args: argparse.Namespace, *, final: bool) -> list[str]:
    command = [
        sys.executable,
        str(args.sealer),
        "--native-1m-receipt",
        str(args.native_1m_receipt),
        "--wrapper",
        str(args.encode_wrapper),
        "--input",
        str(args.input),
        "--base-archive",
        str(args.base_archive),
        "--archive",
        str(args.archive),
        "--encode-guard",
        str(args.encode_guard),
        "--output",
        str(args.final_receipt if final else args.encode_receipt),
    ]
    if final:
        command.extend(
            [
                "--restored",
                str(args.restored),
                "--decode-guard",
                str(args.decode_guard),
                "--archive-second",
                str(args.archive_second),
                "--determinism-guard",
                str(args.determinism_guard),
                "--determinism-wrapper",
                str(args.determinism_wrapper),
            ]
        )
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encode-guard", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--native-1m-receipt", type=Path, required=True)
    parser.add_argument("--encode-wrapper", type=Path, required=True)
    parser.add_argument("--determinism-wrapper", type=Path, required=True)
    parser.add_argument("--run-guard", type=Path, required=True)
    parser.add_argument("--sealer", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=float, default=60.0)
    args = parser.parse_args()
    if args.poll_seconds <= 0:
        parser.error("--poll-seconds must be positive")
    args.restored = args.output_dir / "restored.raw"
    args.decode_guard = args.output_dir / "decode_guard.json"
    args.archive_second = args.output_dir / "archive_second.bin"
    args.determinism_guard = args.output_dir / "determinism_guard.json"
    args.encode_receipt = args.output_dir / "receipt_encode.json"
    args.final_receipt = args.output_dir / "receipt.json"
    return args


def main() -> int:
    args = parse_args()
    guard = wait_for_terminal_guard(args.encode_guard, args.poll_seconds)
    if not (
        guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("rss_guard_exceeded") is False
        and guard.get("official_decimal_over_limit_kib") == 0
    ):
        raise RuntimeError("terminal encode guard failed; codec replay forbidden")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(sealer_command(args, final=False), check=True)
    encode_receipt = load_object(args.encode_receipt)
    if encode_receipt.get("economics", {}).get("economics_pass") is not True:
        print(json.dumps(encode_receipt, sort_keys=True), flush=True)
        return 0

    require_absent(
        [
            args.restored,
            args.decode_guard,
            args.archive_second,
            args.determinism_guard,
            args.final_receipt,
        ]
    )
    try:
        subprocess.run(
            guard_command(
                run_guard=args.run_guard,
                guard_json=args.decode_guard,
                label="endpoint428_pair_layer0_online_native_10m_decode_v1",
                wrapper=args.encode_wrapper,
                mode="d",
                source=args.archive,
                target=args.restored,
                stdout_log=args.output_dir / "decode_stdout.log",
                stderr_log=args.output_dir / "decode_stderr.log",
            ),
            check=True,
        )
        subprocess.run(
            guard_command(
                run_guard=args.run_guard,
                guard_json=args.determinism_guard,
                label="endpoint428_pair_layer0_online_native_10m_determinism_v1",
                wrapper=args.determinism_wrapper,
                mode="c",
                source=args.input,
                target=args.archive_second,
                stdout_log=args.output_dir / "determinism_stdout.log",
                stderr_log=args.output_dir / "determinism_stderr.log",
            ),
            check=True,
        )
    finally:
        pass

    subprocess.run(sealer_command(args, final=True), check=True)
    print(args.final_receipt.read_text(), end="", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
