"""Unit tests for the disjoint-position impossibility bound, analytic step-potential
Lagrangian dual embedding, overlapping non-tiling counterexample, and witness verifier."""

from __future__ import annotations

from collections import defaultdict
import itertools
import unittest

import replay_verify_receipt as replay
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


def all_occurrences_dual_by_definition(texts: dict[str, str], k: int, positions: list[tuple[str, int]]) -> int:
    """The Experiment A dual at the scale = 1 step potential, straight from its definition: every eligible
    token, every occurrence, no shortcuts. Only for tiny corpora."""
    whole = set(texts.values())
    doc_freq: dict[str, set[str]] = defaultdict(set)
    for pid, s in texts.items():
        for a in range(len(s)):
            for b in range(a + 1, len(s) + 1):
                doc_freq[s[a:b]].add(pid)

    def eligible(token: str) -> bool:
        if token in whole:
            return False
        return k == 1 or len(token) == 1 or len(doc_freq[token]) >= k

    pots = {pid: [sum(1 for q, pos in positions if q == pid and pos >= j) for j in range(len(s) + 1)] for pid, s in texts.items()}
    rebates: dict[str, int] = defaultdict(int)
    for pid, s in texts.items():
        for a in range(len(s)):
            for b in range(a + 1, len(s) + 1):
                if eligible(s[a:b]):
                    rebates[s[a:b]] += max(0, pots[pid][a] - pots[pid][b])
    return sum(p[0] - p[-1] for p in pots.values()) + sum(min(0, 1 - rebate) for rebate in rebates.values())


class ImpossibilityBoundTests(unittest.TestCase):
    def test_self_overlap_under_u_keeps_the_bound_and_breaks_the_dual_equality(self):
        # "aa" starts at 0 and at 1, and both occurrences span position 1.
        texts = {"1": "aaa"}
        res = verify_impossibility_witness(texts, 1, [], [("1", 1)])
        self.assertEqual(res["disjoint_bound"], 1)
        self.assertLessEqual(res["disjoint_bound"], brute_force_opt_a(texts, 1))
        self.assertEqual(all_occurrences_dual_by_definition(texts, 1, [("1", 1)]), 0)
        self.assertEqual(res["step_potential_dual"], 0)
        self.assertEqual(res["tokens_counted_twice"], 1)
        self.assertFalse(res["dual_equals_disjoint_bound"])
        # At position 0 only one occurrence of "aa" spans the cut, and the equality holds.
        ok = verify_impossibility_witness(texts, 1, [], [("1", 0)])
        self.assertEqual(all_occurrences_dual_by_definition(texts, 1, [("1", 0)]), 1)
        self.assertEqual((ok["disjoint_bound"], ok["step_potential_dual"], ok["tokens_counted_twice"]), (1, 1, 0))
        self.assertTrue(ok["dual_equals_disjoint_bound"])

    def test_self_overlap_under_w2_keeps_the_bound_and_breaks_the_dual_equality(self):
        # "aa" occurs in both programs, so it is eligible at threshold 2, and it spans position 1 of "aaa" twice.
        texts = {"1": "aaa", "2": "aab"}
        res = verify_impossibility_witness(texts, 2, [("2", 2)], [("1", 1)])
        self.assertEqual(res["disjoint_bound"], 2)
        self.assertEqual(brute_force_opt_a(texts, 2), 2)
        self.assertEqual(all_occurrences_dual_by_definition(texts, 2, [("2", 2), ("1", 1)]), 1)
        self.assertEqual(res["step_potential_dual"], 1)
        self.assertEqual(res["tokens_counted_twice"], 1)
        self.assertFalse(res["dual_equals_disjoint_bound"])
        ok = verify_impossibility_witness(texts, 2, [("2", 2)], [("1", 0)])
        self.assertEqual(all_occurrences_dual_by_definition(texts, 2, [("2", 2), ("1", 0)]), 2)
        self.assertEqual((ok["disjoint_bound"], ok["step_potential_dual"], ok["tokens_counted_twice"]), (2, 2, 0))

    def test_replay_verifier_counts_every_occurrence(self):
        # The replay verifier's own dual evaluation and charge count, against the definition.
        cases = [
            ({"1": "aaa"}, 1, [("1", 1)]),
            ({"1": "aaa"}, 1, [("1", 0)]),
            ({"1": "aaa", "2": "aab"}, 2, [("2", 2), ("1", 1)]),
            ({"1": "aaa", "2": "aab"}, 2, [("2", 2), ("1", 0)]),
            ({"1": "abababx", "2": "cdcdcdy"}, 1, [("1", 3), ("2", 2)]),
            ({"1": "abcabcabc", "2": "abcabd"}, 2, [("2", 5)]),
        ]
        for texts, k, positions in cases:
            whole, alpha, doc_freq, occs, wit = replay.build_shared_index(texts, max_bytes=160)
            pots = replay.step_potentials(texts, positions)
            expected = all_occurrences_dual_by_definition(texts, k, positions)
            self.assertEqual(replay.eval_dual_bound_k(texts, k, 1, pots, whole, alpha, doc_freq, occs, wit=wit), expected, (texts, k, positions))
            charged = replay.witness_charges(texts, k, positions, whole, alpha, doc_freq, occs, wit)
            self.assertEqual(len(positions) - sum(len(where) - 1 for where in charged.values()), expected, (texts, k, positions))

    def test_replay_verifier_rejects_a_witness_whose_cover_sets_share_a_token(self):
        texts = {"1": "abx", "2": "aby"}
        whole, alpha, doc_freq, occs, wit = replay.build_shared_index(texts, max_bytes=160)
        with self.assertRaises(ValueError):
            replay.replay_witness(texts, 2, [("1", 0), ("2", 1)], whole, alpha, doc_freq, occs, wit, "toy")

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
