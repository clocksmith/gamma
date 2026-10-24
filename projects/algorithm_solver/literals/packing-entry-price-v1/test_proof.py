"""Independent tiny dictionaries, complete paths and packing-price oracles.

Only invented supplied inputs. No corpus loader, timing experiment or binding.
"""
import functools
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest

import proof as p


def edges_for(texts, banned):
    return {(pid, i, j): text[i:j] for pid, text in texts.items()
            for i in range(len(text)) for j in range(i + 1, len(text) + 1)
            if text[i:j] not in banned}


def paths(text, words):
    if not text:
        return [()]
    return [(word,) + tail for word in words if text.startswith(word)
            for tail in paths(text[len(word):], words)]


def schedule(text, arcs, weights):
    """Independent backward recursion; skipping is allowed and uncharged."""
    @functools.lru_cache(None)
    def value(i):
        if i == len(text):
            return 0
        return max([value(i + 1)] + [weights[i, j] + value(j)
                                    for start, j in arcs if start == i])
    return value(0)


def explicit_schedules(arcs):
    """Every nonoverlapping subset, including empty; no dynamic program."""
    yield ()
    ordered = sorted(arcs)
    for index, first in enumerate(ordered):
        for tail in explicit_schedules([a for a in ordered[index + 1:] if a[0] >= first[1]]):
            yield (first,) + tail


