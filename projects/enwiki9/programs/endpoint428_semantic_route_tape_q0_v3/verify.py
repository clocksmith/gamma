#!/usr/bin/env python3
"""Coordinate exact A/B identity with the independent native semantic replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
from typing import Any


TAPE_HEADER_BYTES = 192
TAPE_RECORD_BYTES = 88
SIDE_HEADER_BYTES = 64
SIDE_RECORD_BYTES = 232
FULL = {
    "store": (647_798_597, "fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9"),
    "raw": (1_000_000_000, "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"),
    "dictionary": (411_996, "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
}


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def regular(path: Path, label: str) -> Path:
    metadata = path.lstat()
    require(stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
            f"{label} must be a regular non-symlink file")
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256(path)}


def parse_tape_header(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        header = handle.read(TAPE_HEADER_BYTES)
    require(len(header) == TAPE_HEADER_BYTES and header[:8] == b"GSRT2\0\0\0", "tape header")
    version, header_bytes, record_bytes, flags = struct.unpack_from("<IIII", header, 8)
    require((version, header_bytes, record_bytes) == (2, 192, 88), "tape ABI")
    require(flags in (0, 1), "tape flags")
    geometry = struct.unpack_from("<QQQQQQ", header, 24)
    events = list(struct.unpack_from("<9Q", header, 72))
    result = {
        "fixture": bool(flags),
        "store_bytes": geometry[0],
        "wrt_bytes": geometry[1],
        "raw_bytes": geometry[2],
        "dictionary_bytes": geometry[3],
        "record_count": geometry[4],
        "descriptor_count": geometry[5],
        "event_counts": events,
        "deferred_updates": struct.unpack_from("<Q", header, 144)[0],
        "positional_predictive_events": struct.unpack_from("<Q", header, 152)[0],
        "pretruth_violations": struct.unpack_from("<Q", header, 160)[0],
        "parser_digest": struct.unpack_from("<Q", header, 168)[0],
        "raw_digest": struct.unpack_from("<Q", header, 176)[0],
        "wrt_digest": struct.unpack_from("<Q", header, 184)[0],
    }
    require(path.stat().st_size == 192 + 88 * result["record_count"], "tape size")
    require(sum(events) == result["record_count"], "event count sum")
    require(result["positional_predictive_events"] == 0, "positional prediction")
    require(result["pretruth_violations"] == 0, "pretruth violation")
    return result


def verify_side_header(path: Path, header: dict[str, Any]) -> None:
    with path.open("rb") as handle:
        side = handle.read(SIDE_HEADER_BYTES)
    require(len(side) == 64 and side[:8] == b"GSRD2\0\0\0", "side header")
    require(struct.unpack_from("<IIII", side, 8) ==
            (2, 64, 232, 1 if header["fixture"] else 0), "side ABI")
    require(struct.unpack_from("<Q", side, 24)[0] == header["descriptor_count"],
            "side descriptor count")
    require(struct.unpack_from("<Q", side, 32)[0] == header["parser_digest"],
            "side parser digest")
    require(side[40:] == bytes(24), "side reserved bytes")
    require(path.stat().st_size == 64 + 232 * header["descriptor_count"], "side size")


def verify_summary(path: Path, header: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(value.get("schema") == "gamma.enwiki9.endpoint428-semantic-route-tape-summary.v2",
            "summary schema")
    require(value.get("candidate_id") == "endpoint428_semantic_route_tape_q0_v2",
            "parent scanner summary identity")
    expected = {
        "fixture": header["fixture"],
        "store_bytes": header["store_bytes"],
        "wrt_stream_bytes": header["wrt_bytes"],
        "reconstructed_raw_bytes": header["raw_bytes"],
        "dictionary_bytes": header["dictionary_bytes"],
        "record_bytes": 88,
        "record_count": header["record_count"],
        "descriptor_count": header["descriptor_count"],
        "event_counts": header["event_counts"],
        "deferred_update_events": header["deferred_updates"],
        "positional_predictive_events": 0,
        "pretruth_eligibility_violations": 0,
        "parser_fnv1a64": f"{header['parser_digest']:016x}",
        "raw_fnv1a64": f"{header['raw_digest']:016x}",
        "wrt_fnv1a64": f"{header['wrt_digest']:016x}",
        "archive_authority": False,
        "score_credit_bytes": 0,
    }
    for key, expected_value in expected.items():
        require(value.get(key) == expected_value, f"summary {key}")
    return value


def verify_input(path: Path, expected_bytes: int, header_bytes: int,
                 expected_sha: str | None, label: str) -> dict[str, Any]:
    require(path.stat().st_size == expected_bytes == header_bytes, f"{label} geometry")
    row = artifact(path)
    if expected_sha is not None:
        require(row["sha256"] == expected_sha, f"{label} SHA-256")
    return row


def run_native(binary: Path, args: argparse.Namespace) -> dict[str, Any]:
    completed = subprocess.run(
        [str(binary), str(args.store), str(args.raw), str(args.dictionary),
         str(args.tape_a), str(args.sidecar_a)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    require(completed.returncode == 0,
            f"native replay returncode={completed.returncode}: {completed.stderr.strip()}")
    try:
        receipt = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise VerificationError(f"native replay JSON: {error}") from error
    require(receipt.get("semantic_replay_pass") is True, "native replay result")
    require(receipt.get("archive_authority") is False and
            receipt.get("score_credit_bytes") == 0, "native replay authority")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    for option in ("store", "raw", "dictionary", "tape-a", "tape-b", "sidecar-a",
                   "sidecar-b", "summary-a", "summary-b", "native-replay", "receipt"):
        parser.add_argument(f"--{option}", required=True, type=Path)
    args = parser.parse_args()
    for name in ("store", "raw", "dictionary", "tape_a", "tape_b", "sidecar_a",
                 "sidecar_b", "summary_a", "summary_b", "native_replay"):
        regular(getattr(args, name), name)
    require(not args.receipt.exists() and not args.receipt.is_symlink(), "exclusive receipt")

    header_a = parse_tape_header(args.tape_a)
    header_b = parse_tape_header(args.tape_b)
    require(header_a == header_b, "A/B header identity")
    verify_side_header(args.sidecar_a, header_a)
    verify_side_header(args.sidecar_b, header_b)
    summary_a = verify_summary(args.summary_a, header_a)
    summary_b = verify_summary(args.summary_b, header_b)
    require(summary_a == summary_b, "A/B summary content")

    artifacts = {
        "tape_a": artifact(args.tape_a), "tape_b": artifact(args.tape_b),
        "sidecar_a": artifact(args.sidecar_a), "sidecar_b": artifact(args.sidecar_b),
        "summary_a": artifact(args.summary_a), "summary_b": artifact(args.summary_b),
        "native_replay": artifact(args.native_replay),
    }
    require(artifacts["tape_a"]["sha256"] == artifacts["tape_b"]["sha256"], "A/B tape bytes")
    require(artifacts["sidecar_a"]["sha256"] == artifacts["sidecar_b"]["sha256"],
            "A/B sidecar bytes")
    require(artifacts["summary_a"]["sha256"] == artifacts["summary_b"]["sha256"],
            "A/B summary bytes")

    full_hashes = None if header_a["fixture"] else FULL
    inputs = {
        "store": verify_input(args.store, header_a["store_bytes"], args.store.stat().st_size,
                              None if full_hashes is None else FULL["store"][1], "store"),
        "raw": verify_input(args.raw, header_a["raw_bytes"], args.raw.stat().st_size,
                            None if full_hashes is None else FULL["raw"][1], "raw"),
        "dictionary": verify_input(
            args.dictionary, header_a["dictionary_bytes"], args.dictionary.stat().st_size,
            None if full_hashes is None else FULL["dictionary"][1], "dictionary"),
    }
    if full_hashes is not None:
        require((header_a["store_bytes"], header_a["wrt_bytes"], header_a["raw_bytes"],
                 header_a["dictionary_bytes"]) == (647_798_597, 647_798_592,
                                                    1_000_000_000, 411_996),
                "production geometry")

    native = run_native(args.native_replay, args)
    require(native.get("fixture") == header_a["fixture"], "native fixture identity")
    require(native.get("wrt_bytes") == header_a["wrt_bytes"] and
            native.get("raw_bytes") == header_a["raw_bytes"] and
            native.get("record_count") == header_a["record_count"] and
            native.get("descriptor_count") == header_a["descriptor_count"],
            "native aggregate identity")

    receipt = {
        "schema": "gamma.enwiki9.endpoint428-semantic-route-tape-verification.v3",
        "candidate_id": "endpoint428_semantic_route_tape_q0_v3",
        "verification_pass": True,
        "fixture": header_a["fixture"],
        "repeat_identity_pass": True,
        "native_semantic_replay_pass": True,
        "scanned_wrt_bytes": header_a["wrt_bytes"],
        "reconstructed_raw_bytes": header_a["raw_bytes"],
        "record_count": header_a["record_count"],
        "descriptor_count": header_a["descriptor_count"],
        "native": native,
        "inputs": inputs,
        "artifacts": artifacts,
        "archive_authority": False,
        "score_credit_bytes": 0,
        "claim": "bounded-source-validation-only" if header_a["fixture"]
                 else "zero-credit-population-infrastructure",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as error:
        print(f"verification failed: {error}", file=__import__("sys").stderr)
        raise SystemExit(1)
