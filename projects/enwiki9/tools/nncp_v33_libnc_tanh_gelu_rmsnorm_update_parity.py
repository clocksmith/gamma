#!/usr/bin/env python3
"""Replay the bound miniature with measured LibNC GELU and RMSNorm backward."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_rmsnorm_backward_order_parity as rms_order
import nncp_v33_libnc_tanh_gelu_online_update_parity as gelu_replay


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_tanh_gelu_rmsnorm_update_parity_v1"


def libnc_rms_norm(
    value: torch.Tensor, gain: torch.Tensor, bias: torch.Tensor
) -> torch.Tensor:
    normalized = rms_order.OutputOrderRMSNorm.apply(value)
    return normalized * gain + bias


def run_once(
    initial: dict[str, torch.Tensor],
    symbols,
    learning_rate: float,
    gradient_clip: float,
) -> tuple[torch.Tensor, dict[str, torch.Tensor], list[float]]:
    base.rms_norm = libnc_rms_norm
    base.F.gelu = gelu_replay.libnc_gelu
    return base.evaluate_online(
        initial,
        symbols,
        4,
        4,
        2,
        8,
        8,
        torch.device("cpu"),
        torch.float32,
        learning_rate,
        gradient_clip,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_v33_relative_parity_v1/"
            "run_05/export"
        ),
    )
    parser.add_argument(
        "--trace",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_v33_online_update_parity_v1/"
            "run_07_bound/teacher.bin"
        ),
    )
    parser.add_argument(
        "--final-export",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_v33_online_update_parity_v1/"
            "run_07_bound/final_export"
        ),
    )
    parser.add_argument(
        "--gelu-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_activation_backward_parity_v1/decision.json",
    )
    parser.add_argument(
        "--rmsnorm-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_rmsnorm_backward_order_parity_v1/decision.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    parser.add_argument("--learning-rate", type=float, default=0.00016)
    parser.add_argument("--gradient-clip", type=float, default=0.05)
    parser.add_argument("--tolerance", type=float, default=2e-5)
    args = parser.parse_args()
    gelu_decision = json.loads(args.gelu_decision.read_text())
    rmsnorm_decision = json.loads(args.rmsnorm_decision.read_text())
    if not gelu_decision["decision"]["promotion_authorized"]:
        raise ValueError("GELU primitive decision does not authorize replay")
    if not rmsnorm_decision["decision"]["promotion_authorized"]:
        raise ValueError("RMSNorm operation-order decision does not authorize replay")

    initial, exported_types = base.load_export(args.export)
    symbols, distributions = base.load_trace(args.trace)
    teacher = torch.from_numpy(__import__("numpy").stack(distributions))
    teacher_final, _ = base.load_export(args.final_export)
    first_probabilities, first_final, losses = run_once(
        initial, symbols, args.learning_rate, args.gradient_clip
    )
    second_probabilities, second_final, second_losses = run_once(
        initial, symbols, args.learning_rate, args.gradient_clip
    )
    probability_error = (first_probabilities - teacher).abs()
    parameter_errors = {
        name: float((first_final[name] - teacher_final[name]).abs().max())
        for name in sorted(first_final)
    }
    maximum_parameter_error = max(parameter_errors.values())
    first_hash = gelu_replay.final_hash(first_final)
    second_hash = gelu_replay.final_hash(second_final)
    repeat_identical = (
        first_hash == second_hash
        and torch.equal(first_probabilities, second_probabilities)
        and losses == second_losses
    )
    passed = (
        float(probability_error.max()) <= args.tolerance
        and maximum_parameter_error <= args.tolerance
        and repeat_identical
    )
    decision = {
        "schema": "gamma.nncp_v33_libnc_tanh_gelu_rmsnorm_update_parity.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if passed else "REJECT",
        "score_credit_bytes": 0,
        "contract": {
            "layers": 1,
            "d_model": 32,
            "symbols": len(symbols),
            "updates": 1,
            "learning_rate": args.learning_rate,
            "gradient_clip": args.gradient_clip,
            "tolerance": args.tolerance,
            "activation": "libnc_unfused_f32_tanh_formula",
            "rmsnorm_backward": "inverse_times_gradient_minus_output_mean_gradient_output",
            "exported_parameter_types": exported_types,
        },
        "inputs": {
            "initial_manifest_sha256": gelu_replay.sha256(
                args.export / "manifest.json"
            ),
            "teacher_trace_sha256": gelu_replay.sha256(args.trace),
            "final_manifest_sha256": gelu_replay.sha256(
                args.final_export / "manifest.json"
            ),
            "gelu_decision_sha256": gelu_replay.sha256(args.gelu_decision),
            "rmsnorm_decision_sha256": gelu_replay.sha256(
                args.rmsnorm_decision
            ),
            "script_sha256": gelu_replay.sha256(Path(__file__).resolve()),
        },
        "proof": {
            "maximum_absolute_probability_error": float(
                probability_error.max()
            ),
            "mean_absolute_probability_error": float(probability_error.mean()),
            "maximum_absolute_parameter_error": maximum_parameter_error,
            "parameter_maximum_errors": parameter_errors,
            "segment_losses": losses,
            "first_final_tensor_sha256": first_hash,
            "second_final_tensor_sha256": second_hash,
            "repeat_byte_identical": repeat_identical,
        },
        "decision": {
            "promotion_authorized": passed,
            "authorized_next_action": (
                "localize the next primitive or run frozen full-profile parity"
                if passed
                else "retire the combined GELU and RMSNorm repair as sufficient"
            ),
            "forecast_bytes": 109389323,
            "verified_full_1g_score_bytes": None,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
