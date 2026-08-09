#!/usr/bin/env python3
"""Scale the frozen NNCP cache-32 marginal over the mature native trace."""

from __future__ import annotations

import hashlib
import json
import lzma
import math
import mmap
from pathlib import Path
import resource
import struct

import numpy as np

import nncp_symbol_cache32_marginal_qm0 as cache_q0


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_symbol_cache32_marginal_mature_qm1_v1"
PARENT_ID = "nncp_symbol_cache32_marginal_qm0_v1"
TRACE_PATH = (
    ROOT
    / "results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/"
    "teacher_native_trace.bin"
)
TEACHER_ARCHIVE_PATH = (
    ROOT
    / "results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/"
    "teacher_complete_block.nncp"
)
SYMBOL_PATH = cache_q0.SYMBOL_PATH
ROWS = 1_998_848
BLOCK_SYMBOLS = 499_712
STREAMS = 32
STREAM_STRIDE = 15_616
SEGMENT = 64
VOCABULARY = 16_392
EXPECTED_BRANCHES = 27_984_335
GAIN_GATE_BYTES = 30_000
CONTROL_MARGIN_BYTES = 8_000
SOURCE_LIMIT_BYTES = 65_536
TRACE_HEADER = struct.Struct("<8sQQQQ")
TRACE_ROW = struct.Struct("<QQQQQQQQHHBBB")
TRACE_BRANCH = struct.Struct("<HB")
TRACE_MAGIC = b"NNNTR4\0\0"

