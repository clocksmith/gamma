"""Unit tests for the disjoint-position impossibility bound, analytic step-potential
Lagrangian dual embedding, overlapping non-tiling counterexample, and witness verifier."""

from __future__ import annotations

from collections import defaultdict
import itertools
import unittest

from impossibility_bound import (
    compute_disjoint_bound_k,
    compute_disjoint_bound_u,
    overlapping_non_tiling_counterexample,
    shared_substrings,
    solve_dual_and_milp_k,
    verify_impossibility_witness,
)


def can_tile(source: str, vocab: set[str]) -> bool:
    reach = [False] * (len(source) + 1)
    reach[0] = True
    for i in range(len(source)):
        if reach[i]:
            for tok in vocab:
                if source.startswith(tok, i):
                    reach[i + len(tok)] = True
    return reach[len(source)]


def brute_force_opt_a(texts: dict[str, str], k: int) -> int:
    whole = set(texts.values())
    alpha = set().union(*map(set, whole)) - whole
    if k == 1:
        elig = sorted({s[a:b] for s in texts.values() for a in range(len(s)) for b in range(a + 1, len(s) + 1) if s[a:b] not in whole})
    else:
        _, _, doc_freq, _, _ = shared_substrings(texts, max_bytes=160)
        elig = sorted(alpha | {s for s, df in doc_freq.items() if df >= k})
    for size in range(1, len(alpha) + 1):
        for comb in itertools.combinations(elig, size):
            vset = set(comb)
            if all(can_tile(s, vset) for s in texts.values()):
                return size
    return len(alpha)


class ImpossibilityBoundTests(unittest.TestCase):
    def test_overlapping_non_tiling_counterexample(self):
        ce = overlapping_non_tiling_counterexample()
        self.assertEqual(ce["every_position_covered_by_4_tokens"], True)
        self.assertLessEqual(ce["disjoint_bound"], 4)
        self.assertEqual(ce["hitting_set_upper_bound"], 4)
        self.assertEqual(ce["certified_lagrangian_dual"], 5)
        self.assertEqual(ce["exact_tiling_opt"], 5)
        self.assertEqual(brute_force_opt_a(ce["texts"], 2), 5)

    def test_step_potential_matches_standard_dual_formula(self):
        texts = {"1": "x+y=1", "2": "x-z=2", "3": "w*y=3"}
        whole, alpha, doc_freq, occs, _ = shared_substrings(texts, max_bytes=160)
        f_pos, e_pos, disj_b = compute_disjoint_bound_k(texts, 2, whole, alpha, doc_freq, occs)
        res = verify_impossibility_witness(texts, 2, f_pos, e_pos, doc_freq=doc_freq)
        self.assertEqual(res["disjoint_bound"], disj_b)
        self.assertEqual(res["step_potential_dual"], disj_b)

        # Recompute standard A dual numerator with scale = 1 over ALL eligible tokens:
        by_pid = defaultdict(list)
        for pid, pos in f_pos + e_pos:
            by_pid[pid].append(pos)
        pots = {pid: [sum(1 for wp in by_pid[pid] if wp >= j) for j in range(len(s) + 1)] for pid, s in texts.items()}
        numer = sum(pots[pid][0] - pots[pid][-1] for pid in texts)
        rebates = defaultdict(int)
        for pid, s in texts.items():
            p = pots[pid]
            for i, ch in enumerate(s):
                if ch in alpha and p[i] > p[i + 1]:
                    rebates[ch] += p[i] - p[i + 1]
        for pid, a, b, sub in occs:
            if doc_freq[sub] >= 2 and pots[pid][a] > pots[pid][b]:
                rebates[sub] += pots[pid][a] - pots[pid][b]
        numer += sum(min(0, 1 - reb) for reb in rebates.values())
        self.assertEqual(numer, disj_b)

    def test_verifier_rejects_overlapping_and_non_singleton_witnesses(self):
        texts = {"1": "abx", "2": "aby"}
        _, _, doc_freq, _, _ = shared_substrings(texts, max_bytes=160)
        # ('1', 0) has cover set {'a', 'ab'} of size 2 -> must fail as forced singleton
        with self.assertRaises(ValueError):
            verify_impossibility_witness(texts, 2, [("1", 0)], [], doc_freq=doc_freq)
        # ('1', 0) and ('2', 1) both contain shared substring 'ab' -> must fail disjointness!
        with self.assertRaises(ValueError):
            verify_impossibility_witness(texts, 2, [("1", 2), ("2", 2)], [("1", 0), ("2", 1)], doc_freq=doc_freq)

    def test_soundness_against_brute_force_tiny_cohorts(self):
        cohorts = [
            {"1": "abca", "2": "bcab", "3": "cabc"},
            {"1": "fn(a)", "2": "fn(b)", "3": "gn(a)", "4": "hz"},
        ]
        for texts in cohorts:
            whole, alpha, doc_freq, occs, wit = shared_substrings(texts, max_bytes=160)
            _, _, disj_u = compute_disjoint_bound_u(texts, wit=wit)
            opt_u = brute_force_opt_a(texts, 1)
            self.assertLessEqual(disj_u, opt_u)
            for k in (2, 3):
                f_pos, _, disj_k = compute_disjoint_bound_k(texts, k, whole, alpha, doc_freq, occs)
                _lp, cert_k, _pots, _vocab = solve_dual_and_milp_k(texts, k, whole, alpha, doc_freq, occs, run_milp=False)
                opt_k = brute_force_opt_a(texts, k)
                self.assertLessEqual(len(f_pos), disj_k)
                self.assertLessEqual(disj_k, cert_k)
                self.assertLessEqual(cert_k, opt_k)


if __name__ == "__main__":
    unittest.main()
