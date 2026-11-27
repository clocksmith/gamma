"""Unit tests for the v4-dev residual proposer (CPU only).

    .venv/bin/python -m unittest projects/self_transform_neural_proposer_v4_dev/test_identity_v4dev.py -v

The sealed v3 directory is only ever read as text here (never imported, never written).
"""
from __future__ import annotations

import inspect
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

import torch  # noqa: E402

import baselines_v4dev as B  # noqa: E402
import common_v4dev as C  # noqa: E402
import proposer_v4dev as P  # noqa: E402
import tasks_v4dev as T  # noqa: E402

V3_DIR = HERE.parent / "self_transform_neural_proposer_v3"
TOL = 1e-6


def _sealed_def(text: str, name: str, kind: str = "def") -> str:
    """Source of a top-level `def`/`class` in sealed text (up to the next top-level statement)."""
    start = text.index(f"\n{kind} {name}") + 1
    lines = text[start:].split("\n")
    out = [lines[0]]
    for ln in lines[1:]:
        if ln and not ln[0].isspace() and not ln.startswith(")"):
            break
        out.append(ln)
    return "\n".join(out).rstrip() + "\n"


def _sample_tasks() -> list:
    tasks = [C.upstream_task(C.seed_calib(95, k), k) for k in range(4)]
    tasks += [T.build_heldout_task_dev(f, C.seed_heldout(95, fi, 0)) for fi, f in enumerate(T.DEV_HELDOUT_FAMILIES)]
    return tasks


