#!/usr/bin/env python3
"""Probe segmented compression against single-stream compression.

This tool is an evaluator, not a candidate.  It answers whether splitting a
prefix into framed chunks helps a specific program or a small mixture of
programs.  Program size is counted once as the union of selected candidate
source payloads plus a small framing estimate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import struct
import time
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAMS = ROOT / "programs"
DATA_DEFAULT = ROOT / "data" / "enwik9"
OUT_DEFAULT = ROOT / "segmented_split_probe.json"
MAGIC = b"SG1\n"
WRAPPER_ESTIMATE_BYTES = 256


@dataclass
class Program:
    program_id: str
    module: Any
    program_size: int


def load_program(program_id: str) -> Program:
    program_dir = PROGRAMS / program_id
    path = program_dir / "program.py"
    if not path.exists():
        raise SystemExit(f"missing program.py: {path}")
    spec = importlib.util.spec_from_file_location(f"segprobe_{program_id}", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("compress", "decompress"):
        if not callable(getattr(module, name, None)):
            raise SystemExit(f"{program_id}: missing callable {name}()")
    size = 0
    for child in program_dir.iterdir():
        if child.name in ("meta.json", "__pycache__") or child.name.startswith("."):
            continue
        if child.is_file():
            size += child.stat().st_size
    return Program(program_id, module, size)


def equal_chunks(raw: bytes, count: int) -> list[bytes]:
    if count <= 0:
        raise SystemExit("--segments must be positive")
    n = len(raw)
    starts = [(n * index) // count for index in range(count)]
    starts.append(n)
    return [raw[starts[index] : starts[index + 1]] for index in range(count)]


def page_aligned_chunks(raw: bytes, count: int) -> list[bytes]:
    if count <= 1:
        return [raw]
    marker = b"<page>"
    n = len(raw)
    starts = [0]
    for index in range(1, count):
        target = (n * index) // count
        before = raw.rfind(marker, 0, target)
        after = raw.find(marker, target)
        choices = [pos for pos in (before, after) if pos > starts[-1] and pos >= 0]
        if choices:
            starts.append(min(choices, key=lambda pos: abs(pos - target)))
        else:
            starts.append(target)
    starts.append(n)
    starts = sorted(set(starts))
    return [raw[starts[index] : starts[index + 1]] for index in range(len(starts) - 1)]


def frame(chunks: list[tuple[int, bytes]]) -> bytes:
    out = bytearray(MAGIC)
    out += struct.pack(">I", len(chunks))
    for codec_index, payload in chunks:
        out += struct.pack(">BI", codec_index, len(payload))
        out += payload
    return bytes(out)


def unframe(blob: bytes) -> list[tuple[int, bytes]]:
    if not blob.startswith(MAGIC):
        raise ValueError("bad segmented magic")
    pos = len(MAGIC)
    (count,) = struct.unpack(">I", blob[pos : pos + 4])
    pos += 4
    chunks = []
    for _ in range(count):
        codec_index, size = struct.unpack(">BI", blob[pos : pos + 5])
        pos += 5
        chunks.append((codec_index, blob[pos : pos + size]))
        pos += size
    if pos != len(blob):
        raise ValueError("trailing bytes")
    return chunks


def compress_segment(programs: list[Program], chunk: bytes) -> tuple[int, bytes, list[dict[str, Any]]]:
    options = []
    for index, program in enumerate(programs):
        t0 = time.perf_counter()
        payload = program.module.compress(chunk)
        elapsed = time.perf_counter() - t0
        options.append(
            {
                "codec_index": index,
                "program_id": program.program_id,
                "compressed_size": len(payload),
                "compress_time_s": round(elapsed, 6),
                "payload": payload,
            }
        )
    best = min(options, key=lambda row: row["compressed_size"])
    visible = [{k: v for k, v in row.items() if k != "payload"} for row in options]
    return best["codec_index"], best["payload"], visible


def run(program_ids: list[str], raw: bytes, segments: int, boundary: str) -> dict[str, Any]:
    programs = [load_program(program_id) for program_id in program_ids]
    chunks = page_aligned_chunks(raw, segments) if boundary == "page" else equal_chunks(raw, segments)

    single_rows = []
    for index, program in enumerate(programs):
        payload = program.module.compress(raw)
        decoded = program.module.decompress(payload)
        single_rows.append(
            {
                "codec_index": index,
                "program_id": program.program_id,
                "archive_size": len(payload),
                "roundtrip_ok": decoded == raw,
                "program_size": program.program_size,
                "hutter_score": len(payload) + program.program_size,
            }
        )
    best_single = min(single_rows, key=lambda row: row["hutter_score"])

    framed_chunks: list[tuple[int, bytes]] = []
    chunk_rows = []
    for chunk_index, chunk in enumerate(chunks):
        codec_index, payload, options = compress_segment(programs, chunk)
        framed_chunks.append((codec_index, payload))
        chunk_rows.append(
            {
                "chunk": chunk_index,
                "raw_size": len(chunk),
                "selected_program": programs[codec_index].program_id,
                "selected_archive_size": len(payload),
                "options": options,
            }
        )

    archive = frame(framed_chunks)
    decoded_parts = [
        programs[codec_index].module.decompress(payload)
        for codec_index, payload in unframe(archive)
    ]
    decoded = b"".join(decoded_parts)
    used_indexes = sorted({codec_index for codec_index, _ in framed_chunks})
    program_union_size = sum(programs[index].program_size for index in used_indexes)
    estimated_program_size = program_union_size + WRAPPER_ESTIMATE_BYTES
    segmented_score = len(archive) + estimated_program_size

    return {
        "program_ids": program_ids,
        "boundary": boundary,
        "requested_segments": segments,
        "actual_segments": len(chunks),
        "data_size": len(raw),
        "data_md5": hashlib.md5(raw).hexdigest(),
        "data_sha256": hashlib.sha256(raw).hexdigest(),
        "single_stream": single_rows,
        "best_single_by_score": best_single,
        "segmented": {
            "archive_size": len(archive),
            "framing_overhead": len(archive) - sum(len(payload) for _, payload in framed_chunks),
            "program_union_size": program_union_size,
            "wrapper_estimate_bytes": WRAPPER_ESTIMATE_BYTES,
            "estimated_program_size": estimated_program_size,
            "estimated_hutter_score": segmented_score,
            "roundtrip_ok": decoded == raw,
            "used_programs": [programs[index].program_id for index in used_indexes],
            "score_delta_vs_best_single": segmented_score - best_single["hutter_score"],
            "archive_delta_vs_best_single": len(archive) - best_single["archive_size"],
        },
        "chunks": chunk_rows,
        "interpretation": (
            "Negative deltas mean segmentation helped. Positive deltas mean cold starts, "
            "framing, or extra decoder payload outweighed any per-chunk specialization."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("program_ids", nargs="+")
    parser.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    parser.add_argument("--limit", type=int, default=1_000_000)
    parser.add_argument("--segments", type=int, default=10)
    parser.add_argument("--boundary", choices=("equal", "page"), default="equal")
    parser.add_argument("--json-out", type=pathlib.Path, default=OUT_DEFAULT)
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"dataset missing: {args.data}")
    if args.limit <= 0:
        raise SystemExit("--limit must be positive")
    raw = args.data.read_bytes()[: args.limit]
    result = run(args.program_ids, raw, args.segments, args.boundary)
    args.json_out.write_text(json.dumps(result, indent=2) + "\n")

    seg = result["segmented"]
    best = result["best_single_by_score"]
    print(f"data_size={result['data_size']} segments={result['actual_segments']} boundary={args.boundary}")
    print(
        "best_single "
        f"program={best['program_id']} archive={best['archive_size']} "
        f"program_size={best['program_size']} score={best['hutter_score']}"
    )
    print(
        "segmented "
        f"archive={seg['archive_size']} estimated_program_size={seg['estimated_program_size']} "
        f"estimated_score={seg['estimated_hutter_score']} "
        f"score_delta={seg['score_delta_vs_best_single']} "
        f"archive_delta={seg['archive_delta_vs_best_single']} "
        f"roundtrip_ok={seg['roundtrip_ok']} "
        f"used={','.join(seg['used_programs'])}"
    )
    print(f"wrote {args.json_out}")
    return 0 if seg["roundtrip_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
