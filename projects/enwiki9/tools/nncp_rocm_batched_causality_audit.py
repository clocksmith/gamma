#!/usr/bin/env python3
"""Audit shifted-input causality of the frozen batched ROCm teacher."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


ROCM_PYTHON = Path(
    "/home/x/enwiki9-nonproof/external/rocm-pytorch-venv/bin/python"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preprocessed", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def ensure_rocm() -> None:
    if os.environ.get("NNCP_BATCH_CAUSAL_REEXEC") == "1":
        return
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing ROCm interpreter: {ROCM_PYTHON}")
    environment = os.environ.copy()
    environment["NNCP_BATCH_CAUSAL_REEXEC"] = "1"
    environment["AMD_SERIALIZE_KERNEL"] = "3"
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    ensure_rocm()

    import numpy as np
    import torch

    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import nncp_rocm_q0_teacher_gate as q0

    if not torch.cuda.is_available() or torch.version.hip is None:
        raise SystemExit("a PyTorch ROCm device is required")

    config = q0.Config()
    source = np.memmap(args.preprocessed, mode="r", dtype=">u2")
    target_a = np.asarray(source[: config.segment_length], dtype=np.uint16)
    if len(target_a) != config.segment_length:
        raise ValueError("preprocessed source is shorter than one segment")
    if int(target_a.max()) >= config.vocabulary:
        raise ValueError("symbol exceeds frozen vocabulary")

    target_b = target_a.copy()
    target_b[8] = (int(target_b[8]) + 17) % config.vocabulary
    input_a = np.empty(config.segment_length, dtype=np.int64)
    input_b = np.empty(config.segment_length, dtype=np.int64)
    input_a[0] = 0
    input_b[0] = 0
    input_a[1:] = target_a[:-1]
    input_b[1:] = target_b[:-1]
    differing_inputs = np.flatnonzero(input_a != input_b).tolist()
    if differing_inputs != [9]:
        raise ValueError(
            f"shifted counterfactual changed unexpected inputs: {differing_inputs}"
        )

    torch.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)
    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda")
    model = q0.RocmTeacher(config).to(device)
    model.eval()

    def batched(values: np.ndarray):
        tensor = torch.from_numpy(values)[None, :].to(device)
        memories = model.empty_memory(device, torch.bfloat16)
        with torch.no_grad(), torch.autocast(
            device_type="cuda", dtype=torch.bfloat16
        ):
            logits, _ = model(tensor, memories, detach_memory=False)
        return logits

    logits_a = batched(input_a)
    logits_b = batched(input_b)
    prefix_error = float(
        (logits_a[:, :9] - logits_b[:, :9]).abs().max().cpu()
    )
    position_nine_error = float(
        (logits_a[:, 9] - logits_b[:, 9]).abs().max().cpu()
    )

    incremental_parts = []
    incremental_memory = model.empty_memory(device, torch.bfloat16)
    with torch.no_grad(), torch.autocast(
        device_type="cuda", dtype=torch.bfloat16
    ):
        for index in range(config.segment_length):
            current, incremental_memory = model(
                torch.from_numpy(input_a[index : index + 1])[
                    None, :
                ].to(device),
                incremental_memory,
                detach_memory=False,
            )
            incremental_parts.append(current)
    incremental_logits = torch.cat(incremental_parts, dim=1)
    incremental_logit_error = float(
        (logits_a - incremental_logits).abs().max().cpu()
    )
    batched_probabilities = torch.softmax(logits_a.float(), dim=-1)
    incremental_probabilities = torch.softmax(
        incremental_logits.float(), dim=-1
    )
    incremental_probability_error = float(
        (batched_probabilities - incremental_probabilities)
        .abs()
        .max()
        .cpu()
    )

    dependency_isolated = q0.causal_mask_dependency_graph_isolated(
        config.segment_length, 0
    )
    passed = prefix_error == 0.0 and dependency_isolated
    decision = {
        "schema": "nncp_rocm_batched_causality_audit_v1",
        "candidate": "nncp_rocm_batched_causal_teacher_v1",
        "verdict": "PASS" if passed else "REJECT",
        "score_credit_bytes": 0,
        "input": {
            "preprocessed": str(args.preprocessed),
            "preprocessed_sha256": sha256(args.preprocessed),
            "symbols": config.segment_length,
            "changed_target_position": 8,
            "changed_shifted_input_positions": differing_inputs,
        },
        "causality": {
            "dependency_graph_isolated": dependency_isolated,
            "compared_output_positions": [0, 8],
            "maximum_prefix_logit_error": prefix_error,
            "position_9_logit_error_legal": position_nine_error,
            "shifted_inputs_only": True,
        },
        "separate_numerical_diagnostic": {
            "batched_vs_incremental_maximum_logit_error": (
                incremental_logit_error
            ),
            "batched_vs_incremental_maximum_probability_error": (
                incremental_probability_error
            ),
            "required_for_offline_teacher_authorization": False,
            "constructive_decoder_claim": False,
        },
        "environment": {
            "device": torch.cuda.get_device_name(device),
            "hip": torch.version.hip,
            "torch": torch.__version__,
        },
        "claims": {
            "future_leakage_absent_for_audited_segment": passed,
            "libnc_parity": False,
            "model_decoder_constructive": False,
            "teacher_headroom_measured": False,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
