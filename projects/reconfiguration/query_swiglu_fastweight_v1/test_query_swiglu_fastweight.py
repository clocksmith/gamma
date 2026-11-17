"""Unit and contract tests for query_swiglu_fastweight_v1."""
from __future__ import annotations

from pathlib import Path
import sys
import torch

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from tasks import DEV_DOMAINS, HOLDOUT_DOMAINS, build_dev_family_tasks, build_holdout_family_tasks
from score_receipts import canonicalize_answer, is_equivalent_output, score_subset
from transforms import (
    CANDIDATE_NAMES,
    derive_fastweight_From_states,
    extract_query_features_for_donor,
    make_random_adapter,
    make_zero_adapter,
    safe_norm,
)


def test_task_populations_and_seed_disjointness():
    s1 = build_dev_family_tasks(seed=810001, count_per_domain=4)
    s2 = build_dev_family_tasks(seed=920001, count_per_domain=4)
    ho = build_holdout_family_tasks(seed=930001, count_per_domain=4)

    assert {t["domain"] for t in s1} == set(DEV_DOMAINS)
    assert {t["domain"] for t in ho} == set(HOLDOUT_DOMAINS)
    assert {t["prompt"] for t in s1}.isdisjoint({t["prompt"] for t in s2})

    for t in s1 + s2 + ho:
        assert t["prompt"] == t["context_text"] + t["query_text"]
        assert t["expected"] not in t["query_text"]
        assert len(t["half_a_prompt"]) < len(t["prompt"])
        assert len(t["half_b_prompt"]) < len(t["prompt"])


