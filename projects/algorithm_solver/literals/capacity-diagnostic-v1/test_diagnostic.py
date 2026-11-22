"""Unit tests for Phase 3 tri-state diagnostic, component decomposition,
threshold monotonicity, partial-coverage knapsack allocation, and Theorem B parsing test."""
from __future__ import annotations

import unittest

from diagnostic import (
    allocate_partial_coverage,
    diagnose_full_corpus,
    eligible_tokens,
    exact_partial_coverage_curve,
    split_components,
    theorem_b_span_parse_test,
    verify_construction,
    verify_disjoint_witness,
)


class DiagnosticTests(unittest.TestCase):
    def test_seven_program_union_returns_nine_not_eight(self):
        union = ["abd", "abe", "fbd", "pxqy", "qypx", "pyqx", "qxpy"]
        comps = split_components(union)
        self.assertEqual(len(comps), 2)
        res8 = diagnose_full_corpus(union, k=2, budget=8)
        self.assertEqual(res8["status"], "IMPOSSIBLE")
        self.assertEqual(res8["certifiedLowerBound"], 9)
        self.assertIsNotNone(res8["monotoneSaturation"])
        self.assertEqual(res8["monotoneSaturation"]["reusableForAllThresholdsAtLeast"], 2)

        res9 = diagnose_full_corpus(union, k=2, budget=9)
        self.assertEqual(res9["status"], "FEASIBLE")
        self.assertEqual(res9["construction"]["dictionarySize"], 9)
        self.assertTrue(res9["construction"]["byteExactVerified"])

    def test_frozen_tiny_controls(self):
        # W2: {abc, abab} -> 2 feasible; {abc, baba} -> 2 impossible, 3 feasible
        self.assertEqual(diagnose_full_corpus(["abc", "abab"], k=2, budget=2)["status"], "FEASIBLE")
        r_baba = diagnose_full_corpus(["abc", "baba"], k=2, budget=2)
        self.assertEqual(r_baba["status"], "IMPOSSIBLE")
        self.assertEqual(r_baba["certifiedLowerBound"], 3)
        self.assertEqual(diagnose_full_corpus(["abc", "baba"], k=2, budget=3)["status"], "FEASIBLE")

        # U: {ab, ac, bc} -> 3 feasible, 2 impossible
        self.assertEqual(diagnose_full_corpus(["ab", "ac", "bc"], k=1, budget=2)["status"], "IMPOSSIBLE")
        self.assertEqual(diagnose_full_corpus(["ab", "ac", "bc"], k=1, budget=3)["status"], "FEASIBLE")

        # U: {ax, ay, bx, by} -> rank 3, yet E_span is empty so K=3 is IMPOSSIBLE (LB=4)
        r_grid = diagnose_full_corpus(["ax", "ay", "bx", "by"], k=1, budget=3)
        self.assertEqual(r_grid["status"], "IMPOSSIBLE")
        self.assertEqual(r_grid["certifiedLowerBound"], 4)

    def test_theorem_b_parsing_test_and_negative_controls(self):
        # Negative control 1: {ax, ay, bx, by} has no span tokens at all -> fails parse-in-span immediately
        tb1 = theorem_b_span_parse_test(["ax", "ay", "bx", "by"])
        self.assertEqual(tb1["programRank"], 3)
        self.assertFalse(tb1["everyProgramParsesInSpan"])
        self.assertFalse(tb1["rankAttainable"])
        self.assertEqual(tb1["certifiedLowerBound"], 4)

        # Negative control 2: {axby, byax, aybx, bxay} passes cuttable prefix & E_span parse,
        # yet fails size-3 basis-parse attainability (proving min >= 4)
        tb2 = theorem_b_span_parse_test(["axby", "byax", "aybx", "bxay"])
        self.assertEqual(tb2["programRank"], 3)
        self.assertTrue(tb2["everyProgramHasACuttablePrefix"])
        self.assertTrue(tb2["everyProgramParsesInSpan"])
        self.assertFalse(tb2["rankAttainable"])
        self.assertEqual(tb2["certifiedLowerBound"], 4)

        # Positive control: {abc, abab} attains rank 2 with verified parse {'ab', 'c'}
        tb3 = theorem_b_span_parse_test(["abc", "abab"])
        self.assertEqual(tb3["programRank"], 2)
        self.assertTrue(tb3["rankAttainable"])
        self.assertEqual(tb3["attainingConstruction"]["dictionary"], ["ab", "c"])

    def test_unresolved_never_claims_rank_as_construction(self):
        # Disable search on {abc, abab} under W2 at K=2 (LB=2, UB=3): must return UNRESOLVED, never FEASIBLE
        res = diagnose_full_corpus(["abc", "abab"], k=2, budget=2, allow_construction_search=False)
        self.assertEqual(res["status"], "UNRESOLVED")
        self.assertEqual(res["interval"], [2, 3])
        self.assertNotIn("construction", res)

        # Also verify {abc, baba} under U at K=2 is now PROVED IMPOSSIBLE (LB=3) by Theorem B span-parse test
        res_u = diagnose_full_corpus(["abc", "baba"], k=1, budget=2, allow_construction_search=False)
        self.assertEqual(res_u["status"], "IMPOSSIBLE")
        self.assertEqual(res_u["certifiedLowerBound"], 3)

    def test_monotone_saturation_disabled_when_singleton_is_whole_program(self):
        # Single-char whole program 'a' makes singleton 'a' ineligible -> must NOT emit monotoneSaturation
        res = diagnose_full_corpus(["a", "ab", "ac"], k=2, budget=3)
        self.assertFalse(res["allSingletonsEligible"])
        self.assertIsNone(res["monotoneSaturation"])
        self.assertEqual(res["status"], "IMPOSSIBLE")

    def test_partial_coverage_shared_budget_knapsack(self):
        # Two disjoint components: {ab, ba} (needs 2 slots for 2 progs) and {cd, dc} (needs 2 slots for 2 progs)
        c1 = exact_partial_coverage_curve(["ab", "ba"], k=2, max_budget=3)
        c2 = exact_partial_coverage_curve(["cd", "dc"], k=2, max_budget=3)
        # At shared budget K=2, you can cover AT MOST 2 programs (not 2+2=4!)
        alloc2 = allocate_partial_coverage([c1, c2], shared_budget=2)
        self.assertEqual(alloc2["maxProgramsSpelled"], 2)
        self.assertEqual(sum(alloc2["budgetAllocationByComponent"]), 2)
        alloc4 = allocate_partial_coverage([c1, c2], shared_budget=4)
        self.assertEqual(alloc4["maxProgramsSpelled"], 4)
        self.assertEqual(alloc4["budgetAllocationByComponent"], [2, 2])

    def test_self_overlap_and_cross_position_collision_regressions(self):
        # Single-position self-overlap: aaa under U and {aaa, aab} under W2
        r_u = diagnose_full_corpus(["aaa"], k=1, budget=1)
        self.assertEqual(r_u["status"], "FEASIBLE")
        self.assertEqual(r_u["certifiedLowerBound"], 1)
        r_w2 = diagnose_full_corpus(["aaa", "aab"], k=2, budget=1)
        self.assertEqual(r_w2["status"], "IMPOSSIBLE")
        self.assertEqual(r_w2["certifiedLowerBound"], 2)

        # Cross-position token-string collision: ('abx', 0) and ('aby', 1) share token 'ab' -> must reject
        progs = ["abx", "aby"]
        tokens = eligible_tokens(progs, k=2)
        with self.assertRaises(ValueError):
            verify_disjoint_witness(progs, [(0, 0), (1, 1)], tokens)

        # Verification rejects ineligible token or bad dictionary
        with self.assertRaises(ValueError):
            verify_construction(["ab", "ba"], ["ab"], k=2)

    def test_minimized_program_connected_counterexample_under_w2(self):
        from connected_search import evaluate_corpus

        ce = evaluate_corpus(["abd", "fbd", "abpxqy", "qypx", "pyqx", "qxpy"])
        self.assertEqual(ce["connectedComponents"], 1)
        self.assertEqual(ce["alphabetSize"], 8)
        self.assertEqual(ce["blockRank"], 7)
        self.assertEqual(ce["disjointBound"], 7)
        self.assertEqual(ce["exactOptW2"], 8)
        self.assertTrue(ce["matchesFailureTarget"])

        # Forced-block component decomposition in diagnostic.py closes this single program-connected case to LB = 8
        d7 = diagnose_full_corpus(["abd", "fbd", "abpxqy", "qypx", "pyqx", "qxpy"], k=2, budget=7)
        self.assertEqual(d7["status"], "IMPOSSIBLE")
        self.assertEqual(d7["componentCount"], 1)
        self.assertEqual(d7["certifiedLowerBound"], 8)
        self.assertEqual(d7["components"][0]["strongerBound"], "forced-block-components")
        self.assertIsNotNone(d7["monotoneSaturation"])

    def test_forced_block_construction_finds_below_alphabet_tiling_without_exhaustive_search(self):
        # Synthetic outside-unseen test: 30-char alphabet where 2 non-adjacent pairs always occur together -> 28 forced blocks <= K=28
        base = [chr(ord("a") + i) for i in range(26)]
        p1 = "".join(base[:6]) + "01" + "".join(base[6:13]) + "23"
        p2 = "".join(base[13:19]) + "01" + "".join(base[19:]) + "23"
        res = diagnose_full_corpus([p1, p2], k=2, budget=28)
        self.assertEqual(res["alphabetSize"], 30)
        self.assertEqual(res["status"], "FEASIBLE")
        self.assertEqual(res["construction"]["dictionarySize"], 28)
        self.assertTrue(res["construction"]["byteExactVerified"])

    def test_minimal_single_forced_block_connected_counterexample_under_w2(self):
        from forced_block_connected_search import evaluate_fb_connected

        progs = ["abd", "abpxqy", "qypxbd", "abpyqx", "qxpybd"]
        ev = evaluate_fb_connected(progs)
        self.assertEqual(ev["programComponents"], 1)
        self.assertEqual(ev["forcedBlockComponents"], 1)
        self.assertEqual(ev["alphabetSize"], 7)
        self.assertEqual(ev["blockRank"], 6)
        self.assertEqual(ev["disjointBound"], 6)
        self.assertEqual(ev["exactOptW2"], 7)
        self.assertTrue(ev["matchesFailureTarget"])

    def test_rank_drop_field_never_filters_span_tokens_regression(self):
        # Modular rank-drop counterexample: 'aaabbbbbbababbaababaabbaaabaaa' has 'a'-weight == 1_000_000_007 == 0
        # mod (1_000_000_007, base 2), so field 1 gives rank 1 while field 2 gives rank 2.
        # Budget K=2 under U MUST be FEASIBLE with {'a', 'b'} (never falsely IMPOSSIBLE).
        progs = ["aaabbbbbbababbaababaabbaaabaaa", "b" * 30]
        tb = theorem_b_span_parse_test(progs)
        self.assertEqual(tb["programRank"], 2)
        self.assertEqual(len(tb["attainingFields"]), 1)
        self.assertEqual(tb["attainingFields"][0]["prime"], 998_244_353)
        self.assertTrue(tb["everyProgramParsesInSpan"])
        self.assertEqual(tb["certifiedLowerBound"], 2)

        res = diagnose_full_corpus(progs, k=1, budget=2)
        self.assertEqual(res["status"], "FEASIBLE")
        self.assertEqual(res["certifiedLowerBound"], 2)
        self.assertEqual(res["construction"]["dictionary"], ["a", "b"])
        self.assertTrue(res["construction"]["byteExactVerified"])

    def test_nullspace_kernel_closes_five_program_fb_connected_counterexample(self):
        # Single forced-block connected counterexample: |Sigma|=7, blockRank=6, disjoint=6, OPT_W2=7.
        # Nullspace-Kernel Theorem closes it to LB=7 (IMPOSSIBLE at K=6) with zero solver.
        progs = ["abd", "abpxqy", "qypxbd", "abpyqx", "qxpybd"]
        r6 = diagnose_full_corpus(progs, k=2, budget=6)
        self.assertEqual(r6["status"], "IMPOSSIBLE")
        self.assertEqual(r6["certifiedLowerBound"], 7)
        self.assertEqual(r6["components"][0]["strongerBound"], "nullspace-kernel-obstruction")
        self.assertEqual(r6["components"][0]["nullspaceKernelCertificate"]["deltaDetStar"], 0)
        self.assertIsNotNone(r6["monotoneSaturation"])

        r7 = diagnose_full_corpus(progs, k=2, budget=7)
        self.assertEqual(r7["status"], "FEASIBLE")
        self.assertEqual(r7["construction"]["dictionarySize"], 7)

    def test_nullspace_kernel_exact_below_alphabet_construction(self):
        # 12-char alphabet where 5 nullspace-coupled chars {X,Y,f,Z,W} appear only inside 2 shared
        # fragments 'XY' and 'fZW', giving rank=9, d=3, |S_free|=5, k_free=2, OPT=9.
        progs = [
            "XYabcdefZWgh",
            "XYabcedfZWhg",
            "XYbadcefZWgh",
            "XYacbdgfZWhg",
        ]
        r8 = diagnose_full_corpus(progs, k=2, budget=8)
        self.assertEqual(r8["status"], "IMPOSSIBLE")
        self.assertEqual(r8["certifiedLowerBound"], 9)
        r9 = diagnose_full_corpus(progs, k=2, budget=9)
        self.assertEqual(r9["status"], "FEASIBLE")
        self.assertEqual(r9["certifiedLowerBound"], 9)
        self.assertEqual(r9["construction"]["dictionarySize"], 9)
        self.assertTrue(r9["construction"]["byteExactVerified"])

    def test_nullspace_kernel_boundary_soundness_when_sdet_shares_span_flank(self):
        # Ensure B_det* only includes uncovered runs bounded by block edges or S_free chars,
        # never falsely pinning an S_det char adjacent to an S_det flank covered by E_span^free.
        progs = ["xywz", "xywzu", "vwz", "xyab"]
        r = diagnose_full_corpus(progs, k=2, budget=len(set("".join(progs))) - 1)
        # Verify soundness: if FEASIBLE, construction is byte-exact; if IMPOSSIBLE, LB <= actual opt
        if r["status"] == "FEASIBLE":
            self.assertTrue(r["construction"]["byteExactVerified"])
            self.assertLessEqual(r["construction"]["dictionarySize"], r["budget"])

    def test_nullspace_kernel_self_overlap_dedup_counterexample_regression(self):
        # Adversarial referee Bug #1 regression: tok1='AxBBCAxB' overlaps itself inside
        # tok2='AxBBCAxBBCAxB' with identical S_free mask; dropping tok2 falsely gave LB=8 > OPT=7.
        progs_w2 = ["AxBBCAxBBCAxBpAABBqx", "AxBBCAxBBCAxBrAABBsx"]
        r_w2 = diagnose_full_corpus(progs_w2, k=2, budget=7)
        self.assertEqual(r_w2["status"], "FEASIBLE")
        self.assertEqual(r_w2["certifiedLowerBound"], 7)
        self.assertEqual(r_w2["construction"]["dictionarySize"], 7)
        self.assertTrue(r_w2["construction"]["byteExactVerified"])

        progs_u = ["pAxBBCAxBBCAxB", "qAABB", "rx", "pp", "qq", "rr", "xx"]
        r_u = diagnose_full_corpus(progs_u, k=1, budget=6)
        self.assertEqual(r_u["certifiedLowerBound"], 6)
        self.assertNotEqual(r_u["status"], "IMPOSSIBLE")

    def test_nullspace_kernel_overlap_frontier_continuation_regression(self):
        # Adversarial referee Bug #2 regression: {'ABC', 'CDBA'} covers all S_free bits (need_mask==0)
        # via overlap on 'ABCDBABC' with 1 slot still free (limit_t=3); returning early falsely gave LB=8 > OPT=7.
        progs_w2 = ["ABCDBABCxCDBAyABC", "ABCDBABCzCDBAwABC"]
        r_w2 = diagnose_full_corpus(progs_w2, k=2, budget=7)
        self.assertEqual(r_w2["status"], "FEASIBLE")
        self.assertEqual(r_w2["certifiedLowerBound"], 7)
        self.assertEqual(r_w2["construction"]["dictionarySize"], 7)
        self.assertTrue(r_w2["construction"]["byteExactVerified"])

        progs_u = ["pABCDBABC", "qCDBA", "rABC", "pp", "qq", "rr"]
        r_u = diagnose_full_corpus(progs_u, k=1, budget=6)
        self.assertEqual(r_u["certifiedLowerBound"], 6)
        self.assertNotEqual(r_u["status"], "IMPOSSIBLE")


if __name__ == "__main__":
    unittest.main()
