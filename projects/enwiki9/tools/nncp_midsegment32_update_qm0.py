#!/usr/bin/env python3
"""Exact NNCP gate for one causal 32/32 mid-segment Adam update."""

from __future__ import annotations

from array import array
import hashlib
import json
import lzma
import os
from pathlib import Path
import sys
import time


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
import torch.nn.functional as F

import nncp_evicted_ema_memory_qm0 as comparison_harness


parent = comparison_harness.parent
core = parent.core
cache_q0 = parent.cache_q0
CANDIDATE_ID = "nncp_midsegment32_update_qm0_v1"
BASELINE_ID = comparison_harness.BASELINE_ID
BASELINE_ARCHIVE_BYTES = comparison_harness.BASELINE_ARCHIVE_BYTES
BASELINE_ARCHIVE_SHA256 = comparison_harness.BASELINE_ARCHIVE_SHA256
BASELINE_TRACE_SHA256 = comparison_harness.BASELINE_TRACE_SHA256
SYMBOL_COUNT = comparison_harness.SYMBOL_COUNT
STREAM_LENGTH = comparison_harness.STREAM_LENGTH
MIDPOINT = 32
ACTUAL_GAIN_GATE_BYTES = 800
SOURCE_LIMIT_BYTES = 65_536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def update_slice(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    logits: torch.Tensor,
    targets: torch.Tensor,
    config: object,
) -> float:
    loss = F.cross_entropy(
        logits.reshape(-1, config.vocabulary), targets.reshape(-1)
    )
    loss.backward()
    core.per_parameter_clip(model, config.gradient_clip)
    optimizer.step()
    return float(loss.detach().cpu())


def causal_inputs(
    values: torch.Tensor,
    segment_start: int,
    known_states: int,
    segment_length: int,
) -> torch.Tensor:
    inputs = torch.zeros(
        values.shape[0],
        segment_length,
        dtype=torch.long,
        device=values.device,
    )
    if segment_start:
        inputs[:, 0] = values[:, segment_start - 1]
    if known_states > 1:
        inputs[:, 1:known_states] = values[
            :, segment_start : segment_start + known_states - 1
        ]
    return inputs


def input_symbol(
    values: torch.Tensor, absolute: int
) -> torch.Tensor:
    if absolute == 0:
        return torch.zeros(
            values.shape[0], dtype=torch.long, device=values.device
        )
    return values[:, absolute - 1]


