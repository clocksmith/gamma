#!/usr/bin/env python3
"""Price a literal side ledger for the frozen QM4 residual."""

from __future__ import annotations

import hashlib
import json
import lzma
import mmap
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_helical_xmlsafe_literal_ledger_control_qm4_v1"
SCOPE = 250_000_000
CHUNK_BYTES = 8 << 20
COPY_RESULT = ROOT / "results/cmix_obias_helical_xmlsafe_prefix_qm4_v1"
ARTIFACT_ROOT = Path("/home/x/enwiki9-nonproof/results/cmix_obias_helical_xmlsafe_prefix_qm4_v1")
OUTPUT_DIR = ROOT / "results" / CANDIDATE_ID
ARTIFACT_DIR = Path("/home/x/enwiki9-nonproof/results") / CANDIDATE_ID
EXPECTED_ORIGINAL_SHA256 = "ba261e954bbbbad2e07b46936263250e6132a82b9ab1b05041b79510e6959de8"
EXPECTED_RESIDUAL_SHA256 = "e550869c0870630f70da36fb472f056375eaf1dfc0962b4730e3fe6caadd7ba4"
EXPECTED_COPY_LEDGER_SHA256 = "162eb2ef76dc13a84f8860aa6c0ca9847605c6df43a6635c0352ab62b02189ce"
EXPECTED_RECORDS = 5_967
EXPECTED_LITERAL_BYTES = 592_920


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


def parse_copy_ledger(path: Path) -> tuple[bytes, bytes, list[int], list[int]]:
    payload = path.read_bytes()
    if len(payload) < 40 or payload[:8] != b"FHCLQ1\0\0":
        raise ValueError("invalid copy ledger header")
    records, gap_size, distance_size, length_size = struct.unpack_from("<QQQQ", payload, 8)
    if records != EXPECTED_RECORDS or 40 + gap_size + distance_size + length_size != len(payload):
        raise ValueError("invalid copy ledger dimensions")
    gap_end = 40 + gap_size
    distance_end = gap_end + distance_size
    gap_column = payload[40:gap_end]
    length_column = payload[distance_end:]
    return (
        gap_column,
        length_column,
        decode_ulebs(gap_column, records),
        decode_ulebs(length_column, records),
    )


def build_literal_ledger(original_path: Path, gap_column: bytes, length_column: bytes,
                         gaps: list[int], lengths: list[int]) -> bytes:
    literals = bytearray()
    position = 0
    with original_path.open("rb") as handle:
        original = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            for gap, length in zip(gaps, lengths, strict=True):
                target = position + gap
                literals.extend(original[target:target + length])
                position = target + length
        finally:
            original.close()
    if len(literals) != EXPECTED_LITERAL_BYTES:
        raise ValueError("literal byte count mismatch")
    header = b"FHLLQ1\0\0" + struct.pack(
        "<QQQQ", EXPECTED_RECORDS, len(gap_column), len(length_column), len(literals)
    )
    return header + gap_column + length_column + literals


def parse_literal_ledger(payload: bytes) -> tuple[list[int], list[int], memoryview]:
    if len(payload) < 40 or payload[:8] != b"FHLLQ1\0\0":
        raise ValueError("invalid literal ledger header")
    records, gap_size, length_size, literal_size = struct.unpack_from("<QQQQ", payload, 8)
    if records != EXPECTED_RECORDS or 40 + gap_size + length_size + literal_size != len(payload):
        raise ValueError("invalid literal ledger dimensions")
    gap_end = 40 + gap_size
    length_end = gap_end + length_size
    gaps = decode_ulebs(payload[40:gap_end], records)
    lengths = decode_ulebs(payload[gap_end:length_end], records)
    return gaps, lengths, memoryview(payload)[length_end:]


def copy_range(output, source: mmap.mmap, start: int, end: int) -> None:
    for offset in range(start, end, CHUNK_BYTES):
        output.write(source[offset:min(end, offset + CHUNK_BYTES)])