class Gen0EqualsKfacTest(unittest.TestCase):
    def setUp(self) -> None:
        torch.set_num_threads(1)

    def test_gen0_updates_equal_kfac_no_proposer(self) -> None:
        """Every one of the 10 updates of the gen-0 residual proposer matches `kfac_no_proposer` within 1e-6."""
        pool = C.kfac_pool()
        cfgs = [pool[0], pool[21], pool[55], {"lr": 0.075, "basis_weights": [0.5, 0.2, 0.4, 0.4, 0.2], "weight_decay": 0.025}]
        worst = 0.0
        for cfg in cfgs:
            base = P.KfacBaseConfig.from_cfg(cfg)
            phi = P.init_residual_proposer(C.seed_init(95))
            for task in _sample_tasks():
                ref_traj = C.kfac_trajectory(cfg, task)
                got = C.run_residual_cold(phi, base, task, return_layers=True)
                self.assertEqual(len(ref_traj), 10)
                for ref_layers, got_layers in zip(ref_traj, got["trajectory"]):
                    for a, b in zip(ref_layers, got_layers):
                        worst = max(worst, float((a - b).abs().max()))
                # and the final metrics agree with the (source-identical) sealed runner
                ref = B.run_kfac_no_proposer_v3(cfg, task)
                for k in ("final_query_loss", "final_support_loss", "query_accuracy", "query_r2"):
                    self.assertAlmostEqual(ref[k], got[k], delta=TOL)
        self.assertLess(worst, TOL)
        print(f"\n  max |W_proposer_gen0 - W_kfac| over all steps/layers/tasks/configs = {worst:.3e}")

    def test_trajectory_helper_matches_sealed_runner(self) -> None:
        cfg = C.kfac_pool()[10]
        for task in _sample_tasks():
            traj = C.kfac_trajectory(cfg, task)
            oracle = B.ChargedTargetOracleV3(task)
            fin = oracle.evaluate_query(traj[-1])
            ref = B.run_kfac_no_proposer_v3(cfg, task)
            self.assertEqual(fin["query_loss"], ref["final_query_loss"])

    def test_ablation_modes_equal_kfac_at_gen0(self) -> None:
        cfg = C.kfac_pool()[30]
        base = P.KfacBaseConfig.from_cfg(cfg)
        phi = P.init_residual_proposer(C.seed_init(96))
        zero = torch.zeros(P.OUT_DIM_V3, dtype=torch.float64)
        for task in _sample_tasks()[:3]:
            ref = B.run_kfac_no_proposer_v3(cfg, task)
            for kw in ({"row_mode": "layer_mean"}, {"row_mode": "constant", "const_raw": zero}):
                got = C.run_residual_cold(phi if kw["row_mode"] != "constant" else None, base, task, **kw)
                self.assertAlmostEqual(ref["final_query_loss"], got["final_query_loss"], delta=TOL)

    def test_differentiable_path_matches_cold_path_at_gen0(self) -> None:
        """The meta-training unroll starts from the same function as the baseline."""
        cfg = C.kfac_pool()[21]
        base = P.KfacBaseConfig.from_cfg(cfg)
        phi = P.init_residual_proposer(C.seed_init(95))
        params = [w.requires_grad_(True) for w in phi.as_list()]
        phi_g = P.ProposerWeightsV3.from_list(params)
        task = _sample_tasks()[1]
        obj = C.diff_task_objective(phi_g, base, task)
        cold = C.run_residual_cold(phi, base, task)
        oracle = B.ChargedTargetOracleV3(task, allow_meta_query_pass=True)
        oracle.passes_used = 0
        traj = C.kfac_trajectory(cfg, task)
        ref_obj = oracle.evaluate_diff_query_v3(traj[-1], cold["init_query_loss"])
        self.assertAlmostEqual(float(obj.item()), float(ref_obj.item()), delta=TOL)
        obj.backward()
        self.assertGreater(float(params[2].grad.abs().max()), 0.0)  # W_out receives a meta-gradient
        self.assertEqual(float(params[0].grad.abs().max()), 0.0)    # W_gate / W_up are blocked only at exact zero W_out

    def test_network_is_live_and_decay_cap_is_lifted(self) -> None:
        cfg = {"lr": 0.075, "basis_weights": [0.5, 0.2, 0.4, 0.4, 0.2], "weight_decay": 0.025}
        base = P.KfacBaseConfig.from_cfg(cfg)
        phi = P.init_residual_proposer(C.seed_init(95))
        phi.W_out[5, -1] = 0.4
        task = _sample_tasks()[0]
        ref = B.run_kfac_no_proposer_v3(cfg, task)
        got = C.run_residual_cold(phi, base, task)
        self.assertGreater(abs(ref["final_query_loss"] - got["final_query_loss"]), 1e-4)
        raw = torch.zeros((1, 8), dtype=torch.float64)
        raw[0, 7] = 3.0
        self.assertGreater(float(P.residual_controls(raw, base)["decay"]), 0.03)  # v3 hard cap was 0.03
        raw[0, 7] = 0.0
        ctl = P.residual_controls(raw, base)
        self.assertEqual(float(ctl["decay"]), 0.025)
        self.assertEqual(float(ctl["lr_eff"]), 0.075)
        self.assertEqual(ctl["mix"].tolist(), [[0.5, 0.2, 0.4, 0.4, 0.2]])


