#!/usr/bin/env python3
"""Test one fixed decoder-built evicted-state EMA in the 65,536-symbol NNCP gate."""

from __future__ import annotations

import hashlib
import json
import lzma
import math
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
ROCM_PYTHON = Path("/home/x/deco/gamma/.venv_rocm/bin/python")
os.environ.setdefault("AMD_SERIALIZE_KERNEL", "3")
os.environ.setdefault("HSA_OVERRIDE_GFX_VERSION", "11.0.0")
if Path(sys.executable) != ROCM_PYTHON:
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing receipt-bound ROCm interpreter: {ROCM_PYTHON}")
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        os.environ.copy(),
    )

import numpy as np
import torch

import nncp_v33_rocm_incremental_kv_65536_headroom_q1 as parent


CANDIDATE_ID = "nncp_evicted_ema_memory_qm0_v1"
BASELINE_ID = "nncp_v33_rocm_incremental_kv_65536_headroom_q1_v1"
BASELINE_ARCHIVE_BYTES = 96_142
BASELINE_ARCHIVE_SHA256 = (
    "787a7b8510b7f8daec38aa54166d82440ca3ba6c5f078728d3395068c4349d59"
)
BASELINE_TRACE_SHA256 = (
    "bbba5b7060bfde6accf46255416c49ee77688e5ebea8765a854f45da7efac383"
)
SYMBOL_COUNT = 65_536
STREAMS = 32
STREAM_LENGTH = SYMBOL_COUNT // STREAMS
SEGMENT = 64
VOCABULARY = 16_392
PROBABILITY_TOTAL = 1 << 15
ACTUAL_GAIN_GATE_BYTES = 800
SOURCE_LIMIT_BYTES = 65_536
DECAY = 0.5


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_bits(symbol: int) -> list[int]:
    start = 0
    active = VOCABULARY
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
        raise ValueError("balanced symbol path did not terminate at truth")
    return bits


