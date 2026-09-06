#!/usr/bin/env python3
"""Bounded observer successor build and streamed first-divergence diagnostics.

The codec law and v1 sources remain unchanged. SHA-256 witnesses cover serialized
bytes only; fixture snapshots permit direct equality and independent coverage
checks. Neither this wrapper nor a matching digest grants a corpus certificate.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import midas_open_codec_v1 as parent

FILES = ("data", "state.bin", "summary.json", "probabilities.bin", "boundaries.jsonl", "snapshots.bin")
FILE_LIMIT = 32 * 1024**2
PART_NAMES = (
    "complete_state", "complete_predictor", "parent_identity_projection", "normalized_coder",
    "reference_model_projection", "scheduler", "byte_prefix", "decoded_prefix", "sequence_origin",
    "scheduler_update_counters", "discarded_shadow", "model_header_prefix", "model_probability_cache",
    "recurrent_memory", "parameters", "optimizer_moments_and_compensation", "incremental_cache",
)
SOURCES = (ROOT / "tools/midas_open_boundary_observer_v1.cpp", *parent.SOURCES[1:],
           parent.CORE / "profile_population.cpp")


def build(cache_dir: Path):
    return parent.build_cpp_cached(sources=SOURCES, flags=parent.FLAGS,
                                   cache_dir=cache_dir, timeout_seconds=120)


@contextlib.contextmanager
def bounded_input(path: Path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(fd, "rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= FILE_LIMIT:
            raise ValueError(f"observer input is not a bounded regular file: {path}")
        yield source
        after, current = os.fstat(source.fileno()), path.lstat()
        identity = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns, row.st_ctime_ns)
        if identity(before) != identity(after) or identity(after) != identity(current):
            raise ValueError(f"observer input changed while read: {path}")


def probability_header(source) -> dict:
    header = source.read(21)
    if len(header) != 21 or header[:8] != b"MOPROB01":
        raise ValueError("probability trace header missing or malformed")
    raw, model, arm = struct.unpack("<QIB", header[8:])
    if raw > 250000 or model != 0x4F504601 or arm > 2:
        raise ValueError("probability trace coordinates/model/arm invalid")
    actual = os.fstat(source.fileno()).st_size
    if actual != 21 + 16 * raw:
        raise ValueError(f"probability trace incomplete: observed {actual} bytes, expected {21 + 16 * raw}")
    return {"raw_bytes": raw, "model_tag": model, "archive_arm": arm, "records": raw * 8}


def boundary_rows(path: Path, raw_bytes: int):
    expected = [("initial", 0), *(("boundary", n * 8) for n in range(32, raw_bytes + 1, 32)),
                ("final", raw_bytes * 8)]
    with bounded_input(path) as source:
        for kind, position in expected:
            line = source.readline(8193)
            if not line.endswith(b"\n") or len(line) > 8192:
                raise ValueError(f"boundary trace missing/truncated at {kind}:{position}")
            row = json.loads(line)
            if row.get("kind") != kind or row.get("bit_position") != position:
                raise ValueError(f"boundary coordinates differ at {kind}:{position}")
            if [part.get("name") for part in row.get("parts", [])] != list(PART_NAMES):
                raise ValueError("boundary state component population differs")
            for part in row["parts"]:
                if (type(part.get("offset")) is not int or type(part.get("bytes")) is not int or
                        part["offset"] < 0 or part["bytes"] < 0 or
                        part["offset"] + part["bytes"] > row["parts"][0]["bytes"] or
                        not isinstance(part.get("sha256"), str) or len(part["sha256"]) != 64 or
                        any(c not in "0123456789abcdef" for c in part["sha256"])):
                    raise ValueError("boundary component range/digest invalid")
            if any(type(row.get(name)) is not int or row[name] < 0 for name in (
                    "model_updates", "parent_updates", "midpoint_updates", "shadow_updates")):
                raise ValueError("boundary update counters invalid")
            yield row
        if source.read(1):
            raise ValueError("boundary trace has extra records")


def snapshot_records(path: Path):
    with bounded_input(path) as source:
        header = source.read(9)
        if header not in (b"MOSNAP01\0", b"MOSNAP01\1"):
            raise ValueError("snapshot header differs")
        if header[-1] == 0:
            if source.read(1):
                raise ValueError("disabled snapshots contain records")
            return
        for _ in range(6):  # initial + four 32-byte boundaries + final at <=129 bytes
            header = source.read(17)
            if not header:
                return
            if len(header) != 17:
                raise ValueError("truncated snapshot record header")
            kind, bit, size = struct.unpack("<BQQ", header)
            if kind > 2 or bit > 129 * 8 or size > 8 * 1024**2:
                raise ValueError("snapshot record exceeds fixture bounds")
            state = source.read(size)
            if len(state) != size:
                raise ValueError("snapshot record truncated")
            yield {"kind": ("initial", "boundary", "final")[kind], "bit_position": bit, "state": state}
        if source.read(1):
            raise ValueError("snapshot population exceeds fixture bound")


def validate_snapshot(row: dict, snapshot: dict) -> None:
    if (row["kind"], row["bit_position"]) != (snapshot["kind"], snapshot["bit_position"]):
        raise ValueError("snapshot boundary differs")
    state = snapshot["state"]
    if len(state) != row["parts"][0]["bytes"] or state[:5] != b"GMST\1":
        raise ValueError("snapshot envelope differs")
    for part in row["parts"]:
        block = state[part["offset"]:part["offset"] + part["bytes"]]
        if len(block) != part["bytes"] or hashlib.sha256(block).hexdigest() != part["sha256"]:
            raise ValueError("snapshot digest differs: " + part["name"])


def validate_bundle(directory: Path) -> dict:
    with bounded_input(directory / "summary.json") as source:
        summary = json.load(source)
    if summary.get("schema") != "midas_open_boundary_observer_v1":
        raise ValueError("observer summary schema differs")
    with bounded_input(directory / "probabilities.bin") as source:
        header = probability_header(source)
        while chunk := source.read(65536):
            if any(value == 0 for (value,) in struct.iter_unpack("<H", chunk)):
                raise ValueError("probability trace contains invalid Q16 zero")
    if summary["raw_bytes"] != header["raw_bytes"] or summary["probability_records"] != header["records"]:
        raise ValueError("summary probability counts differ")
    arm = summary.get("arm")
    if arm not in "PKFS" or len(arm) != 1 or header["archive_arm"] != (1 if arm == "F" else 2 if arm == "S" else 0):
        raise ValueError("summary arm differs from probability law")
    snapshots = snapshot_records(directory / "snapshots.bin")
    count = 0
    for row in boundary_rows(directory / "boundaries.jsonl", header["raw_bytes"]):
        n = row["bit_position"] // 8
        midpoint = n // 64 + int(n % 64 >= 32)
        expected = (n // 64 + (midpoint if arm in "FS" else 0), n // 64,
                    midpoint if arm in "FS" else 0, midpoint if arm == "K" else 0)
        if tuple(row[name] for name in ("model_updates", "parent_updates", "midpoint_updates", "shadow_updates")) != expected:
            raise ValueError("boundary counters differ from causal schedule")
        if summary["exact_snapshots"]:
            snapshot = next(snapshots, None)
            if snapshot is None:
                raise ValueError("mandatory exact snapshot missing")
            validate_snapshot(row, snapshot)
        count += 1
    if next(snapshots, None) is not None:
        raise ValueError("unexpected extra snapshot")
    if count != summary["boundary_records"]:
        raise ValueError("summary boundary count differs")
    records = {name: parent.file_record(directory / name) for name in FILES}
    for name, key in (("probabilities.bin", "probability_bytes"), ("boundaries.jsonl", "boundary_bytes"),
                      ("snapshots.bin", "snapshot_bytes"), ("state.bin", "state_bytes")):
        if records[name]["bytes"] != summary[key]:
            raise ValueError("summary artifact bytes differ: " + name)
    with bounded_input(directory / "state.bin") as source:
        final_state = source.read()
    if hashlib.sha256(final_state).hexdigest() != row["parts"][0]["sha256"]:
        raise ValueError("final boundary differs from final state")
    return {"summary": summary, "artifacts": records, "header": header}


def execute(built, *, operation: str, arm: str, max_raw_bytes: int, source: Path,
            output: Path, wall_seconds: int, snapshots: bool = False) -> dict:
    if operation not in ("encode", "decode") or arm not in tuple("PKFS"):
        raise ValueError("invalid codec operation/arm")
    if not 1 <= max_raw_bytes <= 250000 or not 1 <= wall_seconds <= 120:
        raise ValueError("explicit raw/wall bounds exceed observer limits")
    before = parent.verified_binary(built)
    command = [str(built.binary), operation, arm, str(max_raw_bytes), str(source), str(output),
               "snapshots" if snapshots else "digest"]
    start = time.monotonic()
    result = subprocess.run(command, capture_output=True, text=True, timeout=wall_seconds,
                            env={"PATH": os.defpath, "LC_ALL": "C", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    if parent.file_record(built.binary) != before:
        raise ValueError("observer executable changed during operation")
    if result.returncode:
        raise ValueError(f"observer process failed rc={result.returncode}: {result.stderr.strip()}")
    bundle = validate_bundle(output)
    if bundle["summary"] != json.loads(result.stdout):
        raise ValueError("observer stdout differs from published summary")
    return {"schema": "midas_open_boundary_observer_execution_v1", "bundle": bundle,
            "binary": before, "external_wall_seconds": time.monotonic() - start,
            "timing_scope": "shared-host whole codec including observation and publication; not kernel-only",
            "resource_qualified": False, "complete_package_bytes": None, "objective_credit_bytes": 0}


def _context(source, record: int, total: int) -> dict:
    start, end = max(0, record - 4), min(total, record + 5)
    source.seek(21 + 2 * start)
    return {"first_bit": start, "probabilities": [x[0] for x in struct.iter_unpack("<H", source.read(2 * (end - start)))]}


def _comparison(reference: Path, target: Path, projection: str) -> dict:
    if projection not in ("complete", "parent"):
        raise ValueError("comparison projection must be complete or parent")
    with bounded_input(reference / "probabilities.bin") as a, bounded_input(target / "probabilities.bin") as b:
        ah, bh = probability_header(a), probability_header(b)
        if ah != bh:
            return {"equal": False, "kind": "probability-identity", "reference": ah, "target": bh}
        offset = 0
        while left := a.read(65536):
            right = b.read(len(left))
            if left != right:
                first = next(i for i, pair in enumerate(zip(left, right)) if pair[0] != pair[1])
                bit = (offset + first) // 2
                return {"equal": False, "kind": "probability", "bit_position": bit,
                        "reference_context": _context(a, bit, ah["records"]),
                        "target_context": _context(b, bit, ah["records"])}
            offset += len(left)
    a_rows = boundary_rows(reference / "boundaries.jsonl", ah["raw_bytes"])
    b_rows = boundary_rows(target / "boundaries.jsonl", ah["raw_bytes"])
    previous = None
    while True:
        a, b = next(a_rows, None), next(b_rows, None)
        if a is None or b is None:
            if a is not b:
                raise ValueError("boundary population differs")
            break
        names = PART_NAMES if projection == "complete" else ("parent_identity_projection", "normalized_coder")
        ap, bp = ({p["name"]: (p["bytes"], p["sha256"]) for p in row["parts"]} for row in (a, b))
        differing = [name for name in names if ap[name] != bp[name]]
        if differing:
            after = {"reference": next(a_rows, None), "target": next(b_rows, None)}
            # Context contains actual adjacent boundary records; hashes are not
            # expanded into invented detailed state. Exact snapshots are separate.
            return {"equal": False, "kind": "boundary", "bit_position": a["bit_position"],
                    "boundary_kind": a["kind"], "components": differing, "previous": previous,
                    "current": {"reference": a, "target": b}, "next": after}
        previous = {"reference": a, "target": b}
    return {"equal": True, "probability_records": ah["records"],
            "boundary_records": ah["raw_bytes"] // 32 + 2,
            "claim_scope": "all pre-truth Q16 records and selected serialized-state SHA-256 witnesses; no unobserved state claim"}


def compare(reference: Path, target: Path, *, projection: str = "complete", diagnostic: Path | None = None) -> dict:
    try:
        result = _comparison(reference, target, projection)
        if result["equal"]:
            # Equality of two malformed traces cannot certify synchronization.
            # Validate both closed bundles before publishing a passing result;
            # preserve first-divergence context when their traces already differ.
            validate_bundle(reference)
            validate_bundle(target)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {"equal": False, "kind": "trace-completeness", "error": str(error)}
    result.update({"schema": "midas_open_boundary_comparison_v1", "reference_path": str(reference),
                   "target_path": str(target), "projection": projection, "objective_credit_bytes": 0})
    if diagnostic is not None:
        data = (json.dumps(result, sort_keys=True) + "\n").encode()
        if len(data) > 64 * 1024:
            raise ValueError("first-divergence diagnostic exceeds byte ceiling")
        # Exclusive atomic link publication also rejects an existing symlink.
        fd, name = tempfile.mkstemp(prefix=".midas-comparison-", dir=diagnostic.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.link(name, diagnostic)
        finally:
            os.unlink(name)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("build", "encode", "decode"):
        command = sub.add_parser(action)
        command.add_argument("--cache-dir", type=Path, required=True)
        if action != "build":
            command.add_argument("--arm", choices=tuple("PKFS"), required=True)
            command.add_argument("--max-raw-bytes", type=int, required=True)
            command.add_argument("--wall-seconds", type=int, required=True)
            command.add_argument("--input", type=Path, required=True)
            command.add_argument("--output-dir", type=Path, required=True)
            command.add_argument("--snapshots", action="store_true")
    command = sub.add_parser("compare")
    command.add_argument("--reference", type=Path, required=True)
    command.add_argument("--target", type=Path, required=True)
    command.add_argument("--projection", choices=("complete", "parent"), default="complete")
    command.add_argument("--diagnostic", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "compare":
            result = compare(args.reference, args.target, projection=args.projection, diagnostic=args.diagnostic)
        else:
            built = build(args.cache_dir)
            result = ({"binary": str(built.binary), "manifest": built.manifest, "cache_hit": built.cache_hit}
                      if args.action == "build" else execute(
                          built, operation=args.action, arm=args.arm, max_raw_bytes=args.max_raw_bytes,
                          source=args.input, output=args.output_dir, wall_seconds=args.wall_seconds,
                          snapshots=args.snapshots))
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("equal", True) else 1
    except (OSError, ValueError, parent.BuildCacheError, subprocess.SubprocessError) as error:
        print("midas_open_boundary_observer_v1: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
