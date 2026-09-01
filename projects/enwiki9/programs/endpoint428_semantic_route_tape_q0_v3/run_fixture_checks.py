#!/usr/bin/env python3
"""Run bounded positive replay and paired semantic-record corruption controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
from typing import Callable


ROOT = Path(__file__).resolve().parent
HEADER_BYTES = 192
RECORD_BYTES = 88


def run(command: list[str], expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, check=False)
    if (completed.returncode == 0) != expect_success:
        raise RuntimeError(
            f"unexpected return code {completed.returncode}: {command}\n{completed.stdout}"
        )
    return completed


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_count(data: bytearray) -> int:
    return struct.unpack_from("<Q", data, 56)[0]


def record_offset(index: int) -> int:
    return HEADER_BYTES + index * RECORD_BYTES


def mutate_ordinal(data: bytearray) -> None:
    for index in range(record_count(data)):
        offset = record_offset(index)
        if data[offset + 85] & 1:
            value = struct.unpack_from("<Q", data, offset + 72)[0]
            struct.pack_into("<Q", data, offset + 72, value + 1)
            return
    raise RuntimeError("no routed record for ordinal mutation")


def mutate_depth(data: bytearray) -> None:
    for index in range(record_count(data)):
        offset = record_offset(index)
        if data[offset + 86] < 16:
            data[offset + 86] += 1
            return
    raise RuntimeError("no record for depth mutation")


def mutate_field(data: bytearray) -> None:
    for index in range(record_count(data)):
        offset = record_offset(index)
        if data[offset + 85] & 1:
            value = struct.unpack_from("<I", data, offset + 80)[0]
            struct.pack_into("<I", data, offset + 80, value + 1)
            return
    raise RuntimeError("no routed record for field mutation")


def mutate_raw_coordinate(data: bytearray) -> None:
    for index in range(record_count(data)):
        offset = record_offset(index)
        before = struct.unpack_from("<Q", data, offset + 24)[0]
        after = struct.unpack_from("<Q", data, offset + 32)[0]
        if before < after:
            struct.pack_into("<Q", data, offset + 24, before + 1)
            return
    raise RuntimeError("no nonempty raw span for mutation")


def mutate_event_order(data: bytearray) -> None:
    for index in range(record_count(data) - 1):
        left = record_offset(index)
        right = record_offset(index + 1)
        availability_left = struct.unpack_from("<Q", data, left + 8)[0]
        availability_right = struct.unpack_from("<Q", data, right + 8)[0]
        if availability_left == availability_right and data[left + 84] != 3 and data[right + 84] == 3:
            first = bytes(data[left:left + RECORD_BYTES])
            second = bytes(data[right:right + RECORD_BYTES])
            data[left:left + RECORD_BYTES] = second
            data[right:right + RECORD_BYTES] = first
            return
    raise RuntimeError("no equal-availability state/prediction pair")


def verifier_command(inputs: Path, native: Path, tape_a: Path, tape_b: Path,
                     receipt: Path) -> list[str]:
    return [
        "python3", str(ROOT / "verify.py"),
        "--store", str(inputs / "store.bin"),
        "--raw", str(inputs / "raw.bin"),
        "--dictionary", str(inputs / "dictionary.txt"),
        "--tape-a", str(tape_a), "--tape-b", str(tape_b),
        "--sidecar-a", str(inputs / "descriptors-a.bin"),
        "--sidecar-b", str(inputs / "descriptors-b.bin"),
        "--summary-a", str(inputs / "summary-a.json"),
        "--summary-b", str(inputs / "summary-b.json"),
        "--native-replay", str(native), "--receipt", str(receipt),
    ]


def paired_corruption(source: Path, work: Path, name: str,
                      mutation: Callable[[bytearray], None]) -> tuple[Path, Path]:
    data = bytearray(source.read_bytes())
    mutation(data)
    first = work / f"{name}-a.bin"
    second = work / f"{name}-b.bin"
    first.write_bytes(data)
    second.write_bytes(data)
    return first, second


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--scanner-source", required=True, type=Path)
    parser.add_argument("--compiler", default="/usr/bin/x86_64-linux-gnu-g++-15")
    args = parser.parse_args()
    if args.receipt.exists() or args.receipt.is_symlink():
        raise RuntimeError("receipt path must not exist")
    required_scanner_sha = "b44fffb2b95c540535d293e1d0021f544a5b7e4d8fbb740721752a69b0c7866e"
    if sha256(args.scanner_source) != required_scanner_sha:
        raise RuntimeError("sealed v2 scanner source identity mismatch")

    with tempfile.TemporaryDirectory(prefix="gamma-semantic-route-v3-fixture-") as temporary:
        work = Path(temporary)
        inputs = work / "inputs"
        run(["python3", str(ROOT / "build_fixture.py"), str(inputs)])
        scanner = work / "semantic-route-tape"
        native = work / "semantic-replay"
        flags = ["-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-fno-fast-math", "-ffp-contract=off", "-march=x86-64",
                 "-mtune=generic", "-Wl,--build-id=none"]
        run([args.compiler, *flags, str(args.scanner_source), "-o", str(scanner)])
        run([args.compiler, *flags, str(ROOT / "semantic-replay.cpp"), "-o", str(native)])
        for arm in ("a", "b"):
            run([
                str(scanner), str(inputs / "store.bin"), str(inputs / "raw.bin"),
                str(inputs / "dictionary.txt"), str(inputs / f"tape-{arm}.bin"),
                str(inputs / f"descriptors-{arm}.bin"),
                str(inputs / f"summary-{arm}.json"), "--fixture",
            ])
        positive = work / "positive.json"
        run(verifier_command(inputs, native, inputs / "tape-a.bin", inputs / "tape-b.bin",
                             positive))

        controls: dict[str, bool] = {}
        mutations: dict[str, Callable[[bytearray], None]] = {
            "paired_ordinal_rejected": mutate_ordinal,
            "paired_depth_rejected": mutate_depth,
            "paired_field_rejected": mutate_field,
            "paired_raw_coordinate_rejected": mutate_raw_coordinate,
            "paired_event_order_rejected": mutate_event_order,
        }
        for name, mutation in mutations.items():
            first, second = paired_corruption(inputs / "tape-a.bin", work, name, mutation)
            failed = run(
                verifier_command(inputs, native, first, second, work / f"unexpected-{name}.json"),
                expect_success=False,
            )
            controls[name] = failed.returncode != 0 and "native replay" in failed.stdout

        positive_receipt = json.loads(positive.read_text(encoding="utf-8"))
        receipt = {
            "schema": "gamma.enwiki9.endpoint428-semantic-route-tape-fixture-check.v3",
            "candidate_id": "endpoint428_semantic_route_tape_q0_v3",
            "fixture_pass": positive_receipt.get("verification_pass") is True
                            and all(controls.values()),
            "positive": positive_receipt,
            "paired_corruption_controls": controls,
            "paired_corruption_reject_count": sum(controls.values()),
            "compiler": {"path": str(Path(args.compiler).resolve()),
                         "sha256": sha256(Path(args.compiler))},
            "compile_flags": flags,
            "parent_scanner_sha256": required_scanner_sha,
            "native_replay_sha256": sha256(ROOT / "semantic-replay.cpp"),
            "verification_coordinator_sha256": sha256(ROOT / "verify.py"),
            "fixture_builder_sha256": sha256(ROOT / "build_fixture.py"),
            "archive_authority": False,
            "score_credit_bytes": 0,
            "claim": "bounded-source-validation-only",
        }
        if not receipt["fixture_pass"]:
            raise RuntimeError(f"fixture failure: {receipt}")
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
