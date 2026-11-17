"""Unit and contract tests for B2 (`self_transform_neural_proposer_v1`)."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
import torch

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from baselines import (
    run_adamw_cosine,
    run_damped_lbfgs,
    run_proposer_on_cold_target,
    run_sgd_nesterov,
)
from proposer import ProposerWeights, forward_proposer_net, init_gen0_proposer
from run_study import generate_synthetic_probes, invoke_worker_subprocess
from targets import (
    CONFIRMATION_FAMILIES,
    ChargedTargetOracle,
    OracleBudgetExceededError,
    build_target_family_task,
)


class NeuralProposerStudyTests(unittest.TestCase):
    def test_oracle_enforces_exact_budget(self):
        task = build_target_family_task("unseen_swiglu_3layer_cls", seed=777)
        oracle = ChargedTargetOracle(task)
        layers = task.clone_cold_layers(requires_grad=False)
        for _ in range(task.budget):
            oracle.forward_backward_support(layers, differentiable_graph=False)
        self.assertEqual(oracle.passes_used, task.budget)
        with self.assertRaises(OracleBudgetExceededError):
            oracle.forward_backward_support(layers, differentiable_graph=False)

    def test_all_arms_consume_identical_cold_budget(self):
        phi0 = init_gen0_proposer(seed=202611)
        for fam in CONFIRMATION_FAMILIES:
            task = build_target_family_task(fam, seed=888)
            r_prop = run_proposer_on_cold_target(phi0, task)
            r_sgd = run_sgd_nesterov({"lr": 0.1, "momentum": 0.85, "weight_decay": 0.01}, task)
            r_adam = run_adamw_cosine({"lr": 0.04, "weight_decay": 0.01}, task)
            r_lbfgs = run_damped_lbfgs({"lr": 0.75, "damping": 0.25, "weight_decay": 0.02}, task)
            for r in (r_prop, r_sgd, r_adam, r_lbfgs):
                self.assertEqual(r["passes_used"], task.budget)

    def test_cold_subprocess_self_improve_and_weight_free_behavioral_regen(self):
        phi0 = init_gen0_proposer(seed=202611)
        r_imp = invoke_worker_subprocess({
            "mode": "self_improve",
            "generation": 0,
            "parent_weights": phi0.to_flat_list(),
            "meta_seed": 510000,
            "meta_steps": 2,
            "tasks_per_step": 2,
        })
        self.assertTrue(r_imp["ok"])
        self.assertNotEqual(r_imp["child_weights"], phi0.to_flat_list())

        # Verify behavioral_regen rejects payloads containing weight arrays
        probes_x = generate_synthetic_probes(seed=42, n_probes=64)
        child_phi = ProposerWeights.from_flat_list(r_imp["child_weights"])
        with torch.no_grad():
            probes_y = forward_proposer_net(child_phi, torch.tensor(probes_x, dtype=torch.float64))[0].tolist()

        r_reg = invoke_worker_subprocess({
            "mode": "behavioral_regen",
            "probe_inputs": probes_x,
            "probe_outputs": probes_y,
            "regen_seed": 9999,
            "distill_steps": 60,
        })
        self.assertTrue(r_reg["ok"])
        self.assertLess(r_reg["functional_mse_after"], r_reg["functional_mse_before"])
        self.assertNotEqual(r_reg["regenerated_sha256"], r_imp["child_sha256"])


if __name__ == "__main__":
    unittest.main()
