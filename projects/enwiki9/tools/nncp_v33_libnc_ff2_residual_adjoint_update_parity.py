#!/usr/bin/env python3
"""Apply the confirmed LibNC residual adjoint in one bound online update."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_decoder_graph_update_parity as decoder_graph
import nncp_v33_libnc_ff2_residual_adjoint_replay as residual_replay
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_tanh_gelu_online_update_parity as gelu_replay


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_ff2_residual_adjoint_update_parity_v1"
STATES = 4


def make_repaired_forward(native_adjoint: np.ndarray):
    native = torch.from_numpy(native_adjoint)

    def repaired_forward(
        weights: dict[str, torch.Tensor],
        token: torch.Tensor,
        memory: torch.Tensor,
        segment: int,
        memory_length: int,
        heads: int,
        d_key: int,
        d_value: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        hook_count = 0
        original_norm = decoder_graph.libnc_rms_norm

        def norm_with_residual_hook(
            value: torch.Tensor, gain: torch.Tensor, bias: torch.Tensor
        ) -> torch.Tensor:
            nonlocal hook_count
            if gain is weights["ln_g_2"]:
                state = hook_count
                if state >= STATES:
                    raise RuntimeError("too many residual-adjoint hooks")
                replacement = native[:, state].reshape_as(value).clone()
                replacement = replacement.to(dtype=value.dtype, device=value.device)
                value.register_hook(lambda _gradient, item=replacement: item)
                hook_count += 1
            return original_norm(value, gain, bias)

        decoder_graph.libnc_rms_norm = norm_with_residual_hook
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
        if hook_count != STATES:
            raise RuntimeError(
                f"installed {hook_count} residual hooks, expected {STATES}"
            )
        return result

    return repaired_forward


def run_once(
    initial: dict[str, torch.Tensor],
    symbols: np.ndarray,
    learning_rate: float,
    gradient_clip: float,
    native_adjoint: np.ndarray | None,
) -> tuple[torch.Tensor, dict[str, torch.Tensor], list[float]]:
    original_forward = base.forward_segment
    base.forward_segment = (
        decoder_graph.decoder_graph_segment
        if native_adjoint is None
        else make_repaired_forward(native_adjoint)
    )
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


def parameter_errors(
    reference: dict[str, torch.Tensor], candidate: dict[str, torch.Tensor]
) -> dict[str, float]:
    return {
        name: float((candidate[name] - reference[name]).abs().max())
        for name in sorted(reference)
    }


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
        "--adjoint-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_ff2_output_adjoint_trajectory_v1/decision.json",
    )
    parser.add_argument(
        "--gradient-replay-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_ff2_residual_adjoint_replay_v1/decision.json",
    )
    parser.add_argument(
        "--parent-update-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_decoder_graph_update_parity_v1/decision.json",
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

    required = [
        args.export / "manifest.json",
        args.trace,
        args.final_export / "manifest.json",
        args.adjoint_decision,
        args.gradient_replay_decision,
        args.parent_update_decision,
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing export, trace, or parent decision")
    gradient_replay = json.loads(args.gradient_replay_decision.read_text())
    if not gradient_replay["gate"]["passed"]:
        raise ValueError("residual-adjoint gradient replay did not authorize update")
    native_adjoint, adjoint_decision = residual_replay.load_native_adjoint(
        args.adjoint_decision
    )
    initial, exported_types = base.load_export(args.export)
    symbols, distributions = base.load_trace(args.trace)
    teacher_probabilities = torch.from_numpy(np.stack(distributions))
    teacher_final, _ = base.load_export(args.final_export)
    parent_update = json.loads(args.parent_update_decision.read_text())

    baseline_probabilities, baseline_final, baseline_losses = run_once(
        initial, symbols, args.learning_rate, args.gradient_clip, None
    )
    repaired_runs = [
        run_once(
            initial,
            symbols,
            args.learning_rate,
            args.gradient_clip,
            native_adjoint,
        )
        for _ in range(2)
    ]
    first_probabilities, first_final, first_losses = repaired_runs[0]
    second_probabilities, second_final, second_losses = repaired_runs[1]

    baseline_errors = parameter_errors(teacher_final, baseline_final)
    repaired_errors = parameter_errors(teacher_final, first_final)
    baseline_maximum = max(baseline_errors.values())
    repaired_maximum = max(repaired_errors.values())
    teacher_probability_error = (first_probabilities - teacher_probabilities).abs()
    forward_unchanged = torch.equal(first_probabilities, baseline_probabilities)
    first_hash = gelu_replay.final_hash(first_final)
    second_hash = gelu_replay.final_hash(second_final)
    repeat_identical = (
        first_hash == second_hash
        and torch.equal(first_probabilities, second_probabilities)
        and first_losses == second_losses
    )
    parent_baseline_maximum = parent_update["proof"][
        "maximum_absolute_parameter_error"
    ]
    baseline_reproduced = baseline_maximum == parent_baseline_maximum
    passed = (
        baseline_reproduced
        and baseline_maximum > args.tolerance
        and forward_unchanged
        and float(teacher_probability_error.max()) <= args.tolerance
        and repaired_maximum <= args.tolerance
        and repeat_identical
    )
    result = {
        "schema": "gamma.nncp_v33_libnc_ff2_residual_adjoint_update_parity.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if passed else "REJECT",
        "score_credit_bytes": 0,
        "contract": {
            "symbols": len(symbols),
            "states": STATES,
            "updates": 1,
            "learning_rate": args.learning_rate,
            "gradient_clip": args.gradient_clip,
            "tolerance": args.tolerance,
            "exported_parameter_types": exported_types,
            "intervention": "captured_adjoint_at_post_ff2_residual_join",
        },
        "inputs": {
            "script_sha256": internal.sha256(Path(__file__).resolve()),
            "initial_manifest_sha256": internal.sha256(args.export / "manifest.json"),
            "teacher_trace_sha256": internal.sha256(args.trace),
            "final_manifest_sha256": internal.sha256(
                args.final_export / "manifest.json"
            ),
            "adjoint_decision_sha256": internal.sha256(args.adjoint_decision),
            "gradient_replay_decision_sha256": internal.sha256(
                args.gradient_replay_decision
            ),
            "parent_update_decision_sha256": internal.sha256(
                args.parent_update_decision
            ),
            "captured_adjoint_sha256": adjoint_decision["capture"][
                "native_adjoint_sha256"
            ],
        },
        "proof": {
            "baseline_reproduces_parent_maximum_error": baseline_reproduced,
            "baseline_maximum_absolute_parameter_error": baseline_maximum,
            "baseline_parameter_maximum_errors": baseline_errors,
            "baseline_segment_losses": baseline_losses,
            "forward_probabilities_byte_identical_to_baseline": forward_unchanged,
            "maximum_absolute_probability_error": float(
                teacher_probability_error.max()
            ),
            "mean_absolute_probability_error": float(
                teacher_probability_error.mean()
            ),
            "maximum_absolute_parameter_error": repaired_maximum,
            "parameter_maximum_errors": repaired_errors,
            "segment_losses": first_losses,
            "first_final_tensor_sha256": first_hash,
            "second_final_tensor_sha256": second_hash,
            "repeat_byte_identical": repeat_identical,
        },
        "decision": {
            "promotion_authorized": passed,
            "authorized_next_action": (
                "derive and test the causal multi-update LibNC residual-adjoint contract"
                if passed
                else "retire the captured residual-adjoint contract as sufficient for update parity"
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
