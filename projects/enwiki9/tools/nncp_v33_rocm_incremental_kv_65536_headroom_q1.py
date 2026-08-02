#!/usr/bin/env python3
"""Run the authorized 65,536-symbol incremental-KV NNCP headroom gate."""

from __future__ import annotations

from array import array
import json
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

import nncp_v33_rocm_constructive_65536_headroom_q1 as headroom_q1
import nncp_v33_rocm_incremental_kv_runtime_q0 as cache_q0


core = headroom_q1.core
CANDIDATE_ID = "nncp_v33_rocm_incremental_kv_65536_headroom_q1_v1"
AUTHORIZATION = (
    ROOT
    / "programs/nncp_v33_rocm_incremental_kv_65536_headroom_q1_v1/"
    "q1_authorization.json"
)
PARENT_DECISION = (
    ROOT / "results/nncp_v33_rocm_incremental_kv_runtime_q0_v1/decision.json"
)
EXPECTED_PARENT_SHA256 = (
    "5582933409eba8045cb04121c9c3c7fdc2c15730c67b9d9774c27b013f6db0b2"
)


def run_once(
    symbols: np.ndarray,
    config: core.Config,
    device: torch.device,
    mode: str,
    payload: bytes | None = None,
) -> dict[str, object]:
    if mode not in ("encode_first", "encode_second", "decode"):
        raise ValueError(f"invalid run mode: {mode}")
    print(json.dumps({"event": "run_start", "mode": mode}), flush=True)
    torch.cuda.reset_peak_memory_stats(device)
    model = core.make_model(config, device)
    optimizer = core.optimizer_for(model, config)
    memories = model.empty_memory(device)
    source_matrix = symbols.reshape(config.streams, headroom_q1.STREAM_LENGTH)
    if mode == "decode":
        values = torch.zeros(
            config.streams,
            headroom_q1.STREAM_LENGTH,
            dtype=torch.long,
            device=device,
        )
        coder: core.RangeEncoder | core.RangeDecoder = core.RangeDecoder(payload or b"")
    else:
        values = torch.from_numpy(source_matrix.astype(np.int64)).to(device)
        coder = core.RangeEncoder()
    trace = array("H")
    losses: list[float] = []
    segment_count = headroom_q1.STREAM_LENGTH // config.segment_length
    torch.cuda.synchronize(device)
    started = time.monotonic()

    for segment in range(segment_count):
        segment_start = segment * config.segment_length
        segment_end = segment_start + config.segment_length
        with torch.inference_mode():
            caches = cache_q0.make_layer_caches(model, memories)
            for state in range(config.segment_length):
                absolute = segment_start + state
                input_symbols = (
                    torch.zeros(config.streams, dtype=torch.long, device=device)
                    if absolute == 0
                    else values[:, absolute - 1]
                )
                logits = cache_q0.incremental_logits(
                    model, input_symbols, caches, state
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
        torch.cuda.empty_cache()

        targets = values[:, segment_start:segment_end]
        inputs = torch.zeros_like(targets)
        if segment:
            inputs[:, 0] = values[:, segment_start - 1]
        inputs[:, 1:] = targets[:, :-1]
        optimizer.zero_grad(set_to_none=True)
        train_logits, next_memories = model(inputs, memories)
        losses.append(
            core.update_model(model, optimizer, train_logits, targets, config)
        )
        memories = [memory.detach() for memory in next_memories]
        del train_logits, next_memories, targets, inputs
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
    adam_state = headroom_q1.optimizer_hash(model, optimizer)
    persistent_state = headroom_q1.memory_hash(memories)
    complete_state = headroom_q1.complete_state_hash(
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
    if core.sha256(PARENT_DECISION) != EXPECTED_PARENT_SHA256:
        raise ValueError("incremental-KV Q0 decision identity mismatch")
    authorization = json.loads(AUTHORIZATION.read_text())
    if (
        authorization["actual_parent_decision_sha256"] != EXPECTED_PARENT_SHA256
        or authorization["actual_parent_status"]
        != "AUTHORIZED_CHANGED_STREAM_65536_HEADROOM"
    ):
        raise ValueError("invalid changed-stream authorization receipt")
    if "--q0-decision" not in sys.argv:
        sys.argv.extend(("--q0-decision", str(AUTHORIZATION)))
    print(
        "[run-contract] "
        "run_name=nncp_v33_rocm_incremental_kv_65536_headroom_q1_v1 "
        "pairs_input_spec=receipt-bound-nncp-preprocessed-prefix-65536 "
        "resume_from=none resume_stage=none decode=greedy "
        "eval_dataset_paths=data/enwik9_10000000.bin device=cuda "
        "schedule=mixed_from_start runtime_mode=rocm_gfx_override "
        "sweep_mode=live",
        flush=True,
    )
    headroom_q1.CANDIDATE_ID = CANDIDATE_ID
    headroom_q1.run_once = run_once
    status = headroom_q1.main()
    output_dir = ROOT / "results" / CANDIDATE_ID
    if "--output-dir" in sys.argv:
        output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1])
    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    decision["schema"] = (
        "gamma.nncp_v33_rocm_incremental_kv_65536_headroom_q1.v1"
    )
    decision["candidate_id"] = CANDIDATE_ID
    decision["claim_boundary"] = (
        "Exact changed-stream 65,536-symbol incremental-KV headroom only; "
        "no published-score inheritance, package/forecast credit, or "
        "full-corpus claim."
    )
    decision["runtime"]["prediction_schedule"] = "incremental_kv"
    decision["inputs"]["actual_q0_decision_sha256"] = EXPECTED_PARENT_SHA256
    decision["inputs"]["driver_script_sha256"] = core.sha256(
        Path(__file__).resolve()
    )
    decision["inputs"]["shared_headroom_script_sha256"] = decision[
        "inputs"
    ].pop("script_sha256")
    reserved = decision["resource"]["peak_reserved_bytes"]
    decision["resource"]["decimal_10gb_reserved_pass"] = (
        reserved < 10_000_000_000
    )
    if not decision["resource"]["decimal_10gb_reserved_pass"]:
        decision["status"] = "REJECT"
        decision["decision"]["promotion_authorized"] = False
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "decision_sha256": core.sha256(decision_path),
                "event": "incremental_kv_q1_decision_rebound",
                "status": decision["status"],
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
        print(f"nncp-v33-incremental-kv-q1: {error}", file=sys.stderr)
        raise
