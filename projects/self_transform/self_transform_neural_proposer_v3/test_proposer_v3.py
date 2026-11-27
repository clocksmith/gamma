"""Unit tests for Track B2 v3 (`self_transform_neural_proposer_v3`).

Never opens or evaluates sealed confirmation seeds (`>= 5,000,000`).
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import torch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from baselines_v3 import (
    BASELINE_RUNNERS_V3,
    ChargedTargetOracleV3,
    OracleBudgetExceededError,
    build_progressive_meta_task_v3,
    run_proposer_v3_cold,
)
from proposer_v3 import ProposerWeightsV3, forward_proposer_v3, init_gen0_proposer_v3
import run_study_v3 as driver
from tasks_b2_v3 import V3_CONFIRMATION_FAMILIES, build_v3_confirmation_task
from worker_v3 import handle_behavioral_regen_v3, handle_self_improve_v3


class TestNeuralProposerV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        torch.set_num_threads(1)

    def _dev_task(self):
        return build_progressive_meta_task_v3(101, 0, 1)

    def test_preflight_and_disjoint_confirmation_seeds(self) -> None:
        protocol, addendum = driver.preflight(verify_checkpoint=False)
        self.assertEqual(len(protocol["lineage_seeds"]), 12)
        self.assertFalse(protocol["gamma_head_present"])
        self.assertEqual(set(protocol["confirmation_families"]), set(V3_CONFIRMATION_FAMILIES))
        self.assertIn("tasks_b2_v3.py", addendum["bound_code_sha256"])
        self.assertIn("run_study_v3.py", addendum["bound_code_sha256"])

        seeds = [
            r["seed"]
            for i in range(len(protocol["lineage_seeds"]))
            for r in driver.confirmation_specs(protocol, i)
        ]
        self.assertEqual(len(seeds), 12 * 4 * 12)
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertTrue(all(s >= protocol["confirmation_seed_minimum_lock"] for s in seeds))

    def test_default_cli_is_preflight_only(self) -> None:
        with patch("sys.argv", ["run_study_v3.py"]), patch.object(driver, "execute") as ex_mock:
            driver.main()
            ex_mock.assert_not_called()

    def test_serialization_and_zero_gamma_head(self) -> None:
        phi = init_gen0_proposer_v3(701)
        self.assertEqual(phi.num_parameters(), 1688)
        restored = ProposerWeightsV3.from_flat_list(phi.to_flat_list())
        for a, b in zip(phi.as_list(), restored.as_list()):
            self.assertTrue(torch.equal(a, b))

    def test_meta_query_pass_billed_in_oracle(self) -> None:
        task = self._dev_task()
        oracle = ChargedTargetOracleV3(task, allow_meta_query_pass=True)
        layers = task.clone_cold_layers()
        init_loss = oracle.evaluate_query(layers)["query_loss"]
        for _ in range(task.budget):
            oracle.forward_backward_support(layers)
        self.assertEqual(oracle.passes_used, 10)
        with self.assertRaises(OracleBudgetExceededError):
            oracle.forward_backward_support(layers)
        q_loss = oracle.evaluate_diff_query_v3(layers, init_loss)
        self.assertTrue(torch.isfinite(q_loss))
        self.assertEqual(oracle.passes_used, 11)
        with self.assertRaises(OracleBudgetExceededError):
            oracle.evaluate_diff_query_v3(layers, init_loss)

    def test_all_six_baselines_and_dev_families_run_on_dev_seed(self) -> None:
        phi = init_gen0_proposer_v3(202)
        for fam in V3_CONFIRMATION_FAMILIES:
            # Strictly dev seed (< 10,000), synthetic fallback allowed for unit-test speed
            t = build_v3_confirmation_task(fam, seed=4242, allow_synthetic_qwen_fallback=True)
            r_prop = run_proposer_v3_cold(phi, t)
            self.assertEqual(r_prop["passes_used"], 10)
            self.assertTrue(math.isfinite(r_prop["final_query_loss"]))
            for bname, fn in BASELINE_RUNNERS_V3.items():
                cfg = {
                    "lr": 0.05,
                    "momentum": 0.75,
                    "beta1": 0.85,
                    "beta2": 0.96,
                    "weight_decay": 0.01,
                    "damping": 0.2,
                    "max_step": 1.0,
                    "basis_weights": [0.3, 0.2, 0.5, 0.5, 0.3],
                }
                rb = fn(cfg, t)
                self.assertEqual(rb["passes_used"], 10, msg=f"{bname} on {fam}")
                self.assertTrue(math.isfinite(rb["final_query_loss"]), msg=f"{bname} on {fam}")

    def test_worker_billing_and_honest_regen_flop_conversion(self) -> None:
        phi = init_gen0_proposer_v3(303)
        out = handle_self_improve_v3({
            "lineage_seed": 303,
            "generation": 0,
            "parent_weights": phi.to_flat_list(),
            "lineage_tag": "exact",
            "meta_steps": 1,
            "train_tasks_per_step": 1,
            "anchor_tasks": 1,
        })
        self.assertTrue(out["ok"])
        self.assertEqual(out["oracle_passes_billed"], 10 + 11 + 10)

        x = torch.zeros((4, 16), dtype=torch.float64)
        y = forward_proposer_v3(phi, x, capture_activations=False)[0].detach()
        reg = handle_behavioral_regen_v3({
            "probe_inputs": x.tolist(),
            "probe_outputs": y.tolist(),
            "regen_seed": 304,
            "distill_steps": 2,
            "mean_target_pass_flops": 2500.0,
        })
        expected_flops = (1 + 3 * 2) * 2 * 4 * 1688
        self.assertEqual(reg["reconstruction_flops_measured"], expected_flops)
        self.assertEqual(reg["oracle_pass_equivalents_billed"], math.ceil(expected_flops / 2500.0))

    def test_lineage_statistical_tests_and_mocked_driver_rows(self) -> None:
        # Exact Wilcoxon and Student-t sanity check on 12 paired values
        focal = [0.20 + 0.001 * i + 0.0002 * (i % 3) for i in range(12)]
        ref = [0.25 + 0.001 * i for i in range(12)]
        st = driver.paired_lineage_summary(focal, ref, higher_is_better=False)
        self.assertEqual(st["wins"], 12)
        self.assertAlmostEqual(st["exact_wilcoxon_two_sided_p"], 2.0 / 4096.0, places=7)
        self.assertLess(st["two_sided_t_p"], 1e-6)

        # Mocked 2-seed execution retains all per-task rows
        protocol, addendum = copy.deepcopy(driver.preflight(verify_checkpoint=False))
        protocol.update(
            lineage_seeds=[1001, 1002],
            generations=1,
            confirmation_tasks_per_family_per_seed=1,
        )
        fake_cal = {
            b: {bt: {1: {"best_config": {}}} for bt in ("exact_matched", "regen_matched")}
            for b in protocol["required_baselines"]
        }
        fake_row = {
            "init_query_loss": 2.0,
            "final_query_loss": 0.8,
            "final_support_loss": 0.7,
            "passes_used": 10,
            "query_accuracy": 0.65,
            "query_r2": 0.55,
        }

        def fake_worker(req):
            if req["mode"] == "evaluate_cold_v3":
                return {
                    "ok": True,
                    "results": [
                        {**fake_row, "task_id": f"{sp['family']}-{sp['seed']}", "family": sp["family"], "seed": sp["seed"], "loss_type": "mse" if "reg" in sp["family"] else "cross_entropy"}
                        for sp in req["tasks"]
                    ],
                }
            if req["mode"] == "self_improve_v3":
                return {
                    "ok": True,
                    "oracle_passes_billed": protocol["proposer_exact_passes_per_generation"],
                    "child_weights": req["parent_weights"],
                    "measured_mean_target_pass_flops": 286515.0,
                    "candidates": [{"accepted": True}],
                }
            return {
                "ok": True,
                "oracle_pass_equivalents_billed": 205,
                "regenerated_weights": init_gen0_proposer_v3(1001).to_flat_list(),
            }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_ckpt = root / "fake.safetensors"
            fake_ckpt.write_bytes(b"test")
            def fake_build(family, seed, **kwargs):
                return SimpleNamespace(task_id=f"{family}-{seed}", family=family, loss_type="mse" if "reg" in family else "cross_entropy")
            with patch("tasks_b2_v3.QWEN35_SAFETENSORS_FILE", fake_ckpt), \
                 patch("tasks_b2_v3.build_v3_confirmation_task", side_effect=fake_build), \
                 patch("baselines_v3.calibrate_all_baselines_v3", return_value=fake_cal), \
                 patch.dict("baselines_v3.BASELINE_RUNNERS_V3", {b: (lambda cfg, t: dict(fake_row)) for b in protocol["required_baselines"]}, clear=True), \
                 patch.object(driver, "invoke_worker", side_effect=fake_worker):
                res = driver.execute(root / "out", protocol, addendum, workers=1)
                self.assertTrue(res["completed"])
                self.assertTrue(res["acceptance_gates_evaluated"])
                self.assertGreater(len(res["rows"]), 0)


if __name__ == "__main__":
    unittest.main()
