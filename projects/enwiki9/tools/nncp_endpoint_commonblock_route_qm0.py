#!/usr/bin/env python3
"""Measure NNCP/Endpoint routing on identical common-boundary raw blocks."""

from __future__ import annotations

import argparse
from bisect import bisect_left
import hashlib
import json
import lzma
from pathlib import Path
import struct

import numpy as np

from radix_island_oracle import emission_groups
from wrt_exact import parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_endpoint_commonblock_route_qm0_v1"
QBITS = 256
BLOCK_RAW_BYTES = 65_536
BLOCK_FRAME_BYTES = 8
ROTATION_BLOCKS = 7
SELECTION_START = 1_499_136
SELECTION_END = 1_998_848
EXECUTION_SYMBOLS = 1_998_848
RAW_START = 6_757_802
RAW_END = 8_991_577
WRT_START = 4_182_331
WRT_END = 5_618_556
VOCABULARY = 16_392
TRACE_MAGIC = b"NNNTR4\0\0"
TRACE_HEADER = struct.Struct("<8sQQQQ")
TRACE_ROW = struct.Struct("<QQQQQQQQHHBBB")
TRACE_BRANCH = struct.Struct("<HB")
P1_MAGIC = b"CMX21P1\0"
MAP_DTYPE = np.dtype(
    [("raw_start", "<u8"), ("raw_end", "<u8"), ("symbol", "<u2")]
)