def reconstruct(residual_path: Path, restored_path: Path, payload: bytes) -> None:
    gaps, lengths, literals = parse_literal_ledger(payload)
    literal_position = 0
    residual_position = 0
    output_position = 0
    with residual_path.open("rb") as residual_handle, restored_path.open("xb") as output:
        residual = mmap.mmap(residual_handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            for gap, length in zip(gaps, lengths, strict=True):
                copy_range(output, residual, residual_position, residual_position + gap)
                residual_position += gap
                output.write(literals[literal_position:literal_position + length])
                literal_position += length
                output_position += gap + length
            copy_range(output, residual, residual_position, len(residual))
            output_position += len(residual) - residual_position
        finally:
            residual.close()
    if output_position != SCOPE or literal_position != len(literals):
        raise ValueError("literal reconstruction dimensions mismatch")


def main() -> int:
    original_path = ARTIFACT_ROOT / "original.bin"
    residual_path = ARTIFACT_ROOT / "residual.bin"
    copy_ledger_path = COPY_RESULT / "ledger.bin"
    copy_ledger_lzma_path = COPY_RESULT / "ledger.lzma"
    if original_path.stat().st_size != SCOPE or sha256_file(original_path) != EXPECTED_ORIGINAL_SHA256:
        raise ValueError("frozen original mismatch")
    if residual_path.stat().st_size + EXPECTED_LITERAL_BYTES != SCOPE:
        raise ValueError("frozen residual size mismatch")
    if sha256_file(residual_path) != EXPECTED_RESIDUAL_SHA256:
        raise ValueError("frozen residual hash mismatch")
    if sha256_file(copy_ledger_path) != EXPECTED_COPY_LEDGER_SHA256:
        raise ValueError("frozen copy ledger mismatch")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=False)
    gap_column, length_column, gaps, lengths = parse_copy_ledger(copy_ledger_path)
    payload = build_literal_ledger(original_path, gap_column, length_column, gaps, lengths)
    ledger_path = OUTPUT_DIR / "literal_ledger.bin"
    compressed_path = OUTPUT_DIR / "literal_ledger.lzma"
    ledger_path.write_bytes(payload)
    compressed_path.write_bytes(lzma.compress(payload, preset=9 | lzma.PRESET_EXTREME))
    decoded_payload = lzma.decompress(compressed_path.read_bytes())
    restored_path = ARTIFACT_DIR / "restored_literal.bin"
    reconstruct(residual_path, restored_path, decoded_payload)
    restored_sha = sha256_file(restored_path)
    copy_compressed_bytes = copy_ledger_lzma_path.stat().st_size
    literal_compressed_bytes = compressed_path.stat().st_size
    failed: list[str] = []
    if restored_sha != EXPECTED_ORIGINAL_SHA256:
        failed.append("literal_ledger_reconstruction_failed")
    if literal_compressed_bytes <= copy_compressed_bytes:
        failed.append("copy_source_relation_not_positive")
    decision = {
        "schema": "enwiki9_cmix_obias_helical_xmlsafe_literal_ledger_control_qm4_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "exact_matched_attribution_control",
        "verdict": "copy_source_relation_positive" if not failed else "copy_source_relation_unproven",
        "scope_bytes": SCOPE,
        "matched_residual": artifact(residual_path),
        "copy_ledger": artifact(copy_ledger_lzma_path),
        "literal_ledger": artifact(compressed_path),
        "literal_ledger_raw": artifact(ledger_path),
        "restored": artifact(restored_path),
        "records": EXPECTED_RECORDS,
        "removed_literal_bytes": EXPECTED_LITERAL_BYTES,
        "copy_ledger_bytes": copy_compressed_bytes,
        "literal_ledger_bytes": literal_compressed_bytes,
        "copy_relation_saving_bytes": literal_compressed_bytes - copy_compressed_bytes,
        "proof": {
            "residual_identical_to_qm4": True,
            "literal_ledger_finite_and_self_delimiting": True,
            "literal_ledger_decompressed_before_inverse": True,
            "literal_reconstruction_exact": restored_sha == EXPECTED_ORIGINAL_SHA256,
        },
        "failed_conditions": failed,
        "claim_boundary": "Matched ledger attribution only. No backend archive delta or target-scale score claim.",
    }
    (OUTPUT_DIR / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": decision["verdict"],
        "copy_ledger_bytes": copy_compressed_bytes,
        "literal_ledger_bytes": literal_compressed_bytes,
        "copy_relation_saving_bytes": literal_compressed_bytes - copy_compressed_bytes,
        "restored_sha256": restored_sha,
        "failed_conditions": failed,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
