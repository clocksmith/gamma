#!/usr/bin/env python3
"""Run the frozen JANUS exact MDL-pruned sparse context DAG Q0."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gc
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
from typing import Any, Sequence
import zlib

import numpy as np

import paid_block_vector_codebook as range_codec
from janus_paid_residual_mdl_oracle import range_decode
from wrt_exact import parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "janus_sparse_context_dag_q0_v1"
PLAN = ROOT / "docs/janus_sparse_context_dag_q0_plan.md"
SCHEMA = ROOT / "docs/janus_sparse_context_dag_q0_decision.schema.json"
P1_MAGIC = b"CMX21P1\0"
PAGE_MAP_MAGIC = b"SIBMAP1\0"
PAGE_RECORD = struct.Struct("<QQQQ")
MODEL_MAGIC = b"JSDAG1\0\0"
MODEL_RECORD = struct.Struct("<QBB")
MAX_DEPTH = 6
MIN_SUPPORT = 8
CONFIDENCE_BITS = 4
CONFIDENCE_BINS = 1 << CONFIDENCE_BITS
RECORD_BYTES = MODEL_RECORD.size
RECORD_QBITS = RECORD_BYTES * 8 * 256
DECODER_ALLOWANCE = 32_768
FRAME_BYTES = 64
PACKAGE_CEILING = 192 * 1024
GROSS_GATE_BPM = 3_000.0
NET_GATE_BPM = 2_100.0
ROTATION = 17
CORRECTIONS = (
    (1, 4),
    (1, 2),
    (2, 3),
    (1, 1),
    (3, 2),
    (2, 1),
    (4, 1),
    (1, 1),
)
IDENTITY_CODE = 3
CODE_ORDER = (1, 3, 2, 0, 4, 5, 6, 7)


@dataclass
class Level:
    depth: int
    keys: np.ndarray
    counts: np.ndarray
    costs: np.ndarray
    parent_index: np.ndarray | None = None
    best_delta: np.ndarray | None = None
    choices: np.ndarray | None = None


@dataclass(frozen=True)
class Record:
    depth: int
    key: int
    code: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--parent-archive", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--page-map", type=Path, required=True)
    parser.add_argument("--parent-trace-decision", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def read_p1(path: Path, rows: int) -> np.ndarray:
    raw = path.read_bytes()
    if len(raw) < 16 or raw[:8] != P1_MAGIC:
        raise ValueError("invalid endpoint428 P1 trace")
    declared = struct.unpack_from("<Q", raw, 8)[0]
    values = np.frombuffer(raw, dtype="<u2", offset=16).copy()
    if declared != rows or len(values) != rows or np.any(values == 0):
        raise ValueError("endpoint428 P1 trace differs from WRT truth")
    return values


def qbit_tables() -> tuple[np.ndarray, np.ndarray]:
    values = np.arange(65536, dtype=np.float64)
    values[0] = 1.0
    p1 = values / 65536.0
    p0 = 1.0 - p1
    return (
        np.rint(-np.log2(p0) * 256.0).astype(np.int32),
        np.rint(-np.log2(p1) * 256.0).astype(np.int32),
    )


def correction_maps() -> np.ndarray:
    base = np.arange(65536, dtype=np.int64)
    base[0] = 1
    output = np.empty((len(CORRECTIONS), 65536), dtype=np.uint16)
    for code, (numerator, denominator) in enumerate(CORRECTIONS):
        top = 65536 * numerator * base
        bottom = denominator * (65536 - base) + numerator * base
        corrected = (top + bottom // 2) // bottom
        output[code] = np.clip(corrected, 1, 65535).astype(np.uint16)
    return output


def row_costs(
    parent_p1: np.ndarray,
    truth: np.ndarray,
    adjusted: np.ndarray,
) -> np.ndarray:
    zero, one = qbit_tables()
    costs = np.empty((len(CORRECTIONS), len(truth)), dtype=np.int32)
    for code in range(len(CORRECTIONS)):
        candidate = adjusted[code, parent_p1]
        costs[code] = np.where(truth != 0, one[candidate], zero[candidate])
    return costs


def base_keys(wrt: np.ndarray, parent_p1: np.ndarray) -> np.ndarray:
    keys = np.empty(len(parent_p1), dtype=np.uint64)
    confidence = parent_p1.astype(np.uint64) >> (16 - CONFIDENCE_BITS)
    for bit_position in range(8):
        if bit_position == 0:
            prefix = np.zeros(len(wrt), dtype=np.uint16)
        else:
            prefix = wrt.astype(np.uint16) >> (8 - bit_position)
        node = np.uint64(1 << bit_position) + prefix.astype(np.uint64)
        keys[bit_position::8] = node * np.uint64(CONFIDENCE_BINS) + confidence[bit_position::8]
    return keys


def suffix_values(wrt: np.ndarray, depth: int) -> np.ndarray:
    output = np.zeros(len(wrt), dtype=np.uint64)
    for lag in range(1, depth + 1):
        output[lag:] |= wrt[:-lag].astype(np.uint64) << np.uint64(8 * (lag - 1))
    return output


def context_keys(base: np.ndarray, wrt: np.ndarray, depth: int) -> np.ndarray:
    if depth == 0:
        return base.copy()
    suffix = np.repeat(suffix_values(wrt, depth), 8)
    return (base << np.uint64(8 * depth)) | suffix


def aggregate_level(
    depth: int,
    keys: np.ndarray,
    costs: np.ndarray,
) -> Level:
    unique, inverse, counts = np.unique(
        keys,
        return_inverse=True,
        return_counts=True,
    )
    qualified = counts >= MIN_SUPPORT
    if depth == 0:
        qualified[:] = True
    selected_keys = unique[qualified]
    selected_counts = counts[qualified].astype(np.int64)
    selected_costs = np.empty((len(selected_keys), len(CORRECTIONS)), dtype=np.int64)
    for code in range(len(CORRECTIONS)):
        aggregate = np.bincount(
            inverse,
            weights=costs[code],
            minlength=len(unique),
        )
        selected_costs[:, code] = np.rint(aggregate[qualified]).astype(np.int64)
    return Level(depth, selected_keys, selected_counts, selected_costs)


def parent_keys(keys: np.ndarray, depth: int) -> np.ndarray:
    if depth <= 0:
        raise ValueError("depth-zero nodes have no parent")
    base = keys >> np.uint64(8 * depth)
    if depth == 1:
        suffix = np.zeros(len(keys), dtype=np.uint64)
    else:
        suffix = keys & np.uint64((1 << (8 * (depth - 1))) - 1)
    return (base << np.uint64(8 * (depth - 1))) | suffix


def fit_sparse_dag(
    wrt: np.ndarray,
    base: np.ndarray,
    costs: np.ndarray,
    maximum_depth: int,
) -> tuple[list[Record], dict[str, Any]]:
    levels: list[Level] = []
    for depth in range(maximum_depth + 1):
        print(f"phase=aggregate depth={depth} max_depth={maximum_depth}", flush=True)
        level = aggregate_level(depth, context_keys(base, wrt, depth), costs)
        if depth:
            parent = levels[-1]
            desired = parent_keys(level.keys, depth)
            positions = np.searchsorted(parent.keys, desired)
            if np.any(positions >= len(parent.keys)) or not np.array_equal(parent.keys[positions], desired):
                raise ValueError("supported suffix context is missing its parent")
            level.parent_index = positions.astype(np.int64)
        levels.append(level)
        print(f"phase=aggregate_done depth={depth} contexts={len(level.keys)}", flush=True)

    for depth in range(maximum_depth, -1, -1):
        level = levels[depth]
        child_sums = np.zeros((len(level.keys), len(CORRECTIONS)), dtype=np.int64)
        if depth < maximum_depth:
            child = levels[depth + 1]
            assert child.parent_index is not None
            assert child.best_delta is not None
            for inherited in range(len(CORRECTIONS)):
                aggregate = np.bincount(
                    child.parent_index,
                    weights=child.best_delta[:, inherited],
                    minlength=len(level.keys),
                )
                child_sums[:, inherited] = np.rint(aggregate).astype(np.int64)
        best = child_sums.copy()
        choices = np.full(best.shape, -1, dtype=np.int8)
        for inherited in range(len(CORRECTIONS)):
            for code in CODE_ORDER:
                candidate = (
                    RECORD_QBITS
                    + level.costs[:, code]
                    - level.costs[:, inherited]
                    + child_sums[:, code]
                )
                improves = candidate < best[:, inherited]
                best[improves, inherited] = candidate[improves]
                choices[improves, inherited] = code
        level.best_delta = best
        level.choices = choices

    records: list[Record] = []
    active: np.ndarray | None = None
    for depth, level in enumerate(levels):
        assert level.choices is not None
        if depth == 0:
            inherited = np.full(len(level.keys), IDENTITY_CODE, dtype=np.uint8)
        else:
            assert active is not None and level.parent_index is not None
            inherited = active[level.parent_index]
        chosen = level.choices[np.arange(len(level.keys)), inherited]
        active = inherited.copy()
        selected = chosen >= 0
        active[selected] = chosen[selected].astype(np.uint8)
        for key, code in zip(level.keys[selected], chosen[selected], strict=True):
            records.append(Record(depth, int(key), int(code)))

    root = levels[0]
    assert root.best_delta is not None
    estimated_delta = int(root.best_delta[:, IDENTITY_CODE].sum())
    metrics = {
        "maximum_depth": maximum_depth,
        "minimum_support": MIN_SUPPORT,
        "contexts_by_depth": [len(level.keys) for level in levels],
        "retained_records_by_depth": [
            sum(record.depth == depth for record in records)
            for depth in range(maximum_depth + 1)
        ],
        "retained_records": len(records),
        "selection_record_bytes": len(records) * RECORD_BYTES,
        "estimated_net_qbits_after_record_charge": -estimated_delta,
    }
    return records, metrics


def serialize_model(records: Sequence[Record], maximum_depth: int) -> bytes:
    ordered = sorted(records, key=lambda row: (row.depth, row.key, row.code))
    output = bytearray(MODEL_MAGIC)
    output.extend(
        struct.pack(
            "<IIIIII",
            1,
            maximum_depth,
            MIN_SUPPORT,
            CONFIDENCE_BITS,
            RECORD_BYTES,
            len(ordered),
        )
    )
    output.extend(struct.pack("<I", len(CORRECTIONS)))
    for numerator, denominator in CORRECTIONS:
        output.extend(struct.pack("<HH", numerator, denominator))
    for record in ordered:
        output.extend(MODEL_RECORD.pack(record.key, record.depth, record.code))
    return bytes(output)


def records_by_depth(records: Sequence[Record], maximum_depth: int) -> list[tuple[np.ndarray, np.ndarray]]:
    output: list[tuple[np.ndarray, np.ndarray]] = []
    for depth in range(maximum_depth + 1):
        rows = sorted((record.key, record.code) for record in records if record.depth == depth)
        output.append(
            (
                np.asarray([row[0] for row in rows], dtype=np.uint64),
                np.asarray([row[1] for row in rows], dtype=np.uint8),
            )
        )
    return output


def apply_records(
    wrt: np.ndarray,
    parent_p1: np.ndarray,
    base: np.ndarray,
    adjusted: np.ndarray,
    records: Sequence[Record],
    maximum_depth: int,
) -> np.ndarray:
    codes = np.full(len(parent_p1), IDENTITY_CODE, dtype=np.uint8)
    for depth, (record_keys, record_codes) in enumerate(records_by_depth(records, maximum_depth)):
        if not len(record_keys):
            continue
        keys = context_keys(base, wrt, depth)
        positions = np.searchsorted(record_keys, keys)
        valid = positions < len(record_keys)
        matched = np.zeros(len(keys), dtype=bool)
        matched[valid] = record_keys[positions[valid]] == keys[valid]
        codes[matched] = record_codes[positions[matched]]
    return adjusted[codes, parent_p1]


def rotate_records(records: Sequence[Record], maximum_depth: int) -> list[Record]:
    output: list[Record] = []
    for depth in range(maximum_depth + 1):
        rows = sorted((record.key, record.code) for record in records if record.depth == depth)
        if not rows:
            continue
        codes = np.roll(np.asarray([row[1] for row in rows], dtype=np.uint8), ROTATION)
        output.extend(
            Record(depth, key, int(code))
            for (key, _), code in zip(rows, codes, strict=True)
        )
    return output


def exact_decode(payload: bytes, probabilities: np.ndarray, truth: np.ndarray) -> bool:
    return np.array_equal(range_decode(payload, probabilities), truth)


def read_page_splits(path: Path, wrt_bytes: int) -> dict[str, dict[str, Any]]:
    data = path.read_bytes()
    if len(data) < 16 or data[:8] != PAGE_MAP_MAGIC:
        raise ValueError("invalid page map")
    count = struct.unpack_from("<Q", data, 8)[0]
    if len(data) != 16 + count * PAGE_RECORD.size:
        raise ValueError("page-map record count mismatch")
    development_end = count * 3 // 5
    selection_end = count * 4 // 5
    result = {
        name: {"ranges": [], "raw_bytes": 0, "pages": 0}
        for name in ("development", "selection", "sealed_confirmation")
    }
    for index in range(count):
        raw_start, raw_end, row_start, row_end = PAGE_RECORD.unpack_from(
            data, 16 + index * PAGE_RECORD.size
        )
        if row_start % 8 or row_end % 8 or row_end > wrt_bytes * 8:
            raise ValueError("page map is not valid for the WRT stream")
        name = (
            "development"
            if index < development_end
            else "selection"
            if index < selection_end
            else "sealed_confirmation"
        )
        row = result[name]
        row["ranges"].append((row_start, row_end))
        row["raw_bytes"] += raw_end - raw_start
        row["pages"] += 1
    return result


def split_economics(
    splits: dict[str, dict[str, Any]],
    parent_p1: np.ndarray,
    candidate_p1: np.ndarray,
    truth: np.ndarray,
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for name, split in splits.items():
        ranges = split["ranges"]
        parent = np.concatenate([parent_p1[start:end] for start, end in ranges])
        candidate = np.concatenate([candidate_p1[start:end] for start, end in ranges])
        bits = np.concatenate([truth[start:end] for start, end in ranges])
        parent_payload = range_codec.encode_payload(parent, bits)
        candidate_payload = range_codec.encode_payload(candidate, bits)
        gain = len(parent_payload) - len(candidate_payload)
        output[name] = {
            "pages": split["pages"],
            "raw_bytes": split["raw_bytes"],
            "rows": len(bits),
            "parent_payload_bytes": len(parent_payload),
            "candidate_payload_bytes": len(candidate_payload),
            "gain_bytes": gain,
            "gain_bytes_per_million": gain * 1_000_000.0 / split["raw_bytes"],
        }
    return output


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in (
        args.p1,
        args.wrt_store,
        args.raw_input,
        args.parent_archive,
        args.dictionary,
        args.backend,
        args.page_map,
        args.parent_trace_decision,
        PLAN,
        SCHEMA,
    ):
        if not path.is_file():
            raise ValueError(f"missing input: {path}")

    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("exact WRT parse differs from raw input")
    wrt_bytes = parsed.stream
    wrt = np.frombuffer(wrt_bytes, dtype=np.uint8).copy()
    truth = np.unpackbits(wrt, bitorder="big")
    parent_p1 = read_p1(args.p1, len(truth))
    receipt_payload, parent_header_bytes, declared_wrt = range_codec.read_archive(args.parent_archive)
    if declared_wrt != len(wrt):
        raise ValueError("parent archive WRT length mismatch")
    parent_payload = range_codec.encode_payload(parent_p1, truth)
    if parent_payload != receipt_payload:
        raise ValueError("parent P1 does not reproduce the receipt-bound payload")

    adjusted = correction_maps()
    costs = row_costs(parent_p1, truth, adjusted)
    base = base_keys(wrt, parent_p1)

    print("phase=fit_D2_A", flush=True)
    records_a, metrics_a = fit_sparse_dag(wrt, base, costs, MAX_DEPTH)
    model_a = serialize_model(records_a, MAX_DEPTH)
    candidate_a = apply_records(wrt, parent_p1, base, adjusted, records_a, MAX_DEPTH)
    payload_a = range_codec.encode_payload(candidate_a, truth)

    gc.collect()
    print("phase=fit_D2_B", flush=True)
    records_b, metrics_b = fit_sparse_dag(wrt, base, costs, MAX_DEPTH)
    model_b = serialize_model(records_b, MAX_DEPTH)
    candidate_b = apply_records(wrt, parent_p1, base, adjusted, records_b, MAX_DEPTH)
    payload_b = range_codec.encode_payload(candidate_b, truth)

    print("phase=fit_D1", flush=True)
    flat_records, flat_metrics = fit_sparse_dag(wrt, base, costs, 0)
    flat_model = serialize_model(flat_records, 0)
    flat_p1 = apply_records(wrt, parent_p1, base, adjusted, flat_records, 0)
    flat_payload = range_codec.encode_payload(flat_p1, truth)

    rotated_records = rotate_records(records_a, MAX_DEPTH)
    rotated_model = serialize_model(rotated_records, MAX_DEPTH)
    rotated_p1 = apply_records(wrt, parent_p1, base, adjusted, rotated_records, MAX_DEPTH)
    rotated_payload = range_codec.encode_payload(rotated_p1, truth)

    exactness = {
        "parent_payload_identity": parent_payload == receipt_payload,
        "D2_A_B_model_identity": model_a == model_b,
        "D2_A_B_P1_identity": np.array_equal(candidate_a, candidate_b),
        "D2_A_B_payload_identity": payload_a == payload_b,
        "D1_arithmetic_decode": exact_decode(flat_payload, flat_p1, truth),
        "D2_A_arithmetic_decode": exact_decode(payload_a, candidate_a, truth),
        "D2_B_arithmetic_decode": exact_decode(payload_b, candidate_b, truth),
        "DR_arithmetic_decode": exact_decode(rotated_payload, rotated_p1, truth),
        "all_probabilities_legal_nonzero": all(
            not np.any(values == 0)
            for values in (flat_p1, candidate_a, candidate_b, rotated_p1)
        ),
        "WRT_reconstruction": True,
    }

    reconstructed_store = args.wrt_store.read_bytes()
    store_path = args.output_dir / "d2.wrt_store.bin"
    store_path.write_bytes(reconstructed_store)
    restored_path = args.output_dir / "d2.restored.raw"
    with (args.output_dir / "d2_inverse.stdout.log").open("wb") as stdout, (
        args.output_dir / "d2_inverse.stderr.log"
    ).open("wb") as stderr:
        inverse = subprocess.run(
            [
                str(args.backend),
                "-d",
                str(args.dictionary),
                str(store_path),
                str(restored_path),
            ],
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    official_inverse = (
        inverse.returncode == 0
        and restored_path.is_file()
        and restored_path.read_bytes() == raw
    )
    exactness["official_raw_inverse"] = official_inverse

    splits = read_page_splits(args.page_map, len(wrt))
    split_rows = split_economics(splits, parent_p1, candidate_a, truth)
    compressed_model = zlib.compress(model_a, level=9)
    compressed_flat = zlib.compress(flat_model, level=9)
    compressed_rotated = zlib.compress(rotated_model, level=9)
    package_bytes = len(compressed_model) + DECODER_ALLOWANCE + FRAME_BYTES
    gross_gain = len(parent_payload) - len(payload_a)
    gross_bpm = gross_gain * 1_000_000.0 / len(raw)
    net_bpm = gross_bpm - package_bytes / 1000.0
    conditions = {
        "D2_gross_at_least_3000_BPM": gross_bpm >= GROSS_GATE_BPM,
        "D2_package_adjusted_at_least_2100_BPM": net_bpm >= NET_GATE_BPM,
        "development_gain_positive": split_rows["development"]["gain_bytes"] > 0,
        "selection_gain_positive": split_rows["selection"]["gain_bytes"] > 0,
        "sealed_confirmation_gain_positive": split_rows["sealed_confirmation"]["gain_bytes"] > 0,
        "D2_beats_depth_zero_D1": len(payload_a) < len(flat_payload),
        "D2_beats_rotated_DR": len(payload_a) < len(rotated_payload),
        "complete_package_at_most_192KiB": package_bytes <= PACKAGE_CEILING,
        **exactness,
    }
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed
    decision = "AUTHORIZED_10M" if authorized else "REJECT"

    (args.output_dir / "model.jsdag1").write_bytes(model_a)
    (args.output_dir / "model.jsdag1.zlib").write_bytes(compressed_model)
    (args.output_dir / "d1.payload").write_bytes(flat_payload)
    (args.output_dir / "d2.payload").write_bytes(payload_a)
    (args.output_dir / "dr.payload").write_bytes(rotated_payload)

    tool_source = Path(__file__).read_bytes()
    receipt = {
        "schema": "janus_sparse_context_dag_q0_v1",
        "candidate_id": CANDIDATE_ID,
        "decision": decision,
        "claim_boundary": (
            "Paid opening-1M fixed-population sparse-DAG evidence only. "
            "No native decoder, distant transfer, forecast credit, larger "
            "archive, or full-1G claim exists."
        ),
        "inputs": {
            "p1": artifact(args.p1),
            "wrt_store": artifact(args.wrt_store),
            "raw_input": artifact(args.raw_input),
            "parent_archive": artifact(args.parent_archive),
            "dictionary": artifact(args.dictionary),
            "backend": artifact(args.backend),
            "page_map": artifact(args.page_map),
            "parent_trace_decision": artifact(args.parent_trace_decision),
            "plan": artifact(PLAN),
            "decision_schema": artifact(SCHEMA),
            "oracle_tool": artifact(Path(__file__)),
        },
        "population": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(wrt),
            "trace_rows": len(truth),
            "complete_pages": sum(split["pages"] for split in splits.values()),
            "page_splits": {
                name: {"pages": split["pages"], "raw_bytes": split["raw_bytes"]}
                for name, split in splits.items()
            },
        },
        "construction": {
            "maximum_history_depth": MAX_DEPTH,
            "minimum_support": MIN_SUPPORT,
            "confidence_bits": CONFIDENCE_BITS,
            "corrections": [list(row) for row in CORRECTIONS],
            "record_bytes_charged_during_selection": RECORD_BYTES,
            "record_qbits_charged_during_selection": RECORD_QBITS,
            "rotation": ROTATION,
            "tie_order": list(CODE_ORDER),
        },
        "models": {
            "D1": {
                **flat_metrics,
                "raw_bytes": len(flat_model),
                "compressed_bytes": len(compressed_flat),
                "raw_sha256": sha256_bytes(flat_model),
                "compressed_sha256": sha256_bytes(compressed_flat),
            },
            "D2": {
                **metrics_a,
                "second_fit_metrics_identical": metrics_a == metrics_b,
                "raw_bytes": len(model_a),
                "compressed_bytes": len(compressed_model),
                "raw_sha256": sha256_bytes(model_a),
                "compressed_sha256": sha256_bytes(compressed_model),
                "decoder_allowance_bytes": DECODER_ALLOWANCE,
                "framing_bytes": FRAME_BYTES,
                "complete_package_bytes": package_bytes,
                "package_ceiling_bytes": PACKAGE_CEILING,
            },
            "DR": {
                "retained_records": len(rotated_records),
                "raw_bytes": len(rotated_model),
                "compressed_bytes": len(compressed_rotated),
                "raw_sha256": sha256_bytes(rotated_model),
                "compressed_sha256": sha256_bytes(compressed_rotated),
            },
            "oracle_tool_gzip9_bytes": len(gzip.compress(tool_source, compresslevel=9, mtime=0)),
        },
        "payloads": {
            "D0_parent": {
                "bytes": len(parent_payload),
                "sha256": sha256_bytes(parent_payload),
                "archive_header_bytes": parent_header_bytes,
            },
            "D1_depth_zero": {
                "bytes": len(flat_payload),
                "sha256": sha256_bytes(flat_payload),
            },
            "D2_sparse_dag": {
                "bytes": len(payload_a),
                "sha256": sha256_bytes(payload_a),
            },
            "DR_rotated": {
                "bytes": len(rotated_payload),
                "sha256": sha256_bytes(rotated_payload),
            },
        },
        "split_economics": split_rows,
        "economics": {
            "gross_gain_bytes": gross_gain,
            "gross_gain_bytes_per_million": gross_bpm,
            "complete_package_bytes": package_bytes,
            "package_adjusted_gain_bytes_per_million": net_bpm,
            "literal_1m_two_part_bytes": len(payload_a) + package_bytes,
            "forecast_score_bytes_unchanged": 109_389_323,
            "forecast_debt_bytes": 1_389_323,
        },
        "gates": {
            "conditions": conditions,
            "failed_conditions": failed,
            "gross_required_bytes_per_million": GROSS_GATE_BPM,
            "net_required_bytes_per_million": NET_GATE_BPM,
            "next_action": (
                "run one unchanged canonical-10M replay"
                if authorized
                else "retire the frozen sparse suffix DAG realization"
            ),
        },
        "exactness": exactness,
        "proof": {
            "WRT_sha256": sha256_bytes(wrt_bytes),
            "raw_sha256": sha256_bytes(raw),
            "restored_raw_sha256": sha256_file(restored_path) if restored_path.is_file() else None,
        },
        "score_credit_bytes": 0,
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "candidate_id": CANDIDATE_ID,
        "decision": decision,
        "gross_BPM": gross_bpm,
        "net_BPM": net_bpm,
        "D2_records": len(records_a),
        "failed_conditions": failed,
        "decision_path": str(decision_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"janus-sparse-context-dag: {error}", file=sys.stderr)
        raise

