"""Invented supplied-input checks; no corpus paths or execution loader."""
import itertools
import random
import subprocess
import sys
import unittest
import prototype as p


def words(texts, banned):
    owners = {}
    for pid, text in texts.items():
        for i in range(len(text)):
            for j in range(i+1, len(text)+1):
                word = text[i:j]
                if word not in banned:
                    owners.setdefault(word, set()).add(pid)
    return owners


def fixture(texts, banned=(), seed=(), rng=None, zero=False):
    rng = rng or random.Random(4)
    owners = words(texts, banned)
    alphabet = sorted(set(''.join(texts.values())) | {'z'})
    pool = sorted({w for w, ids in owners.items() if len(w) >= 2 and len(ids) >= 2}
                  | set(alphabet) | set(seed))
    q, byedge = [], {}
    for pid, text in sorted(texts.items()):
        for i in range(len(text)):
            for j in range(i+1, len(text)+1):
                if text[i:j] in pool:
                    value = 0 if zero else rng.randrange(0, 70)
                    q.append(value); byedge[pid, i, j] = value
    kwargs = dict(texts=texts, banned=set(banned), old_pool=pool, old_q=q,
                  seed=list(seed), alphabet=alphabet, denominator=7,
                  old_source_hashes=p.source_hashes(texts), old_banned=set(banned))
    return kwargs, byedge


def oracle(lift, banned, byedge):
    owners = words(lift.texts, banned)
    weights = dict.fromkeys(owners, 0)
    distances = {}
    for pid, text in lift.texts.items():
        cost = [None]*len(text)+[0]
        for i in range(len(text)-1, -1, -1):
            choices = []
            for j in range(i+1, len(text)+1):
                w = text[i:j]
                if w not in owners:
                    continue
                base = 9 if j == i+1 else -1
                q = byedge.get((pid, i, j))
                if q is None:
                    q = max(0, lift.d[pid][i]-lift.d[pid][j]-base*lift.D)
                assert q == lift.penalty(pid, i, j)
                assert base*lift.D+q >= lift.d[pid][i]-lift.d[pid][j]
                weights[w] += q
                choices.append(base*lift.D+q+cost[j])
            cost[i] = min(choices)
        distances[pid] = cost
    return owners, weights, distances


def entry_word(lift, gid, length):
    g = lift.index.groups[gid]
    pid, start = lift.positions[g['lo']]
    return lift.texts[pid][start:start+length]


