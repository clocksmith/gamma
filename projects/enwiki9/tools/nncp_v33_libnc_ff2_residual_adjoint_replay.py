#!/usr/bin/env python3
"""Replay the source-captured LibNC FF2 adjoint at the residual join."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_decoder_graph_update_parity as decoder_graph
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_named_gradient_trajectory as named


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_ff2_residual_adjoint_replay_v1"
THRESHOLD = 2e-6
STATES = 4


def load_native_adjoint(decision_path: Path) -> tuple[np.ndarray, dict[str, object]]:
    decision = json.loads(decision_path.read_text())
    if decision.get("status") != "UPSTREAM_ADJOINT_LOCALIZED":
        raise ValueError("FF2 adjoint receipt did not authorize this child")
    capture = decision["capture"]
    shape = tuple(int(value) for value in capture["native_adjoint_shape"])
    raw = base64.b64decode(
        capture["native_adjoint_f32le_fortran_base64"], validate=True
    )
    digest = hashlib.sha256(raw).hexdigest()
    if digest != capture["native_adjoint_sha256"]:
        raise ValueError("captured FF2 adjoint hash mismatch")
    adjoint = np.frombuffer(raw, dtype="<f4").reshape(shape, order="F").copy()
    if adjoint.shape != (32, STATES):
        raise ValueError(f"unexpected captured adjoint shape {adjoint.shape}")
    return adjoint, decision


def load_bound_gradients(
    export: Path, bound_dir: Path, named_decision_path: Path
) -> tuple[list[str], dict[str, np.ndarray], dict[str, object]]:
    names, dimensions = named.manifest_contract(export)
    decision = json.loads(named_decision_path.read_text())
    index_by_name = {
        item["name"]: int(item["index"])
        for item in decision["identity"]["positional_receipt_identity"]
    }
    if set(index_by_name) != set(names):
        raise ValueError("named-gradient receipt does not cover the export manifest")
    gradients = {
        name: np.fromfile(
            bound_dir / "gradients" / f"unknown_{index_by_name[name]:04d}.bin",
            dtype="<f4",
        ).reshape(dimensions[name], order="F")
        for name in names
    }
    return names, gradients, decision


def run_variant(
    export: Path,
    trace: Path,
    native_adjoint: np.ndarray,
    mode: str,
) -> tuple[np.ndarray, dict[str, np.ndarray], int]:
    if mode not in {"baseline", "ff2_branch_only", "residual_join"}:
        raise ValueError(f"unknown replay mode {mode}")
    loaded, _ = base.load_export(export)
    weights = {
        name: value.detach().clone().requires_grad_(True)
        for name, value in loaded.items()
    }
    symbols, _ = base.load_trace(trace)
    inputs = np.concatenate((np.zeros(1, dtype=np.int64), symbols[:-1]))
    token = torch.from_numpy(inputs)
    memory = torch.zeros(4, 32, dtype=torch.float32)
    native = torch.from_numpy(native_adjoint)
    hook_count = 0

    original_linear = decoder_graph.F.linear
    original_norm = decoder_graph.libnc_rms_norm

    def replacement_for(state: int, value: torch.Tensor) -> torch.Tensor:
        replacement = native[:, state].reshape_as(value).clone()
        if replacement.dtype != value.dtype or replacement.device != value.device:
            replacement = replacement.to(dtype=value.dtype, device=value.device)
        return replacement

    def linear_with_ff2_hook(
        input_value: torch.Tensor,
        weight: torch.Tensor,
        bias: torch.Tensor | None = None,
    ) -> torch.Tensor:
        nonlocal hook_count
        output = original_linear(input_value, weight, bias)
        if mode == "ff2_branch_only" and weight is weights["ff2_0"]:
            state = hook_count
            if state >= STATES:
                raise RuntimeError("too many FF2 branch hooks")
            replacement = replacement_for(state, output)
            output.register_hook(lambda _gradient, value=replacement: value)
            hook_count += 1
        return output

    def norm_with_residual_hook(
        value: torch.Tensor, gain: torch.Tensor, bias: torch.Tensor
    ) -> torch.Tensor:
        nonlocal hook_count
        if mode == "residual_join" and gain is weights["ln_g_2"]:
            state = hook_count
            if state >= STATES:
                raise RuntimeError("too many residual-join hooks")
            replacement = replacement_for(state, value)
            value.register_hook(lambda _gradient, item=replacement: item)
            hook_count += 1
        return original_norm(value, gain, bias)

    decoder_graph.F.linear = linear_with_ff2_hook
    decoder_graph.libnc_rms_norm = norm_with_residual_hook
    try:
        logits, _ = decoder_graph.decoder_graph_segment(
            weights, token, memory, 4, 4, 2, 8, 8
        )
    finally:
        decoder_graph.F.linear = original_linear
        decoder_graph.libnc_rms_norm = original_norm
    expected_hooks = 0 if mode == "baseline" else STATES
    if hook_count != expected_hooks:
        raise RuntimeError(
            f"{mode} installed {hook_count} hooks, expected {expected_hooks}"
        )
    target = torch.from_numpy(symbols)
    loss = torch.nn.functional.cross_entropy(logits, target, reduction="mean")
    loss.backward()
    gradients: dict[str, np.ndarray] = {}
    for name, value in weights.items():
        if value.grad is None:
            raise RuntimeError(f"missing {mode} gradient for {name}")
        gradients[name] = value.grad.detach().numpy().copy()
    probabilities = torch.softmax(logits, dim=-1).detach().numpy()
    return probabilities, gradients, hook_count


def probability_sha256(probabilities: np.ndarray) -> str:
    return hashlib.sha256(
        np.asarray(probabilities, dtype="<f4").tobytes(order="C")
    ).hexdigest()


def summarize(
    names: list[str],
    reference: dict[str, np.ndarray],
    candidate: dict[str, np.ndarray],
) -> dict[str, object]:
    comparisons = {
        name: named.metrics(reference[name], candidate[name]) for name in names
    }
    matched = [
        name
        for name in names
        if comparisons[name]["maximum_absolute_error"] <= THRESHOLD
        and comparisons[name]["sign_mismatches"] == 0
    ]
    return {
        "gradient_sha256": named.gradient_sha256(candidate),
        "matched_names": matched,
        "matched_count": len(matched),
        "all_match": len(matched) == len(names),
        "maximum_absolute_error": max(
            item["maximum_absolute_error"] for item in comparisons.values()
        ),
        "total_sign_mismatches": sum(
            item["sign_mismatches"] for item in comparisons.values()
        ),
        "by_name": comparisons,
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
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    args = parser.parse_args()

    required = [
        args.export / "manifest.json",
        args.bound_dir / "teacher.bin",
        args.adjoint_decision,
        args.named_decision,
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing export, trace, or source-bound decision")
    native_adjoint, adjoint_decision = load_native_adjoint(args.adjoint_decision)
    names, bound_gradients, named_decision = load_bound_gradients(
        args.export, args.bound_dir, args.named_decision
    )
    _, teacher_distributions = base.load_trace(args.bound_dir / "teacher.bin")
    teacher = np.stack(teacher_distributions)

    modes = ("baseline", "ff2_branch_only", "residual_join")
    runs: dict[str, list[dict[str, object]]] = {mode: [] for mode in modes}
    first_gradients: dict[str, dict[str, np.ndarray]] = {}
    first_probabilities: dict[str, np.ndarray] = {}
    for mode in modes:
        for repetition in range(2):
            probabilities, gradients, hook_count = run_variant(
                args.export,
                args.bound_dir / "teacher.bin",
                native_adjoint,
                mode,
            )
            runs[mode].append(
                {
                    "repetition": repetition,
                    "hook_count": hook_count,
                    "probability_sha256": probability_sha256(probabilities),
                    "gradient_sha256": named.gradient_sha256(gradients),
                }
            )
            if repetition == 0:
                first_probabilities[mode] = probabilities
                first_gradients[mode] = gradients

    repeat_identity = {
        mode: runs[mode][0] == {
            **runs[mode][1],
            "repetition": 0,
        }
        for mode in modes
    }
    probability_metrics = {
        mode: named.metrics(teacher, first_probabilities[mode]) for mode in modes
    }
    forward_identity = (
        len({runs[mode][0]["probability_sha256"] for mode in modes}) == 1
        and all(
            item["maximum_absolute_error"] <= THRESHOLD
            for item in probability_metrics.values()
        )
    )
    summaries = {
        mode: summarize(names, bound_gradients, first_gradients[mode])
        for mode in modes
    }
    baseline_repeats_parent = (
        summaries["baseline"]["gradient_sha256"]
        == named_decision["identity"]["pytorch_gradient_sha256"]
    )
    ff2_only_local_match = all(
        name in summaries["ff2_branch_only"]["matched_names"]
        for name in ("ff2_0", "ff_bias2_0")
    )
    ff2_only_insufficient = not summaries["ff2_branch_only"]["all_match"]
    residual_all_match = summaries["residual_join"]["all_match"]
    passed = (
        all(repeat_identity.values())
        and forward_identity
        and baseline_repeats_parent
        and not summaries["baseline"]["all_match"]
        and ff2_only_local_match
        and ff2_only_insufficient
        and residual_all_match
    )
    status = "RESIDUAL_ADJOINT_CONTRACT_CONFIRMED" if passed else "REJECT"
    result = {
        "schema": "gamma.nncp_v33_libnc_ff2_residual_adjoint_replay.v1",
        "candidate_id": CANDIDATE_ID,
        "status": status,
        "score_credit_bytes": 0,
        "contract": {
            "states": STATES,
            "threshold": THRESHOLD,
            "variants": list(modes),
            "intervention": (
                "replace_only_backward_adjoint_at_post_ff2_residual_join"
            ),
        },
        "inputs": {
            "script_sha256": internal.sha256(Path(__file__).resolve()),
            "teacher_trace_sha256": internal.sha256(args.bound_dir / "teacher.bin"),
            "adjoint_decision_sha256": internal.sha256(args.adjoint_decision),
            "named_decision_sha256": internal.sha256(args.named_decision),
            "captured_adjoint_sha256": adjoint_decision["capture"][
                "native_adjoint_sha256"
            ],
        },
        "identity": {
            "repeat_byte_identical": repeat_identity,
            "forward_probability_identity": forward_identity,
            "baseline_repeats_parent_pytorch_gradient": baseline_repeats_parent,
            "runs": runs,
            "probability_vs_teacher": probability_metrics,
        },
        "comparisons": summaries,
        "gate": {
            "baseline_is_known_miss": not summaries["baseline"]["all_match"],
            "ff2_branch_only_matches_ff2_and_bias": ff2_only_local_match,
            "ff2_branch_only_is_insufficient_upstream": ff2_only_insufficient,
            "residual_join_matches_all_named_gradients": residual_all_match,
            "passed": passed,
        },
        "decision": {
            "promotion_authorized": passed,
            "authorized_next_action": (
                "apply the confirmed residual-adjoint contract in one exact first-update replay"
                if passed
                else "retire receipt-bound residual-adjoint replacement as sufficient"
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