def aligned_ideal_gain(
    symbols: np.ndarray, baseline_trace: np.ndarray, candidate_trace: np.ndarray
) -> dict[str, object]:
    if len(baseline_trace) != len(candidate_trace):
        raise ValueError("candidate branch population differs from faithful parent")
    matrix = symbols.reshape(STREAMS, STREAM_LENGTH)
    gain_bits = 0.0
    thirds = [0.0, 0.0, 0.0]
    branch = 0
    for segment_start in range(0, STREAM_LENGTH, SEGMENT):
        for state in range(SEGMENT):
            absolute = segment_start + state
            for stream in range(STREAMS):
                symbol = int(matrix[stream, absolute])
                original = stream * STREAM_LENGTH + absolute
                third = min(2, original * 3 // SYMBOL_COUNT)
                for bit in expected_bits(symbol):
                    base_zero = int(baseline_trace[branch])
                    candidate_zero = int(candidate_trace[branch])
                    base_mass = base_zero if bit == 0 else PROBABILITY_TOTAL - base_zero
                    candidate_mass = (
                        candidate_zero
                        if bit == 0
                        else PROBABILITY_TOTAL - candidate_zero
                    )
                    if min(base_mass, candidate_mass) <= 0:
                        raise ValueError("illegal branch frequency")
                    delta = math.log2(candidate_mass / base_mass)
                    gain_bits += delta
                    thirds[third] += delta
                    branch += 1
    if branch != len(baseline_trace):
        raise ValueError("branch trace was not consumed exactly")
    return {
        "branch_frequencies": branch,
        "gain_bits": gain_bits,
        "gain_bytes": gain_bits / 8.0,
        "chronological_third_gain_bytes": [value / 8.0 for value in thirds],
    }


def install_ema_memory() -> None:
    block_type = parent.core.RelativeBlock
    faithful_forward = block_type.forward

    def ema_forward(
        self: object,
        value: torch.Tensor,
        memory: torch.Tensor,
        shared_relative_bias: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        output, faithful_next = faithful_forward(
            self, value, memory, shared_relative_bias
        )
        if memory.shape[1] != 256 or faithful_next.shape[1] != 256:
            raise ValueError("EMA child requires the frozen 256-slot memory")
        evicted_exact = memory[:, 1:65, :].float().mean(dim=1)
        prior_summary = memory[:, 0, :].float()
        summary = (
            DECAY * prior_summary + (1.0 - DECAY) * evicted_exact
        ).to(memory.dtype)
        next_memory = torch.cat(
            (summary[:, None, :], faithful_next[:, -255:, :]), dim=1
        )
        return output, next_memory

    block_type.forward = ema_forward


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if "--output-dir" not in sys.argv:
        sys.argv.extend(("--output-dir", str(output_dir)))
    else:
        output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve()
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")

    baseline_dir = ROOT / "results" / BASELINE_ID
    baseline_archive = baseline_dir / "archive.bin"
    baseline_trace_path = baseline_dir / "branch_trace.bin"
    if (
        baseline_archive.stat().st_size != BASELINE_ARCHIVE_BYTES
        or sha256_file(baseline_archive) != BASELINE_ARCHIVE_SHA256
        or sha256_file(baseline_trace_path) != BASELINE_TRACE_SHA256
    ):
        raise ValueError("faithful 65,536-symbol baseline identity mismatch")

    install_ema_memory()
    parent.CANDIDATE_ID = CANDIDATE_ID
    status = parent.main()

    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    candidate_archive = output_dir / "archive.bin"
    candidate_trace_path = output_dir / "branch_trace.bin"
    preprocessed_path = Path(
        "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
        "preprocessed.bin"
    )
    symbols = np.asarray(
        np.memmap(preprocessed_path, mode="r", dtype=">u2")[:SYMBOL_COUNT],
        dtype=np.uint16,
    )
    baseline_trace = np.memmap(baseline_trace_path, mode="r", dtype="<u2")
    candidate_trace = np.memmap(candidate_trace_path, mode="r", dtype="<u2")
    ideal = aligned_ideal_gain(symbols, baseline_trace, candidate_trace)
    actual_gain = BASELINE_ARCHIVE_BYTES - candidate_archive.stat().st_size

    source_paths = (
        Path(__file__),
        ROOT / "docs/nncp_evicted_ema_memory_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)

    failed: list[str] = []
    integrity = decision["integrity"]
    if not all(bool(value) for value in integrity.values()):
        failed.append("exact_identity_failed")
    if actual_gain < ACTUAL_GAIN_GATE_BYTES:
        failed.append("actual_archive_gain_below_800")
    if any(value <= 0 for value in ideal["chronological_third_gain_bytes"]):
        failed.append("aligned_ideal_chronological_third_nonpositive")
    resource = decision["resource"]
    if not (
        resource["decimal_10gb_allocated_pass"]
        and resource["decimal_10gb_reserved_pass"]
    ):
        failed.append("decimal_10gb_memory_failed")
    if len(source_package) > SOURCE_LIMIT_BYTES:
        failed.append("incremental_source_exceeds_65536")

    promotion = not failed
    decision.update(
        {
            "schema": "enwiki9_nncp_evicted_ema_memory_qm0_v1",
            "candidate_id": CANDIDATE_ID,
            "epistemic_tier": "exact_65536_symbol_constructive_child_zero_credit",
            "status": "AUTHORIZED_MATURE_EMA" if promotion else "REJECT",
            "verdict": (
                "authorize_mature_evicted_ema"
                if promotion
                else "retire_evicted_ema_memory"
            ),
            "score_credit_bytes": 0,
            "ema_memory": {
                "decay": DECAY,
                "summary_slots_per_layer_stream": 1,
                "exact_recent_slots_per_layer_stream": 255,
                "summarized_oldest_exact_slots_per_update": 64,
                "parameter_delta": 0,
                "resident_memory_shape_delta": 0,
            },
            "faithful_baseline": {
                "candidate_id": BASELINE_ID,
                "archive_bytes": BASELINE_ARCHIVE_BYTES,
                "archive_sha256": BASELINE_ARCHIVE_SHA256,
                "branch_trace_sha256": BASELINE_TRACE_SHA256,
            },
            "ema_comparison": {
                "candidate_archive_bytes": candidate_archive.stat().st_size,
                "candidate_archive_sha256": sha256_file(candidate_archive),
                "actual_gain_bytes": actual_gain,
                "required_actual_gain_bytes": ACTUAL_GAIN_GATE_BYTES,
                "aligned_ideal": ideal,
                "incremental_source_package_bytes": len(source_package),
                "incremental_source_limit_bytes": SOURCE_LIMIT_BYTES,
            },
            "failed_conditions": failed,
            "claim_boundary": (
                "Exact fixed-decay one-slot evicted-state EMA child at 65,536 "
                "symbols. No decay, slot-count, pooling, context-length, published "
                "score, package forecast, or full-corpus inheritance."
            ),
        }
    )
    decision["decision"]["promotion_authorized"] = promotion
    decision["inputs"]["ema_driver_script_sha256"] = sha256_file(Path(__file__))
    decision["artifacts"] = {
        "incremental_source_package": {
            "path": str(source_path.relative_to(ROOT)),
            "bytes": len(source_package),
            "sha256": sha256_file(source_path),
        }
    }
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "actual_gain_bytes": actual_gain,
                "candidate_archive_bytes": candidate_archive.stat().st_size,
                "failed_conditions": failed,
                "ideal_third_gain_bytes": ideal[
                    "chronological_third_gain_bytes"
                ],
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return status


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"nncp-evicted-ema-memory-qm0: {error}", file=sys.stderr)
        raise