class Tests(unittest.TestCase):
    def test_optimized_python_rejected_explicitly(self):
        code = ('import prototype as p\n'
                'try: p.Lift({},(),[],[],[],[],1,old_source_hashes={},old_banned=())\n'
                'except RuntimeError: pass\n'
                'else: raise RuntimeError("optimized checks accepted")\n')
        result = subprocess.run([sys.executable, '-O', '-B', '-c', code],
                                cwd=p.Path(__file__).resolve().parent,
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def check(self, texts, banned=(), seed=(), capacity=3, rng=None, zero=False):
        kw, old = fixture(texts, banned, seed, rng, zero)
        lift = p.Lift(**kw)
        result = lift.certificate(capacity)
        owners, weights, distances = oracle(lift, banned, old)
        self.assertEqual(distances, lift.d)  # every suffix, not merely source start
        self.assertEqual(result['class_counts'], {s: sum((1 if len(v) == 1 else 2) == s for v in owners.values()) for s in (1, 2)})
        for support in (1, 2):
            expected = []
            for gid, g in enumerate(lift.index.groups):
                for length in range(g['first'], g['last']+1):
                    if length in g['excluded_lengths']:
                        continue
                    word = entry_word(lift, gid, length)
                    if (1 if len(owners[word]) == 1 else 2) == support:
                        expected.append((weights[word], gid, length))
            expected.sort(key=lambda r: (-r[0], r[1], r[2]))
            self.assertEqual(result['top_entries'][support], expected[:capacity])
        self.assertGreaterEqual(result['rows'][0]['numerator'], result['old_numerator'])
        return lift, result, owners, weights

    def test_random_explicit_paths_weights_and_all_support_caps(self):
        rng = random.Random(506)
        for _ in range(100):
            texts = {str(pid): ''.join(rng.choice('abc') for _ in range(rng.randrange(2, 7))) for pid in range(3)}
            banned = {v for v in texts.values() if len(v) > 1}
            owners = words(texts, banned)
            choices = sorted(w for w, ids in owners.items() if len(ids) == 1 and len(w) > 1)
            seed = choices[:2] + ['zz']
            self.check(texts, banned, seed, rng.randrange(0, 6), rng)

    def test_exhaustive_dictionary_weak_duality(self):
        rng = random.Random(7)
        for _ in range(16):
            texts = {str(i): ''.join(rng.choice('ab') for _ in range(4)) for i in range(2)}
            banned = set(texts.values())
            lift, result, owners, weights = self.check(texts, banned, capacity=3, rng=rng)
            maxcharges = [0]*4
            for size in range(4):
                for selected in itertools.combinations(owners, size):
                    one = sum(len(owners[v]) == 1 for v in selected)
                    charge = sum(weights[v] for v in selected)
                    for k in range(one, 4):
                        maxcharges[k] = max(maxcharges[k], charge)
                    total = 0
                    for text in texts.values():
                        cost = [None]*len(text)+[0]
                        for i in range(len(text)-1, -1, -1):
                            choices = [(9 if len(v) == 1 else -1)+cost[i+len(v)] for v in selected
                                       if text.startswith(v, i) and cost[i+len(v)] is not None]
                            cost[i] = min(choices) if choices else None
                        if cost[0] is None:
                            break
                        total += cost[0]
                    else:
                        for k in range(one, 4):
                            self.assertGreaterEqual(total*lift.D, result['rows'][k]['numerator'])
            self.assertEqual(maxcharges, [r['charge'] for r in result['rows']])

    def test_repeated_owner_overlaps_global_bans_and_old_exceptions(self):
        lift, result, owners, weights = self.check(
            {'0': 'aaaaabaaaa', '1': 'bcabc'}, {'aaaa', 'aaaaabaaaa', 'bcabc'}, ['aaaab', 'zz'])
        self.assertGreater(result['repeated_occurrence_work'], 0)
        self.assertEqual(owners['aaa'], {'0'})
        self.assertNotIn('aaaa', weights)

    def test_unique_endpoint_splitting_bans_old_overrides_and_zero_ties(self):
        for zero in (False, True):
            lift, result, owners, weights = self.check(
                {'0': 'abcdefghijk', '1': 'ak'}, {'abcdefghijk', 'bcde', 'efg'}, ['cdef', 'zz'], 4, zero=zero)
            self.assertGreater(result['unique_range_queries'], 0)
            self.assertLessEqual(result['unique_entries_extracted'], 4)
            self.assertEqual(result['repeated_occurrence_work'], 0)

    def test_source_ban_q_and_occurrence_identity_fail_closed(self):
        kw, old = fixture({'0': 'abca', '1': 'bcad'}, {'abca', 'bcad'})
        lift = p.Lift(**kw)
        p.Lift(**kw, expected_occurrence_sha256=lift.occurrence_sha256)
        for patch in ({'old_source_hashes': {}}, {'old_banned': {'wrong'}},
                      {'old_q': kw['old_q'][:-1]}, {'old_q': kw['old_q']+[0]},
                      {'old_q': [True]+kw['old_q'][1:]}, {'old_q': [-1]+kw['old_q'][1:]},
                      {'old_q': [0.5]+kw['old_q'][1:]}, {'expected_occurrence_sha256': 'wrong'}):
            with self.assertRaises(AssertionError):
                p.Lift(**(kw | patch))

    def test_shared_pool_completeness_and_extra_entry_rejection(self):
        kw, old = fixture({'0': 'abc', '1': 'abd'})
        # Build matching q in the modified order: failure must be pool scope,
        # not merely a q-length mismatch.
        for pool in ([v for v in kw['old_pool'] if v != 'ab'], sorted(kw['old_pool']+['bc'])):
            q = [0 for pid, text in sorted(kw['texts'].items()) for i in range(len(text))
                 for j in range(i+1, len(text)+1) if text[i:j] in pool]
            with self.assertRaises(AssertionError):
                p.Lift(**(kw | {'old_pool': pool, 'old_q': q}))

    def test_all_paid_singletons_support_and_absent_old_entries(self):
        lift, result, owners, weights = self.check({'0': 'ab', '1': 'ac'}, {'ab', 'ac'}, ['zz'], capacity=256)
        self.assertEqual(owners['b'], {'0'})
        self.assertNotIn('z', owners)
        self.assertEqual(len(result['rows']), 257)
        self.assertEqual(result['rows'][0]['one_owner_slots'], 0)
        self.assertEqual(result['class_counts'], {1: 2, 2: 1})

    def test_positive_k_zero_lift_and_negative_full_endpoint_rounding(self):
        lift, result, owners, weights = self.check(
            {'0': 'abcd', '1': 'aefg'}, {'abcd', 'aefg'}, capacity=256, zero=True)
        self.assertEqual(result['old_numerator'], 72*7)
        self.assertEqual(result['rows'][0]['integer_lower_bound'], 72)
        self.assertLess(result['rows'][-1]['numerator'], 0)
        for row in result['rows']:
            bound = row['integer_lower_bound']
            self.assertLess((bound-1)*lift.D, row['numerator'])
            self.assertGreaterEqual(bound*lift.D, row['numerator'])


if __name__ == '__main__':
    unittest.main()
