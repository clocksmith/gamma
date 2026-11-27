"""Unit tests for B2 v2 (`self_transform_neural_proposer_v2`, Items 5–7)."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
import torch

THIS_DIR = Path(__file__).resolve().parent
V1_B2_DIR = THIS_DIR.parent / "self_transform_neural_proposer_v1"
for d in (THIS_DIR, V1_B2_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from proposer_v2 import (
    FEAT_DIM_V2,
    ProposerWeightsV2,
    forward_proposer_v2,
    init_gen0_proposer_v2,
    init_opt_state_v2,
    propose_update_v2,
)
from run_study_v2 import calibrate_conventional_by_budget, invoke_worker_v2
from tasks_b2_v2 import (
    ChargedTargetOracleV2,
    V2_CONFIRMATION_FAMILIES,
    build_progressive_meta_task,
    build_v2_confirmation_task,
)


class TestNeuralProposerV2(unittest.TestCase):
    def test_zero_extra_passes_and_differentiable_forward_parity(self) -> None:
        phi = init_gen0_proposer_v2(seed=701)
        self.assertEqual(phi.num_parameters(), 2073)
        task = build_progressive_meta_task(lineage_seed=7, gen_idx=1, task_idx=2)

        # Cold non-differentiable trajectory
        oracle_cold = ChargedTargetOracleV2(task)
        layers_cold = task.clone_cold_layers(requires_grad=False)
        st_cold = init_opt_state_v2(layers_cold)
        for s_idx in range(oracle_cold.budget):
            loss_s, grads_s, act_in, err_out = oracle_cold.forward_backward_support(layers_cold, differentiable_graph=False)
            with torch.no_grad():
                layers_cold = propose_update_v2(
                    phi=phi,
                    layers=layers_cold,
                    grads=grads_s,
                    act_inputs=act_in,
                    err_outputs=err_out,
                    opt_state=st_cold,
                    step_idx=s_idx,
                    total_steps=oracle_cold.budget,
                    cur_loss=loss_s,
                    differentiable_target=False,
                )
        self.assertEqual(oracle_cold.passes_used, 10)

        # Differentiable unrolled trajectory must match cold trajectory to < 1e-12 AND consume exact 10 passes
        phi_grad = phi.clone_detached(requires_grad=True)
        oracle_diff = ChargedTargetOracleV2(task)
        layers_diff = task.clone_cold_layers(requires_grad=True)
        st_diff = init_opt_state_v2(layers_diff)
        for s_idx in range(oracle_diff.budget):
            loss_s, grads_s, act_in, err_out = oracle_diff.forward_backward_support(layers_diff, differentiable_graph=True)
            layers_diff = propose_update_v2(
                phi=phi_grad,
                layers=layers_diff,
                grads=grads_s,
                act_inputs=act_in,
                err_outputs=err_out,
                opt_state=st_diff,
                step_idx=s_idx,
                total_steps=oracle_diff.budget,
                cur_loss=loss_s,
                differentiable_target=True,
            )
        self.assertEqual(oracle_diff.passes_used, 10)
        for wc, wd in zip(layers_cold, layers_diff):
            self.assertLess(float((wc - wd.detach()).abs().max().item()), 1e-12)

    def test_unseen_confirmation_families_and_budget_parity(self) -> None:
        for fam in V2_CONFIRMATION_FAMILIES:
            t = build_v2_confirmation_task(fam, seed=710001)
            self.assertEqual(t.budget, 10)
        conv = calibrate_conventional_by_budget(lineage_seed=77, generations=2)
        for cname in ("sgd_nesterov", "adamw_cosine", "damped_lbfgs"):
            self.assertEqual(conv[cname][1]["cumulative_upstream_passes"], 1400)
            self.assertEqual(conv[cname][2]["cumulative_upstream_passes"], 2800)

    def test_subprocess_elitist_ledger_and_weight_free_regen(self) -> None:
        phi0 = init_gen0_proposer_v2(seed=808)
        r_imp = invoke_worker_v2({
            "mode": "self_improve_v2",
            "lineage_seed": 808,
            "generation": 0,
            "parent_weights": phi0.to_flat_list(),
            "meta_batches": 3,
            "train_tasks_per_batch": 4,
            "anchor_tasks": 12,
        })
        self.assertNotEqual(r_imp["pid"], os.getpid())
        self.assertEqual(r_imp["oracle_passes_billed"], 1320)
        self.assertEqual(len(r_imp["candidates"]), 6)
        self.assertLessEqual(r_imp["anchor_opp_score_after"], r_imp["anchor_opp_score_before"] + 1e-12)
        self.assertEqual(sum(c["oracle_passes_billed"] for c in r_imp["candidates"]), 960)
        for c in r_imp["candidates"]:
            self.assertIn("parent_sha256", c)
            self.assertIn("candidate_sha256", c)
            self.assertIn("active_opponent", c)
            self.assertIn("accepted", c)

        # Behavioral regeneration must reject weight tensors and fit functionally
        gen = torch.Generator().manual_seed(909)
        X = torch.randn((128, FEAT_DIM_V2), generator=gen, dtype=torch.float64)
        child_phi = ProposerWeightsV2.from_flat_list(r_imp["child_weights"])
        with torch.no_grad():
            Y = forward_proposer_v2(child_phi, X)[0]
        r_reg = invoke_worker_v2({
            "mode": "behavioral_regen_v2",
            "probe_inputs": X.tolist(),
            "probe_outputs": Y.tolist(),
            "regen_seed": 999,
            "distill_steps": 120,
        })
        self.assertNotEqual(r_reg["pid"], os.getpid())
        self.assertLess(r_reg["functional_mse_after"], r_reg["functional_mse_before"] * 0.1)


if __name__ == "__main__":
    unittest.main()
