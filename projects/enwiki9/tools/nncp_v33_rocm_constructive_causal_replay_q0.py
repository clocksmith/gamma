#!/usr/bin/env python3
"""Constructive NNCP Q0 with decoder-identical state-major inference."""

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

import nncp_v33_rocm_constructive_one_update_q0 as core


CANDIDATE_ID = "nncp_v33_rocm_constructive_causal_replay_q0_v1"
DEFAULT_OUTPUT = ROOT / "results" / CANDIDATE_ID


def causal_audit(
    config: core.Config, device: torch.device
) -> float:
    """Prove that the prediction schedule never materializes future truth."""

    model = core.make_model(config, device)
    memories = model.empty_memory(device)
    first = torch.arange(
        config.streams * config.segment_length, device=device
    ).reshape(config.streams, config.segment_length) % config.vocabulary
    second = first.clone()
    second[:, 9] = (second[:, 9] + 17) % config.vocabulary
    maximum = 0.0
    with torch.inference_mode():
        for state in range(10):
            first_inputs = torch.zeros_like(first)
            second_inputs = torch.zeros_like(second)
            if state:
                first_inputs[:, 1 : state + 1] = first[:, :state]
                second_inputs[:, 1 : state + 1] = second[:, :state]
            first_logits, _ = model(first_inputs, memories)
            second_logits, _ = model(second_inputs, memories)
            error = float(
                (first_logits[:, state] - second_logits[:, state])
                .abs()
                .max()
                .cpu()
            )
            maximum = max(maximum, error)
    del model, memories, first, second, first_logits, second_logits
    torch.cuda.empty_cache()
    return maximum


def encode_once(
    symbols: np.ndarray,
    config: core.Config,
    device: torch.device,
    label: str,
) -> dict[str, object]:
    """Encode with exactly the zero-future state schedule used by decode."""

    print(json.dumps({"event": "encode_start", "label": label}), flush=True)
    torch.cuda.reset_peak_memory_stats(device)
    model = core.make_model(config, device)
    contract = core.model_contract(config, model)
    optimizer = core.optimizer_for(model, config)
    target_numpy = symbols.reshape(config.streams, config.segment_length)
    targets = torch.from_numpy(target_numpy.astype(np.int64)).to(device)
    inputs = torch.zeros_like(targets)
    memories = model.empty_memory(device)
    encoder = core.RangeEncoder()
    trace = array("H")
    final_logits = None
    started = time.monotonic()

    for state in range(config.segment_length):
        if state:
            inputs[:, state] = targets[:, state - 1]
        if state + 1 == config.segment_length:
            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(inputs, memories)
            final_logits = logits
        else:
            with torch.no_grad():
                logits, _ = model(inputs, memories)
        probability = torch.softmax(
            logits[:, state, :].detach(), dim=-1
        ).cpu().numpy()
        core.branch_encode(
            encoder, probability, target_numpy[:, state], trace
        )
        if state + 1 != config.segment_length:
            del logits
        del probability
        if (state + 1) % 8 == 0:
            print(
                json.dumps(
                    {
                        "event": "encode_checkpoint",
                        "label": label,
                        "states": state + 1,
                        "total_states": config.segment_length,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    if final_logits is None:
        raise AssertionError("missing final differentiable logits")
    payload = encoder.finish()
    loss = core.update_model(
        model, optimizer, final_logits, targets, config
    )
    torch.cuda.synchronize(device)
    result = {
        "archive": payload,
        "branch_trace": trace,
        "elapsed_seconds": time.monotonic() - started,
        "final_state_sha256": core.parameter_state_hash(model),
        "loss_nats": loss,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
        **contract,
    }
    del optimizer, model, final_logits, targets, inputs, memories
    torch.cuda.empty_cache()
    print(
        json.dumps(
            {
                "archive_bytes": len(payload),
                "event": "encode_complete",
                "label": label,
                "state_sha256": result["final_state_sha256"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return result


def output_path_from_argv() -> Path:
    if "--output-dir" in sys.argv:
        index = sys.argv.index("--output-dir")
        return Path(sys.argv[index + 1])
    sys.argv.extend(("--output-dir", str(DEFAULT_OUTPUT)))
    return DEFAULT_OUTPUT


def main() -> int:
    output_dir = output_path_from_argv()
    core.causal_audit = causal_audit
    core.encode_once = encode_once
    status = core.main()
    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    core_script = decision["inputs"].pop("script_sha256")
    decision["schema"] = (
        "gamma.nncp_v33_rocm_constructive_causal_replay_q0.v1"
    )
    decision["candidate_id"] = CANDIDATE_ID
    decision["claim_boundary"] = (
        "Self-consistent state-major one-update construction only; no LibNC "
        "parity, published-score inheritance, or score credit."
    )
    decision["inputs"]["core_script_sha256"] = core_script
    decision["inputs"]["driver_script_sha256"] = core.sha256(
        Path(__file__).resolve()
    )
    decision["integrity"]["decoder_known_future_fill"] = "all_zero"
    decision["integrity"]["prediction_schedule"] = (
        "state_major_prefix_replay"
    )
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "decision_sha256": core.sha256(decision_path),
                "event": "causal_replay_decision_rebound",
                "status": decision["status"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return status


if __name__ == "__main__":
    raise SystemExit(main())