def test_zero_query_answer_leakage_and_control_invariants():
    torch.manual_seed(42)
    V, d = 64, 32
    nl_id = 1
    E_tok = torch.randn(V, d, dtype=torch.bfloat16)
    W_lm = torch.randn(V, d, dtype=torch.bfloat16)

    # Construct 12 structured context demos + query + sentinel future answer tokens after T_prompt
    rows = []
    for r in range(12):
        a = 10 + (r % 2)
        b = 20 + ((r // 2) % 2)
        lbl = 30 + (r % 4)
        rows.extend([5, a, 6, b, 7, 8, lbl, nl_id])
    c_len = len(rows)
    qry = [5, 11, 6, 21, 7, 8]
    p_base = torch.tensor([rows + qry], dtype=torch.long)
    T = p_base.shape[1]

    h_early = torch.randn(T, d, dtype=torch.bfloat16)
    h_mid = torch.randn(T, d, dtype=torch.bfloat16)
    h_last = torch.randn(T, d, dtype=torch.bfloat16)
    # Align syntactic state `8` across demos and query cursor
    role_vec = torch.randn(d, dtype=torch.bfloat16)
    for pos in range(T):
        if int(p_base[0, pos].item()) == 8:
            h_last[pos] = role_vec + 0.01 * torch.randn(d, dtype=torch.bfloat16)

    for cand in CANDIDATE_NAMES:
        ad1, xq1 = derive_fastweight_From_states(
            cand, p_base, c_len, nl_id, E_tok, h_last, W_lm, h_early, h_mid
        )
        # Mutate tokens strictly at/after c_len (except syntactic role at T-1) -> context adapter W_down must be identical!
        p_mut = p_base.clone()
        p_mut[0, c_len] = 9  # mutate query start token
        ad2, _ = derive_fastweight_From_states(
            cand, p_mut, c_len, nl_id, E_tok, h_last, W_lm, h_early, h_mid
        )
        assert ad1.anchors_count == ad2.anchors_count
        for off in ad1.step_weights:
            u1, w1 = ad1.step_weights[off]
            u2, w2 = ad2.step_weights[off]
            assert torch.equal(u1, u2)
            assert torch.allclose(w1, w2, atol=1e-6)

        if xq1 is not None and ad1.step_weights:
            # Zero control produces exact 0.0 logit delta
            z_ad = make_zero_adapter(ad1)
            z_out = z_ad.evaluate_query(xq1)
            for _, (_, dv) in z_out.items():
                assert float(dv.abs().max().item()) == 0.0

            # Random control preserves Frobenius norm of each step weight matrix
            r_ad = make_random_adapter(ad1, seed=123)
            for off, (_, wd_orig) in ad1.step_weights.items():
                _, wd_rand = r_ad.step_weights[off]
                assert abs(float(wd_orig.norm().item()) - float(wd_rand.norm().item())) < 1e-4

            # Donor query extraction returns matching dimensionality
            xq_donor = extract_query_features_for_donor(ad1, p_base, nl_id, E_tok, h_last, h_early, h_mid)
            assert xq_donor is not None and xq_donor.shape == xq1.shape


def test_safe_norm_matches_ieee_on_noncontiguous_views():
    x = torch.randn(12, 8, 64)
    cat = torch.cat([x.reshape(12, -1), (2.0 * x).reshape(12, -1)], dim=-1)
    sn = safe_norm(cat)
    norms = sn.pow(2).sum(dim=-1).sqrt()
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)


import unittest


def test_symmetric_scorer_punctuation_and_equivalent_forms():
    # Symmetric trailing punctuation & formatting equivalence
    assert is_equivalent_output("lead_tu89", "lead_tu89.")
    assert is_equivalent_output(" lead_tu89. \nExtra commentary", "lead_tu89.")
    assert is_equivalent_output("`SLA=mo-P1`;", "SLA=mo-P1")
    assert is_equivalent_output('"LANE=ka2",', "LANE=ka2")
    assert is_equivalent_output("  DECISION=ALLOW-ve9   ", "DECISION=ALLOW-ve9.")
    assert canonicalize_answer("a   b\tc.") == "a b c"

    # Strict non-equivalence: distinct delimiters, quantities, and keys must NEVER match
    assert not is_equivalent_output("DOSE=mo-15mg", "DOSE=mo-10mg")
    assert not is_equivalent_output("nd_209 : mi-66", "nd_209/mi-66")
    assert not is_equivalent_output("lead_tu89", "lead_tu88.")
    assert not is_equivalent_output("SLA=mo-P1", "SLA=mo-P2")

    # Verify score_subset preserves raw_original vs symmetric_canonical side-by-side without mutating rows
    sample_rows = [
        {"id": "p1", "domain": "prose_fact_registry", "arm": "base", "output": "lead_ru37", "expected": "lead_tu89.", "correct": False, "setup_ms": 0.0, "first_token_ms": 10.0, "decode_ms": 5.0, "total_ms": 15.0, "logical_bytes": 0},
        {"id": "p1", "domain": "prose_fact_registry", "arm": "focal_fastweight", "output": "lead_tu89", "expected": "lead_tu89.", "correct": False, "setup_ms": 1.0, "first_token_ms": 10.5, "decode_ms": 5.0, "total_ms": 15.5, "logical_bytes": 128},
    ]
    raw_res = score_subset(sample_rows, mode="raw")
    sym_res = score_subset(sample_rows, mode="symmetric")
    assert raw_res["arms"]["focal_fastweight"]["correct"] == 0
    assert sym_res["arms"]["focal_fastweight"]["correct"] == 1
    assert sym_res["paired_tests"]["focal_vs_base"]["focal_wins"] == 1
    assert sample_rows[1]["correct"] is False  # original row unmodified


class QuerySwiGLUFastWeightTests(unittest.TestCase):
    def test_populations(self):
        test_task_populations_and_seed_disjointness()

    def test_invariants(self):
        test_zero_query_answer_leakage_and_control_invariants()

    def test_safe_norm(self):
        test_safe_norm_matches_ieee_on_noncontiguous_views()

    def test_symmetric_scorer(self):
        test_symmetric_scorer_punctuation_and_equivalent_forms()


if __name__ == "__main__":
    unittest.main()