class ProofTests(unittest.TestCase):
    def check(self, texts, banned, q, prices, B=3, D=1):
        banned = set(banned)
        result = p.certificate(texts, banned, q, prices, B, D)
        edges = edges_for(texts, banned)
        words = sorted(set(edges.values()))
        ids = sorted(texts)
        owners = {w: {pid for (pid, _, _), word in edges.items() if word == w} for w in words}
        weights = {w: sum(q[e] for e, word in edges.items() if word == w) for w in words}
        counts = {w: {pid: sum(source == pid and word == w for (source, _, _), word in edges.items())
                      for pid in ids} for w in words}
        packed = {w: {pid: min(counts[w][pid], len(texts[pid]) // len(w)) for pid in ids} for w in words}
        m = {w: sum(counts[w].values()) for w in words}
        n = {w: sum(packed[w].values()) for w in words}
        self.assertEqual(result['occurrence_counts_per_source'], counts)
        self.assertEqual(result['packing_counts_per_source'], packed)
        self.assertEqual(result['occurrence_counts'], m)
        self.assertEqual(result['packing_counts'], n)
        self.assertTrue(all(1 <= n[w] <= m[w] for w in words))
        shared = [w for w in words if len(owners[w]) > 1]
        forced = [pid for pid in ids if not paths(texts[pid], shared)]
        self.assertEqual(result['forced_owners'], forced)
        self.assertEqual(result['coverage_floor'], len(forced))
        # Per-word packing bound counts all occurrences, including zero-q arcs.
        for word in words:
            for pid in ids:
                occurrences = [(i, j) for (source, i, j), w in edges.items() if source == pid and w == word]
                maximum = schedule(texts[pid], occurrences, {arc: 1 for arc in occurrences})
                self.assertLessEqual(maximum, packed[word][pid])
        caps = {'owner': {}, 'global': {}}
        for pid in ids:
            for mode in caps:
                arcs = [(i, j) for (source, i, j), w in edges.items()
                        if source == pid and (mode == 'global' or owners[w] == {pid})]
                cap = []
                for index, price in enumerate(prices):
                    residual = {(i, j): max(q[pid, i, j] - price // n[edges[pid, i, j]], 0) for i, j in arcs}
                    oracle = schedule(texts[pid], arcs, residual)
                    if len(texts[pid]) <= 5:
                        self.assertEqual(oracle, max(sum(residual[a] for a in selected)
                                                     for selected in explicit_schedules(arcs)))
                    cap.append(oracle)
                    forward = result[mode + '_price_schedules'][pid][index]
                    self.assertEqual(len(forward), len(texts[pid]) + 1)
                    for end in range(len(texts[pid]) + 1):
                        before = [a for a in arcs if a[1] <= end]
                        self.assertEqual(forward[end], schedule(texts[pid][:end], before, residual))
                caps[mode][pid] = cap
                self.assertEqual(result[mode + '_price_caps'][pid], cap)
        prefixes = {}
        for pid in ids:
            A = [0]
            for weight in sorted((weights[w] for w in words if owners[w] == {pid}), reverse=True)[:B]:
                A.append(A[-1] + weight)
            affine = [min(price * t + cap for price, cap in zip(prices, caps['owner'][pid]))
                      for t in range(len(A))]
            prefixes[pid] = [min(a, b) for a, b in zip(A, affine)]
            self.assertEqual(result['owner_affine_envelopes'][pid], affine)
            increments = [b - a for a, b in zip(prefixes[pid], prefixes[pid][1:])]
            self.assertEqual(increments, sorted(increments, reverse=True))
            self.assertTrue(all(x >= 0 for x in increments))
        self.assertEqual(result['owner_priced_prefixes'], prefixes)
        shared_weights = sorted((weights[w] for w in shared), reverse=True)
        for mode, required in [('owner', set()), ('required', set(forced))]:
            allocations = list(itertools.product(*(range(int(pid in required), len(prefixes[pid])) for pid in ids)))
            for row in result[mode + '_rows']:
                k = row['k']
                if k < len(required):
                    self.assertTrue(row['empty_by_required_owners'])
                    self.assertTrue(all(v is None for key, v in row.items() if key not in ('k', 'empty_by_required_owners')))
                    continue
                candidates = [(sum(prefixes[pid][t] for pid, t in zip(ids, allocation))
                               + sum(shared_weights[:B - sum(allocation)]), -sum(allocation))
                              for allocation in allocations if sum(allocation) <= min(k, B)]
                charge, negj = max(candidates)
                self.assertEqual(row['charge'], charge)
                self.assertEqual(row['one_owner_slots'], -negj)
                self.assertEqual(row['shared_slots'], min(B + negj, len(shared)))
                old = result['old63' if mode == 'owner' else 'old68']['rows'][k]
                self.assertLessEqual(charge, old['charge'])
                self.assertEqual(row['charge_reduction_vs63' if mode == 'owner' else 'charge_reduction_vs68'], old['charge'] - charge)
        # Independent complete source paths, including negative multiword arcs.
        L = 0
        for pid in ids:
            alternatives = []
            for selected in paths(texts[pid], words):
                pos = cost = 0
                for word in selected:
                    end = pos + len(word)
                    cost += D * (9 if len(word) == 1 else -1) + q[pid, pos, end]
                    pos = end
                alternatives.append(cost)
            L += min(alternatives)
        self.assertEqual(result['base57']['L'], L)
        for index, row in enumerate(result['global_price_rows']):
            charge = prices[index] * B + sum(caps['global'][pid][index] for pid in ids)
            self.assertEqual(row['entry_charge'], prices[index] * B)
            self.assertEqual(row['residual_cap'], charge - prices[index] * B)
            self.assertEqual(row['charge'], charge)
            self.assertLessEqual(charge, result['old66']['price_rows'][index]['charge'])
            self.assertEqual(row['numerator'], L - charge)
            self.assertEqual(row['integer_lower_bound'], -(-(L - charge) // D))
        winner = min(range(len(prices)), key=lambda i: result['global_price_rows'][i]['charge'])
        self.assertEqual(result['global']['price_index'], winner)
        G = result['global_price_rows'][winner]['charge']
        for row in result['global_rows']:
            self.assertEqual(row['charge'], min(G, result['base57']['rows'][row['k']]['charge']))
            self.assertLessEqual(row['charge'], result['old66']['rows'][row['k']]['charge'])
        for family in ('owner_rows', 'required_rows', 'global_rows'):
            for row in result[family]:
                if row['charge'] is not None:
                    self.assertEqual(row['numerator'], L - row['charge'])
                    self.assertEqual(row['integer_lower_bound'], -(-row['numerator'] // D))
        covered = []
        joint_count = 0
        for size in range(min(B, len(words)) + 1):
            for dictionary in itertools.combinations(words, size):
                alternatives = [paths(texts[pid], dictionary) for pid in ids]
                if not all(alternatives):
                    continue
                k = sum(len(owners[w]) == 1 for w in dictionary)
                covered.append((dictionary, k))
                self.assertGreaterEqual(k, len(forced))
                for selected in itertools.product(*alternatives):
                    uses = dict.fromkeys(words, 0)
                    Q = F = 0
                    joint_count += 1
                    for pid, sequence in zip(ids, selected):
                        pos = 0
                        for word in sequence:
                            end = pos + len(word)
                            uses[word] += 1
                            Q += q[pid, pos, end]
                            F += 9 if len(word) == 1 else -1
                            pos = end
                    self.assertTrue(all(uses[w] <= n[w] for w in words))
                    for family in ('owner_rows', 'required_rows', 'global_rows'):
                        for row in result[family][k:]:
                            self.assertLessEqual(Q, row['charge'])
                            self.assertLessEqual(row['numerator'], D * F)
                            self.assertLessEqual(row['integer_lower_bound'], F)
                    self.assertLessEqual(Q, G)
        return result, covered, joint_count

    def test_strict_owner_overlap_with_covering_dictionary(self):
        texts = {'p': 'aaaaX', 's': 'Xa'}
        banned = set(texts.values())
        q = {edge: 10 if word == 'aa' else 15 if word == 'aX' else 0
             for edge, word in edges_for(texts, banned).items()}
        result, covered, count = self.check(texts, banned, q, [0] + [2 ** r for r in range(14)], B=3)
        self.assertIn((tuple(sorted(('a', 'X', 'aa'))), 1), covered)
        self.assertGreater(count, 0)
        self.assertEqual(result['occurrence_counts']['aa'], 3)
        self.assertEqual(result['packing_counts']['aa'], 2)
        self.assertEqual(result['base57']['L'], 26)
        self.assertEqual(result['old63']['rows'][1]['charge'], 24)
        self.assertEqual(result['owner_rows'][1]['charge'], 20)
        self.assertEqual(result['owner_rows'][1]['integer_lower_bound'], 6)
        self.assertEqual(result['old63']['rows'][1]['integer_lower_bound'], 2)
        self.assertEqual(result['old68']['rows'][1]['charge'], 24)
        self.assertEqual(result['required_rows'][1]['charge'], 20)

    def test_strict_global_joint_sources_and_zero_weight_occurrences(self):
        texts = {'p': 'aaaabaaaab', 's': 'aaaabaaaab'}
        banned = set(texts.values())
        q = {edge: 10 if word == 'aa' else 5 if word == 'b' else 0
             for edge, word in edges_for(texts, banned).items()}
        result, covered, count = self.check(texts, banned, q, [0] + [2 ** r for r in range(14)], B=1)
        self.assertIn((('aaaab',), 0), covered)
        self.assertGreater(count, 0)
        self.assertEqual((result['occurrence_counts']['aa'], result['packing_counts']['aa']), (12, 10))
        self.assertEqual((result['old66']['global']['charge'], result['old66']['global']['lambda']), (92, 16))
        self.assertEqual((result['global']['charge'], result['global']['lambda']), (88, 32))
        self.assertEqual(result['base57']['rows'][0]['charge'], 120)
        self.assertEqual(result['base57']['L'], -8)
        self.assertEqual(result['old66']['global']['integer_lower_bound'], -100)
        self.assertEqual(result['global']['integer_lower_bound'], -96)

    def test_nonoverlap_counts_unchanged_and_conservative_bound_not_exact_packing(self):
        texts = {'p': 'ab', 's': 'ba'}
        banned = set(texts.values())
        q = {edge: i + 1 for i, edge in enumerate(edges_for(texts, banned))}
        result, _, _ = self.check(texts, banned, q, [0, 1, 4], B=4)
        self.assertEqual(result['packing_counts'], result['occurrence_counts'])
        for new, old in [('owner_rows', 'old63'), ('required_rows', 'old68'), ('global_rows', 'old66')]:
            self.assertEqual([r['charge'] for r in result[new]], [r['charge'] for r in result[old]['rows']])
        # n is a conservative length/count bound, not exact interval packing.
        texts = {'p': 'aaab'}
        banned = {'aaab'}
        q = {edge: 0 for edge in edges_for(texts, banned)}
        result, _, _ = self.check(texts, banned, q, [0, 2], B=1)
        self.assertEqual(result['packing_counts']['aa'], 2)
        self.assertEqual(schedule('aaab', [(0, 2), (1, 3)], {(0, 2): 1, (1, 3): 1}), 1)

    def test_zero_ties_finite_slots_banned_singletons_and_capacity(self):
        for texts, banned in (({'p': 'a', 's': 'a'}, set()), ({'p': 'aa', 's': 'bb'}, {'aa', 'bb'}),
                              ({'p': 'ab', 's': 'ba'}, {'a', 'b'})):
            q = {edge: 0 for edge in edges_for(texts, banned)}
            for B in (0, 1, 4):
                result, _, _ = self.check(texts, banned, q, [0, 1, 4], B=B, D=3)
                self.assertEqual(result['global']['price_index'], 0)
                if B < result['coverage_floor']:
                    self.assertTrue(all(row['empty_by_required_owners'] for row in result['required_rows']))
                if B == 0:
                    self.assertTrue(all(row['charge'] == 0 for row in result['global_price_rows']))

    def test_random_joint_paths_and_exact_allocations(self):
        rng = random.Random(7101)
        for _ in range(18):
            texts = {str(i): ''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            banned = set(texts.values())
            q = {edge: rng.randrange(12) for edge in edges_for(texts, banned)}
            self.check(texts, banned, q, [0, 1, 4, 16], B=3, D=3)
        texts = {'p': 'aaaa', 's': 'aaaa'}
        banned = {'aaaa'}
        q = {edge: int(word == 'aa') for edge, word in edges_for(texts, banned).items()}
        result, _, _ = self.check(texts, banned, q, [0, 1, 4, 16], B=1, D=3)
        self.assertTrue(any(row['numerator'] < 0 and row['numerator'] % 3 for row in result['owner_rows']))

    def test_generators_malformed_inputs_and_optimized_python(self):
        texts = {'p': 'aa'}
        banned = {'aa'}
        q = {edge: 0 for edge in edges_for(texts, banned)}
        self.assertEqual(p.certificate(texts, iter(banned), q, [0, 2], 3),
                         p.certificate(texts, banned, q, [0, 2], 3))
        for prices in ([], [1], [0, -1], [0, True], [0, 0], [1, 0]):
            with self.assertRaises(AssertionError):
                p.certificate(texts, banned, q, prices)
        for bad in ({}, {**q, ('p', 0, 2): 0}, {('p', False, 1): 0, ('p', 1, 2): 0},
                    {**q, ('p', 1, 2): True}, {**q, ('p', 1, 2): -1}):
            with self.assertRaises(AssertionError):
                p.certificate(texts, banned, bad, [0])
        for B, D in ((True, 1), (-1, 1), (1, True), (1, 0)):
            with self.assertRaises(AssertionError):
                p.certificate(texts, banned, q, [0], B, D)
        proc = subprocess.run([sys.executable, '-O', '-B', '-c', 'import proof;proof.certificate({},set(),{},[0])'],
                              cwd=Path(__file__).resolve().parent, capture_output=True, timeout=5)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn(b'normal assertions required', proc.stderr)


if __name__ == '__main__':
    unittest.main()
