#!/usr/bin/env python3
"""Test decoder-causal incremental KV inference for NNCP v3.3 on ROCm."""

from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import struct
import sys
import time
from typing import Any


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

import nncp_v33_rocm_constructive_causal_replay_q0 as causal_q0


core = causal_q0.core
CANDIDATE_ID = "nncp_v33_rocm_incremental_kv_runtime_q0_v1"
SYMBOL_COUNT = core.Config.streams * core.Config.segment_length
REFERENCE_MEDIAN_SECONDS = 18.22064109100029
REQUIRED_REDUCTION = 0.50
MAX_ARCHIVE_DELTA_BYTES = 16
DECIMAL_10GB = 10_000_000_000
EXPECTED = {
    "baseline_decision": "a9867196c1655da5b60296454f07d1a24d08f57b0dcf458c38fab7d86492b308",
    "baseline_archive": "823ca1f776e8db93911b0670a1043a5190621d2cfd60d40c3e29ce1b830683e4",
    "baseline_trace": "9d76279b8e8ecd40be9011a8e12df755534b98bdee1ecd4eb21b856f62685cd3",
    "preprocessed": "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
}
REFERENCE_MODEL_SHA256 = "2ae4efe57f08736c3e7d3f67104b74a496f4c54af6ee24b142904ab0be5014f5"
REFERENCE_LOSS = 9.782143592834473


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def tensor_bytes(value: torch.Tensor) -> bytes:
    host = value.detach().contiguous().cpu()
    if host.dtype == torch.bfloat16:
        return host.view(torch.uint16).numpy().tobytes()
    return host.numpy().tobytes()


def optimizer_hash(
    model: torch.nn.Module, optimizer: torch.optim.Optimizer
) -> str:
    digest = hashlib.sha256()
    for index, parameter in enumerate(model.parameters()):
        digest.update(struct.pack("<I", index))
        state = optimizer.state.get(parameter, {})
        for key in sorted(state):
            digest.update(str(key).encode("ascii") + b"\0")
            value = state[key]
            if torch.is_tensor(value):
                digest.update(str(value.dtype).encode("ascii") + b"\0")
                digest.update(tensor_bytes(value))
            else:
                digest.update(repr(value).encode("ascii") + b"\0")
    return digest.hexdigest()