class SealedSourceIdentityTest(unittest.TestCase):
    """The reference baseline in the dev copy is the sealed v3 code, compared as text."""

    def test_baseline_and_basis_code_is_unchanged(self) -> None:
        base_txt = (V3_DIR / "baselines_v3.py").read_text()
        prop_txt = (V3_DIR / "proposer_v3.py").read_text()
        for name, kind, mod, txt in [
            ("run_kfac_no_proposer_v3", "def", B, base_txt),
            ("forward_target_v3", "def", B, base_txt),
            ("ChargedTargetOracleV3", "class", B, base_txt),
            ("smooth_anchor_score", "def", B, base_txt),
            ("normalized_loss_ratio", "def", B, base_txt),
            ("_build_baseline_pools_56", "def", B, base_txt),
            ("compute_five_basis_v3", "def", P, prop_txt),
            ("kfac_woodbury_solve", "def", P, prop_txt),
            ("_newton_schulz_polar", "def", P, prop_txt),
            ("init_opt_state_v3", "def", P, prop_txt),
            ("forward_proposer_v3", "def", P, prop_txt),
        ]:
            self.assertEqual(inspect.getsource(getattr(mod, name)).rstrip() + "\n", _sealed_def(txt, name, kind), name)

    def test_task_generators_are_unchanged(self) -> None:
        sealed = (V3_DIR / "tasks_b2_v3.py").read_text()
        dev = (HERE / "tasks_v4dev.py").read_text()
        marker = '    if family == "fourier_kan_multifreq_reg":'
        self.assertEqual(sealed[sealed.index(marker):], dev[dev.index(marker):])
        sealed_b = (V3_DIR / "baselines_v3.py").read_text()
        dev_b = (HERE / "baselines_v4dev.py").read_text()
        m0, m1 = "    mode = task_idx % 4", "\ndef build_shared_val_anchor_v3"
        m1_dev = "\ndef run_proposer_v3_cold"
        self.assertEqual(
            sealed_b[sealed_b.index(m0):sealed_b.index(m1)].rstrip(),
            dev_b[dev_b.index(m0):dev_b.index(m1_dev)].rstrip(),
        )

    def test_dev_seeds_are_disjoint_from_v3(self) -> None:
        import json
        proto = json.loads((V3_DIR / "protocol_v3.json").read_text())
        n = proto["num_lineage_seeds"]
        v3_max_conf = proto["confirmation_seed_base"] + (n - 1) * 10000 + 3 * 1000 + (proto["confirmation_tasks_per_family_per_seed"] - 1)
        v3_max_upstream = 100000 + (max(proto["lineage_seeds"]) + 900) * 701 + 3 * 5003 + 39 * 97
        self.assertEqual(v3_max_conf, C.MAX_V3_SEED)
        self.assertLess(max(v3_max_conf, v3_max_upstream, 950000 + 1012 * 10 + 4, 7777), B.DEV_SEED_FLOOR)
        for fn, a in [
            (C.seed_init, (0,)), (C.seed_meta_train, (0, 0)), (C.seed_upstream_val, (0, 0)), (C.seed_calib, (0, 0)),
            (C.seed_heldout, (0, 0, 0)), (C.seed_stage3_child, (0, 0)), (C.seed_infamily_train, (0, 0)),
            (C.seed_infamily_calib, (0, 0, 0)), (C.seed_infamily_val, (0, 0, 0)),
        ]:
            self.assertGreaterEqual(fn(*a), B.DEV_SEED_FLOOR)
        # the plan's blocks do not overlap each other
        blocks = [
            (C.seed_init(0), C.seed_init(99)), (C.seed_meta_train(0, 0), C.seed_meta_train(99, 99_999)),
            (C.seed_upstream_val(0, 0), C.seed_upstream_val(99, 9_999)), (C.seed_calib(0, 0), C.seed_calib(99, 9_999)),
            (C.seed_heldout(0, 0, 0), C.seed_heldout(99, 9, 999)), (C.seed_stage3_child(0, 0), C.seed_stage3_child(99, 99_999)),
            (C.seed_infamily_train(0, 0), C.seed_infamily_train(99, 99_999)),
            (C.seed_infamily_calib(0, 0, 0), C.seed_infamily_calib(99, 9, 999)),
            (C.seed_infamily_val(0, 0, 0), C.seed_infamily_val(99, 9, 999)),
        ]
        blocks.sort()
        for (_, hi), (lo, _) in zip(blocks, blocks[1:]):
            self.assertLess(hi, lo)
        with self.assertRaises(AssertionError):
            B.build_upstream_task_dev(raw_seed=9_750_000, gen_idx=0, task_idx=0)
        with self.assertRaises(AssertionError):
            T.build_heldout_task_dev("fourier_kan_multifreq_reg", 9_750_000)
        with self.assertRaises(AssertionError):
            T.build_heldout_task_dev("real_qwen35_swiglu_lora_cls", 50_000_000)


if __name__ == "__main__":
    unittest.main()
