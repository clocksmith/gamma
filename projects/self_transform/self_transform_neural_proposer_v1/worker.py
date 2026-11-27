"""Isolated cold-subprocess worker for B2 (`self_transform_neural_proposer_v1`).

Every invocation runs in a fresh OS process, reads one JSON command on stdin, and emits one JSON receipt on stdout:
1. `mode == "self_improve"`: Reconstructs `Phi_g`, runs `meta_steps` of self-application (`M_Phi` modifying its own
   3 weight matrices via `self_modify_proposer_step`, zero external optimizer!), and emits `Phi_{g+1}` + compute ledger.
2. `mode == "behavioral_regen"`: Asserts ZERO weight tensors appear in stdin payload; initializes a fresh random
   `ProposerWeights` from scratch and distills `(probe_inputs, probe_outputs)` to reconstruct functional child `hat_Phi`.
3. `mode == "evaluate_cold"`: Reconstructs `Phi` in a fresh process with `opt_state = None` and evaluates unseen cold
   neural target tasks under the strict `B = 10` forward-backward pass oracle.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sys
import torch
import torch.nn.functional as F

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from baselines import run_proposer_on_cold_target
from proposer import (
    FEAT_DIM,
    ProposerWeights,
    forward_proposer_net,
    init_gen0_proposer,
    init_optimizer_state,
    propose_network_update,
    self_modify_proposer_step,
)
from targets import (
    ChargedTargetOracle,
    build_meta_training_task,
    build_target_family_task,
    evaluate_differentiable_query_loss,
)


def weights_sha256(vals: list[float]) -> str:
    raw = ",".join(f"{v:.12g}" for v in vals).encode("utf-8")
    return sha256(raw).hexdigest()


def evaluate_meta_validation(phi: ProposerWeights, meta_seed: int, gen_idx: int, n_val: int = 6) -> tuple[float, int]:
    """Evaluate normalized held-out query loss on `n_val` disjoint 2-layer meta-validation tasks."""
    phi_det = phi.clone_detached(requires_grad=False)
    ratios = []
    passes = 0
    for v_idx in range(n_val):
        task = build_meta_training_task(seed=meta_seed + 500000, gen_idx=gen_idx, task_idx=v_idx)
        res = run_proposer_on_cold_target(phi_det, task)
        passes += res["passes_used"]
        r = res["final_query_loss"] / max(res["init_query_loss"], 1e-6)
        ratios.append(r if math.isfinite(r) else 10.0)
    return sum(ratios) / len(ratios), passes


def handle_self_improve(req: dict) -> dict:
    gen_idx = int(req["generation"])
    meta_seed = int(req["meta_seed"])
    meta_steps = int(req.get("meta_steps", 12))
    tasks_per_step = int(req.get("tasks_per_step", 4))

    cur_phi = ProposerWeights.from_flat_list(req["parent_weights"])
    self_state = init_optimizer_state(cur_phi.as_list())

    val_before, val_passes0 = evaluate_meta_validation(cur_phi, meta_seed, gen_idx)
    best_val = val_before
    best_phi = cur_phi.clone_detached(requires_grad=False)
    oracle_passes_billed = val_passes0

    step_trace = []
    for m_step in range(meta_steps):
        phi_grad = cur_phi.clone_detached(requires_grad=True)
        captured_forwards: list[dict[str, torch.Tensor]] = []
        norm_q_losses = []

        for k in range(tasks_per_step):
            t_idx = m_step * tasks_per_step + k
            task = build_meta_training_task(seed=meta_seed, gen_idx=gen_idx, task_idx=t_idx)
            oracle = ChargedTargetOracle(task)
            layers = task.clone_cold_layers(requires_grad=True)
            init_q = float(oracle.evaluate_query(layers)["query_loss"])
            opt_state = init_optimizer_state(layers)

            for s_idx in range(oracle.budget):
                loss_s, grads_s, act_in, err_out = oracle.forward_backward_support(
                    layers, differentiable_graph=False
                )
                layers = propose_network_update(
                    phi=phi_grad,
                    layers=layers,
                    grads=grads_s,
                    act_inputs=act_in,
                    err_outputs=err_out,
                    opt_state=opt_state,
                    step_idx=s_idx,
                    total_steps=oracle.budget,
                    cur_loss=loss_s,
                    capture_self_acts=captured_forwards,
                )
            oracle_passes_billed += oracle.passes_used
            q_loss_t = evaluate_differentiable_query_loss(task, layers)
            norm_q_losses.append(q_loss_t / max(init_q, 1e-6))

        meta_loss = torch.stack(norm_q_losses).mean()
        # SELF-MODIFICATION: `phi_grad` applies ITSELF to its own layers & meta-activations!
        cand_phi = self_modify_proposer_step(
            parent_phi=phi_grad,
            meta_loss=meta_loss,
            captured_forwards=captured_forwards,
            self_opt_state=self_state,
            meta_step_idx=m_step,
            total_meta_steps=meta_steps,
        )

        # Check finite & meta-validation progress
        flat_cand = cand_phi.to_flat_list()
        if all(math.isfinite(x) for x in flat_cand):
            cur_phi = cand_phi
            val_now, vp = evaluate_meta_validation(cur_phi, meta_seed, gen_idx)
            oracle_passes_billed += vp
            if val_now < best_val:
                best_val = val_now
                best_phi = cur_phi.clone_detached(requires_grad=False)
            step_trace.append({"step": m_step, "meta_train_ratio": float(meta_loss.item()), "meta_val_ratio": val_now})
        else:
            # Revert to best_phi and damp self_state if an exploratory self-step overflowed
            cur_phi = best_phi.clone_detached(requires_grad=False)
            step_trace.append({"step": m_step, "meta_train_ratio": float(meta_loss.item()), "meta_val_ratio": best_val, "reverted": True})

    out_flat = best_phi.to_flat_list()
    return {
        "ok": True,
        "pid": os.getpid(),
        "generation_in": gen_idx,
        "generation_out": gen_idx + 1,
        "meta_val_ratio_before": val_before,
        "meta_val_ratio_after": best_val,
        "oracle_passes_billed": oracle_passes_billed,
        "child_weights": out_flat,
        "child_sha256": weights_sha256(out_flat),
        "step_trace": step_trace,
    }


def handle_behavioral_regen(req: dict) -> dict:
    # Hard invariant: NO weights may cross the OS process boundary in functional self-regeneration!
    for forbidden in ("parent_weights", "child_weights", "weights", "W_gate", "W_up", "W_out"):
        assert forbidden not in req, f"Forbidden weight key '{forbidden}' in behavioral_regen payload!"

    X_probe = torch.tensor(req["probe_inputs"], dtype=torch.float64)       # (N_p, 14)
    Y_probe = torch.tensor(req["probe_outputs"], dtype=torch.float64)      # (N_p, 7)
    regen_seed = int(req["regen_seed"])
    distill_steps = int(req.get("distill_steps", 220))

    # Initialize a brand-new SwiGLU proposer from a fresh random seed (completely different neuron permutation!)
    student = init_gen0_proposer(seed=regen_seed)
    w_params = [student.W_gate.requires_grad_(True), student.W_up.requires_grad_(True), student.W_out.requires_grad_(True)]
    student_Grad = ProposerWeights.from_list(w_params)

    # Fit student strictly to the behavioral input-output transcript `(X_probe, Y_probe)`
    opt = torch.optim.Adam(w_params, lr=0.035)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=distill_steps, eta_min=0.002)
    init_mse = None
    for s in range(distill_steps):
        opt.zero_grad()
        pred, _ = forward_proposer_net(student_Grad, X_probe, capture_activations=False)
        loss = F.mse_loss(pred, Y_probe)
        if s == 0:
            init_mse = float(loss.item())
        loss.backward()
        opt.step()
        sched.step()

    final_mse = float(F.mse_loss(forward_proposer_net(student_Grad, X_probe)[0], Y_probe).item())
    out_flat = student_Grad.to_flat_list()
    return {
        "ok": True,
        "pid": os.getpid(),
        "probe_count": int(X_probe.shape[0]),
        "distill_steps_billed": distill_steps,
        "functional_mse_before": init_mse,
        "functional_mse_after": final_mse,
        "regenerated_weights": out_flat,
        "regenerated_sha256": weights_sha256(out_flat),
    }


def handle_evaluate_cold(req: dict) -> dict:
    phi = ProposerWeights.from_flat_list(req["weights"])
    specs = req["tasks"]  # list of {"family": str, "seed": int}
    results = []
    for sp in specs:
        task = build_target_family_task(family=sp["family"], seed=int(sp["seed"]))
        res = run_proposer_on_cold_target(phi, task)
        results.append({
            "task_id": task.task_id,
            "family": task.family,
            "seed": int(sp["seed"]),
            **res,
        })
    return {
        "ok": True,
        "pid": os.getpid(),
        "proposer_sha256": weights_sha256(req["weights"]),
        "results": results,
    }


def main() -> None:
    torch.set_num_threads(1)
    req = json.loads(sys.stdin.read())
    mode = req["mode"]
    if mode == "self_improve":
        resp = handle_self_improve(req)
    elif mode == "behavioral_regen":
        resp = handle_behavioral_regen(req)
    elif mode == "evaluate_cold":
        resp = handle_evaluate_cold(req)
    else:
        raise ValueError(f"Unknown worker mode: {mode}")
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
