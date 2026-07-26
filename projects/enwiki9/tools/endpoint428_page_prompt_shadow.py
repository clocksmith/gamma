#!/usr/bin/env python3
"""Run SIBYL V0 exact page-prompt calibration on a pinned P1 trace."""

from __future__ import annotations

import argparse
from bisect import bisect_left
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
from typing import Any

from wrt_exact import detect_storage_header, parse_store


ROOT = Path(__file__).resolve().parents[1]
CPP = Path(__file__).with_suffix(".cpp")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def fnv64(value: bytes) -> int:
    state = 0xCBF29CE484222325
    for byte in value:
        state ^= byte
        state = (state * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return state


def all_offsets(value: bytes, marker: bytes) -> list[int]:
    rows: list[int] = []
    cursor = 0
    while True:
        found = value.find(marker, cursor)
        if found < 0:
            return rows
        rows.append(found)
        cursor = found + 1


def prompt_segments(parsed) -> list[tuple[int, int, int, int]]:
    raw = parsed.decoded
    starts = all_offsets(raw, b"<page>")
    closes = all_offsets(raw, b"</page>")
    event_raw_ends: list[int] = []
    event_wrt_ends: list[int] = []
    raw_cursor = 0
    for event in parsed.events:
        raw_cursor += len(event.decoded)
        if event.decoded:
            event_raw_ends.append(raw_cursor)
            event_wrt_ends.append(event.end * 8)

    def row_after_raw(raw_end: int) -> int:
        if raw_end >= len(raw):
            return len(parsed.stream) * 8
        index = bisect_left(event_raw_ends, raw_end)
        if index >= len(event_wrt_ends):
            return len(parsed.stream) * 8
        return event_wrt_ends[index]

    segments: list[tuple[int, int, int, int]] = []
    close_index = 0
    for page_index, start in enumerate(starts):
        while close_index < len(closes) and closes[close_index] < start:
            close_index += 1
        raw_end = (
            closes[close_index] + len(b"</page>")
            if close_index < len(closes)
            else len(raw)
        )
        if close_index < len(closes):
            close_index += 1
        title_open = raw.find(b"<title>", start, raw_end)
        title_close = raw.find(b"</title>", start, raw_end)
        if title_open < 0 or title_close < 0:
            continue
        title = raw[title_open + len(b"<title>") : title_close]
        prompt_start = row_after_raw(title_close + len(b"</title>"))
        page_end = row_after_raw(raw_end)
        if prompt_start > page_end:
            raise RuntimeError("page prompt begins after page end")
        title_feature = fnv64(
            bytes([min(len(title) // 8, 31)])
            + title[:1].lower()
            + bytes([sum(byte >= 128 for byte in title) > 0])
        )
        segments.append((prompt_start, page_end, title_feature, page_index))
    return segments


def write_segments(path: Path, rows: list[tuple[int, int, int, int]]) -> None:
    with path.open("wb") as output:
        output.write(struct.pack("<Q", len(rows)))
        for row in rows:
            output.write(struct.pack("<QQQQ", *row))


def compile_helper(binary: Path) -> list[str]:
    command = [
        "g++",
        "-O3",
        "-std=c++17",
        "-DNDEBUG",
        str(CPP),
        "-o",
        str(binary),
    ]
    subprocess.run(command, check=True, cwd=ROOT.parent.parent)
    return command


def run(args: argparse.Namespace) -> dict[str, Any]:
    parsed = parse_store(args.store, args.dictionary)
    raw = args.raw.read_bytes()
    if raw[: parsed.raw_length] != parsed.decoded:
        raise RuntimeError("WRT stream does not reconstruct the pinned raw population")
    stored = args.store.read_bytes()
    header_bytes = detect_storage_header(stored)
    segments = prompt_segments(parsed)
    with tempfile.TemporaryDirectory(prefix="sibyl-v0-") as temporary:
        temporary_path = Path(temporary)
        segment_path = temporary_path / "segments.bin"
        helper_path = temporary_path / "sibyl_helper"
        helper_output = temporary_path / "helper.json"
        write_segments(segment_path, segments)
        compile_command = compile_helper(helper_path)
        helper_command = [
            str(helper_path),
            str(args.store.resolve()),
            str(header_bytes),
            str(args.p1.resolve()),
            str(segment_path),
            str(helper_output),
        ]
        subprocess.run(helper_command, check=True, cwd=ROOT.parent.parent)
        exact = json.loads(helper_output.read_text())
        helper_sha256 = digest(helper_path)

    gross = exact["saved_bytes"]["Z16_GROSS"]
    net = exact["saved_bytes"]["Z16"]
    if gross < args.gross_gate_bytes:
        verdict = "retire_simple_page_calibration_gross_gate_miss"
    elif net < args.net_gate_bytes:
        verdict = "retire_simple_page_calibration_net_gate_miss"
    else:
        verdict = "mechanism_positive_requires_frozen_offset_transfer"
    source_bytes = CPP.stat().st_size + Path(__file__).stat().st_size
    return {
        "schema": "endpoint428_page_prompt_shadow_v0",
        "candidate_id": "endpoint428_page_prompt_calibration_v0",
        "evidence_level": "exact_arithmetic_trace_shadow_zero_score_credit",
        "trace_classification": args.trace_classification,
        "inputs": {
            "raw": artifact(args.raw),
            "wrt_store": artifact(args.store),
            "dictionary": artifact(args.dictionary),
            "p1": artifact(args.p1),
            "trace_receipt": artifact(args.trace_receipt),
            "storage_header_bytes": header_bytes,
        },
        "scope": {
            "raw_bytes": parsed.raw_length,
            "wrt_stream_bytes": len(parsed.stream),
            "p1_rows": len(parsed.stream) * 8,
            "started_pages": parsed.decoded.count(b"<page>"),
            "promptable_pages": len(segments),
            "prompt_position": "after complete title WRT event and before remaining page payload",
        },
        "controls": {
            "Z0": "unchanged final P1 trace",
            "Z1": "one curve selected on page-index-mod-5 development pages",
            "Z16_GROSS": "sixteen-choice whole-page oracle without label cost",
            "Z16": "sixteen-choice oracle with adaptive exact four-bit page labels",
            "ZR": "rotated oracle labels with the same label multiset",
            "ZP": "title-feature prompt predicted from prior completed page oracle labels",
        },
        "exact_replay": exact,
        "economics": {
            "design_target_bytes": 108_000_000,
            "planning_baseline_bytes": 109_524_268,
            "design_debt_bytes": 1_524_268,
            "gross_gate_bytes_at_10m": args.gross_gate_bytes,
            "net_gate_bytes_at_10m": args.net_gate_bytes,
            "gross_saved_bytes": gross,
            "net_saved_bytes_before_source_amortization": net,
            "provisional_source_bytes": source_bytes,
            "source_amortization_bytes_at_10m": source_bytes / 100.0,
            "net_after_source_amortization_screen": net - source_bytes / 100.0,
        },
        "construction": {
            "helper_compile_command": compile_command,
            "helper_binary_sha256": helper_sha256,
            "integer_probability_tables": True,
            "exact_arithmetic_label_and_payload_interleaving": True,
            "underlying_model_trajectory_unchanged": True,
        },
        "verdict": verdict,
        "promotion_authorized": False,
        "score_credit_bytes": 0,
        "claim_boundary": (
            "This is an exact arithmetic replay over a hash-pinned probability trace. "
            "Its current trace classification must not be upgraded to endpoint428 "
            "evidence. Native integration, transmitted codebook/source accounting, "
            "offset transfer, roundtrip, determinism, resources, runtime, and full "
            "1G proof remain."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--p1", type=Path, required=True)
    parser.add_argument("--trace-receipt", type=Path, required=True)
    parser.add_argument("--trace-classification", required=True)
    parser.add_argument("--gross-gate-bytes", type=int, default=30_000)
    parser.add_argument("--net-gate-bytes", type=int, default=23_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path in (
        args.raw,
        args.store,
        args.dictionary,
        args.p1,
        args.trace_receipt,
    ):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                "gross_saved_bytes": receipt["economics"]["gross_saved_bytes"],
                "net_saved_bytes": receipt["economics"][
                    "net_saved_bytes_before_source_amortization"
                ],
                "trace_classification": receipt["trace_classification"],
                "verdict": receipt["verdict"],
                "score_credit_bytes": 0,
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
