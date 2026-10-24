"""Invented-only independent checker tests; no corpus paths or benchmark."""
import copy
import hashlib
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch

import independent as audit
import prototype


def universe(texts, banned):
    occurrences = {}
    for pid, text in texts.items():
        for start in range(len(text)):
            for end in range(start+1, len(text)+1):
                word = text[start:end]
                if word not in banned:
                    occurrences.setdefault(word, []).append((pid, start, end))
    return occurrences


def supplied(texts, banned=(), seed=(), rng=None, pool=None):
    rng = rng or random.Random(170)
    banned = set(banned)
    entries = universe(texts, banned)
    alphabet = sorted(set(''.join(texts.values())) | {'z'})
    if pool is None:
        pool = sorted(set(alphabet) | set(seed) | {
            word for word, rows in entries.items()
            if len(word) >= 2 and len({pid for pid, _, _ in rows}) >= 2})
    q = [rng.randrange(90) for pid, text in sorted(texts.items())
         for start in range(len(text)) for end in range(start+1, len(text)+1)
         if text[start:end] in pool]
    return dict(texts=texts, banned=banned, old_pool=pool, old_q=q,
                seed=list(seed), alphabet=alphabet, D=11,
                expected_source_hashes={pid: hashlib.sha256(t.encode()).hexdigest()
                                        for pid, t in texts.items()},
                expected_old_banned=banned)


def optimized(kw, capacity):
    return prototype.Lift(kw['texts'], kw['banned'], kw['old_pool'], kw['old_q'],
                          kw['seed'], kw['alphabet'], kw['D'],
                          old_source_hashes=kw['expected_source_hashes'],
                          old_banned=kw['expected_old_banned']).certificate(capacity)


def explicit(kw):
    texts, D = kw['texts'], kw['D']
    entries = universe(texts, kw['banned'])
    qvalues = iter(kw['old_q'])
    old = {(pid, start, end): next(qvalues)
           for pid, text in sorted(texts.items()) for start in range(len(text))
           for end in range(start+1, len(text)+1) if text[start:end] in kw['old_pool']}
    potentials, full_potentials = {}, {}
    weights = dict.fromkeys(entries, 0)
    for pid, text in texts.items():
        d = [None]*len(text)+[0]
        for start in range(len(text)-1, -1, -1):
            d[start] = min((9 if end == start+1 else -1)*D+old[pid, start, end]+d[end]
                           for end in range(start+1, len(text)+1) if (pid, start, end) in old)
        full = [None]*len(text)+[0]
        for start in range(len(text)-1, -1, -1):
            candidates = []
            for end in range(start+1, len(text)+1):
                word = text[start:end]
                if word not in entries:
                    continue
                base = (9 if end == start+1 else -1)*D
                penalty = old.get((pid, start, end), max(0, d[start]-d[end]-base))
                weights[word] += penalty
                candidates.append(base+penalty+full[end])
            full[start] = min(candidates)
        potentials[pid], full_potentials[pid] = d, full
    assert potentials == full_potentials
    owners = {word: len({pid for pid, _, _ in rows}) for word, rows in entries.items()}
    return entries, owners, weights, potentials


