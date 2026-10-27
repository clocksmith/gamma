"""Synthetic source-free checks for the bounded batch H reference contract."""
from copy import deepcopy
from itertools import product
import json
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_parallel_h_oracles as o

EXAMPLES = {
    3534: [([5,[1,8,3,4,2],3,[[0,3],[2,4]]],[1,1]),
           ([5,[5,3,1,9,10],2,[[0,1],[0,2],[2,3],[4,3]]],[1,2,-1,1]),
           ([3,[3,6,1],1,[[0,0],[0,1],[1,2]]],[0,-1,-1])],
    3568: [([['S.','XL'],2],2), ([['LS','RL'],4],3), ([['L.S','RXL'],3],-1)],
    3600: [([3,[[0,1,2,1],[1,2,3,0]],1],2), ([3,[[0,1,4,0],[1,2,3,0],[0,2,1,0]],2],6),
           ([3,[[0,1,1,1],[1,2,1,1],[2,0,1,1]],0],-1)],
    3613: [([5,[[0,1,4],[1,2,3],[1,3,2],[3,4,6]],2],4), ([4,[[0,1,5],[1,2,5],[2,3,5]],1],5)],
    3620: [([[[0,1,5],[1,3,10],[0,2,3],[2,3,4]],[True]*4,10],3),
           ([[[0,1,7],[1,4,5],[0,2,6],[2,3,6],[3,4,2],[2,4,6]],[True,True,True,False,True],12],6)],
}


def fixture(pid):
    return ''.join('Input: '+', '.join(f'{key} = {json.dumps(value)}' for key,value in zip(o.PARAMETERS[pid],args))+
                   '\n\nOutput: '+json.dumps(answer)+'\nExplanation: Synthetic transcription.\n' for args,answer in EXAMPLES[pid]).encode()


class ParallelHOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {pid:fixture(pid) for pid in o.IDS};cls.pins = {pid:q.sha(raw) for pid,raw in cls.raw.items()}
        with patch.dict(o.STATEMENT_SHA256,cls.pins):
            cls.built = {pid:o.build_cases(pid,cls.raw[pid]) for pid in o.IDS}

    def test_public_examples(self):
        for pid,rows in EXAMPLES.items():
            for args,answer in rows:
                self.assertTrue(q.exact(o.expected(pid,args),answer))

    def test_fixed_identity_and_ordered_shapes(self):
        for pid,args in [(True,[]),(3534.0,[]),(1,[]),(3534,()),(3534,[]),(3568,[['S']]),(3620,[[],[True,True],0,1])]:
            with self.subTest(pid=pid,args=args),self.assertRaises(ValueError):o.validate(pid,args)

    def test_threshold_full_domain_and_exact_integer_types(self):
        for args in [[True,[0],0,[[0,0]]],[1,[True],0,[[0,0]]],[1,[0],False,[[0,0]]],
                     [1,[0],0,[[0,False]]],[1,[0],0,[]],[1,[0],0,[[0,1]]],[1,[0,1],0,[[0,0]]],
                     [1,[-1],0,[[0,0]]],[1,[100001],0,[[0,0]]],[1,[0],100001,[[0,0]]]]:
            with self.subTest(args=args),self.assertRaises(ValueError):o.validate(3534,args)
        o.validate(3534,[100000,[100000]*100000,100000,[[0,99999]]])

    def test_classroom_domain(self):
        for args in [[[],1],[[''],1],[['S','..'],1],[['SS'],1],[['L'],1],[['Sa'],1],[['S'],0],[['S'],51],
                     [['S'],True],[['S'+'L'*11],1],[['S'*21],1],[('S',),1]]:
            with self.subTest(args=args),self.assertRaises(ValueError):o.validate(3568,args)
        o.validate(3568,[['S'+'L'*10+'.'*9]+['.'*20]*19,50])

    def test_spanning_domain_no_loops_or_duplicate_undirected_edges(self):
        for args in [[1,[[0,0,1,0]],0],[2,[],0],[2,[[0,0,1,0]],0],[2,[[0,1,1,0],[1,0,2,1]],0],
                     [2,[[0,1,0,0]],0],[2,[[0,1,100001,0]],0],[2,[[0,1,1,True]],0],
                     [2,[[0,1,1,0]],3],[2,[[0,1,1,0]],True]]:
            with self.subTest(args=args),self.assertRaises(ValueError):o.validate(3600,args)
        o.validate(3600,[100000,[[0,99999,100000,1]],100000])

    def test_component_domain_keeps_loops_parallel_edges_and_connectivity(self):
        o.validate(3613,[2,[[0,1,1],[1,0,2],[0,0,1000000]],1]);o.validate(3613,[1,[],1])
        for args in [[2,[],1],[2,[[0,0,1]],1],[1,[],0],[50001,[],1],[2,[[0,1,1000001]],1],
                     [2,[[0,1,1]],True],[2,[[0,1,1.0]],1]]:
            with self.subTest(args=args),self.assertRaises(ValueError):o.validate(3613,args)

    def test_dag_domain_exact_bool_endpoints_and_acyclicity(self):
        for args in [[[],[True],0],[[],[1,True],0],[[],[True,False],0],[[],[False,True],0],
                     [[[0,0,1]],[True,True],1],[[[0,1,1],[1,0,1]],[True]*3,2],
                     [[[0,1,10**9+1]],[True,True],0],[[],[True,True],5*10**13+1],[[],[True,True],False]]:
            with self.subTest(args=args),self.assertRaises(ValueError):o.validate(3620,args)
        o.validate(3620,[[[0,2,0],[0,2,10**9]],[True,False,True],5*10**13])
        o.validate(3620,[[[0,2,1],[2,1,2],[1,3,3]],[True]*4,6])

    def test_full_domain_is_not_reference_budget(self):
        for pid,args in [(3534,[13,[0]*13,0,[[0,12]]]),(3568,[['S'+'L'*6],1]),
                         (3568,[['S'],9]),(3600,[8,[[0,1,1,0]],0]),(3613,[1,[[0,0,1]]*13,1]),
                         (3620,[[],[True]*11,0])]:
            o.validate(pid,args)
            with self.subTest(pid=pid),self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,args)

    def test_budget_check_precedes_search(self):
        with patch.object(o,'_spanning_subsets',side_effect=AssertionError('must not enumerate')):
            with self.assertRaisesRegex(ValueError,'budget'):o.expected(3600,[100000,[[0,1,1,0]],0])

    def test_threshold_identity_connectivity_and_unsorted_indices(self):
        self.assertEqual(o.expected(3534,[4,[9,0,6,3],3,[[0,1],[1,0],[2,2]]]),[3,3,0])
        self.assertEqual(o.expected(3534,[3,[7,7,8],0,[[0,1],[0,2],[0,0]]]),[1,-1,0])

    def test_energy_zero_arrival_refill_and_no_litter(self):
        for args,answer in [([['S'],1],0),([['SL'],1],1),([['SRL'],1],2),([['S.L'],1],-1),
                            ([['LSL'],2],-1),([['LSL'],3],3),([['LRSRL'],1],-1)]:
            self.assertEqual(o.expected(3568,args),answer)

    def test_mandatory_cycles_and_nonupgradable_edges(self):
        self.assertEqual(o.expected(3600,[3,[[0,1,2,1],[1,2,5,0]],2]),2)
        self.assertEqual(o.expected(3600,[3,[[0,1,7,0],[1,2,7,0]],1]),7)
        self.assertEqual(o.expected(3600,[3,[[0,1,7,0],[1,2,7,0]],2]),14)
        self.assertEqual(o.expected(3600,[4,[[0,1,10,0],[2,3,10,0]],4]),-1)

    def test_component_at_most_k_and_removable_loops(self):
        for args,answer in [([1,[[0,0,1000000]],1],0),([2,[[0,1,1],[0,1,1000000]],1],1),
                            ([3,[[0,1,2],[1,2,7]],1],7),([3,[[0,1,2],[1,2,7]],2],2),
                            ([3,[[0,1,2],[1,2,7]],3],0)]:
            self.assertEqual(o.expected(3613,args),answer)

    def test_dag_zero_cost_budget_and_offline_nodes(self):
        for args,answer in [([[[0,1,0]],[True,True],0],0),([[],[True,True],0],-1),
                            ([[[0,1,1],[1,2,1]],[True,False,True],10],-1),
                            ([[[0,2,9],[0,2,0]],[True,True,True],8],0),
                            ([[[0,2,9],[2,1,8],[1,3,7]],[True]*4,24],7),
                            ([[[0,1,10**9],[1,2,10**9]],[True]*3,2*10**9],10**9)]:
            self.assertEqual(o.expected(3620,args),answer)

    def test_small_homologues_of_large_analytic_cases(self):
        for n in range(2,8):
            self.assertEqual(o.expected(3534,[n,list(range(n)),1,[[0,n-1]]]),[n-1])
            self.assertEqual(o.expected(3600,[n,[[i,i+1,7,0] for i in range(n-1)],n-1]),14)
            self.assertEqual(o.expected(3613,[n,[[i,i+1,7] for i in range(n-1)],n-1]),7)
            self.assertEqual(o.expected(3620,[[[i,i+1,0] for i in range(n-1)],[True]*n,0]),0)
        for n in range(2,9):
            self.assertEqual(o.expected(3568,[['S'+'R'*(n-2)+'L'],1]),n-1)

    def test_floyd_crosscheck_small_threshold_graphs(self):
        for values in product((0,1,3),repeat=3):
            for difference in (0,1,2):
                distances = [[0 if a == b else 1 if abs(values[a]-values[b]) <= difference else 99 for b in range(3)] for a in range(3)]
                for k in range(3):
                    for a in range(3):
                        for b in range(3):distances[a][b] = min(distances[a][b],distances[a][k]+distances[k][b])
                queries = [[a,b] for a in range(3) for b in range(3)]
                self.assertEqual(o.expected(3534,[3,list(values),difference,queries]),[d if d<99 else -1 for row in distances for d in row])

    def test_no_mutation_or_candidate_source_needed(self):
        for pid,rows in EXAMPLES.items():
            for args,_ in rows:
                original=deepcopy(args);o.expected(pid,args);self.assertEqual(args,original)

    def test_statement_pin_precedes_reference_work(self):
        with patch.object(o,'expected',side_effect=AssertionError('must not calculate')):
            with self.assertRaisesRegex(ValueError,'pinned statement'):o.public_examples(3534,b'not pinned')

    def test_missing_examples_and_argument_order_fail_closed(self):
        for raw in (b'Constraints only',b'Input: energy = 1, classroom = ["S"]\nOutput: 0\n'):
            with patch.dict(o.STATEMENT_SHA256,{3568:q.sha(raw)}),self.assertRaises(ValueError):o.public_examples(3568,raw)

    def test_return_types_are_exact(self):
        raw=self.raw[3568].replace(b'Output: 2',b'Output: true',1)
        with patch.dict(o.STATEMENT_SHA256,{3568:q.sha(raw)}),self.assertRaisesRegex(ValueError,'disagrees'):o.public_examples(3568,raw)

    def test_frozen_case_and_category_lengths(self):
        for pid,(cases,categories) in self.built.items():
            self.assertEqual(len(cases),o.CASE_COUNT[pid]);self.assertEqual(len(cases),len(categories))
            self.assertEqual(q.sha(q.encoded(cases)),o.CASES_SHA256[pid])

    def test_bad_case_population_or_pin_is_rejected(self):
        for target,change in [(o.CASE_COUNT,{3534:1}),(o.CASES_SHA256,{3534:None})]:
            with patch.dict(o.STATEMENT_SHA256,self.pins),patch.dict(target,change),self.assertRaisesRegex(ValueError,'frozen batch'):
                o.build_cases(3534,self.raw[3534])

    def test_unchanged_file_packet_and_observer_caps(self):
        for cases,_ in self.built.values():
            self.assertLessEqual(len(q.encoded(cases)),q.MAX_FILE)
            for _,batch in q.batches(cases):
                self.assertLessEqual(len(batch),32);self.assertLessEqual(len(q.encoded(q.packet(batch))),q.MAX_PACKET)
                for language in ('python','javascript'):
                    self.assertLessEqual(o.expected_observation_bytes(batch,language),q.LIMITS['max_output_bytes'])

    def test_success_projection_fails_closed(self):
        with self.assertRaises(ValueError):o.expected_observation_bytes([],'unknown')
        with patch.dict(o.STATEMENT_SHA256,self.pins),patch.dict(q.LIMITS,{'max_output_bytes':1}),self.assertRaisesRegex(ValueError,'output cap'):
            o.build_cases(3568,self.raw[3568])

    def test_valid_large_tree_exceeds_packet_without_domain_shrink(self):
        args=[100000,[[i,i+1,100000,0] for i in range(99999)],99999];o.validate(3600,args)
        with self.assertRaisesRegex(ValueError,'packet cap'):list(q.batches([{'args':args,'expected':200000,'compare':'return'}]))


if __name__ == '__main__':unittest.main()
