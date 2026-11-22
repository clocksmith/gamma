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


if __name__ == "__main__":
    unittest.main()