def run_once(
    symbols: np.ndarray,
    config: object,
    device: torch.device,
    mode: str,
    payload: bytes | None = None,
) -> dict[str, object]:
    if mode not in ("encode_first", "encode_second", "decode"):
        raise ValueError(f"invalid run mode: {mode}")
    if config.segment_length != 64:
        raise ValueError("midsegment gate requires the frozen length 64")
    print(json.dumps({"event": "run_start", "mode": mode}), flush=True)
    torch.cuda.reset_peak_memory_stats(device)
    model = core.make_model(config, device)
    optimizer = core.optimizer_for(model, config)
    memories = model.empty_memory(device)
    source_matrix = symbols.reshape(config.streams, STREAM_LENGTH)
    if mode == "decode":
        values = torch.zeros(
            config.streams,
            STREAM_LENGTH,
            dtype=torch.long,
            device=device,
        )
        coder: core.RangeEncoder | core.RangeDecoder = core.RangeDecoder(
            payload or b""
        )
    else:
        values = torch.from_numpy(source_matrix.astype(np.int64)).to(device)
        coder = core.RangeEncoder()
    trace = array("H")
    losses: list[float] = []
    segment_count = STREAM_LENGTH // config.segment_length
    torch.cuda.synchronize(device)
    started = time.monotonic()

    for segment in range(segment_count):
        segment_start = segment * config.segment_length
        segment_end = segment_start + config.segment_length

        with torch.inference_mode():
            caches = cache_q0.make_layer_caches(model, memories)
            for state in range(MIDPOINT):
                absolute = segment_start + state
                logits = cache_q0.incremental_logits(
                    model, input_symbol(values, absolute), caches, state
                )
                probability = torch.softmax(logits, dim=-1).cpu().numpy()
                if mode == "decode":
                    for stream in range(config.streams):
                        values[stream, absolute] = core.branch_decode_one(
                            coder, probability[stream], trace
                        )
                else:
                    core.branch_encode(
                        coder, probability, source_matrix[:, absolute], trace
                    )
                del logits, probability
        del caches

        first_inputs = causal_inputs(
            values, segment_start, MIDPOINT, config.segment_length
        )
        first_targets = values[:, segment_start : segment_start + MIDPOINT]
        optimizer.zero_grad(set_to_none=True)
        first_logits, _ = model(first_inputs, memories)
        losses.append(
            update_slice(
                model,
                optimizer,
                first_logits[:, :MIDPOINT],
                first_targets,
                config,
            )
        )
        del first_inputs, first_targets, first_logits
        torch.cuda.empty_cache()

        with torch.inference_mode():
            caches = cache_q0.make_layer_caches(model, memories)
            for state in range(MIDPOINT):
                absolute = segment_start + state
                replay_logits = cache_q0.incremental_logits(
                    model, input_symbol(values, absolute), caches, state
                )
                del replay_logits
            for state in range(MIDPOINT, config.segment_length):
                absolute = segment_start + state
                logits = cache_q0.incremental_logits(
                    model, input_symbol(values, absolute), caches, state
                )
                probability = torch.softmax(logits, dim=-1).cpu().numpy()
                if mode == "decode":
                    for stream in range(config.streams):
                        values[stream, absolute] = core.branch_decode_one(
                            coder, probability[stream], trace
                        )
                else:
                    core.branch_encode(
                        coder, probability, source_matrix[:, absolute], trace
                    )
                del logits, probability
        del caches

        full_inputs = causal_inputs(
            values, segment_start, config.segment_length, config.segment_length
        )
        second_targets = values[:, segment_start + MIDPOINT : segment_end]
        optimizer.zero_grad(set_to_none=True)
        full_logits, next_memories = model(full_inputs, memories)
        losses.append(
            update_slice(
                model,
                optimizer,
                full_logits[:, MIDPOINT:],
                second_targets,
                config,
            )
        )
        memories = [memory.detach() for memory in next_memories]
        del full_inputs, second_targets, full_logits, next_memories
        if (segment + 1) % 4 == 0:
            torch.cuda.synchronize(device)
            print(
                json.dumps(
                    {
                        "elapsed_seconds": time.monotonic() - started,
                        "event": "run_checkpoint",
                        "mode": mode,
                        "segments": segment + 1,
                        "total_segments": segment_count,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    archive = coder.finish() if mode != "decode" else payload
    torch.cuda.synchronize(device)
    model_state = core.parameter_state_hash(model)
    adam_state = parent.headroom_q1.optimizer_hash(model, optimizer)
    persistent_state = parent.headroom_q1.memory_hash(memories)
    complete_state = parent.headroom_q1.complete_state_hash(
        model_state, adam_state, persistent_state
    )
    result = {
        "archive": archive,
        "branch_trace": trace,
        "complete_state_sha256": complete_state,
        "decoded": (
            values.detach().cpu().numpy().astype(np.uint16)
            if mode == "decode"
            else None
        ),
        "elapsed_seconds": time.monotonic() - started,
        "losses": losses,
        "model_sha256": model_state,
        "optimizer_sha256": adam_state,
        "persistent_memory_sha256": persistent_state,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
    }
    del optimizer, model, memories, values
    torch.cuda.empty_cache()
    print(
        json.dumps(
            {
                "archive_bytes": len(archive or b""),
                "complete_state_sha256": complete_state,
                "elapsed_seconds": result["elapsed_seconds"],
                "event": "run_complete",
                "mode": mode,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return result


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

    parent.run_once = run_once
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
    ideal = comparison_harness.aligned_ideal_gain(
        symbols, baseline_trace, candidate_trace
    )
    actual_gain = BASELINE_ARCHIVE_BYTES - candidate_archive.stat().st_size

    source_paths = (
        Path(__file__),
        ROOT / "docs/nncp_midsegment32_update_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)

    failed: list[str] = []
    if not all(bool(value) for value in decision["integrity"].values()):
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
            "schema": "enwiki9_nncp_midsegment32_update_qm0_v1",
            "candidate_id": CANDIDATE_ID,
            "epistemic_tier": "exact_65536_symbol_constructive_child_zero_credit",
            "status": "AUTHORIZED_MATURE_MIDSEGMENT32" if promotion else "REJECT",
            "verdict": (
                "authorize_mature_midsegment32_update"
                if promotion
                else "retire_midsegment_update_schedule"
            ),
            "score_credit_bytes": 0,
            "update_schedule": {
                "segment_symbols": 64,
                "first_update_after_symbols": MIDPOINT,
                "second_update_after_symbols": 64,
                "updates_per_segment": 2,
                "first_loss_population": "states_0_through_31_only",
                "second_loss_population": "states_32_through_63_only",
                "post_midpoint_kv_rebuilt": True,
                "outgoing_memory_convention": "pre_second_update_forward",
                "parameter_delta": 0,
                "archive_side_information_bytes": 0,
            },
            "faithful_baseline": {
                "candidate_id": BASELINE_ID,
                "archive_bytes": BASELINE_ARCHIVE_BYTES,
                "archive_sha256": BASELINE_ARCHIVE_SHA256,
                "branch_trace_sha256": BASELINE_TRACE_SHA256,
            },
            "midsegment_comparison": {
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
                "Exact frozen 32/32 causal update-schedule child at 65,536 "
                "symbols. No split-point, learning-rate, optimizer, loss-weight, "
                "segment-length, published-score, or full-corpus inheritance."
            ),
        }
    )
    decision["decision"]["promotion_authorized"] = promotion
    decision["inputs"]["midsegment_driver_script_sha256"] = sha256_file(
        Path(__file__)
    )
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
        print(f"nncp-midsegment32-update-qm0: {error}", file=sys.stderr)
        raise
