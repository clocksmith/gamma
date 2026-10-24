"""Supplied invented prefixes only; exhaustive allocation and frozen61 oracle."""
import copy
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest import mock

import allocation as a
import proof


def prefix(increments):
    values = [0]
    for value in increments:
        values.append(values[-1]+value)
    return values


class AllocationTests(unittest.TestCase):
    def compare(self, owners, shared, forced, L, D, B):
        inputs = copy.deepcopy((owners, shared, forced, L, D, B))
        got = a.allocate(*inputs)
        self.assertEqual(got, a.independent(*inputs))
        self.assertEqual(inputs, (owners, shared, forced, L, D, B))
        totals, choices, mandatory = proof.required_allocation(owners, forced, B)
        self.assertEqual(got['required_owner_prefix'], totals)
        self.assertEqual(got['remaining_marginal_choices'], choices)
        self.assertEqual(got['mandatory_value'], mandatory)
        ids = sorted(owners)
        allocations = list(itertools.product(*(range(1 if pid in forced else 0, len(owners[pid])) for pid in ids)))
        for j, value in totals.items():
            exact = [sum(owners[pid][n] for pid, n in zip(ids, vector)) for vector in allocations if sum(vector) == j]
            self.assertEqual(value, max(exact))
        for row in got['rows']:
            k = row['k']
            if k < len(forced):
                self.assertTrue(row['empty_by_required_owners'])
                self.assertTrue(all(row[name] is None for name in ('one_owner_slots','shared_slots','charge','numerator','integer_lower_bound')))
                continue
            options = []
            for vector in allocations:
                j = sum(vector)
                if j <= min(B, k):
                    s = min(B-j, len(shared)-1)
                    options.append((sum(owners[pid][n] for pid,n in zip(ids,vector))+shared[s], -j))
            value, minus_j = max(options)
            self.assertFalse(row['empty_by_required_owners'])
            self.assertEqual(row['charge'], value)
            self.assertEqual(row['one_owner_slots'], -minus_j)
            self.assertEqual(row['shared_slots'], min(B+minus_j, len(shared)-1))
            self.assertEqual(row['numerator'], L-value)
            self.assertEqual(row['integer_lower_bound'], -(-(L-value)//D))
        if len(forced) > B:
            self.assertIsNone(got['final_owner_counts'])
        else:
            counts = {pid:int(pid in forced) for pid in ids}
            for pid, rank, gain in choices:
                self.assertEqual(rank, counts[pid]+1)
                self.assertEqual(gain, owners[pid][rank]-owners[pid][rank-1])
                counts[pid] = rank
            self.assertEqual(counts, got['final_owner_counts'])
            self.assertEqual(sum(counts.values()), max(totals))
        return got

    def test_random_exhaustive_integer_allocations(self):
        rng = random.Random(6101)
        for _ in range(180):
            owners = {str(i):prefix(sorted([rng.randrange(11) for _ in range(rng.randrange(5))],reverse=True)) for i in range(rng.randrange(5))}
            forced = sorted(pid for pid,v in owners.items() if len(v)>1 and rng.randrange(2))
            shared = prefix(sorted([rng.randrange(11) for _ in range(rng.randrange(5))],reverse=True))
            self.compare(owners,shared,forced,rng.randrange(-100,101),rng.randrange(1,8),rng.randrange(8))

    def test_fixed_q53_strict_known_example(self):
        texts = {'p':'abba','q':'cc','r':'aa'}
        banned = set(texts.values())
        q = {edge:0 if edge[2]-edge[1]==1 else 9*(edge[2]-edge[1])+1 for edge in proof.parent.allowed(texts,banned)}
        expected = proof.certificate(texts,banned,q,3,1)
        base = expected['base57']
        got = self.compare(base['capped_prefixes'],base['shared_prefix'],expected['forced_owners'],base['L'],1,3)
        for actual, oracle in zip(got['rows'], expected['rows']):
            self.assertEqual(actual, {key:oracle[key] for key in actual})
        self.assertEqual(base['rows'][2]['charge'],38)
        self.assertEqual(got['rows'][2]['charge'],28)
        self.assertEqual(got['rows'][3]['charge'],base['rows'][3]['charge'])
        self.assertEqual(got['coverage_floor'],2)

    def test_finite_availability_capacity_zero_and_large(self):
        for B in (0,1,2,10):
            self.compare({'a':[0,0],'b':[0,0],'c':[0]},[0],['a','b'],-4,3,B)
            self.compare({},[0],[],0,1,B)
        got = self.compare({'a':[0,4,7],'b':[0]},[0,3],[],20,3,8)
        self.assertEqual(max(got['required_owner_prefix']),2)
        self.assertEqual(got['rows'][8]['one_owner_slots'],2)
        self.assertEqual(got['rows'][8]['shared_slots'],1)
        self.assertEqual(len(got['remaining_marginal_choices']),2)

    def test_mandatory_first_entry_is_clipped_by_full_path_cap(self):
        from test_proof import ProofTests
        texts = {'p':'aaaa', 'q':'bb'}
        banned = set(texts.values())
        q = {edge:0 if edge[2]-edge[1]==1 else 9*(edge[2]-edge[1])+1
             for edge in proof.parent.allowed(texts,banned)}
        # Enumerates every tiny covering dictionary/path and interval subset.
        expected, covering, _ = ProofTests().compare(texts,banned,q,B=2,D=1)
        self.assertIn((('a','b'),2),covering)
        base = expected['base57']
        self.assertEqual(base['owner_prefixes']['p'][1],57)
        self.assertEqual(base['owner_caps']['p'],38)
        got = self.compare(base['capped_prefixes'],base['shared_prefix'],
                           expected['forced_owners'],base['L'],1,2)
        self.assertEqual(got['mandatory_value'],38)
        self.assertEqual(got['rows'][2]['shared_slots'],0)
        self.assertEqual(got['rows'][2]['integer_lower_bound'],16)

    def test_stable_ties_zero_marginals_and_input_order(self):
        owners = {'c':[0,4,8],'b':[0,0,0],'a':[0,4,8,8]}
        got = self.compare(owners,[0,4,8],['b'],5,2,7)
        self.assertEqual(got['remaining_marginal_choices'],[('a',1,4),('a',2,4),('c',1,4),('c',2,4),('a',3,0),('b',2,0)])
        self.assertEqual(got,a.allocate(dict(reversed(list(owners.items()))),[0,4,8],['b'],5,2,7))
        zero = self.compare({'b':[0,0],'a':[0,0,0]},[0,0],['b'],0,1,4)
        self.assertTrue(all(row['one_owner_slots']==1 for row in zero['rows'][1:]))
        self.assertEqual(zero['final_owner_counts'],{'a':2,'b':1})

    def test_arbitrary_precision_and_negative_ceiling(self):
        huge = 10**90
        for L in (-huge,0,huge):
            self.compare({'a':[0,huge,2*huge]},[0,huge],['a'],L,7,3)

    def test_invalid_inputs_fail_closed_both_algorithms(self):
        valid = ({'a':[0,4,7],'b':[0,0]},[0,4,7],['a'],7,3,2)
        cases = []
        for at, values in (
            (0,[[],{1:[0]}, {'a':[]}, {'a':[False,1]}, {'a':[1]}, {'a':[0,1,3]}, {'a':[0,4,3]}, {'a':[0,float('inf')]}, {'a':(0,1)}]),
            (1,[[],[False],[1],[0,-1],[0,1,3],[0,float('nan')],(0,1)]),
            (2,[('a',),['a','a'],['b','a'],['missing'],[True]]),
            (3,[True,1.0,float('inf')]),
            (4,[True,0,-1,1.0]),
            (5,[True,-1,1.0])):
            for value in values:
                bad = list(copy.deepcopy(valid));bad[at]=value;cases.append(bad)
        # Impossible forced owners rejected even when the whole budget is empty.
        cases.extend([({'a':[0]},[0],['a'],0,1,B) for B in (0,1,2)])
        for fn in (a.allocate,a.independent):
            for inputs in cases:
                with self.subTest(function=fn.__name__,inputs=inputs):
                    with self.assertRaises(AssertionError):fn(*inputs)

    def test_independent_does_not_call_production_helpers(self):
        inputs = ({'a':[0,2,3]},[0,2],['a'],8,3,2)
        expected = a.allocate(*inputs)
        with mock.patch.object(a,'allocate',side_effect=RuntimeError('production forbidden')),mock.patch.object(a,'_validate',side_effect=RuntimeError('production validator forbidden')),mock.patch.object(a.heapq,'heappush',side_effect=RuntimeError('heap forbidden')):
            self.assertEqual(a.independent(*inputs),expected)
            with self.assertRaises(AssertionError):a.independent({'a':[0,1,3]},[0],[],0,1,2)

    def test_optimized_python_rejected(self):
        for function in ('allocate','independent'):
            code = f'import allocation; allocation.{function}({{}},[0],[],0,1,0)'
            proc = subprocess.run([sys.executable,'-O','-B','-c',code],cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('normal assertions required',proc.stderr)


if __name__ == '__main__':
    unittest.main()
