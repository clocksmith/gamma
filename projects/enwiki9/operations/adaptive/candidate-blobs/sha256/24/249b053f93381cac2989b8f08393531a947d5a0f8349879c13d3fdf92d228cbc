#!/usr/bin/env python3
"""Compile and exercise positive and negative semantic-route source fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RECORD_BYTES = 88
HEADER_BYTES = 192


def run(command: list[str], *, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, check=False)
    if (completed.returncode == 0) != expect_success:
        raise RuntimeError(
            f"unexpected return code {completed.returncode}: {command}\n{completed.stdout}"
        )
    return completed


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verifier_command(inputs: Path, tape_a: Path, sidecar_a: Path, receipt: Path) -> list[str]:
    return [
        "python3", str(ROOT / "verify.py"),
        "--store", str(inputs / "store.bin"),
        "--raw", str(inputs / "raw.bin"),
        "--dictionary", str(inputs / "dictionary.txt"),
        "--tape-a", str(tape_a),
        "--tape-b", str(inputs / "tape-b.bin"),
        "--sidecar-a", str(sidecar_a),
        "--sidecar-b", str(inputs / "descriptors-b.bin"),
        "--summary-a", str(inputs / "summary-a.json"),
        "--summary-b", str(inputs / "summary-b.json"),
        "--receipt", str(receipt),
    ]


def corrupt_route(source: Path, destination: Path) -> None:
    data = bytearray(source.read_bytes())
    count = struct.unpack_from("<Q", data, 56)[0]
    for index in range(count):
        offset = HEADER_BYTES + index * RECORD_BYTES
        if data[offset + 85] & 1:
            data[offset + 40] ^= 1
            destination.write_bytes(data)
            return
    raise RuntimeError("fixture has no routed record")


def corrupt_order(source: Path, destination: Path) -> None:
    data = bytearray(source.read_bytes())
    count = struct.unpack_from("<Q", data, 56)[0]
    for index in range(count - 1):
        left = HEADER_BYTES + index * RECORD_BYTES
        right = left + RECORD_BYTES
        left_availability = struct.unpack_from("<Q", data, left + 8)[0]
        right_availability = struct.unpack_from("<Q", data, right + 8)[0]
        left_event = data[left + 84]
        right_event = data[right + 84]
        if left_availability == right_availability and left_event != 3 and right_event == 3:
            first = bytes(data[left:left + RECORD_BYTES])
            second = bytes(data[right:right + RECORD_BYTES])
            data[left:left + RECORD_BYTES] = second
            data[right:right + RECORD_BYTES] = first
            destination.write_bytes(data)
            return
    raise RuntimeError("fixture has no state-action/prediction pair")


def corrupt_witness(source: Path, destination: Path) -> None:
    data = bytearray(source.read_bytes())
    count = struct.unpack_from("<Q", data, 24)[0]
    if count == 0:
        raise RuntimeError("fixture has no descriptor")
    data[64 + 16] ^= 1
    destination.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--compiler", default="/usr/bin/x86_64-linux-gnu-g++-15")
    args = parser.parse_args()
    if args.receipt.exists() or args.receipt.is_symlink():
        raise RuntimeError("receipt path must not exist")

    with tempfile.TemporaryDirectory(prefix="gamma-semantic-route-fixture-") as temporary:
        work = Path(temporary)
        inputs = work / "inputs"
        run(["python3", str(ROOT / "build_fixture.py"), str(inputs)])
        binary = work / "semantic-route-tape"
        flags = [
            "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
            "-fno-fast-math", "-ffp-contract=off", "-march=x86-64", "-mtune=generic",
            "-Wl,--build-id=none",
        ]
        run([args.compiler, *flags, str(ROOT / "semantic-route-tape.cpp"), "-o", str(binary)])
        for arm in ("a", "b"):
            run([
                str(binary), str(inputs / "store.bin"), str(inputs / "raw.bin"),
                str(inputs / "dictionary.txt"), str(inputs / f"tape-{arm}.bin"),
                str(inputs / f"descriptors-{arm}.bin"), str(inputs / f"summary-{arm}.json"),
                "--fixture",
            ])
        positive = work / "positive.json"
        run(verifier_command(inputs, inputs / "tape-a.bin", inputs / "descriptors-a.bin", positive))

        negative_cases: dict[str, bool] = {}
        corrupt_tape = work / "corrupt-route.bin"
        corrupt_route(inputs / "tape-a.bin", corrupt_tape)
        negative_cases["unknown_route_rejected"] = run(
            verifier_command(inputs, corrupt_tape, inputs / "descriptors-a.bin",
                             work / "unexpected-route-receipt.json"),
            expect_success=False,
        ).returncode != 0

        corrupt_tape = work / "corrupt-order.bin"
        corrupt_order(inputs / "tape-a.bin", corrupt_tape)
        negative_cases["causal_order_rejected"] = run(
            verifier_command(inputs, corrupt_tape, inputs / "descriptors-a.bin",
                             work / "unexpected-order-receipt.json"),
            expect_success=False,
        ).returncode != 0

        corrupt_sidecar = work / "corrupt-witness.bin"
        corrupt_witness(inputs / "descriptors-a.bin", corrupt_sidecar)
        negative_cases["witness_corruption_rejected"] = run(
            verifier_command(inputs, inputs / "tape-a.bin", corrupt_sidecar,
                             work / "unexpected-witness-receipt.json"),
            expect_success=False,
        ).returncode != 0

        positive_receipt = json.loads(positive.read_text(encoding="utf-8"))
        receipt = {
            "schema": "gamma.enwiki9.endpoint428-semantic-route-tape-fixture-check.v2",
            "candidate_id": "endpoint428_semantic_route_tape_q0_v2",
            "fixture_pass": positive_receipt.get("verification_pass") is True
                            and all(negative_cases.values()),
            "positive": positive_receipt,
            "negative_cases": negative_cases,
            "compiler": {"path": str(Path(args.compiler).resolve()),
                         "sha256": sha256(Path(args.compiler))},
            "compile_flags": flags,
            "source_sha256": sha256(ROOT / "semantic-route-tape.cpp"),
            "verifier_sha256": sha256(ROOT / "verify.py"),
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
