#!/usr/bin/env python3
"""Materialize and invert the frozen full-1G far-history residual transform."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import mmap
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "far_history_residual_container_qc0_v1"
EXPECTED_INPUT_BYTES = 1_000_000_000
EXPECTED_RECORDS = 584_693
EXPECTED_COPIED_BYTES = 64_526_086
CHUNK_BYTES = 8 << 20


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


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
    if shift:
        raise ValueError("truncated ULEB128 value")
    if len(values) != expected:
        raise ValueError(f"expected {expected} ULEBs, found {len(values)}")
    return values


def parse_ledger(compressed_path: Path) -> tuple[list[int], list[int], list[int], dict[str, int]]:
    payload = lzma.decompress(compressed_path.read_bytes())
    if len(payload) < 40 or payload[:8] != b"FHCLQ1\0\0":
        raise ValueError("invalid far-history ledger header")
    records, gap_size, distance_size, length_size = struct.unpack_from("<QQQQ", payload, 8)
    if records != EXPECTED_RECORDS:
        raise ValueError(f"unexpected ledger record count {records}")
    if 40 + gap_size + distance_size + length_size != len(payload):
        raise ValueError("ledger columns do not cover payload")
    gap_end = 40 + gap_size
    distance_end = gap_end + distance_size
    gaps = decode_ulebs(payload[40:gap_end], records)
    distances = decode_ulebs(payload[gap_end:distance_end], records)
    lengths = decode_ulebs(payload[distance_end:], records)
    return gaps, distances, lengths, {
        "records": records,
        "raw_bytes": len(payload),
        "gap_stream_bytes": gap_size,
        "distance_stream_bytes": distance_size,
        "length_stream_bytes": length_size,
    }


def hash_mmap_ranges(source: mmap.mmap, ranges: list[tuple[int, int]]) -> str:
    digest = hashlib.sha256()
    for start, end in ranges:
        for offset in range(start, end, CHUNK_BYTES):
            digest.update(source[offset:min(end, offset + CHUNK_BYTES)])
    return digest.hexdigest()


def write_mmap_range(output, source: mmap.mmap, start: int, end: int) -> None:
    for offset in range(start, end, CHUNK_BYTES):
        output.write(source[offset:min(end, offset + CHUNK_BYTES)])


def build_residual(input_path: Path, residual_path: Path, gaps: list[int],
                   distances: list[int], lengths: list[int]) -> dict[str, object]:
    literal_ranges: list[tuple[int, int]] = []
    copied = 0
    raw_position = 0
    with input_path.open("rb") as input_handle, residual_path.open("xb") as output:
        source = mmap.mmap(input_handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            for gap, distance, length in zip(gaps, distances, lengths, strict=True):
                target = raw_position + gap
                if target < raw_position or target + length > len(source):
                    raise ValueError("copy target outside canonical input")
                if distance <= 0 or distance > target or length > distance:
                    raise ValueError("copy source is not fully decoded")
                source_start = target - distance
                if source[source_start:source_start + length] != source[target:target + length]:
                    raise ValueError("ledger copy is not exact")
                literal_ranges.append((raw_position, target))
                write_mmap_range(output, source, raw_position, target)
                raw_position = target + length
                copied += length
            literal_ranges.append((raw_position, len(source)))
            write_mmap_range(output, source, raw_position, len(source))
            second_digest = hash_mmap_ranges(source, literal_ranges)
        finally:
            source.close()
    return {
        "copied_bytes": copied,
        "literal_bytes": residual_path.stat().st_size,
        "second_derivation_sha256": second_digest,
        "all_commands_exact_prior_and_closed": True,
    }


def reconstruct(residual_path: Path, restored_path: Path, gaps: list[int],
                distances: list[int], lengths: list[int]) -> dict[str, int | bool]:
    with residual_path.open("rb") as residual_handle, restored_path.open("xb+") as output_handle:
        residual = mmap.mmap(residual_handle.fileno(), 0, access=mmap.ACCESS_READ)
        output_handle.truncate(EXPECTED_INPUT_BYTES)
        output = mmap.mmap(output_handle.fileno(), EXPECTED_INPUT_BYTES, access=mmap.ACCESS_WRITE)
        residual_position = 0
        output_position = 0
        try:
            for gap, distance, length in zip(gaps, distances, lengths, strict=True):
                if residual_position + gap > len(residual):
                    raise ValueError("residual literal gap exceeds payload")
                for offset in range(0, gap, CHUNK_BYTES):
                    width = min(CHUNK_BYTES, gap - offset)
                    output[output_position + offset:output_position + offset + width] = \
                        residual[residual_position + offset:residual_position + offset + width]
                output_position += gap
                residual_position += gap
                if distance <= 0 or distance > output_position or length > distance:
                    raise ValueError("inverse copy source is not fully decoded")
                source = output_position - distance
                output[output_position:output_position + length] = output[source:source + length]
                output_position += length
            tail = len(residual) - residual_position
            for offset in range(0, tail, CHUNK_BYTES):
                width = min(CHUNK_BYTES, tail - offset)
                output[output_position + offset:output_position + offset + width] = \
                    residual[residual_position + offset:residual_position + offset + width]
            output_position += tail
            residual_position += tail
            output.flush()
        finally:
            output.close()
            residual.close()
    return {
        "consumed_residual_bytes": residual_position,
        "produced_raw_bytes": output_position,
        "residual_consumed_exactly": residual_position == residual_path.stat().st_size,
        "raw_size_exact": output_position == EXPECTED_INPUT_BYTES,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/enwik9")
    parser.add_argument(
        "--ledger",
        type=Path,
        default=ROOT / "results/far_history_cdc_collective_ledger_qm1_v1/ledger.lzma",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/results") / CANDIDATE_ID,
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    args.artifact_dir.mkdir(parents=True, exist_ok=False)

    if args.input.stat().st_size != EXPECTED_INPUT_BYTES:
        raise ValueError("input is not canonical full-1G size")
    gaps, distances, lengths, ledger = parse_ledger(args.ledger)
    residual_path = args.artifact_dir / "residual.bin"
    restored_path = args.artifact_dir / "restored.bin"
    transform = build_residual(args.input, residual_path, gaps, distances, lengths)
    inverse = reconstruct(residual_path, restored_path, gaps, distances, lengths)

    input_sha = sha256_file(args.input)
    residual_sha = sha256_file(residual_path)
    restored_sha = sha256_file(restored_path)
    source_paths = [
        Path(__file__),
        ROOT / "docs/far_history_residual_container_qc0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    ]
    source_blob = b"".join(path.name.encode() + b"\0" + path.read_bytes() for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_repeat = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = args.output_dir / "source_package.lzma"
    source_path.write_bytes(source_package)

    failed: list[str] = []
    if int(transform["copied_bytes"]) != EXPECTED_COPIED_BYTES:
        failed.append("copied_byte_count_mismatch")
    if int(transform["literal_bytes"]) + EXPECTED_COPIED_BYTES != EXPECTED_INPUT_BYTES:
        failed.append("residual_size_identity_failed")
    if str(transform["second_derivation_sha256"]) != residual_sha:
        failed.append("second_residual_derivation_mismatch")
    if not bool(inverse["residual_consumed_exactly"]) or not bool(inverse["raw_size_exact"]):
        failed.append("inverse_stream_consumption_failed")
    if restored_sha != input_sha:
        failed.append("canonical_reconstruction_failed")
    if source_package != source_repeat:
        failed.append("source_package_nondeterministic")
    if len(source_package) > 32_768:
        failed.append("compressed_source_above_32768")

    decision = {
        "schema": "enwiki9_far_history_residual_container_qc0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "full_corpus_reversible_transform_zero_credit",
        "verdict": "authorize_backend_integration" if not failed else "retire_residual_transform",
        "inputs": {
            "canonical_input": artifact(args.input),
            "compressed_ledger": artifact(args.ledger),
            "parent_qm1_decision": artifact(ROOT / "results/far_history_cdc_collective_ledger_qm1_v1/decision.json"),
        },
        "ledger": ledger,
        "transform": transform,
        "inverse": inverse,
        "artifacts": {
            "residual": artifact(residual_path),
            "restored": artifact(restored_path),
            "source_package": artifact(source_path),
        },
        "proof": {
            "ledger_population_frozen_from_qm1": True,
            "all_commands_exact_prior_and_closed": bool(transform["all_commands_exact_prior_and_closed"]),
            "second_residual_derivation_matches": str(transform["second_derivation_sha256"]) == residual_sha,
            "canonical_reconstruction_exact": restored_sha == input_sha,
            "source_package_deterministic": source_package == source_repeat,
        },
        "accounting": {
            "compressed_source_package_bytes": len(source_package),
            "compressed_backend_bytes": None,
            "score_credit_bytes": 0,
            "published_nncp_archive_bytes_external_context": 106_632_363,
            "published_nncp_program_bytes_external_context": 628_955,
        },
        "failed_conditions": failed,
        "claim_boundary": "Exact substrate-independent full-corpus transform and inverse only. The residual is uncompressed, the NNCP values are external context, and this receipt establishes no backend archive, forecast, runtime eligibility, or official score.",
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": decision["verdict"],
        "residual_bytes": residual_path.stat().st_size,
        "residual_sha256": residual_sha,
        "restored_sha256": restored_sha,
        "source_package_bytes": len(source_package),
        "failed_conditions": failed,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