class IndependentTests(unittest.TestCase):
    def compare(self, kw, capacity=3):
        result = audit.check(**kw, capacity=capacity)
        other = optimized(kw, capacity)
        for key in ('denominator', 'path_numerators', 'old_charge', 'old_numerator',
                    'class_counts', 'top_entries', 'rows', 'occurrence_sha256'):
            self.assertEqual(result[key], other[key], key)
        entries, owners, weights, potentials = explicit(kw)
        self.assertEqual(result['path_numerators'], {pid: d[0] for pid, d in potentials.items()})
        self.assertEqual(result['class_counts'], {
            support: sum((1 if count == 1 else 2) == support for count in owners.values())
            for support in (1, 2)})
        self.assertEqual(result['streamed_allowed_depths'], len(entries))
        self.assertEqual(result['old_bellman_edges_checked'], len(kw['old_q']))
        self.assertEqual(result['tight_suffix_positions_checked'], sum(map(len, kw['texts'].values())))
        index = audit.full.Index(kw['texts'], kw['banned'])
        for support in (1, 2):
            expected = []
            for gid, group in enumerate(index.groups):
                pid, start = index.positions[group['lo']]
                for length in range(group['first'], group['last']+1):
                    word = kw['texts'][pid][start:start+length]
                    if word in entries and (1 if owners[word] == 1 else 2) == support:
                        expected.append((weights[word], gid, length))
            expected.sort(key=lambda row: (-row[0], row[1], row[2]))
            self.assertEqual(result['top_entries'][support], expected[:capacity])
        return result, entries, owners, weights

    def test_random_scalar_replay_and_explicit_full_paths(self):
        rng = random.Random(5017)
        for _ in range(60):
            texts = {str(i): ''.join(rng.choice('abc') for _ in range(rng.randrange(2, 7)))
                     for i in range(3)}
            banned = set(texts.values())
            entries = universe(texts, banned)
            seed = [word for word, rows in sorted(entries.items())
                    if len(word) > 1 and len({pid for pid, _, _ in rows}) == 1][:2]+['zz']
            self.compare(supplied(texts, banned, seed, rng), rng.randrange(6))

    def test_exhaustive_allocation_and_dictionary_weak_duality(self):
        kw = supplied({'a': 'abac', 'b': 'baca'}, {'abac', 'baca'}, ['zz'])
        result, entries, owners, weights = self.compare(kw)
        maxima = [0]*4
        for size in range(4):
            for selected in itertools.combinations(entries, size):
                one = sum(owners[word] == 1 for word in selected)
                charge = sum(weights[word] for word in selected)
                for k in range(one, 4):
                    maxima[k] = max(maxima[k], charge)
                total = 0
                for text in kw['texts'].values():
                    distances = [0]+[None]*len(text)
                    for end in range(1, len(text)+1):
                        choices = [distances[end-len(word)]+(9 if len(word) == 1 else -1)
                                   for word in selected if len(word) <= end
                                   and text[end-len(word):end] == word
                                   and distances[end-len(word)] is not None]
                        distances[end] = min(choices) if choices else None
                    if distances[-1] is None:
                        break
                    total += distances[-1]
                else:
                    for k in range(one, 4):
                        self.assertGreaterEqual(total*kw['D'], result['rows'][k]['numerator'])
        self.assertEqual(maxima, [row['charge'] for row in result['rows']])

    def test_overlaps_duplicate_owners_slack_old_overrides_and_all_k(self):
        kw = supplied({'a': 'aaaaabaaaa', 'b': 'bcabc', 'c': 'bcabc'},
                      {'aaaa', 'aaaaabaaaa', 'bcabc'}, ['aaaab', 'zz'])
        kw['old_q'] = [1000000+i for i in range(len(kw['old_q']))]
        result, entries, owners, _ = self.compare(kw, 256)
        self.assertEqual(owners['aaa'], 1)
        self.assertEqual(owners['bc'], 2)
        self.assertEqual(len(result['rows']), 257)
        self.assertGreater(result['new_occurrence_contributions'], result['new_entries_streamed'])
        self.assertNotIn('z', entries)

    def test_unique_depths_all_streamed_bans_and_zero_weights(self):
        kw = supplied({'a': 'abcdefghijklmnop', 'b': 'ap'},
                      {'abcdefghijklmnop', 'bcde', 'efg'}, ['cdef', 'zz'])
        kw['old_q'] = [0]*len(kw['old_q'])
        result, _, _, _ = self.compare(kw, 3)
        self.assertGreater(result['new_entries_streamed'], 3)
        self.assertEqual(result['new_occurrence_contributions'], result['new_entries_streamed'])

    def test_identity_q_old_certificate_and_digest_corruption(self):
        kw = supplied({'a': 'abca', 'b': 'bcad'}, {'abca', 'bcad'})
        result = audit.check(**kw)
        cert = {'denominator': kw['D'], 'numerator': result['old_numerator'],
                'integer_lower_bound': -(-result['old_numerator']//kw['D']),
                'relaxed_paths_numerator': sum(result['path_numerators'].values()),
                'top_capacity_numerator': result['old_charge'],
                'per_program_path_numerators': [result['path_numerators'][pid]
                                                for pid in sorted(result['path_numerators'])]}
        audit.check(**kw, expected_old_certificate=cert,
                    expected_occurrence_sha256=result['occurrence_sha256'])
        for key in cert:
            damaged = copy.deepcopy(cert)
            if isinstance(damaged[key], list):
                damaged[key][0] += 1
            else:
                damaged[key] += 1
            with self.assertRaises(AssertionError):
                audit.check(**kw, expected_old_certificate=damaged)
        for change in ({'expected_source_hashes': {}}, {'expected_old_banned': {'wrong'}},
                       {'old_q': kw['old_q'][:-1]}, {'old_q': kw['old_q']+[0]},
                       {'old_q': [True]+kw['old_q'][1:]}, {'old_q': [-1]+kw['old_q'][1:]},
                       {'old_q': [0.25]+kw['old_q'][1:]}, {'expected_occurrence_sha256': 'wrong'}):
            with self.assertRaises(AssertionError):
                audit.check(**(kw | change))

    def test_complete_shared_pool_and_no_arbitrary_one_owner_extras(self):
        texts = {'a': 'abc', 'b': 'abd'}
        kw = supplied(texts)
        for pool in ([word for word in kw['old_pool'] if word != 'ab'],
                     sorted(kw['old_pool']+['bc'])):
            damaged = supplied(texts, pool=pool)
            with self.assertRaises(AssertionError):
                audit.check(**damaged)

    def test_shared_index_completeness_checks_reject_corruption(self):
        kw = supplied({'a': 'abca', 'b': 'bcad'}, {'abca', 'bcad'})
        constructor = audit.full.Index
        for corrupt in ('drop_group', 'wrong_lcp', 'wrong_ban', 'wrong_multiplicity'):
            def altered(*args, **kwargs):
                index = constructor(*args, **kwargs)
                if corrupt == 'drop_group':
                    index.groups.pop()
                elif corrupt == 'wrong_lcp':
                    index.lcp[-1] += 1
                elif corrupt == 'wrong_ban':
                    next(g for g in index.groups if g['excluded_lengths'])['excluded_lengths'].clear()
                else:
                    index.groups[0]['multiplicity'] += 1
                return index
            with patch.object(audit.full, 'Index', side_effect=altered):
                with self.assertRaises(AssertionError):
                    audit.check(**kw)

    def test_optimized_python_rejected_before_inputs(self):
        child = subprocess.run([sys.executable, '-O', '-c',
                                'import independent; independent.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'],
                               cwd=Path(__file__).resolve().parent, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(child.returncode, 0)
        self.assertIn('independent replay requires assertions', child.stderr)


if __name__ == '__main__':
    unittest.main()
