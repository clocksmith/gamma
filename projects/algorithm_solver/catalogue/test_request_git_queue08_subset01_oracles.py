"""Source-free independent controls for queue 08 subset 01; no candidates."""
from bisect import bisect_left
from collections import Counter
from copy import deepcopy
from itertools import product
import json
import string
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_git_queue08_subset01_oracles as o

EXAMPLES = {
    2981: [(['aaaa'], 2), (['abcdef'], -1), (['abcaba'], 1)],
    2998: [([26, 1], 3), ([54, 2], 4), ([25, 30], 5)],
    3002: [([[1, 2, 1, 2], [1, 1, 1, 1]], 2),
           ([[1, 2, 3, 4, 5, 6], [2, 3, 2, 3, 2, 3]], 5),
           ([[1, 1, 2, 2, 3, 3], [4, 4, 5, 5, 6, 6]], 6)],
    3006: [(['isawsquirrelnearmysquirrelhouseohmy', 'my', 'squirrel', 15], [16, 33]),
           (['abcd', 'a', 'a', 4], [0])],
    3012: [([[1, 4, 3, 1]], 1), ([[5, 5, 5, 10, 5]], 2), ([[2, 3, 4]], 1)],
    3016: [(['abcde'], 5), (['xyzxyzxyzxyz'], 12), (['aabbccddeeffgghhiiiiii'], 24)],
}


def fixture(pid):
    body = f'{pid}. {o.TITLES[pid]}\n' + ''.join(
        'Input: '+', '.join(f'{key} = {json.dumps(value)}' for key, value in zip(o.PARAMETERS[pid], args))+
        '\nOutput: '+json.dumps(want)+'\nExplanation: Synthetic transcription.\n' for args, want in EXAMPLES[pid])
    return q.encoded({'problem_id': pid, 'web_result': body})


def run_lengths(s):
    runs = {c: [] for c in set(s)}
    start = 0
    for end in range(1, len(s)+1):
        if end == len(s) or s[end] != s[start]:
            runs[s[start]].append(end-start); start = end
    return max((length for values in runs.values() for length in range(1, len(s)+1)
                if sum(max(0, n-length+1) for n in values) >= 3), default=-1)


def assigned_distinct(a, b):
    # Allocate each distinct value to neither input, left, or right, subject
    # to membership and half-size capacities. Retained duplicate fillers do
    # not reduce distinct count and always complete a selected valid set.
    values = sorted(set(a+b)); best = 0; half = len(a)//2
    for owners in product((0, 1, 2), repeat=len(values)):
        if owners.count(1) > half or owners.count(2) > half:
            continue
        if all(owner == 0 or value in (a if owner == 1 else b) for value, owner in zip(values, owners)):
            best = max(best, sum(owner != 0 for owner in owners))
    return best


