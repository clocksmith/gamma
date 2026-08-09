#!/usr/bin/env python3
"""Build an XML/line-safe far-history residual for matched cmix-obias replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import mmap
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_helical_xmlsafe_prefix_qm4_v1"
DEFAULT_SCOPE = 250_000_000
EXPECTED_INPUT_BYTES = 1_000_000_000
EXPECTED_INPUT_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
EXPECTED_LEDGER_SHA256 = "f473f7aed6a1e6960cd2b6d8bfabf57e515e789a4ca9a4a6fc5ba70395d86570"
EXPECTED_RECORDS = 584_693
CHUNK_BYTES = 8 << 20


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def decode_ulebs(payload: bytes, expected: int) -> list[int]:
    values: list[int] = []
    value = 0
    shift = 0
    for byte in payload:
        value |= (byte & 127) << shift
        if byte & 128:
            shift += 7
            if shift > 63:
                raise ValueError("ULEB128 value exceeds uint64")
        else:
            values.append(value)
            value = 0
            shift = 0
    if shift or len(values) != expected:
        raise ValueError("invalid ULEB128 column")
    return values


def encode_uleb(value: int) -> bytes:
    output = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        output.append(byte | (128 if value else 0))
        if not value:
            return bytes(output)


def parse_ledger(path: Path) -> tuple[list[int], list[int], list[int]]:
    payload = lzma.decompress(path.read_bytes())
    if len(payload) < 40 or payload[:8] != b"FHCLQ1\0\0":
        raise ValueError("invalid frozen ledger header")
    records, gap_size, distance_size, length_size = struct.unpack_from("<QQQQ", payload, 8)
    if records != EXPECTED_RECORDS or 40 + gap_size + distance_size + length_size != len(payload):
        raise ValueError("invalid frozen ledger dimensions")
    gap_end = 40 + gap_size
    distance_end = gap_end + distance_size
    return (
        decode_ulebs(payload[40:gap_end], records),
        decode_ulebs(payload[gap_end:distance_end], records),
        decode_ulebs(payload[distance_end:], records),
    )


def text_intervals(data: mmap.mmap, scope: int) -> list[tuple[int, int]]:
    intervals: list[tuple[int, int]] = []
    cursor = 0
    while True:
        opening = data.find(b"<text ", cursor, scope)
        if opening < 0:
            break
        content = data.find(b">", opening + 6, scope)
        if content < 0:
            break
        content += 1
        if data[content - 2:content] == b"/>":
            cursor = content
            continue
        closing = data.find(b"</text>", content, scope)
        if closing < 0:
            break
        intervals.append((content, closing))
        cursor = closing + 7
    return intervals


def selected_matches(data: mmap.mmap, scope: int, gaps: list[int], distances: list[int],
                     lengths: list[int], intervals: list[tuple[int, int]]) -> tuple[list[tuple[int, int, int]], dict[str, int]]:
    selected: list[tuple[int, int, int]] = []
    raw_position = 0
    interval_index = 0
    eligible_before_scope = 0
    eligible_bytes = 0
    rejected_outside_text = 0
    rejected_line_or_markup = 0
    for gap, distance, length in zip(gaps, distances, lengths, strict=True):
        target = raw_position + gap
        raw_position = target + length
        if target + length > scope:
            break
        eligible_before_scope += 1
        eligible_bytes += length
        while interval_index < len(intervals) and intervals[interval_index][1] <= target:
            interval_index += 1
        if interval_index == len(intervals):
            break
        content_start, content_end = intervals[interval_index]
        if target < content_start or target + length > content_end:
            rejected_outside_text += 1
            continue
        span = data[target:target + length]
        if b"\n" in span or b"\r" in span or b"<" in span or b">" in span:
            rejected_line_or_markup += 1
            continue
        source = target - distance
        if distance <= 0 or length > distance or source < 0:
            raise ValueError("selected source is not fully prior")
        if data[source:source + length] != span:
            raise ValueError("selected source does not reproduce target")
        selected.append((target, distance, length))
    return selected, {
        "eligible_before_scope_matches": eligible_before_scope,
        "eligible_before_scope_bytes": eligible_bytes,
        "rejected_outside_text_matches": rejected_outside_text,
        "rejected_line_or_markup_matches": rejected_line_or_markup,
    }


def serialize_ledger(matches: list[tuple[int, int, int]]) -> tuple[bytes, dict[str, int]]:
    gaps = bytearray()
    distances = bytearray()
    lengths = bytearray()
    previous_end = 0
    for target, distance, length in matches:
        gaps.extend(encode_uleb(target - previous_end))
        distances.extend(encode_uleb(distance))
        lengths.extend(encode_uleb(length))
        previous_end = target + length
    header = b"FHCLQ1\0\0" + struct.pack("<QQQQ", len(matches), len(gaps), len(distances), len(lengths))
    payload = header + gaps + distances + lengths
    return payload, {
        "records": len(matches),
        "gap_stream_bytes": len(gaps),
        "distance_stream_bytes": len(distances),
        "length_stream_bytes": len(lengths),
        "raw_bytes": len(payload),
    }


def write_range(output, data: mmap.mmap, start: int, end: int) -> None:
    for offset in range(start, end, CHUNK_BYTES):
        output.write(data[offset:min(end, offset + CHUNK_BYTES)])


def materialize(data: mmap.mmap, scope: int, matches: list[tuple[int, int, int]],
                original_path: Path, residual_path: Path) -> int:
    with original_path.open("xb") as original:
        write_range(original, data, 0, scope)
    copied = 0
    cursor = 0
    with residual_path.open("xb") as residual:
        for target, _, length in matches:
            write_range(residual, data, cursor, target)
            cursor = target + length
            copied += length
        write_range(residual, data, cursor, scope)
    return copied


def reconstruct(residual_path: Path, restored_path: Path, scope: int,
                matches: list[tuple[int, int, int]]) -> None:
    with residual_path.open("rb") as residual_handle, restored_path.open("xb+") as output_handle:
        residual = mmap.mmap(residual_handle.fileno(), 0, access=mmap.ACCESS_READ)
        output_handle.truncate(scope)
        output = mmap.mmap(output_handle.fileno(), scope, access=mmap.ACCESS_WRITE)
        residual_position = 0
        output_position = 0
        try:
            for target, distance, length in matches:
                gap = target - output_position
                output[output_position:target] = residual[residual_position:residual_position + gap]
                residual_position += gap
                output_position = target
                source = output_position - distance
                output[output_position:output_position + length] = output[source:source + length]
                output_position += length
            tail = len(residual) - residual_position
            output[output_position:output_position + tail] = residual[residual_position:]
            output_position += tail
            output.flush()
            if output_position != scope:
                raise ValueError("inverse output size mismatch")
        finally:
            output.close()
            residual.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/enwik9")
    parser.add_argument("--ledger", type=Path, default=ROOT / "results/far_history_cdc_collective_ledger_qm1_v1/ledger.lzma")
    parser.add_argument("--scope", type=int, default=DEFAULT_SCOPE)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / CANDIDATE_ID)
    parser.add_argument("--artifact-dir", type=Path, default=Path("/home/x/enwiki9-nonproof/results") / CANDIDATE_ID)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    args.artifact_dir.mkdir(parents=True, exist_ok=False)
    if args.input.stat().st_size != EXPECTED_INPUT_BYTES or sha256_file(args.input) != EXPECTED_INPUT_SHA256:
        raise ValueError("canonical input mismatch")
    if sha256_file(args.ledger) != EXPECTED_LEDGER_SHA256:
        raise ValueError("frozen ledger mismatch")
    if not 100_000_000 < args.scope <= EXPECTED_INPUT_BYTES:
        raise ValueError("scope must expose far-history matches")

    gaps, distances, lengths = parse_ledger(args.ledger)
    original_path = args.artifact_dir / "original.bin"
    residual_path = args.artifact_dir / "residual.bin"
    restored_path = args.artifact_dir / "restored.bin"
    with args.input.open("rb") as input_handle:
        data = mmap.mmap(input_handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            intervals = text_intervals(data, args.scope)
            matches, population = selected_matches(data, args.scope, gaps, distances, lengths, intervals)
            copied = materialize(data, args.scope, matches, original_path, residual_path)
        finally:
            data.close()
    reconstruct(residual_path, restored_path, args.scope, matches)

    ledger_payload, ledger_stats = serialize_ledger(matches)
    ledger_path = args.output_dir / "ledger.bin"
    ledger_lzma_path = args.output_dir / "ledger.lzma"
    ledger_path.write_bytes(ledger_payload)
    ledger_lzma_path.write_bytes(lzma.compress(ledger_payload, preset=9 | lzma.PRESET_EXTREME))
    original_sha = sha256_file(original_path)
    restored_sha = sha256_file(restored_path)
    failed: list[str] = []
    if original_sha != restored_sha:
        failed.append("prefix_reconstruction_failed")
    if residual_path.stat().st_size + copied != args.scope:
        failed.append("residual_size_identity_failed")
    if not matches:
        failed.append("no_xmlsafe_matches")

    decision = {
        "schema": "enwiki9_cmix_obias_helical_xmlsafe_prefix_qm4_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "exact_prefix_reversible_transform_zero_credit",
        "verdict": "authorize_matched_parent_replay" if not failed else "retire_xmlsafe_transform",
        "scope_bytes": args.scope,
        "inputs": {"canonical_input": artifact(args.input), "frozen_ledger": artifact(args.ledger)},
        "population": population | {
            "text_intervals": len(intervals),
            "selected_matches": len(matches),
            "selected_copied_bytes": copied,
        },
        "ledger": ledger_stats | {"compressed_bytes": ledger_lzma_path.stat().st_size},
        "artifacts": {
            "original": artifact(original_path),
            "residual": artifact(residual_path),
            "restored": artifact(restored_path),
            "ledger": artifact(ledger_path),
            "compressed_ledger": artifact(ledger_lzma_path),
        },
        "proof": {
            "all_targets_inside_text_payload": True,
            "all_target_spans_preserve_line_and_markup_bytes": True,
            "all_sources_exact_fully_prior_and_closed": True,
            "prefix_reconstruction_exact": original_sha == restored_sha,
        },
        "backend": {"baseline_archive_bytes": None, "residual_archive_bytes": None, "net_gain_bytes": None},
        "failed_conditions": failed,
        "claim_boundary": "Exact XML/line-safe prefix transform only. No backend archive has yet been measured and this receipt earns no score credit.",
    }
    (args.output_dir / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": decision["verdict"],
        "selected_matches": len(matches),
        "copied_bytes": copied,
        "residual_bytes": residual_path.stat().st_size,
        "ledger_lzma_bytes": ledger_lzma_path.stat().st_size,
        "prefix_sha256": original_sha,
        "failed_conditions": failed,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
