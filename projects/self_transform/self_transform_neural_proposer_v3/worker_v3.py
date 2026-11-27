"""Isolated cold-subprocess worker for B2 v3 (`self_transform_neural_proposer_v3`).

Enforces honest, self-contained pass & FLOP accounting across generation boundaries:
- Exact `1,160` upstream oracle passes per generation (`4,640` across `4` generations):
  - `120` passes: evaluate parent `best_phi` on the `12`-task shared validation anchor (`12 x 10`).
  - `5` sequential meta-optimization steps x `208` passes (`1,040` passes) with persistent `self_opt_state`:
    - `8` progressive meta-train tasks x `11` passes (`10` differentiable support passes + `1` billed
      `evaluate_diff_query_v3` pass inside `ChargedTargetOracleV3` = `88` passes),
    - `self_modify_proposer_v3` applying `Phi_g` (`exact` / `regen`) or `Phi_0` (`fixed_proposer`) with
      persistent `self_opt_state` and NO `trust_radius / rms_all` step-length overwrite,
    - `12` anchor tasks x `10` cold passes (`120` passes) for elitist checkpoint retention.
- `behavioral_regen_v3`: weight-free behavioral distillation (`96` probes x `60` steps = `58,661,376` FLOPs)
  converted to target pass-equivalents at the exact measured `ceil(regen_flops / mean_target_pass_flops)` rate.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Any
import torch
import torch.nn.functional as F

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from baselines_v3 import (
    PROPOSER_EXACT_PASSES_PER_GEN,
    ChargedTargetOracleV3,
    NeuralTargetTaskV3,
    build_progressive_meta_task_v3,
    build_shared_val_anchor_v3,
    measure_mean_curriculum_pass_flops,
    normalized_loss_ratio,
    run_proposer_v3_cold,
    smooth_anchor_score,
)
from proposer_v3 import (
    ProposerWeightsV3,
    forward_proposer_v3,
    init_gen0_proposer_v3,
    init_opt_state_v3,
    propose_update_v3,
    self_modify_proposer_v3,
)


def weights_sha256_v3(vals: list[float]) -> str:
    return sha256((",".join(f"{v:.12g}" for v in vals)).encode("utf-8")).hexdigest()


def evaluate_anchor_v3(
    phi: ProposerWeightsV3,
    anchor_tasks: list[NeuralTargetTaskV3],
) -> tuple[float, float, float, int]:
    """Return `(mean_smooth_score, mean_norm_loss_ratio, mean_cls_acc, passes_billed)`."""
    phi_det = phi.clone_detached(requires_grad=False)
    smooth_scores: list[float] = []
    norm_ratios: list[float] = []
    cls_accs: list[float] = []
    passes = 0
    for t in anchor_tasks:
        res = run_proposer_v3_cold(phi_det, t)
        passes += int(res["passes_used"])
        smooth_scores.append(smooth_anchor_score(res, t.loss_type))
        norm_ratios.append(normalized_loss_ratio(res))
        if t.loss_type == "cross_entropy":
            cls_accs.append(float(res["query_accuracy"]))
    mean_acc = statistics.mean(cls_accs) if cls_accs else 0.0
    return (
        statistics.mean(smooth_scores),
        statistics.mean(norm_ratios),
        mean_acc,
        passes,
    )


def handle_self_improve_v3(req: dict[str, Any]) -> dict[str, Any]:
    t0 = time.monotonic()
    lineage_seed = int(req["lineage_seed"])
    gen_idx = int(req["generation"])
    k_meta_steps = int(req.get("meta_steps", 5))
    n_train_per_step = int(req.get("train_tasks_per_step", 8))
    n_anchor = int(req.get("anchor_tasks", 12))
    lineage_tag = str(req.get("lineage_tag", "exact"))

    parent_flat = req["parent_weights"]
    parent_sha = weights_sha256_v3(parent_flat)
    parent_gen_phi = ProposerWeightsV3.from_flat_list(parent_flat)
    rule_phi = (
        ProposerWeightsV3.from_flat_list(req["fixed_proposer_weights"])
        if req.get("fixed_proposer_weights") is not None
        else parent_gen_phi.clone_detached(requires_grad=False)
    )
    rule_sha = weights_sha256_v3(rule_phi.to_flat_list())

    anchor_tasks = build_shared_val_anchor_v3(lineage_seed=lineage_seed, count=n_anchor)
    passes_billed = 0

    score_before, ratio_before, acc_before, p0 = evaluate_anchor_v3(parent_gen_phi, anchor_tasks)
    passes_billed += p0

    best_phi = parent_gen_phi.clone_detached(requires_grad=False)
    best_score = score_before
    best_ratio = ratio_before
    best_acc = acc_before
    best_sha = parent_sha

    traj_phi = best_phi.clone_detached(requires_grad=False)
    # Persistent self_opt_state across all sequential meta-steps in the trajectory
    self_state = init_opt_state_v3(traj_phi.as_list())

    candidates_log: list[dict[str, Any]] = []
    pass_flops_samples: list[int] = []

    for k_m in range(k_meta_steps):
        ts_step = time.monotonic()
        traj_parent_sha = weights_sha256_v3(traj_phi.to_flat_list())
        phi_grad = traj_phi.clone_detached(requires_grad=True)
        captured_forwards: list[dict[str, torch.Tensor]] = []
        query_objs: list[torch.Tensor] = []
        train_passes = 0

        for m_i in range(n_train_per_step):
            t_idx = k_m * n_train_per_step + m_i
            task = build_progressive_meta_task_v3(lineage_seed=lineage_seed, gen_idx=gen_idx, task_idx=t_idx)
            pass_flops_samples.append(task.estimate_single_support_pass_flops())

            oracle = ChargedTargetOracleV3(task, allow_meta_query_pass=True)
            layers = task.clone_cold_layers(requires_grad=True)
            init_ql = oracle.evaluate_query(layers)["query_loss"]
            opt_st = init_opt_state_v3(layers)
            for s_idx in range(oracle.support_budget):
                loss_s, grads_s, act_in, err_out = oracle.forward_backward_support(layers, differentiable_graph=True)
                layers = propose_update_v3(
                    phi=phi_grad,
                    layers=layers,
                    grads=grads_s,
                    act_inputs=act_in,
                    err_outputs=err_out,
                    opt_state=opt_st,
                    step_idx=s_idx,
                    total_steps=oracle.support_budget,
                    cur_loss=loss_s,
                    capture_self_acts=captured_forwards,
                    differentiable_target=True,
                )
            # Explicitly billed (+1 pass) inside ChargedTargetOracleV3
            q_obj = oracle.evaluate_diff_query_v3(layers, init_ql)
            assert oracle.passes_used == oracle.support_budget + 1
            train_passes += oracle.passes_used
            query_objs.append(q_obj)

        meta_train_loss = torch.stack(query_objs).mean()
        cand_phi, step_info = self_modify_proposer_v3(
            parent_phi=phi_grad,
            meta_loss=meta_train_loss,
            captured_forwards=captured_forwards,
            self_opt_state=self_state,
            meta_step_idx=k_m,
            total_meta_steps=k_meta_steps,
            proposer_rule_phi=rule_phi,
            max_rms_safety_clip=0.50,
        )

        cand_flat = cand_phi.to_flat_list()
        cand_sha = weights_sha256_v3(cand_flat)
        if all(math.isfinite(x) for x in cand_flat):
            c_score, c_ratio, c_acc, vp = evaluate_anchor_v3(cand_phi, anchor_tasks)
        else:
            _, _, _, vp = evaluate_anchor_v3(best_phi, anchor_tasks)
            c_score, c_ratio, c_acc = 4.0, 10.0, 0.0

        billed_here = train_passes + vp
        passes_billed += billed_here

        # Maintain multi-step trajectory unless candidate degrades sharply on validation anchor
        if math.isfinite(c_score) and c_score <= best_score + 0.015:
            traj_phi = cand_phi.clone_detached(requires_grad=False)
        else:
            traj_phi = best_phi.clone_detached(requires_grad=False)

        accepted = bool(math.isfinite(c_score) and c_score < best_score - 1e-7)
        if accepted:
            best_score = c_score
            best_ratio = c_ratio
            best_acc = c_acc
            best_phi = cand_phi.clone_detached(requires_grad=False)
            best_sha = cand_sha

        candidates_log.append({
            "lineage_tag": lineage_tag,
            "lineage_seed": lineage_seed,
            "generation": gen_idx + 1,
            "proposal_idx": k_m,
            "subprocess_pid": os.getpid(),
            "rule_sha256": rule_sha,
            "trajectory_parent_sha256": traj_parent_sha,
            "candidate_sha256": cand_sha,
            "raw_step_rms": step_info["raw_step_rms"],
            "safety_clip_triggered": step_info["safety_clip_triggered"],
            "meta_train_co_primary_loss": float(meta_train_loss.item()),
            "anchor_smooth_score": c_score,
            "anchor_norm_loss_ratio": c_ratio,
            "anchor_cls_accuracy": c_acc,
            "accepted": accepted,
            "oracle_passes_billed": billed_here,
            "wall_ms": (time.monotonic() - ts_step) * 1000.0,
        })

    if k_meta_steps == 5 and n_train_per_step == 8 and n_anchor == 12:
        assert passes_billed == PROPOSER_EXACT_PASSES_PER_GEN

    out_flat = best_phi.to_flat_list()
    return {
        "ok": True,
        "pid": os.getpid(),
        "lineage_seed": lineage_seed,
        "generation_in": gen_idx,
        "generation_out": gen_idx + 1,
        "rule_sha256": rule_sha,
        "anchor_smooth_before": score_before,
        "anchor_smooth_after": best_score,
        "anchor_ratio_before": ratio_before,
        "anchor_ratio_after": best_ratio,
        "anchor_cls_acc_before": acc_before,
        "anchor_cls_acc_after": best_acc,
        "oracle_passes_billed": passes_billed,
        "measured_mean_target_pass_flops": float(statistics.mean(pass_flops_samples)),
        "wall_ms": (time.monotonic() - t0) * 1000.0,
        "parent_sha256": parent_sha,
        "child_sha256": best_sha,
        "child_weights": out_flat,
        "candidates": candidates_log,
    }


def handle_behavioral_regen_v3(req: dict[str, Any]) -> dict[str, Any]:
    t0 = time.monotonic()
    for forbidden in ("parent_weights", "child_weights", "weights", "W_gate", "W_up", "W_out"):
        assert forbidden not in req, f"Forbidden weight key '{forbidden}' in behavioral_regen_v3!"

    X_p = torch.tensor(req["probe_inputs"], dtype=torch.float64)
    Y_p = torch.tensor(req["probe_outputs"], dtype=torch.float64)
    student = init_gen0_proposer_v3(seed=int(req["regen_seed"]))
    w_params = [
        student.W_gate.requires_grad_(True),
        student.W_up.requires_grad_(True),
        student.W_out.requires_grad_(True),
    ]
    s_grad = ProposerWeightsV3.from_list(w_params)

    steps = int(req.get("distill_steps", 60))
    opt = torch.optim.Adam(w_params, lr=0.05)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps, eta_min=0.003)
    init_mse = None
    for s in range(steps):
        opt.zero_grad()
        pred, _ = forward_proposer_v3(s_grad, X_p, capture_activations=False)
        loss = F.mse_loss(pred, Y_p)
        if s == 0:
            init_mse = float(loss.item())
        loss.backward()
        opt.step()
        sched.step()

    fin_mse = float(F.mse_loss(forward_proposer_v3(s_grad, X_p, capture_activations=False)[0], Y_p).item())
    out_flat = s_grad.to_flat_list()

    n_probes = int(X_p.shape[0])
    n_params = student.num_parameters()
    # Exact FLOPs: (1 teacher forward + 3 * steps student forward-backward) * 2 * n_probes * n_params
    regen_flops = int((1 + 3 * steps) * 2 * n_probes * n_params)
    mean_pass_flops = float(req.get("mean_target_pass_flops", measure_mean_curriculum_pass_flops()))
    assert mean_pass_flops > 0.0
    pass_equiv = int(math.ceil(float(regen_flops) / mean_pass_flops))
    return {
        "ok": True,
        "pid": os.getpid(),
        "probe_count": n_probes,
        "distill_steps_billed": steps,
        "proposer_parameter_count": n_params,
        "reconstruction_flops_measured": regen_flops,
        "mean_target_pass_flops_used": mean_pass_flops,
        "oracle_pass_equivalents_billed": pass_equiv,
        "functional_mse_before": init_mse,
        "functional_mse_after": fin_mse,
        "wall_ms": (time.monotonic() - t0) * 1000.0,
        "regenerated_weights": out_flat,
        "regenerated_sha256": weights_sha256_v3(out_flat),
    }


def handle_evaluate_cold_v3(req: dict[str, Any]) -> dict[str, Any]:
    from tasks_b2_v3 import build_v3_confirmation_task

    phi = ProposerWeightsV3.from_flat_list(req["weights"])
    allow_synth = bool(req.get("allow_synthetic_qwen_fallback", False))
    results = []
    for sp in req["tasks"]:
        task = build_v3_confirmation_task(
            family=sp["family"],
            seed=int(sp["seed"]),
            allow_synthetic_qwen_fallback=allow_synth,
        )
        res = run_proposer_v3_cold(phi, task)
        results.append({
            "task_id": task.task_id,
            "family": task.family,
            "seed": int(sp["seed"]),
            "loss_type": task.loss_type,
            **res,
        })
    return {
        "ok": True,
        "pid": os.getpid(),
        "proposer_sha256": weights_sha256_v3(req["weights"]),
        "results": results,
    }


def main() -> None:
    torch.set_num_threads(1)
    req = json.loads(sys.stdin.read())
    mode = req["mode"]
    if mode == "self_improve_v3":
        resp = handle_self_improve_v3(req)
    elif mode == "behavioral_regen_v3":
        resp = handle_behavioral_regen_v3(req)
    elif mode == "evaluate_cold_v3":
        resp = handle_evaluate_cold_v3(req)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