class Queue08Subset01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {pid: fixture(pid) for pid in o.IDS}
        with patch.dict(o.STATEMENT_SHA256, {pid: q.sha(raw) for pid, raw in cls.raw.items()}):
            cls.built = {pid: o.build_cases(pid, cls.raw[pid]) for pid in o.IDS}

    def test_public_examples_and_effects(self):
        for pid, rows in EXAMPLES.items():
            for args, want in rows:
                before = deepcopy(args)
                self.assertTrue(q.exact(o.expected(pid, args), want)); self.assertEqual(args, before)

    def test_strict_identity_shape_and_domain(self):
        invalid = {2981: [['aa'], ['a'*51], ['aéa'], [1], ['AAA']],
                   2998: [[0, 1], [1, 10001], [True, 1], [1, 1.0], ['1', 1]],
                   3002: [[[], []], [[1], [1]], [[1, 2], [1]], [[0, 1], [1, 2]], [[True, 2], [1, 2]], [[1, 10**9+1], [1, 2]]],
                   3006: [['', 'a', 'a', 1], ['a', '', 'b', 1], ['a', 'a'*11, 'b', 1], ['ab', 'a', 'b', 0], ['ab', 'a', 'b', 3], ['ab', 'a', 'b', True]],
                   3012: [[[]], [[0]], [[-1]], [[1.0]], [[True]], [[10**9+1]], [[1]*100001]],
                   3016: [[''], ['a'*100001], ['A'], ['é'], [None]]}
        for pid, rows in invalid.items():
            for args in rows:
                with self.subTest(pid=pid, args=str(args)[:60]), self.assertRaises(ValueError):
                    o.validate(pid, args)
        for pid, args in [(True, []), (2981.0, ['aaa']), (2979, []), (3006, ['a']), (2981, ('aaa',))]:
            with self.assertRaises(ValueError): o.validate(pid, args)
        o.validate(3006, ['a', 'abcdefghij', 'b', 1])
        o.validate(3012, [[10**9]*100000])
        o.validate(3002, [[10**9]*20000, [1]*20000])
        o.validate(3006, ['a'*100000, 'a'*10, 'a'*10, 100000])

    def test_special_independent_run_occurrences(self):
        for case in self.built[2981][0]:
            self.assertEqual(case['expected'], run_lengths(case['args'][0]))

    def test_operations_independent_floyd_warshall(self):
        # Larger interval than every author BFS bound for x,y <= 35.
        n = 100; d = [[1000]*(n+1) for _ in range(n+1)]
        for x in range(1, n+1):
            d[x][x] = 0
            for y in (x-1, x+1, x//5 if x % 5 == 0 else 0, x//11 if x % 11 == 0 else 0):
                if 1 <= y <= n: d[x][y] = min(d[x][y], 1)
        for mid in range(1, n+1):
            for x in range(1, n+1):
                for y in range(1, n+1): d[x][y] = min(d[x][y], d[x][mid]+d[mid][y])
        for x in range(1, 36):
            for y in range(1, 36): self.assertEqual(o.expected(2998, [x, y]), d[x][y])
        self.assertEqual(o.expected(2998, [10, 1]), 2)
        self.assertEqual(o.expected(2998, [1, 10000]), 9999)

    def test_distinct_capacity_assignments_and_large_upper_bounds(self):
        for case in self.built[3002][0]:
            a, b = case['args']; half = len(a)//2
            bound = min(len(set(a+b)), min(half, len(set(a)))+min(half, len(set(b))))
            self.assertEqual(case['expected'], bound)
            if len(set(a+b)) <= 5: self.assertEqual(case['expected'], assigned_distinct(a, b))

    def test_beautiful_independent_character_matches_and_bisect(self):
        for case in self.built[3006][0]:
            s, a, b, k = case['args']
            hits = lambda part: [i for i in range(len(s)-len(part)+1)
                                 if all(s[i+j] == c for j, c in enumerate(part))]
            right = hits(b); want = []
            for i in hits(a):
                j = bisect_left(right, i-k)
                if j < len(right) and right[j] <= i+k: want.append(i)
            self.assertEqual(case['expected'], want)
        self.assertEqual(o.expected(3006, ['ababa', 'aba', 'ba', 1]), [0, 2])

    def test_remainder_reachability_independent_minimum_characterization(self):
        # If every value is divisible by minimum m, copies of m can only be
        # removed in pairs (one permanent zero per pair). Other multiples
        # can be consumed without reducing count(m). Otherwise v % m creates
        # a unique positive value below m, which consumes all others.
        for case in self.built[3012][0]:
            a = case['args'][0]; minimum = min(a)
            want = 1 if any(x % minimum for x in a) else (a.count(minimum)+1)//2
            self.assertEqual(case['expected'], want)
        self.assertEqual(o._remainders((0, 0, 2, 4)), 3)

    def test_key_assignment_independent_exchange_order(self):
        for case in self.built[3016][0]:
            frequencies = sorted(Counter(case['args'][0]).values(), reverse=True)
            want = sum(count*(i//8+1) for i, count in enumerate(frequencies))
            self.assertEqual(case['expected'], want)
        for letters in range(1, 5):
            frequencies = tuple(range(1, letters+1))
            minimum = min(sum(x*(tier+1) for x, tier in zip(frequencies, tiers))
                          for tiers in product(range(4), repeat=letters))
            self.assertEqual(o._key_assignment(frequencies), minimum)

    def test_reference_limits_not_domain_restrictions(self):
        for pid, args in [(3002, [[1]*10, [1]*10]), (3006, ['a'*129, 'a', 'a', 1]), (3012, [[1]*8])]:
            o.validate(pid, args)
            with self.assertRaises(ValueError): o.expected(pid, args)

    def test_frozen_counts_bytes_categories_and_budgets(self):
        for pid, (cases, categories) in self.built.items():
            self.assertEqual(len(cases), o.CASE_COUNT[pid]); self.assertEqual(len(categories), len(cases))
            self.assertEqual(q.sha(q.encoded(cases)), o.CASES_SHA256[pid])
            self.assertEqual(len({q.encoded(c['args']) for c in cases}), len(cases))
            self.assertTrue(any('exhaustive' in c for c in categories))
            self.assertLessEqual(len(q.encoded(cases)), q.MAX_FILE)
            for _, batch in q.batches(cases):
                self.assertLessEqual(len(batch), 32); self.assertLessEqual(len(q.encoded(q.packet(batch))), q.MAX_PACKET)
                self.assertNotIn('expected', q.packet(batch)['calls'][0])
                for language in ('javascript', 'python'):
                    self.assertLessEqual(o.expected_observation_bytes(batch, language), q.LIMITS['max_output_bytes'])
        too_large = [{'args': [[10**9]*100000], 'expected': 50000, 'compare': 'return'}]
        with self.assertRaises(ValueError): list(q.batches(too_large))

    def test_statement_and_case_tamper_fail_closed(self):
        for pid in o.IDS:
            with self.assertRaises(ValueError): o.public_examples(pid, self.raw[pid])
            with patch.dict(o.STATEMENT_SHA256, {pid: q.sha(self.raw[pid])}):
                with self.assertRaises(ValueError): o.public_examples(pid, self.raw[pid]+b' ')
                with self.assertRaises(ValueError): o.public_examples(pid, self.raw[pid].decode())
                with patch.dict(o.CASE_COUNT, {pid: -1}):
                    with self.assertRaises(ValueError): o.build_cases(pid, self.raw[pid])
        wrong = q.encoded({'problem_id': 2981, 'web_result': '2981. Wrong title'})
        with patch.dict(o.STATEMENT_SHA256, {2981: q.sha(wrong)}):
            with self.assertRaises(ValueError): o.public_examples(2981, wrong)

    def test_exact_value_type_mutation_alias_comparison_unchanged(self):
        case = {'args': [[1, 2]], 'expected': [3], 'compare': 'return'}
        record = {'result': [3], 'result_type': 'list', 'args_before': [[1, 2]], 'args_after': [[1, 2]], 'alias_edges': []}
        self.assertIsNone(q.compare(case, record, 'python'))
        for delta, reason in [({'result': [3.0]}, 'result_value'), ({'result': [True]}, 'result_value'),
                              ({'args_after': [[2, 1]]}, 'input_effects'), ({'alias_edges': [[0, 0]]}, 'return_aliases')]:
            self.assertEqual(q.compare(case, dict(record, **delta), 'python'), reason)


if __name__ == '__main__': unittest.main()