EXPECTED = {
    "teacher_trace": (225_871_253, "230eb8823665cfe1724fee7de55103ed4d78fc31a0c3d7a2881754d78507acc9"),
    "symbol_map": (3_610_961_314, "b9e0c570fb12fe3baa35cc8d877a11735065ed56ce30c3fca68b74ce794c3085"),
    "joint_p1": (100_029_648, "b554ddd170df355ab597fa8fd082b2ea4d2098dad540b07dcb9084016cc2e719"),
    "wrt_store": (6_251_857, "867c23e652052268017d4bda543ea86c6b6af7efdaa0d87175997e7fb19a3a5b"),
    "wrt_dictionary": (411_996, "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(label: str, path: Path) -> dict[str, object]:
    expected_bytes, expected_sha = EXPECTED[label]
    actual = {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if actual["bytes"] != expected_bytes or actual["sha256"] != expected_sha:
        raise ValueError(f"{label} identity differs from frozen receipt")
    return actual


def expected_bits(symbol: int, vocabulary: int) -> list[int]:
    start = 0
    active = vocabulary
    bits: list[int] = []
    while active > 1:
        left = active >> 1
        bit = int(symbol >= start + left)
        bits.append(bit)
        if bit:
            start += left
            active -= left
        else:
            active = left
    if start != symbol:
        raise ValueError("NNCP tree path does not terminate at symbol")
    return bits


def qbit_tables(total: int) -> tuple[np.ndarray, np.ndarray]:
    values = np.arange(total + 1, dtype=np.float64)
    p0 = np.clip(values / total, 1.0 / total, 1.0 - 1.0 / total)
    zero = np.rint(-np.log2(p0) * QBITS).astype(np.int32)
    one = np.rint(-np.log2(1.0 - p0) * QBITS).astype(np.int32)
    return zero, one


def read_teacher_costs(
    trace_path: Path, symbols: np.memmap
) -> tuple[np.ndarray, dict[str, int | bool]]:
    zero, one = qbit_tables(32_768)
    costs = np.zeros(SELECTION_END - SELECTION_START, dtype=np.int64)
    seen = np.zeros(EXECUTION_SYMBOLS, dtype=np.uint8)
    selected_rows = 0
    selected_branches = 0
    with trace_path.open("rb") as source:
        header = source.read(TRACE_HEADER.size)
        magic, rows, branches, trees, checkpoints = TRACE_HEADER.unpack(header)
        if magic != TRACE_MAGIC or rows != EXECUTION_SYMBOLS or trees != 0:
            raise ValueError("NNCP trace header differs from frozen contract")
        observed_branches = 0
        for execution in range(rows):
            raw_row = source.read(TRACE_ROW.size)
            if len(raw_row) != TRACE_ROW.size:
                raise ValueError("truncated NNCP trace row")
            (
                original_index,
                observed_execution,
                before_bits,
                after_bits,
                before_bytes,
                after_bytes,
                exact_bits,
                exact_bytes,
                symbol,
                vocabulary,
                branch_count,
                has_tree,
                checkpoint,
            ) = TRACE_ROW.unpack(raw_row)
            if observed_execution != execution:
                raise ValueError("NNCP execution ordinal changed")
            if original_index >= EXECUTION_SYMBOLS or seen[original_index]:
                raise ValueError("NNCP original ordinal is invalid or duplicated")
            seen[original_index] = 1
            if vocabulary != VOCABULARY or symbol != int(symbols[original_index]):
                raise ValueError("NNCP trace symbol identity changed")
            if has_tree or checkpoint or exact_bits or exact_bytes:
                raise ValueError("unexpected NNCP trace row flags")
            if after_bits < before_bits or after_bytes < before_bytes:
                raise ValueError("NNCP coder counters decreased")
            bits = expected_bits(symbol, vocabulary)
            if len(bits) != branch_count:
                raise ValueError("NNCP branch count differs from symbol path")
            selected = SELECTION_START <= original_index < SELECTION_END
            if selected != (SELECTION_START <= execution < SELECTION_END):
                raise ValueError("NNCP selection is not execution-order closed")
            row_cost = 0
            for expected_bit in bits:
                raw_branch = source.read(TRACE_BRANCH.size)
                if len(raw_branch) != TRACE_BRANCH.size:
                    raise ValueError("truncated NNCP trace branch")
                prob0, bit = TRACE_BRANCH.unpack(raw_branch)
                if bit != expected_bit or not 1 <= prob0 < 32_768:
                    raise ValueError("NNCP branch truth or probability is invalid")
                if selected:
                    row_cost += int(one[prob0] if bit else zero[prob0])
                    selected_branches += 1
            if selected:
                costs[original_index - SELECTION_START] = row_cost
                selected_rows += 1
            observed_branches += branch_count
        if source.read(1):
            raise ValueError("NNCP trace has trailing bytes")
    if observed_branches != branches or checkpoints != 0:
        raise ValueError("NNCP trace totals differ from header")
    if not np.all(seen):
        raise ValueError("NNCP original-ordinal permutation is incomplete")
    if selected_rows != SELECTION_END - SELECTION_START:
        raise ValueError("NNCP trace does not cover frozen selection")
    return costs, {
        "execution_order_exact": True,
        "selected_symbols": selected_rows,
        "selected_branches": selected_branches,
        "visited_branches": observed_branches,
    }


def read_p1(path: Path, expected_rows: int) -> np.memmap:
    with path.open("rb") as handle:
        header = handle.read(16)
    if len(header) != 16 or header[:8] != P1_MAGIC:
        raise ValueError("invalid Endpoint P1 header")
    rows = struct.unpack_from("<Q", header, 8)[0]
    if rows != expected_rows or path.stat().st_size != 16 + 2 * rows:
        raise ValueError("Endpoint P1 row binding differs")
    return np.memmap(path, mode="r", dtype="<u2", offset=16, shape=(rows,))


def endpoint_byte_costs(p1: np.memmap, stream: bytes) -> np.ndarray:
    rows = (WRT_END - WRT_START) * 8
    probabilities = np.asarray(
        p1[WRT_START * 8 : WRT_END * 8], dtype=np.uint32
    )
    truth = np.unpackbits(
        np.frombuffer(stream[WRT_START:WRT_END], dtype=np.uint8), bitorder="big"
    )
    if len(probabilities) != rows or len(truth) != rows or np.any(probabilities == 0):
        raise ValueError("Endpoint selected rows are invalid")
    zero, one = qbit_tables(65_536)
    costs = np.where(truth != 0, one[65_536 - probabilities], zero[65_536 - probabilities])
    return costs.reshape(-1, 8).sum(axis=1).astype(np.int64)


def common_boundaries(
    mapping: np.memmap, parsed: object
) -> tuple[list[int], dict[int, int], dict[int, int]]:
    selected = mapping[SELECTION_START:SELECTION_END]
    teacher_boundary = {RAW_START: 0}
    for index, raw_end in enumerate(selected["raw_end"]):
        teacher_boundary[int(raw_end)] = index + 1
    wrt_boundary = {0: 6}
    for group in emission_groups(parsed):
        wrt_boundary[int(group.raw_end)] = int(group.stream_end)
    common = sorted(
        boundary
        for boundary in teacher_boundary.keys() & wrt_boundary.keys()
        if RAW_START <= boundary <= RAW_END
    )
    if not common or common[0] != RAW_START or common[-1] != RAW_END:
        raise ValueError("common boundaries do not cover the frozen raw window")
    if teacher_boundary[RAW_END] != SELECTION_END - SELECTION_START:
        raise ValueError("NNCP terminal boundary differs")
    if wrt_boundary[RAW_START] != WRT_START or wrt_boundary[RAW_END] != WRT_END:
        raise ValueError("Endpoint terminal boundaries differ")
    return common, teacher_boundary, wrt_boundary


def make_blocks(boundaries: list[int]) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    start = RAW_START
    while start < RAW_END:
        target = min(RAW_END, start + BLOCK_RAW_BYTES)
        index = bisect_left(boundaries, target)
        if index >= len(boundaries):
            raise ValueError("cannot close common-boundary block")
        end = boundaries[index]
        if end <= start:
            raise ValueError("common-boundary block did not advance")
        blocks.append((start, end))
        start = end
    if blocks[0][0] != RAW_START or blocks[-1][1] != RAW_END:
        raise ValueError("blocks do not cover frozen window")
    return blocks


def route_summary(
    blocks: list[dict[str, int]], *, rotated: bool = False
) -> dict[str, object]:
    total_gain = 0
    split_gain = [0, 0, 0]
    nncp_blocks = 0
    rows: list[dict[str, int | str]] = []
    frame_qbits = BLOCK_FRAME_BYTES * 8 * QBITS
    for index, block in enumerate(blocks):
        use_nncp = False
        if index:
            source_index = index - 1
            if rotated:
                source_index = (source_index - ROTATION_BLOCKS) % len(blocks)
            source = blocks[source_index]
            use_nncp = source["nncp_qbits"] < source["endpoint_qbits"]
        chosen = block["nncp_qbits"] if use_nncp else block["endpoint_qbits"]
        gain = block["endpoint_qbits"] - chosen - frame_qbits
        split = min(2, index * 3 // len(blocks))
        total_gain += gain
        split_gain[split] += gain
        nncp_blocks += int(use_nncp)
        rows.append({
            "raw_start": block["raw_start"],
            "raw_end": block["raw_end"],
            "selected": "nncp" if use_nncp else "endpoint",
            "gain_qbits_after_frame": gain,
        })
    return {
        "gain_qbits_after_frame": total_gain,
        "gain_bytes_after_frame": total_gain / (8 * QBITS),
        "split_gain_bytes_after_frame": [value / (8 * QBITS) for value in split_gain],
        "nncp_selected_blocks": nncp_blocks,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teacher-trace", type=Path, default=ROOT / "results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/teacher_native_trace.bin")
    parser.add_argument("--symbol-map", type=Path, default=Path("/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/symbol_raw_map.bin"))
    parser.add_argument("--joint-p1", type=Path, default=ROOT / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1")
    parser.add_argument("--wrt-store", type=Path, default=ROOT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin")
    parser.add_argument("--wrt-dictionary", type=Path, default=Path("/home/x/enwiki9-nonproof/results/cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/clean-build-b/build/english.dic"))
    parser.add_argument("--output-dir", type=Path, default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    inputs = {
        label: artifact(label, getattr(args, label))
        for label in EXPECTED
    }
    with args.symbol_map.open("rb") as handle:
        if handle.read(8) != b"NNSMAP1\0":
            raise ValueError("invalid NNCP symbol-map magic")
        map_rows = struct.unpack("<Q", handle.read(8))[0]
    mapping = np.memmap(args.symbol_map, mode="r", dtype=MAP_DTYPE, offset=16, shape=(map_rows,))
    symbols = np.memmap(
        "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/preprocessed.bin",
        mode="r", dtype=">u2",
    )
    parsed = parse_store(args.wrt_store, args.wrt_dictionary)
    with Path("data/enwik9").open("rb") as canonical:
        canonical.seek(RAW_START)
        canonical_window = canonical.read(RAW_END - RAW_START)
    if parsed.decoded[RAW_START:RAW_END] != canonical_window:
        raise ValueError("WRT inverse differs from canonical raw window")

    teacher_costs, teacher_proof = read_teacher_costs(args.teacher_trace, symbols)
    p1 = read_p1(args.joint_p1, len(parsed.stream) * 8)
    endpoint_costs = endpoint_byte_costs(p1, parsed.stream)
    common, teacher_boundary, wrt_boundary = common_boundaries(mapping, parsed)
    block_spans = make_blocks(common)
    teacher_prefix = np.concatenate(([0], np.cumsum(teacher_costs, dtype=np.int64)))
    endpoint_prefix = np.concatenate(([0], np.cumsum(endpoint_costs, dtype=np.int64)))
    blocks: list[dict[str, int]] = []
    for raw_start, raw_end in block_spans:
        symbol_start = teacher_boundary[raw_start]
        symbol_end = teacher_boundary[raw_end]
        wrt_start = wrt_boundary[raw_start]
        wrt_end = wrt_boundary[raw_end]
        blocks.append({
            "raw_start": raw_start,
            "raw_end": raw_end,
            "raw_bytes": raw_end - raw_start,
            "symbol_start": symbol_start + SELECTION_START,
            "symbol_end": symbol_end + SELECTION_START,
            "wrt_start": wrt_start,
            "wrt_end": wrt_end,
            "nncp_qbits": int(teacher_prefix[symbol_end] - teacher_prefix[symbol_start]),
            "endpoint_qbits": int(endpoint_prefix[wrt_end - WRT_START] - endpoint_prefix[wrt_start - WRT_START]),
        })

    causal = route_summary(blocks)
    rotated = route_summary(blocks, rotated=True)
    oracle_frame = (BLOCK_FRAME_BYTES * 8 + 1) * QBITS
    oracle_gain_qbits = sum(
        block["endpoint_qbits"] - min(block["endpoint_qbits"], block["nncp_qbits"]) - oracle_frame
        for block in blocks
    )
    source_paths = [
        Path(__file__),
        ROOT / "docs/nncp_endpoint_commonblock_route_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    ]
    source_blob = b"".join(path.name.encode() + b"\0" + path.read_bytes() for path in source_paths)
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = args.output_dir / "diagnostic_source_package.lzma"
    source_path.write_bytes(source_package)

    failed: list[str] = []
    if causal["gain_bytes_after_frame"] < 20_000:
        failed.append("causal_gain_below_20000")
    if any(value <= 0 for value in causal["split_gain_bytes_after_frame"]):
        failed.append("causal_chronological_third_nonpositive")
    if causal["gain_bytes_after_frame"] - rotated["gain_bytes_after_frame"] < 5_000:
        failed.append("rotated_control_margin_below_5000")
    if len(source_package) > 65_536:
        failed.append("diagnostic_source_exceeds_65536")

    decision = {
        "schema": "enwiki9_nncp_endpoint_commonblock_route_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "cross_alphabet_common_raw_block_causal_shadow_zero_credit",
        "verdict": "authorize_exact_dual_substrate_block_container" if not failed else "retire_commonblock_route",
        "inputs": inputs,
        "scope": {
            "raw_start": RAW_START,
            "raw_end": RAW_END,
            "raw_bytes": RAW_END - RAW_START,
            "common_boundaries": len(common),
            "blocks": len(blocks),
            "target_block_raw_bytes": BLOCK_RAW_BYTES,
            "minimum_block_raw_bytes": min(row["raw_bytes"] for row in blocks),
            "maximum_block_raw_bytes": max(row["raw_bytes"] for row in blocks),
        },
        "accounting": {
            "endpoint_qbit_equivalent_bytes": sum(row["endpoint_qbits"] for row in blocks) / (8 * QBITS),
            "nncp_qbit_equivalent_bytes": sum(row["nncp_qbits"] for row in blocks) / (8 * QBITS),
            "block_frame_bytes": BLOCK_FRAME_BYTES,
            "oracle_gain_bytes_after_frame_and_selector": oracle_gain_qbits / (8 * QBITS),
            "causal_one_block_lag": causal,
            "rotated_control": rotated,
            "causal_margin_over_rotated_bytes": causal["gain_bytes_after_frame"] - rotated["gain_bytes_after_frame"],
            "diagnostic_source_package_bytes": len(source_package),
            "score_credit_bytes": 0,
        },
        "proof": {
            **teacher_proof,
            "wrt_inverse_window_exact": True,
            "common_raw_boundaries_complete": True,
            "cross_alphabet_probability_mixing_absent": True,
            "route_uses_only_preceding_block_loss": True,
        },
        "blocks": blocks,
        "failed_conditions": failed,
        "artifacts": {
            "diagnostic_source_package": {
                "path": str(source_path.resolve().relative_to(ROOT)),
                "bytes": source_path.stat().st_size,
                "sha256": sha256_file(source_path),
            }
        },
        "claim_boundary": "Exact qbit-equivalent causal routing shadow over identical raw blocks with independently continuous NNCP and Endpoint states. It is not a finite dual-codec container, does not establish executable runtime eligibility, and receives zero score or forecast credit.",
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": decision["verdict"],
        "blocks": len(blocks),
        "oracle_gain_bytes": decision["accounting"]["oracle_gain_bytes_after_frame_and_selector"],
        "causal_gain_bytes": causal["gain_bytes_after_frame"],
        "rotated_gain_bytes": rotated["gain_bytes_after_frame"],
        "failed_conditions": failed,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