EXPECTED = {
    "symbols": (
        401_217_922,
        "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    ),
    "trace": (
        225_871_253,
        "230eb8823665cfe1724fee7de55103ed4d78fc31a0c3d7a2881754d78507acc9",
    ),
    "teacher_archive": (
        2_042_820,
        "00b173f3a5d964bc8f1ab8e0f07d790a891d45f7b011b1a78da86c4c96e65507",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, label: str) -> dict[str, object]:
    expected_bytes, expected_sha = EXPECTED[label]
    row = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if row["bytes"] != expected_bytes or row["sha256"] != expected_sha:
        raise ValueError(f"{label} differs from frozen receipt")
    return row


def coordinates(original: int) -> tuple[int, int, int]:
    block = original // BLOCK_SYMBOLS
    within = original - block * BLOCK_SYMBOLS
    stream = within // STREAM_STRIDE
    local = within - stream * STREAM_STRIDE
    if not 0 <= stream < STREAMS:
        raise ValueError("native stream coordinate is invalid")
    return block, stream, local


def source_window(
    symbols: np.ndarray,
    block: int,
    stream: int,
    local: int,
    arm: str,
) -> list[int]:
    if arm == "base":
        return []
    source_stream = stream
    if arm == "cross":
        source_stream = (stream + cache_q0.CROSS_STREAM_OFFSET) % STREAMS
    stream_start = block * BLOCK_SYMBOLS + source_stream * STREAM_STRIDE
    start = stream_start + max(0, local - cache_q0.CACHE_WINDOW)
    end = stream_start + local
    return [int(value) for value in symbols[start:end]]


def validate_header(mapped: mmap.mmap) -> tuple[int, int]:
    magic, rows, branches, trees, checkpoints = TRACE_HEADER.unpack_from(mapped, 0)
    if (
        magic != TRACE_MAGIC
        or rows != ROWS
        or branches != EXPECTED_BRANCHES
        or trees
        or checkpoints
    ):
        raise ValueError("structured trace header differs from frozen contract")
    return rows, branches


def encode(symbols: np.ndarray) -> dict[str, object]:
    arms = ("base", "cache", "cross")
    encoders = {arm: cache_q0.RangeEncoder() for arm in arms}
    repeat = cache_q0.RangeEncoder()
    thirds = {
        arm: [cache_q0.RangeEncoder() for _ in range(3)] for arm in arms
    }
    ideal_bits = {arm: 0.0 for arm in arms}
    visited_branches = 0
    last_after_bytes = 0
    seen = bytearray(ROWS)

    with TRACE_PATH.open("rb") as source:
        mapped = mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ)
        validate_header(mapped)
        offset = TRACE_HEADER.size
        for execution in range(ROWS):
            row = TRACE_ROW.unpack_from(mapped, offset)
            offset += TRACE_ROW.size
            (
                original,
                observed_execution,
                _before_bits,
                _after_bits,
                _before_bytes,
                after_bytes,
                exact_bits,
                exact_bytes,
                symbol,
                vocabulary,
                branch_count,
                has_tree,
                checkpoint,
            ) = row
            if observed_execution != execution or original >= ROWS or seen[original]:
                raise ValueError("trace execution/original permutation is invalid")
            seen[original] = 1
            block, stream, local = coordinates(original)
            expected_execution = block * BLOCK_SYMBOLS + local * STREAMS + stream
            if execution != expected_execution:
                raise ValueError("trace native execution order changed")
            if (
                symbol != int(symbols[original])
                or vocabulary != VOCABULARY
                or has_tree
                or checkpoint
                or exact_bits
                or exact_bytes
            ):
                raise ValueError("trace symbol or flags differ from receipt")
            truth_bits = cache_q0.phase.expected_bits(symbol)
            if len(truth_bits) != branch_count:
                raise ValueError("trace branch count differs from symbol path")
            arm_state: dict[str, dict[str, object]] = {}
            for arm in arms:
                window = source_window(symbols, block, stream, local, arm)
                arm_state[arm] = {
                    "cache": window,
                    "base_weight": cache_q0.BASE_PRIOR,
                    "cache_weight": cache_q0.CACHE_PRIOR if window else 0.0,
                }
            start = 0
            active = VOCABULARY
            for expected_bit in truth_bits:
                base_zero, trace_bit = TRACE_BRANCH.unpack_from(mapped, offset)
                offset += TRACE_BRANCH.size
                if trace_bit != expected_bit or not 1 <= base_zero < 32_768:
                    raise ValueError("trace branch truth/probability is invalid")
                left = active >> 1
                boundary = start + left
                probabilities: dict[str, int] = {}
                for arm in arms:
                    state_row = arm_state[arm]
                    window = state_row["cache"]
                    probability, base_p0, cache_p0 = (
                        cache_q0.mixed_probability_zero(
                            base_zero,
                            window,
                            start,
                            left,
                            float(state_row["base_weight"]),
                            float(state_row["cache_weight"]),
                        )
                    )
                    probabilities[arm] = probability
                    encoders[arm].put_bit(probability, expected_bit)
                    thirds[arm][min(2, original * 3 // ROWS)].put_bit(
                        probability, expected_bit
                    )
                    realized = probability if expected_bit == 0 else 32_768 - probability
                    ideal_bits[arm] -= math.log2(realized / 32_768)
                    base_weight, cache_weight = cache_q0.update_symbol_mixture(
                        expected_bit,
                        base_p0,
                        cache_p0,
                        float(state_row["base_weight"]),
                        float(state_row["cache_weight"]),
                    )
                    state_row["base_weight"] = base_weight
                    state_row["cache_weight"] = cache_weight
                    state_row["cache"] = [
                        cached
                        for cached in window
                        if (cached < boundary) == (expected_bit == 0)
                    ]
                repeat.put_bit(probabilities["cache"], expected_bit)
                if expected_bit:
                    start = boundary
                    active -= left
                else:
                    active = left
                visited_branches += 1
            if start != symbol or active != 1:
                raise ValueError("symbol path did not terminate at truth")
            last_after_bytes = after_bytes
        if offset != len(mapped):
            raise ValueError("structured trace was not consumed exactly")
        mapped.close()
    if visited_branches != EXPECTED_BRANCHES or not all(seen):
        raise ValueError("trace population/permutation is incomplete")

    payloads = {arm: encoder.finish() for arm, encoder in encoders.items()}
    repeat_payload = repeat.finish()
    third_payloads = {
        arm: [encoder.finish() for encoder in coders]
        for arm, coders in thirds.items()
    }
    return {
        "payloads": payloads,
        "repeat_payload": repeat_payload,
        "third_payloads": third_payloads,
        "ideal_bits": ideal_bits,
        "visited_branches": visited_branches,
        "last_trace_after_bytes": last_after_bytes,
    }


def decode_cache(payload: bytes, expected: np.ndarray) -> dict[str, object]:
    decoded = np.zeros(ROWS, dtype=np.uint16)
    decoder = cache_q0.RangeDecoder(payload)
    visited_branches = 0
    with TRACE_PATH.open("rb") as source:
        mapped = mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ)
        validate_header(mapped)
        offset = TRACE_HEADER.size
        for execution in range(ROWS):
            row = TRACE_ROW.unpack_from(mapped, offset)
            offset += TRACE_ROW.size
            original = int(row[0])
            branch_count = int(row[-3])
            block, stream, local = coordinates(original)
            window = source_window(decoded, block, stream, local, "cache")
            base_weight = cache_q0.BASE_PRIOR
            cache_weight = cache_q0.CACHE_PRIOR if window else 0.0
            start = 0
            active = VOCABULARY
            for _ in range(branch_count):
                base_zero, trace_truth = TRACE_BRANCH.unpack_from(mapped, offset)
                offset += TRACE_BRANCH.size
                left = active >> 1
                boundary = start + left
                probability, base_p0, cache_p0 = (
                    cache_q0.mixed_probability_zero(
                        base_zero,
                        window,
                        start,
                        left,
                        base_weight,
                        cache_weight,
                    )
                )
                bit = decoder.get_bit(probability)
                if bit != trace_truth:
                    raise ValueError("cache decoder differs from trace truth")
                base_weight, cache_weight = cache_q0.update_symbol_mixture(
                    bit,
                    base_p0,
                    cache_p0,
                    base_weight,
                    cache_weight,
                )
                window = [
                    cached
                    for cached in window
                    if (cached < boundary) == (bit == 0)
                ]
                if bit:
                    start = boundary
                    active -= left
                else:
                    active = left
                visited_branches += 1
            if active != 1 or start != int(expected[original]):
                raise ValueError("decoded mature symbol differs from input")
            decoded[original] = start
        if offset != len(mapped):
            raise ValueError("decoder did not consume the complete trace")
        mapped.close()
    return {
        "symbols_exact": bool(np.array_equal(decoded, expected[:ROWS])),
        "decoded_sha256": cache_q0.sha256_bytes(
            decoded.astype(">u2", copy=False).tobytes()
        ),
        "branches": visited_branches,
    }


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    inputs = {
        "symbols": artifact(SYMBOL_PATH, "symbols"),
        "trace": artifact(TRACE_PATH, "trace"),
        "teacher_archive": artifact(TEACHER_ARCHIVE_PATH, "teacher_archive"),
    }
    parent_decision_path = ROOT / "results" / PARENT_ID / "decision.json"
    parent = json.loads(parent_decision_path.read_text())
    if parent.get("verdict") != "authorize_open_same_object_cache_port":
        raise ValueError("cache maturity parent is not authorized")

    symbols = np.memmap(SYMBOL_PATH, mode="r", dtype=">u2")
    replay = encode(symbols)
    payloads = replay["payloads"]
    decode = decode_cache(payloads["cache"], symbols)
    output_dir.mkdir(parents=True)
    for arm, payload in payloads.items():
        (output_dir / f"{arm}.bin").write_bytes(payload)

    base_bytes = len(payloads["base"])
    candidate_bytes = len(payloads["cache"])
    control_bytes = len(payloads["cross"])
    candidate_gain = base_bytes - candidate_bytes
    control_gain = base_bytes - control_bytes
    control_margin = candidate_gain - control_gain
    third_gains = [
        len(replay["third_payloads"]["base"][index])
        - len(replay["third_payloads"]["cache"][index])
        for index in range(3)
    ]
    constant_archive_bytes = EXPECTED["teacher_archive"][0] - base_bytes
    trace_substituted_archive_bytes = constant_archive_bytes + candidate_bytes

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_symbol_cache32_marginal_qm0.py",
        ROOT / "tools/nncp_midpoint_phase_attribution_qm0.py",
        ROOT / "docs/nncp_symbol_cache32_marginal_mature_qm1_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        ROOT
        / f"operations/adaptive/proposals/developed/000_{CANDIDATE_ID}.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)

    conditions = {
        "candidate_gain_at_least_30000": candidate_gain >= GAIN_GATE_BYTES,
        "all_chronological_thirds_positive": all(value > 0 for value in third_gains),
        "control_margin_at_least_8000": control_margin >= CONTROL_MARGIN_BYTES,
        "repeat_payload_identical": replay["repeat_payload"] == payloads["cache"],
        "arithmetic_decode_exact": bool(decode["symbols_exact"]),
        "branch_population_exact": replay["visited_branches"] == EXPECTED_BRANCHES,
        "source_at_most_65536": len(source_package) <= SOURCE_LIMIT_BYTES,
    }
    passed = all(conditions.values())
    decision = {
        "schema": "enwiki9_nncp_symbol_cache32_marginal_mature_qm1_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "CAUSAL_MATURE_SHADOW_COMPLETE",
        "verdict": (
            "authorize_native_and_open_cache_integration"
            if passed
            else "retire_mature_symbol_cache32_marginal"
        ),
        "epistemic_tier": "mature_same_symbol_domain_exact_arithmetic_shadow_zero_score_credit",
        "score_credit_bytes": 0,
        "model": {
            "cache_window": cache_q0.CACHE_WINDOW,
            "base_prior_mass": cache_q0.BASE_PRIOR,
            "cache_prior_mass": cache_q0.CACHE_PRIOR,
            "cross_stream_offset": cache_q0.CROSS_STREAM_OFFSET,
            "block_history_reset": True,
            "source_selector_transmitted": False,
            "distance_or_length_transmitted": False,
        },
        "population": {
            "symbols": ROWS,
            "block_symbols": BLOCK_SYMBOLS,
            "blocks": ROWS // BLOCK_SYMBOLS,
            "streams_per_block": STREAMS,
            "symbols_per_stream": STREAM_STRIDE,
            "branches": EXPECTED_BRANCHES,
        },
        "inputs": {
            **inputs,
            "parent_decision_sha256": sha256_file(parent_decision_path),
            "driver_sha256": sha256_file(Path(__file__)),
        },
        "arithmetic": {
            "base_bytes": base_bytes,
            "base_sha256": cache_q0.sha256_bytes(payloads["base"]),
            "candidate_bytes": candidate_bytes,
            "candidate_sha256": cache_q0.sha256_bytes(payloads["cache"]),
            "candidate_repeat_sha256": cache_q0.sha256_bytes(replay["repeat_payload"]),
            "candidate_gain_bytes": candidate_gain,
            "cross_control_bytes": control_bytes,
            "cross_control_sha256": cache_q0.sha256_bytes(payloads["cross"]),
            "cross_control_gain_bytes": control_gain,
            "candidate_margin_over_control_bytes": control_margin,
            "chronological_third_gain_bytes": third_gains,
            "ideal_bits": replay["ideal_bits"],
            "last_trace_after_bytes": replay["last_trace_after_bytes"],
            "teacher_archive_constant_bytes_if_trace_substituted": constant_archive_bytes,
            "trace_substituted_archive_bytes": trace_substituted_archive_bytes,
        },
        "decode": decode,
        "conditions": conditions,
        "decision": {
            "native_integration_authorized": passed,
            "promotion_authorized": False,
            "verified_full_1g_score_bytes": None,
            "forecast_bytes": 109_389_323,
        },
        "claim_boundary": (
            "This mature exact arithmetic replay still consumes a teacher "
            "probability trace. The substituted archive arithmetic is not a "
            "native NNCP file, LibNC remains ineligible, and the result earns "
            "zero Hutter score or forecast credit until decoder-built native "
            "and open-source integration succeeds."
        ),
        "artifacts": {
            "incremental_source_package": {
                "path": str(source_path.relative_to(ROOT)),
                "bytes": len(source_package),
                "sha256": sha256_file(source_path),
                "limit_bytes": SOURCE_LIMIT_BYTES,
            }
        },
        "resource": {
            "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
    }
    decision_path = output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "candidate_gain_bytes": candidate_gain,
                "control_margin_bytes": control_margin,
                "third_gains": third_gains,
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
