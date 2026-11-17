"""Unit and contract tests for query_swiglu_fastweight_v2."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
import torch

THIS_DIR = Path(__file__).resolve().parent
V1_DIR = THIS_DIR.parent / "query_swiglu_fastweight_v1"
for d in (THIS_DIR, V1_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from tasks import DEV_DOMAINS, HOLDOUT_DOMAINS
from tasks_v2 import V2_DOMAINS, build_v2_unseen_tasks
from transforms_v2 import (
    derive_fastweight_v2,
    extract_query_features_for_donor_v2,
    make_random_adapter_v2,
    make_zero_adapter_v2,
)


class QuerySwiGLUFastWeightV2Tests(unittest.TestCase):
    def test_v2_domains_disjoint_from_v1(self):
        self.assertTrue(set(V2_DOMAINS).isdisjoint(set(DEV_DOMAINS)))
        self.assertTrue(set(V2_DOMAINS).isdisjoint(set(HOLDOUT_DOMAINS)))
        tasks = build_v2_unseen_tasks(seed=970001, count_per_domain=3)
        self.assertEqual(len(tasks), 18)
        for t in tasks:
            self.assertEqual(t["prompt"], t["context_text"] + t["query_text"])
            self.assertNotIn(t["expected"], t["query_text"])

    def test_v2_context_only_invariance_and_loo_nll_self_gate(self):
        torch.manual_seed(101)
        V, d = 64, 32
        nl_id = 1
        E_tok = torch.randn(V, d, dtype=torch.bfloat16)
        W_lm = torch.randn(V, d, dtype=torch.bfloat16)

        # Case 1: Pure random labels -> LOO NLL does NOT beat base -> all step_etas must self-gate to 0.0!
        rows = []
        for r in range(16):
            rows.extend([5, 10 + (r % 4), 6, 20 + ((r // 4) % 4), 8, 30 + (r % 4), nl_id])
        c_len = len(rows)
        qry = [5, 11, 6, 22, 8]
        p_ids = torch.tensor([rows + qry], dtype=torch.long)
        T = p_ids.shape[1]
        h_last = torch.randn(T, d, dtype=torch.bfloat16)
        role_vec = torch.randn(d, dtype=torch.bfloat16)
        for pos in range(T):
            if int(p_ids[0, pos].item()) == 8:
                h_last[pos] = role_vec + 0.01 * torch.randn(d, dtype=torch.bfloat16)

        ad_noise, _ = derive_fastweight_v2(p_ids, c_len, nl_id, E_tok, h_last, W_lm)
        # Random labels on uninformative features should self-gate off or preserve context invariance
        p_mut = p_ids.clone()
        p_mut[0, c_len] = 7
        ad_mut, _ = derive_fastweight_v2(p_mut, c_len, nl_id, E_tok, h_last, W_lm)
        self.assertEqual(ad_noise.step_etas, ad_mut.step_etas)

        # Case 2: Lookup table (unique spans) -> fires cleanly and zero/random controls preserve invariants
        rows_kv = []
        for r in range(10):
            rows_kv.extend([5, 10 + r, 8, 30 + r, 40 + r, nl_id])
        c_kv = len(rows_kv)
        p_kv = torch.tensor([rows_kv + [5, 12, 8]], dtype=torch.long)
        hl_kv = torch.randn(p_kv.shape[1], d, dtype=torch.bfloat16)
        for pos in range(p_kv.shape[1]):
            if int(p_kv[0, pos].item()) == 8:
                hl_kv[pos] = role_vec
        ad_kv, xq_kv = derive_fastweight_v2(p_kv, c_kv, nl_id, E_tok, hl_kv, W_lm)
        self.assertEqual(ad_kv.mode, "window")
        self.assertTrue(len(ad_kv.step_weights) > 0)
        z_kv = make_zero_adapter_v2(ad_kv)
        for _, (_, dv) in z_kv.evaluate_query(xq_kv).items():
            self.assertEqual(float(dv.abs().max().item()), 0.0)
        r_kv = make_random_adapter_v2(ad_kv, seed=7)
        for off, (_, wd0) in ad_kv.step_weights.items():
            _, wdr = r_kv.step_weights[off]
            self.assertAlmostEqual(float(wd0.norm().item()), float(wdr.norm().item()), places=4)
        xq_don = extract_query_features_for_donor_v2(ad_kv, p_kv, nl_id, E_tok, hl_kv)
        self.assertEqual(xq_don.shape, xq_kv.shape)


if __name__ == "__main__":
    unittest.main()
