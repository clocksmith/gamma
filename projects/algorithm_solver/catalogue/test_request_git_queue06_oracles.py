"""Stdlib tests of new public-spec references; no candidate/statement-file reads."""
import copy
from itertools import product
import random
import unittest
from . import request_git_queue06_oracles as o

class Queue06ReferenceTests(unittest.TestCase):
    def test_public_examples_by_value(self):
        examples=[(2718,[3,[[0,0,1],[1,2,2],[0,2,3],[1,0,4]]],23),(2718,[3,[[0,0,4],[0,1,2],[1,0,1],[0,2,3],[1,2,1]]],17),
          (2730,['52233'],4),(2730,['5494'],4),(2730,['1111111'],2),
          (2746,[['aa','ab','bc']],4),(2746,[['ab','b']],2),(2746,[['aaa','c','aba']],6),
          (2750,[[0,1,0,0,1]],3),(2750,[[0,1,0]],1),
          (2768,[3,3,[[0,0]]],[3,1,0,0,0]),(2768,[3,3,[[0,0],[1,1],[0,2]]],[0,2,2,0,0]),
          (2769,[4,1],6),(2769,[3,2],7)]
        for pid,args,want in examples:
            with self.subTest(pid=pid,args=args):self.assertEqual(o.expected(pid,args),want)
    def test_dense_overwrites_against_last_timestamps(self):
        rng=random.Random(601)
        for _ in range(100):
            n=rng.randrange(1,6);queries=[[rng.randrange(2),rng.randrange(n),rng.randrange(100001)] for _ in range(rng.randrange(1,20))]
            rows=[(-1,0)]*n;cols=[(-1,0)]*n
            for t,(kind,i,v) in enumerate(queries):(cols if kind else rows)[i]=(t,v)
            want=sum((row if row[0]>col[0] else col)[1] for row in rows for col in cols)
            self.assertEqual(o.expected(2718,[n,queries]),want)
    def test_semirepetition_overlapping_pairs(self):
        for s,want in [('0',1),('000',2),('00100',4),('1234567890',10),('112233',4),('1211221',5)]:
            self.assertEqual(o.expected(2730,[s]),want)
    def test_literal_join_against_boundary_state_dp(self):
        for n in range(1,6):
            for words in product(('a','ab','ba'),repeat=n):
                states={(words[0][0],words[0][-1]):len(words[0])}
                for word in words[1:]:
                    nxt={}
                    for (first,last),length in states.items():
                        for key,value in [((first,word[-1]),length+len(word)-(last==word[0])),((word[0],last),length+len(word)-(word[-1]==first))]:
                            nxt[key]=min(nxt.get(key,10**9),value)
                    states=nxt
                self.assertEqual(o.expected(2746,[list(words)]),min(states.values()))
    def test_cut_masks_against_boundary_gap_count(self):
        for n in range(1,9):
            for values in product((0,1),repeat=n):
                positions=[i for i,v in enumerate(values) if v];want=int(bool(positions))
                for a,b in zip(positions,positions[1:]):want*=b-a
                self.assertEqual(o.expected(2750,[list(values)]),want)
    def test_block_histogram_and_coordinate_order(self):
        cases=[[2,2,[]],[2,2,[[0,0],[0,1],[1,0],[1,1]]],[3,4,[[0,0],[1,2],[2,3]]]]
        for args in cases:
            want=o.expected(2768,args)
            self.assertEqual(sum(want),(args[0]-1)*(args[1]-1))
            self.assertEqual(o.expected(2768,[args[0],args[1],list(reversed(args[2]))]),want)
        self.assertEqual(o.expected(2768,cases[0]),[1,0,0,0,0]);self.assertEqual(o.expected(2768,cases[1]),[0,0,0,0,1])
    def test_reachability_full_scalar_domain(self):
        for num in range(1,51):
            for t in range(1,51):self.assertEqual(o.expected(2769,[num,t]),num+2*t)
    def test_input_preservation(self):
        for pid,args in [(2718,[2,[[0,1,9],[1,0,7]]]),(2746,[['ab','ba','b']]),(2750,[[1,0,1]]),(2768,[3,3,[[0,0],[1,1]]])]:
            before=copy.deepcopy(args);o.expected(pid,args);self.assertEqual(args,before)
    def test_full_domain_boundaries(self):
        for pid,args in [(2718,[10000,[[1,9999,100000]]*50000]),(2730,['9'*50]),(2746,[['z'*50]*1000]),(2750,[[0]*100000]),(2768,[100000,100000,[[0,i] for i in range(10000)]]),(2769,[50,50])]:o.validate(pid,args)
    def test_invalid_domains(self):
        bad={2718:[[0,[[0,0,0]]],[1,[]],[1,[[True,0,1]]],[1,[[0,1,1]]],[1,[[0,0,100001]]]],
             2730:[[''],['1'*51],['１２'],[123]],2746:[[[]],[['']], [['A']],[['a'*51]]],
             2750:[[[]],[[True]],[[1.0]],[[2]]],2768:[[1,2,[]],[2,2,[[0,0],[0,0]]],[2,2,[[0,2]]],[2,2,[[False,0]]],[2,2,[[0,0,0]]]],2769:[[0,1],[1,0],[51,1],[1,51],[True,1],[1,1.0]]}
        for pid,cases in bad.items():
            for args in cases:
                with self.subTest(pid=pid,args=args),self.assertRaises(ValueError):o.validate(pid,args)
        for pid,args in [(True,[1]),(9999,[]),(2730,('1',)),(2730,['1','2'])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
    def test_reference_budget_is_not_domain_rejection(self):
        for pid,args in [(2718,[13,[[0,0,1]]]),(2746,[['a']*11]),(2750,[[1]*15]),(2768,[21,2,[]])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)
    def test_result_types_and_statement_pin(self):
        self.assertFalse(o.valid_answer(2769,[1,1],True));self.assertFalse(o.valid_answer(2750,[[1]],1.0))
        self.assertFalse(o.valid_answer(2768,[2,2,[]],[True,0,0,0,0]))
        self.assertFalse(o.valid_answer(2768,[2,2,[]],[0,0,0,0,0]))
        with self.assertRaises(ValueError):o.public_examples(2730,b'wrong statement')

if __name__=='__main__':unittest.main()