def memory_hash(memories: list[torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for index, memory in enumerate(memories):
        digest.update(struct.pack("<I", index))
        digest.update(tensor_bytes(memory))
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def bind(path: Path, expected: str, label: str) -> dict[str, Any]:
    row = artifact(path)
    if row["sha256"] != expected:
        raise ValueError(f"{label} identity mismatch: {row['sha256']}")
    return row


def make_layer_caches(
    model: core.FaithfulModel, memories: list[torch.Tensor]
) -> list[tuple[torch.Tensor, torch.Tensor]]:
    config = model.config
    caches: list[tuple[torch.Tensor, torch.Tensor]] = []
    for block, memory in zip(model.blocks, memories, strict=True):
        key_value = F.linear(memory, block.key_value)
        key, value = torch.split(
            key_value,
            (
                config.heads * config.key_width,
                config.heads * config.value_width,
            ),
            dim=-1,
        )
        key = key.view(
            config.streams, config.memory_length,
            config.heads, config.key_width,
        ).transpose(1, 2)
        value = value.view(
            config.streams, config.memory_length,
            config.heads, config.value_width,
        ).transpose(1, 2)
        key_cache = torch.empty(
            config.streams, config.heads, config.relative_positions,
            config.key_width, dtype=key.dtype, device=key.device,
        )
        value_cache = torch.empty(
            config.streams, config.heads, config.relative_positions,
            config.value_width, dtype=value.dtype, device=value.device,
        )
        key_cache[:, :, : config.memory_length].copy_(key)
        value_cache[:, :, : config.memory_length].copy_(value)
        caches.append((key_cache, value_cache))
    return caches


def incremental_logits(
    model: core.FaithfulModel,
    input_symbols: torch.Tensor,
    caches: list[tuple[torch.Tensor, torch.Tensor]],
    state: int,
) -> torch.Tensor:
    config = model.config
    value = F.embedding(input_symbols[:, None], model.embedding).to(torch.bfloat16)
    value = value * math.sqrt(config.width)
    cache_position = config.memory_length + state
    active_length = cache_position + 1
    relative_offset = config.segment_length - 1 - state

    for block, (key_cache, value_cache) in zip(
        model.blocks, caches, strict=True
    ):
        normalized = block.attention_norm(value)
        query = F.linear(normalized, block.query)
        current_key_value = F.linear(normalized, block.key_value)
        current_key, current_value = torch.split(
            current_key_value,
            (
                config.heads * config.key_width,
                config.heads * config.value_width,
            ),
            dim=-1,
        )
        query = query.view(
            config.streams, 1, config.heads, config.key_width
        ).transpose(1, 2)
        current_key = current_key.view(
            config.streams, 1, config.heads, config.key_width
        ).transpose(1, 2)
        current_value = current_value.view(
            config.streams, 1, config.heads, config.value_width
        ).transpose(1, 2)
        key_cache[:, :, cache_position : cache_position + 1].copy_(current_key)
        value_cache[:, :, cache_position : cache_position + 1].copy_(current_value)

        keys = key_cache[:, :, :active_length]
        values = value_cache[:, :, :active_length]
        content = torch.einsum("bhtd,bhkd->bhtk", query, keys)
        relative_key = block.relative.transpose(1, 2)[
            :, relative_offset : relative_offset + active_length
        ]
        relative = torch.einsum("bhtd,hkd->bhtk", query, relative_key)
        relative_bias = model.shared_relative_bias[
            relative_offset : relative_offset + active_length
        ].T[None, :, None, :]
        relative = relative + relative_bias * math.sqrt(
            config.key_width * config.width
        )
        score = (content + relative) / math.sqrt(config.key_width)
        attention = torch.softmax(score.float(), dim=-1).to(value.dtype)
        attended = torch.einsum("bhtk,bhkd->bhtd", attention, values)
        attended = attended.transpose(1, 2).reshape(
            config.streams, 1, config.heads * config.value_width
        )
        value = value + F.linear(attended, block.output)

        feedforward = block.feedforward_norm(value)
        gate, content_ff = F.linear(
            feedforward,
            block.feedforward_in,
            block.feedforward_in_bias,
        ).chunk(2, dim=-1)
        hidden = core.libnc_gelu(gate) * content_ff
        value = value + F.linear(
            hidden, block.feedforward_out, block.feedforward_out_bias
        )

    value = model.final_norm(value)
    return F.linear(value, model.output_embedding, model.output_bias).float()[:, 0]


def run_once(
    symbols: np.ndarray,
    config: core.Config,
    device: torch.device,
    mode: str,
    payload: bytes | None = None,
) -> dict[str, Any]:
    if mode not in {"encode_a", "encode_b", "decode"}:
        raise ValueError(f"invalid mode: {mode}")
    print(json.dumps({"event": "run_start", "mode": mode}), flush=True)
    torch.cuda.reset_peak_memory_stats(device)
    model = core.make_model(config, device)
    optimizer = core.optimizer_for(model, config)
    memories = model.empty_memory(device)
    source_matrix = symbols.reshape(config.streams, config.segment_length)
    if mode == "decode":
        values = torch.zeros(
            config.streams, config.segment_length,
            dtype=torch.long, device=device,
        )
        coder: core.RangeEncoder | core.RangeDecoder = core.RangeDecoder(payload or b"")
    else:
        values = torch.from_numpy(source_matrix.astype(np.int64)).to(device)
        coder = core.RangeEncoder()
    trace = array("H")

    torch.cuda.synchronize(device)
    started = time.monotonic()
    with torch.inference_mode():
        caches = make_layer_caches(model, memories)
        for state in range(config.segment_length):
            input_symbols = (
                torch.zeros(config.streams, dtype=torch.long, device=device)
                if state == 0
                else values[:, state - 1]
            )
            logits = incremental_logits(model, input_symbols, caches, state)
            probability = torch.softmax(logits, dim=-1).cpu().numpy()
            if mode == "decode":
                for stream in range(config.streams):
                    values[stream, state] = core.branch_decode_one(
                        coder, probability[stream], trace
                    )
            else:
                core.branch_encode(
                    coder, probability, source_matrix[:, state], trace
                )
            del logits, probability
    del caches
    torch.cuda.empty_cache()

    inputs = core.shifted_inputs(values)
    optimizer.zero_grad(set_to_none=True)
    train_logits, next_memories = model(inputs, memories)
    loss = core.update_model(model, optimizer, train_logits, values, config)
    archive = coder.finish() if mode != "decode" else payload
    torch.cuda.synchronize(device)
    elapsed = time.monotonic() - started
    result = {
        "archive": archive,
        "trace": core.trace_bytes(trace),
        "decoded": (
            values.detach().cpu().numpy().astype(np.uint16)
            if mode == "decode" else None
        ),
        "elapsed_seconds": elapsed,
        "loss_nats": loss,
        "model_sha256": core.parameter_state_hash(model),
        "optimizer_sha256": optimizer_hash(model, optimizer),
        "memory_sha256": memory_hash([item.detach() for item in next_memories]),
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
    }
    del train_logits, next_memories, optimizer, model, memories, values, inputs
    torch.cuda.empty_cache()
    print(
        json.dumps(
            {
                "archive_bytes": len(archive or b""),
                "elapsed_seconds": elapsed,
                "event": "run_complete",
                "mode": mode,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preprocessed", type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/preprocessed.bin"
        ),
    )
    parser.add_argument(
        "--baseline-decision", type=Path,
        default=ROOT / "results/nncp_v33_rocm_constructive_causal_replay_q0_v1/decision.json",
    )
    parser.add_argument(
        "--baseline-archive", type=Path,
        default=ROOT / "results/nncp_v33_rocm_constructive_causal_replay_q0_v1/archive.bin",
    )
    parser.add_argument(
        "--baseline-trace", type=Path,
        default=ROOT / "results/nncp_v33_rocm_constructive_causal_replay_q0_v1/branch_trace.bin",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "results" / CANDIDATE_ID,
    )
    args = parser.parse_args()
    required = (
        args.preprocessed, args.baseline_decision,
        args.baseline_archive, args.baseline_trace,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"missing inputs: {missing}")
    if not torch.cuda.is_available() or torch.version.hip is None:
        raise SystemExit("PyTorch ROCm is required")

    inputs = {
        "preprocessed": bind(args.preprocessed, EXPECTED["preprocessed"], "preprocessed"),
        "baseline_decision": bind(
            args.baseline_decision, EXPECTED["baseline_decision"], "baseline decision"
        ),
        "baseline_archive": bind(
            args.baseline_archive, EXPECTED["baseline_archive"], "baseline archive"
        ),
        "baseline_trace": bind(
            args.baseline_trace, EXPECTED["baseline_trace"], "baseline trace"
        ),
        "script": artifact(Path(__file__).resolve()),
    }
    baseline = json.loads(args.baseline_decision.read_text())
    if baseline["status"] != "AUTHORIZED_65536_HEADROOM":
        raise ValueError("baseline causal replay antecedent is not exact")

    print(
        "[run-contract] "
        "run_name=nncp_v33_rocm_incremental_kv_runtime_q0_v1 "
        f"pairs_input_spec={args.preprocessed} resume_from=none resume_stage=none "
        "decode=greedy eval_dataset_paths=none device=cuda schedule=mixed_from_start "
        "runtime_mode=rocm_gfx_override sweep_mode=live",
        flush=True,
    )
    config = core.Config()
    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda")
    print(
        json.dumps(
            {
                "event": "rocm_preflight",
                "sys_executable": sys.executable,
                "torch": torch.__version__,
                "hip": torch.version.hip,
                "cuda_available": torch.cuda.is_available(),
                "device_count": torch.cuda.device_count(),
                "device_name": torch.cuda.get_device_name(device),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    matrix_sha256 = core.matrix_probe(device)
    source = np.memmap(args.preprocessed, mode="r", dtype=">u2")
    symbols = np.asarray(source[:SYMBOL_COUNT], dtype=np.uint16)
    if len(symbols) != SYMBOL_COUNT or int(symbols.max()) >= config.vocabulary:
        raise ValueError("frozen symbol population is invalid")

    first = run_once(symbols, config, device, "encode_a")
    second = run_once(symbols, config, device, "encode_b")
    decoded = run_once(
        symbols, config, device, "decode", first["archive"]
    )
    candidate_identity = all(
        (
            first["archive"] == second["archive"],
            first["trace"] == second["trace"] == decoded["trace"],
            np.array_equal(decoded["decoded"].reshape(-1), symbols),
            first["loss_nats"] == second["loss_nats"] == decoded["loss_nats"],
            first["model_sha256"] == second["model_sha256"] == decoded["model_sha256"],
            first["optimizer_sha256"] == second["optimizer_sha256"] == decoded["optimizer_sha256"],
            first["memory_sha256"] == second["memory_sha256"] == decoded["memory_sha256"],
        )
    )
    if not candidate_identity:
        raise ValueError("incremental candidate self-consistency failed")

    baseline_archive = args.baseline_archive.read_bytes()
    baseline_trace = args.baseline_trace.read_bytes()
    parent_training_identity = (
        first["model_sha256"] == REFERENCE_MODEL_SHA256
        and first["loss_nats"] == REFERENCE_LOSS
    )
    archive_delta = len(first["archive"]) - len(baseline_archive)
    archive_identity = first["archive"] == baseline_archive
    trace_identity = first["trace"] == baseline_trace
    elapsed_values = [
        first["elapsed_seconds"], second["elapsed_seconds"], decoded["elapsed_seconds"]
    ]
    median_seconds = statistics.median(elapsed_values)
    reduction = 1.0 - median_seconds / REFERENCE_MEDIAN_SECONDS
    peak_allocated = max(
        first["peak_allocated_bytes"], second["peak_allocated_bytes"],
        decoded["peak_allocated_bytes"],
    )
    peak_reserved = max(
        first["peak_reserved_bytes"], second["peak_reserved_bytes"],
        decoded["peak_reserved_bytes"],
    )
    memory_pass = peak_allocated < DECIMAL_10GB and peak_reserved < DECIMAL_10GB
    runtime_pass = reduction >= REQUIRED_REDUCTION
    archive_pass = archive_delta <= MAX_ARCHIVE_DELTA_BYTES
    promotion = candidate_identity and parent_training_identity and memory_pass and runtime_pass and archive_pass
    exact_parent_path = promotion and archive_identity and trace_identity
    if exact_parent_path:
        verdict = "AUTHORIZED_EXACT_65536_RUNTIME"
        next_action = "run one 65,536-symbol exact-stream incremental runtime replay"
    elif promotion:
        verdict = "AUTHORIZED_CHANGED_STREAM_65536_HEADROOM"
        next_action = "run one 65,536-symbol changed-stream headroom replay"
    else:
        verdict = "REJECT"
        next_action = "retire the eager PyTorch incremental-KV realization"

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / "archive.bin"
    trace_path = output_dir / "branch_trace.bin"
    decoded_path = output_dir / "decoded_symbols.bin"
    archive_path.write_bytes(first["archive"])
    trace_path.write_bytes(first["trace"])
    decoded["decoded"].reshape(-1).astype(">u2").tofile(decoded_path)
    decision = {
        "schema": "gamma.nncp_v33_rocm_incremental_kv_runtime_q0.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate_id": CANDIDATE_ID,
        "status": verdict,
        "claim_boundary": (
            "One-segment self-consistent incremental-KV execution and runtime "
            "evidence only; no published-score inheritance or forecast credit."
        ),
        "inputs": inputs,
        "runtime": {
            "sys_executable": sys.executable,
            "torch": torch.__version__,
            "hip": torch.version.hip,
            "device_name": torch.cuda.get_device_name(device),
            "runtime_mode": "rocm_gfx_override",
            "matrix_output_sha256": matrix_sha256,
            "elapsed_seconds": elapsed_values,
            "median_seconds": median_seconds,
            "reference_median_seconds": REFERENCE_MEDIAN_SECONDS,
            "elapsed_reduction_fraction": reduction,
        },
        "population": {
            "symbols": SYMBOL_COUNT,
            "streams": config.streams,
            "segment_length": config.segment_length,
        },
        "model": {
            "parameter_count": baseline["model"]["parameter_count"],
            "loss_nats": first["loss_nats"],
            "model_sha256": first["model_sha256"],
            "optimizer_sha256": first["optimizer_sha256"],
            "memory_sha256": first["memory_sha256"],
        },
        "archive": {
            "bytes": len(first["archive"]),
            "sha256": sha256_bytes(first["archive"]),
            "branch_frequencies": len(first["trace"]) // 2,
            "branch_trace_sha256": sha256_bytes(first["trace"]),
            "parent_bytes": len(baseline_archive),
            "delta_bytes": archive_delta,
            "parent_archive_identity": archive_identity,
            "parent_branch_trace_identity": trace_identity,
        },
        "resource": {
            "peak_allocated_bytes": peak_allocated,
            "peak_reserved_bytes": peak_reserved,
            "decimal_10gb_pass": memory_pass,
        },
        "integrity": {
            "matrix_compute_pass": True,
            "prediction_schedule": "incremental_previous_decoded_symbol_only",
            "candidate_archive_repeat_byte_identical": True,
            "candidate_branch_frequency_identity": True,
            "candidate_decoded_symbol_identity": True,
            "candidate_loss_identity": True,
            "candidate_model_state_identity": True,
            "candidate_optimizer_state_identity": True,
            "candidate_persistent_memory_identity": True,
            "parent_training_state_and_loss_identity": parent_training_identity,
        },
        "gates": {
            "candidate_identity_pass": candidate_identity,
            "parent_training_identity_pass": parent_training_identity,
            "memory_pass": memory_pass,
            "runtime_pass": runtime_pass,
            "archive_delta_pass": archive_pass,
            "promotion_authorized": promotion,
            "exact_parent_stream": exact_parent_path,
        },
        "decision": {
            "verdict": verdict,
            "authorized_next_action": next_action,
            "score_credit_bytes": 0,
            "forecast_bytes": 109_389_323,
            "verified_full_1g_score_bytes": None,
        },
        "artifacts": {
            "archive": artifact(archive_path),
            "branch_trace": artifact(trace_path),
            "decoded_symbols": artifact(decoded_path),
        },
    }
    decision_path = output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "archive_delta_bytes": archive_delta,
                "candidate_id": CANDIDATE_ID,
                "runtime_reduction_fraction": reduction,
                "verdict": verdict,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
