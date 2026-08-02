#!/usr/bin/env python3
"""Validate the causal concat-optimized LibNC RMSNorm backward formula."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_decoder_graph_update_parity as decoder_graph
import nncp_v33_libnc_ff2_residual_adjoint_replay as residual_replay
import nncp_v33_libnc_ff2_residual_adjoint_update_parity as update_replay
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_named_gradient_trajectory as named
import nncp_v33_libnc_tanh_gelu_online_update_parity as gelu_replay


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_concat_rmsnorm_backward_contract_v1"
GRADIENT_THRESHOLD = 2e-6
UPDATE_THRESHOLD = 2e-5
STATES = 4
EPSILON = 1e-5


class ConcatOptimizedRMSNorm(torch.autograd.Function):
    """LibNC concat-root RMSNorm: RMS forward and centered output adjoint."""

    @staticmethod
    def forward(ctx, value: torch.Tensor) -> torch.Tensor:
        inverse = torch.rsqrt(
            value.square().mean(dim=-1, keepdim=True) + EPSILON
        )
        output = value * inverse
        ctx.save_for_backward(inverse, output)
        return output

    @staticmethod
    def backward(ctx, gradient: torch.Tensor) -> torch.Tensor:
        inverse, output = ctx.saved_tensors
        return inverse * (
            gradient
            - gradient.mean(dim=-1, keepdim=True)
            - output
            * (gradient * output).mean(dim=-1, keepdim=True)
        )


def make_analytic_forward(join_inputs: list[torch.Tensor] | None = None):
    def analytic_forward(
        weights: dict[str, torch.Tensor],
        token: torch.Tensor,
        memory: torch.Tensor,
        segment: int,
        memory_length: int,
        heads: int,
        d_key: int,
        d_value: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        final_norm_count = 0
        original_norm = decoder_graph.libnc_rms_norm

        def norm_with_analytic_backward(
            value: torch.Tensor, gain: torch.Tensor, bias: torch.Tensor
        ) -> torch.Tensor:
            nonlocal final_norm_count
            if gain is weights["ln_g_2"]:
                final_norm_count += 1
                if join_inputs is not None:
                    value.retain_grad()
                    join_inputs.append(value)
                return ConcatOptimizedRMSNorm.apply(value) * gain + bias
            return original_norm(value, gain, bias)

        decoder_graph.libnc_rms_norm = norm_with_analytic_backward
        try:
            result = decoder_graph.decoder_graph_segment(
                weights,
                token,
                memory,
                segment,
                memory_length,
                heads,
                d_key,
                d_value,
            )
        finally:
            decoder_graph.libnc_rms_norm = original_norm
        if final_norm_count != STATES:
            raise RuntimeError(
                f"observed {final_norm_count} final norms, expected {STATES}"
            )
        return result

    return analytic_forward


def analytic_gradient_run(
    export: Path, trace: Path
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray]:
    loaded, _ = base.load_export(export)
    weights = {
        name: value.detach().clone().requires_grad_(True)
        for name, value in loaded.items()
    }
    symbols, _ = base.load_trace(trace)
    inputs = np.concatenate((np.zeros(1, dtype=np.int64), symbols[:-1]))
    token = torch.from_numpy(inputs)
    memory = torch.zeros(4, 32, dtype=torch.float32)
    joins: list[torch.Tensor] = []
    logits, _ = make_analytic_forward(joins)(
        weights, token, memory, 4, 4, 2, 8, 8
    )
    loss = torch.nn.functional.cross_entropy(
        logits, torch.from_numpy(symbols), reduction="mean"
    )
    loss.backward()
    if len(joins) != STATES or any(value.grad is None for value in joins):
        raise RuntimeError("analytic residual-join adjoint capture is incomplete")
    gradients = {
        name: value.grad.detach().numpy().copy()
        for name, value in weights.items()
        if value.grad is not None
    }
    if len(gradients) != len(weights):
        raise RuntimeError("analytic graph omitted a parameter gradient")
    adjoint = np.concatenate(
        [value.grad.detach().numpy().T.copy() for value in joins], axis=1
    )
    probabilities = torch.softmax(logits, dim=-1).detach().numpy()
    return probabilities, gradients, adjoint


def analytic_update_run(
    initial: dict[str, torch.Tensor],
    symbols: np.ndarray,
    learning_rate: float,
    gradient_clip: float,
) -> tuple[torch.Tensor, dict[str, torch.Tensor], list[float]]:
    original_forward = base.forward_segment
    base.forward_segment = make_analytic_forward()
    try:
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
    finally:
        base.forward_segment = original_forward


def array_sha256(value: np.ndarray) -> str:
    return hashlib.sha256(
        np.asarray(value, dtype="<f4").tobytes(order="F")
    ).hexdigest()


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
        "--bound-dir",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "nncp_v33_online_update_parity_v1/run_07_bound"
        ),
    )
    parser.add_argument(
        "--adjoint-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_ff2_output_adjoint_trajectory_v1/decision.json",
    )
    parser.add_argument(
        "--named-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_named_gradient_trajectory_v1/decision.json",
    )
    parser.add_argument(
        "--update-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_ff2_residual_adjoint_update_parity_v1/decision.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    parser.add_argument("--learning-rate", type=float, default=0.00016)
    parser.add_argument("--gradient-clip", type=float, default=0.05)
    args = parser.parse_args()

    trace = args.bound_dir / "teacher.bin"
    final_export = args.bound_dir / "final_export"
    required = [
        args.export / "manifest.json",
        trace,
        final_export / "manifest.json",
        args.adjoint_decision,
        args.named_decision,
        args.update_decision,
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing export, bound trace, or parent decision")
    update_decision = json.loads(args.update_decision.read_text())
    if update_decision.get("status") != "PASS":
        raise ValueError("captured-adjoint update did not authorize analytic child")
    native_adjoint, adjoint_decision = residual_replay.load_native_adjoint(
        args.adjoint_decision
    )
    names, bound_gradients, _ = residual_replay.load_bound_gradients(
        args.export, args.bound_dir, args.named_decision
    )
    initial, exported_types = base.load_export(args.export)
    symbols, distributions = base.load_trace(trace)
    teacher_probabilities = np.stack(distributions)
    teacher_final, _ = base.load_export(final_export)

    gradient_runs = [analytic_gradient_run(args.export, trace) for _ in range(2)]
    first_probabilities, first_gradients, analytic_adjoint = gradient_runs[0]
    second_probabilities, second_gradients, second_adjoint = gradient_runs[1]
    gradient_repeat = (
        named.gradient_sha256(first_gradients)
        == named.gradient_sha256(second_gradients)
        and np.array_equal(first_probabilities, second_probabilities)
        and np.array_equal(analytic_adjoint, second_adjoint)
    )
    probability_metrics = named.metrics(teacher_probabilities, first_probabilities)
    adjoint_metrics = named.metrics(native_adjoint, analytic_adjoint)
    gradient_summary = residual_replay.summarize(
        names, bound_gradients, first_gradients
    )

    baseline_probabilities, _, _ = update_replay.run_once(
        initial, symbols, args.learning_rate, args.gradient_clip, None
    )
    update_runs = [
        analytic_update_run(
            initial, symbols, args.learning_rate, args.gradient_clip
        )
        for _ in range(2)
    ]
    first_update_probabilities, first_final, first_losses = update_runs[0]
    second_update_probabilities, second_final, second_losses = update_runs[1]
    final_errors = update_replay.parameter_errors(teacher_final, first_final)
    maximum_final_error = max(final_errors.values())
    first_final_hash = gelu_replay.final_hash(first_final)
    second_final_hash = gelu_replay.final_hash(second_final)
    update_repeat = (
        first_final_hash == second_final_hash
        and torch.equal(first_update_probabilities, second_update_probabilities)
        and first_losses == second_losses
    )
    forward_unchanged = torch.equal(
        first_update_probabilities, baseline_probabilities
    )
    passed = (
        gradient_repeat
        and probability_metrics["maximum_absolute_error"] <= GRADIENT_THRESHOLD
        and adjoint_metrics["maximum_absolute_error"] <= GRADIENT_THRESHOLD
        and adjoint_metrics["sign_mismatches"] == 0
        and gradient_summary["all_match"]
        and forward_unchanged
        and maximum_final_error <= UPDATE_THRESHOLD
        and update_repeat
    )
    result = {
        "schema": "gamma.nncp_v33_libnc_concat_rmsnorm_backward_contract.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if passed else "REJECT",
        "score_credit_bytes": 0,
        "contract": {
            "states": STATES,
            "updates": 1,
            "epsilon": EPSILON,
            "gradient_threshold": GRADIENT_THRESHOLD,
            "update_threshold": UPDATE_THRESHOLD,
            "learning_rate": args.learning_rate,
            "gradient_clip": args.gradient_clip,
            "formula": "inverse*(g-mean(g)-output*mean(g*output))",
            "scope": "final_rmsnorm_nodes_combined_by_concat_optimization",
            "captured_adjoint_used_for_replay": False,
            "exported_parameter_types": exported_types,
        },
        "inputs": {
            "script_sha256": internal.sha256(Path(__file__).resolve()),
            "initial_manifest_sha256": internal.sha256(args.export / "manifest.json"),
            "teacher_trace_sha256": internal.sha256(trace),
            "final_manifest_sha256": internal.sha256(
                final_export / "manifest.json"
            ),
            "adjoint_decision_sha256": internal.sha256(args.adjoint_decision),
            "named_decision_sha256": internal.sha256(args.named_decision),
            "update_decision_sha256": internal.sha256(args.update_decision),
            "source_adjoint_sha256": adjoint_decision["capture"][
                "native_adjoint_sha256"
            ],
        },
        "gradient_proof": {
            "repeat_byte_identical": gradient_repeat,
            "probability_vs_teacher": probability_metrics,
            "analytic_adjoint_sha256": array_sha256(analytic_adjoint),
            "analytic_adjoint_vs_source": adjoint_metrics,
            "named_gradients": gradient_summary,
        },
        "update_proof": {
            "forward_probabilities_byte_identical_to_baseline": forward_unchanged,
            "maximum_absolute_parameter_error": maximum_final_error,
            "parameter_maximum_errors": final_errors,
            "segment_losses": first_losses,
            "first_final_tensor_sha256": first_final_hash,
            "second_final_tensor_sha256": second_final_hash,
            "repeat_byte_identical": update_repeat,
        },
        "decision": {
            "promotion_authorized": passed,
            "authorized_next_action": (
                "run one native source-bound multi-update receipt with the frozen analytic contract"
                if passed
                else "retire the analytic concat-RMSNorm backward formula"
            ),
            "forecast_bytes": 109389323,
            "verified_full_1g_score_bytes": None,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
