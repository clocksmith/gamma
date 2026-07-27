#!/usr/bin/env python3
"""Build the frozen AF-1 source closure and certify an exact P1 trace."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import lzma
import os
import pathlib
import struct
import subprocess
import tarfile
import tempfile
import time
from datetime import datetime, timezone


MAGIC = b"AF1P1V1\0"
HEADER_BYTES = 32
ROW_BYTES = 3
TOTAL = 1 << 16
MASK32 = (1 << 32) - 1
FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
FLAGS = (
    "-std=c++14 -Wall -O3 "
    "-DCMIX_PAQ8_LEVEL=5 "
    "-DCMIX_PPMD_MEMORY_MB=21 -DCMIX_PPMD_MEMORY_KB=20352 "
    "-DCMIX_PAQ8_MAIN_CONTEXT_SCALE=1 -DCMIX_PAQ8_MAIN_CONTEXT_DIV=1 "
    "-DCMIX_PAQ8_TEXT_MODEL_SCALE=1 -DCMIX_PAQ8_TEXT_MODEL_DIV=1 "
    "-DCMIX_PAQ8_MATCH_SCALE=1 -DCMIX_PAQ8_MATCH_DIV=1 "
    "-DCMIX_PAQ8_SPARSE_MATCH_DIV=8 -DCMIX_PAQ8_RCM_DIV=32 "
    "-DCMIX_PAQ8_BUF_SCALE=1 -DCMIX_PAQ8_BUF_DIV=32 "
    "-DCMIX_FXCM_CMC2_DIV=1 -DCMIX_FXCM_RCM_DIV=20 "
    "-DCMIX_FXCM_MHASH_DIV=1 -DCMIX_FXCM_CMC2_IDX13_DIV=2 "
    "-DCMIX_FXCM_CMC2_ASSOC=10 -DCMIX_AF1_P1_TRACE=1"
)


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: pathlib.Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def extract_closure(payload: pathlib.Path, destination: pathlib.Path) -> None:
    raw = lzma.decompress(
        payload.read_bytes(), format=lzma.FORMAT_RAW, filters=FILTERS
    )
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        members = archive.getmembers()
        for member in members:
            path = pathlib.PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not member.isfile():
                raise ValueError("unsafe source-closure member")
        archive.extractall(destination)


def run_codec(
    binary: pathlib.Path,
    dictionary: pathlib.Path,
    mode: str,
    source: pathlib.Path,
    destination: pathlib.Path,
    work: pathlib.Path,
    trace: pathlib.Path | None = None,
) -> float:
    environment = os.environ.copy()
    environment["CMIX_MMAP_ALLOC"] = "1"
    environment["CMIX_MMAP_DIR"] = str(work)
    if trace is None:
        environment.pop("CMIX_AF1_P1_TRACE", None)
    else:
        environment["CMIX_AF1_P1_TRACE"] = str(trace.resolve())
    start = time.monotonic()
    subprocess.run(
        [str(binary), mode, str(dictionary), str(source), str(destination)],
        cwd=work,
        env=environment,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return time.monotonic() - start


def archive_payload(data: bytes) -> tuple[bytes, int, int]:
    if len(data) < 6:
        raise ValueError("archive is truncated")
    wrt_bytes = data[0] & 0x7F
    for value in data[1:5]:
        wrt_bytes = (wrt_bytes << 8) | value
    header_bytes = 5 if wrt_bytes < 10_000 else 37
    if len(data) <= header_bytes:
        raise ValueError("archive has no arithmetic payload")
    return data[header_bytes:], header_bytes, wrt_bytes


def read_trace_header(path: pathlib.Path) -> int:
    with path.open("rb") as source:
        header = source.read(HEADER_BYTES)
    if len(header) != HEADER_BYTES or header[:8] != MAGIC:
        raise ValueError("invalid AF-1 P1 trace header")
    version, header_bytes, row_bytes, total = struct.unpack_from(
        "<IIII", header, 8
    )
    rows = struct.unpack_from("<Q", header, 24)[0]
    if (
        version != 1
        or header_bytes != HEADER_BYTES
        or row_bytes != ROW_BYTES
        or total != TOTAL
        or rows == 0
    ):
        raise ValueError("unsupported AF-1 P1 trace contract")
    if path.stat().st_size != HEADER_BYTES + rows * ROW_BYTES:
        raise ValueError("AF-1 P1 trace length mismatch")
    return rows


def replay_trace(path: pathlib.Path) -> bytes:
    rows = read_trace_header(path)
    x1 = 0
    x2 = MASK32
    output = bytearray()
    with path.open("rb") as source:
        source.seek(HEADER_BYTES)
        remaining = rows
        while remaining:
            count = min(remaining, 1 << 20)
            data = source.read(count * ROW_BYTES)
            if len(data) != count * ROW_BYTES:
                raise ValueError("truncated AF-1 P1 trace")
            for offset in range(0, len(data), ROW_BYTES):
                bit = data[offset]
                probability = data[offset + 1] | (data[offset + 2] << 8)
                if bit > 1 or probability == 0:
                    raise ValueError("invalid AF-1 P1 trace row")
                delta = x2 - x1
                midpoint = x1 + (delta >> 16) * probability
                midpoint += ((delta & 0xFFFF) * probability) >> 16
                if bit:
                    x2 = midpoint
                else:
                    x1 = midpoint + 1
                while ((x1 ^ x2) & 0xFF000000) == 0:
                    output.append((x2 >> 24) & 0xFF)
                    x1 = (x1 << 8) & MASK32
                    x2 = ((x2 << 8) & MASK32) + 255
            remaining -= count
    while ((x1 ^ x2) & 0xFF000000) == 0:
        output.append((x2 >> 24) & 0xFF)
        x1 = (x1 << 8) & MASK32
        x2 = ((x2 << 8) & MASK32) + 255
    output.append((x2 >> 24) & 0xFF)
    return bytes(output)


def run(args: argparse.Namespace) -> dict[str, object]:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = args.output_dir / "archive.bin"
    trace_path = args.output_dir / "p1_trace.bin"
    with tempfile.TemporaryDirectory(prefix="af1-p1-gate-") as raw:
        temporary = pathlib.Path(raw)
        extract_closure(args.source_package, temporary)
        source = temporary / "cmix21"
        subprocess.run(
            ["patch", "-p1", "-i", str(args.patch.resolve())],
            cwd=source,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        build_start = time.monotonic()
        subprocess.run(
            ["make", "-C", str(source), "cmix", "CXX=g++", f"LFLAGS={FLAGS}"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        build_seconds = time.monotonic() - build_start
        prefix = temporary / "input"
        with args.input.open("rb") as source_input:
            prefix.write_bytes(source_input.read(args.limit))
        if prefix.stat().st_size != args.limit:
            raise ValueError("input is shorter than requested limit")
        off_work = temporary / "off"
        on_work = temporary / "on"
        decode_work = temporary / "decode"
        off_work.mkdir()
        on_work.mkdir()
        decode_work.mkdir()
        archive_off = temporary / "archive_off"
        archive_on = temporary / "archive_on"
        decoded = temporary / "decoded"
        off_seconds = run_codec(
            source / "cmix",
            source / "english.dic",
            "-t",
            prefix,
            archive_off,
            off_work,
        )
        on_seconds = run_codec(
            source / "cmix",
            source / "english.dic",
            "-t",
            prefix,
            archive_on,
            on_work,
            trace_path,
        )
        decode_seconds = run_codec(
            source / "cmix",
            source / "english.dic",
            "-d",
            archive_on,
            decoded,
            decode_work,
        )
        archive_identity = archive_off.read_bytes() == archive_on.read_bytes()
        roundtrip = decoded.read_bytes() == prefix.read_bytes()
        if not archive_identity or not roundtrip:
            raise ValueError("observer changed archive or roundtrip")
        archive_path.write_bytes(archive_on.read_bytes())

    payload, header_bytes, wrt_bytes = archive_payload(archive_path.read_bytes())
    rows = read_trace_header(trace_path)
    replay = replay_trace(trace_path)
    replay_identity = replay == payload
    row_identity = rows == wrt_bytes * 8
    if not replay_identity or not row_identity:
        raise ValueError("trace does not reproduce the arithmetic payload")
    receipt = {
        "schema": "af1_p1_trace_gate_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "af1_paid_block_vector_codebook_v1",
        "evidence_tier": "causal_shadow",
        "claim_boundary": (
            "Observation-only exact P1 trace. It changes no probability and "
            "receives zero score credit."
        ),
        "inputs": {
            "source_package": artifact(args.source_package),
            "patch": artifact(args.patch),
            "input": artifact(args.input),
            "raw_prefix_bytes": args.limit,
        },
        "outputs": {
            "archive": artifact(archive_path),
            "trace": artifact(trace_path),
            "archive_header_bytes": header_bytes,
            "arithmetic_payload_bytes": len(payload),
            "wrt_bytes": wrt_bytes,
            "trace_rows": rows,
        },
        "identity": {
            "trace_on_off_archive_identity": archive_identity,
            "roundtrip_ok": roundtrip,
            "trace_rows_equal_wrt_bits": row_identity,
            "trace_replay_payload_identity": replay_identity,
            "replay_payload_sha256": hashlib.sha256(replay).hexdigest(),
            "archive_payload_sha256": hashlib.sha256(payload).hexdigest(),
        },
        "runtime_seconds": {
            "build": build_seconds,
            "trace_off_compress": off_seconds,
            "trace_on_compress": on_seconds,
            "decompress": decode_seconds,
        },
        "score_credit_bytes": 0,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def parse_args() -> argparse.Namespace:
    project = pathlib.Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-package",
        type=pathlib.Path,
        default=project
        / "programs/cmix21_b2_source_closure_rawlzma2_v1/source.tar.raw",
    )
    parser.add_argument(
        "--patch",
        type=pathlib.Path,
        default=project / "patches/af1_p1_trace_v1.patch",
    )
    parser.add_argument(
        "--input", type=pathlib.Path, default=project / "data/enwik9"
    )
    parser.add_argument("--limit", type=int, default=1_000_000)
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=project / "results/af1_paid_block_vector_codebook_v1",
    )
    parser.add_argument(
        "--receipt",
        type=pathlib.Path,
        default=project
        / "results/af1_paid_block_vector_codebook_v1/trace_receipt.json",
    )
    return parser.parse_args()


def main() -> int:
    result = run(parse_args())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

