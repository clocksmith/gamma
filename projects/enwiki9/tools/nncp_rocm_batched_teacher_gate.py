#!/usr/bin/env python3
"""Exact zero-credit gate for the shifted-input batched ROCm teacher."""

from __future__ import annotations

from array import array
import json
import math
import os
from pathlib import Path
import sys
import time


ROCM_PYTHON = Path(
    "/home/x/enwiki9-nonproof/external/rocm-pytorch-venv/bin/python"
)


def ensure_rocm() -> None:
    if os.environ.get("NNCP_BATCH_TEACHER_REEXEC") == "1":
        return
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing ROCm interpreter: {ROCM_PYTHON}")
    environment = os.environ.copy()
    environment["NNCP_BATCH_TEACHER_REEXEC"] = "1"
    environment["AMD_SERIALIZE_KERNEL"] = "3"
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )


def main() -> int:
    ensure_rocm()

    import numpy as np
    import torch
    import torch.nn.functional as F

    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import nncp_rocm_q0_teacher_gate as q0

    def shifted_batch_audit(model, config, device) -> float:
        target_a = (
            torch.arange(config.segment_length, device=device)
            .remainder(config.vocabulary)
            .to(torch.long)
        )
        target_b = target_a.clone()
        target_b[8] = (target_b[8] + 17) % config.vocabulary
        input_a = torch.empty_like(target_a)
        input_b = torch.empty_like(target_b)
        input_a[0] = 0
        input_b[0] = 0
        input_a[1:] = target_a[:-1]
        input_b[1:] = target_b[:-1]
        with torch.no_grad(), torch.autocast(
            device_type="cuda", dtype=torch.bfloat16
        ):
            outputs = []
            for values in (input_a, input_b):
                memories = model.empty_memory(device, torch.bfloat16)
                logits, _ = model(
                    values[None, :], memories, detach_memory=False
                )
                outputs.append(logits)
        return float(
            (outputs[0][:, :9] - outputs[1][:, :9])
            .abs()
            .max()
            .cpu()
        )

    def run_teacher_batched(symbols, config, device):
        torch.manual_seed(config.seed)
        torch.cuda.manual_seed_all(config.seed)
        model = q0.RocmTeacher(config).to(device)
        parameter_count = sum(
            parameter.numel() for parameter in model.parameters()
        )
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=config.learning_rate,
            betas=(config.adam_beta1, config.adam_beta2),
            eps=config.adam_epsilon,
        )
        if not q0.causal_mask_dependency_graph_isolated(
            config.segment_length, config.memory_length
        ):
            raise ValueError("causal mask dependency graph is not isolated")
        audit_error = shifted_batch_audit(model, config, device)
        print(
            json.dumps(
                {
                    "event": "shifted_batch_causal_audit",
                    "maximum_prefix_error": audit_error,
                    "compared_outputs": [0, 8],
                    "exact_required": True,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if not math.isfinite(audit_error) or audit_error != 0.0:
            raise ValueError("shifted batched causal audit failed")

        model.train()
        memories = model.empty_memory(device, torch.bfloat16)
        previous = np.empty_like(symbols)
        previous[0] = 0
        previous[1:] = symbols[:-1]
        encoder = q0.RangeEncoder()
        trace = array("H")
        loss_sum = 0.0
        started = time.monotonic()
        for start in range(0, len(symbols), config.segment_length):
            end = min(start + config.segment_length, len(symbols))
            input_tensor = torch.from_numpy(
                previous[start:end].astype(np.int64, copy=False)
            )[None, :].to(device)
            target_tensor = torch.from_numpy(
                symbols[start:end].astype(np.int64, copy=False)
            )[None, :].to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(
                device_type="cuda", dtype=torch.bfloat16
            ):
                logits, segment_memories = model(
                    input_tensor, memories, detach_memory=False
                )
                loss = F.cross_entropy(
                    logits.reshape(-1, config.vocabulary),
                    target_tensor.reshape(-1),
                )
            probability = (
                torch.softmax(logits.detach(), dim=-1)[0].cpu().numpy()
            )
            q0.encode_distribution(
                encoder, probability, symbols[start:end], trace
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), config.gradient_clip
            )
            optimizer.step()
            memories = [
                memory.detach() for memory in segment_memories
            ]
            loss_sum += float(loss.detach().cpu()) * (end - start)
            if end % 8192 == 0 or end == len(symbols):
                torch.cuda.synchronize(device)
                print(
                    json.dumps(
                        {
                            "event": "batched_teacher_checkpoint",
                            "symbols": end,
                            "total_symbols": len(symbols),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        payload = encoder.finish()
        torch.cuda.synchronize(device)
        return {
            "archive": payload,
            "branch_trace": trace,
            "causal_audit_maximum_error": audit_error,
            "elapsed_seconds": time.monotonic() - started,
            "final_model_fingerprint": q0.model_fingerprint(model),
            "mean_cross_entropy_nats": loss_sum / len(symbols),
            "parameter_count": parameter_count,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(
                device
            ),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
        }

    q0.run_teacher = run_teacher_batched
    q0.__file__ = str(Path(__file__).resolve())
    return_code = q0.main()

    output_index = sys.argv.index("--output-dir") + 1
    output_dir = Path(sys.argv[output_index])
    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    decision["schema"] = "nncp_rocm_batched_teacher_gate_v1"
    decision["candidate"] = "nncp_rocm_batched_causal_teacher_v1"
    decision["execution"] = {
        "prediction": "one masked shifted-input segment per forward pass",
        "update": "one Adam update after each fully observed segment",
        "segment_length": decision["config"]["segment_length"],
        "offline_teacher_only": True,
    }
    decision["causality"]["audit"] = (
        "change target 8 and shifted input 9; compare outputs 0 through 8"
    )
    decision["claims"]["model_decoder_constructive"] = False
    decision["claims"]["libnc_parity"] = False
    decision["claims"]["score_credit"] = False
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
