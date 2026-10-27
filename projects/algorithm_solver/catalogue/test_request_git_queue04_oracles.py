"""Source-free queue04 tests: synthetic fixtures, independent checks, no candidates."""
from copy import deepcopy
from itertools import combinations, permutations, product
import json
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_git_queue04_oracles as o

EXAMPLES = {
    2375:[(['IIIDIDDD'],'123549876'),(['DDD'],'4321')],
    2384:[(['444947137'],'7449447'),(['00009'],'9')],
    2396:[([9],False),([4],False)],
    2428:[([[[6,2,1,3],[4,2,1,5],[9,2,8,7],[4,1,2,9]]],30),([[[1,2,3],[4,5,6],[7,8,9]]],35)],
    2438:[([15,[[0,1],[2,2],[0,3]]],[2,4,64]),([2,[[0,0]]],[2])],
    2443:[([443],True),([63],False),([181],True)],
    2449:[([[8,12,6],[2,14,10]],2),([[1,2,5],[4,1,3]],1),([[1]*5,[1]*5],0)],
    2452:[([['word','note','ants','wood'],['wood','joke','moat']],['word','note','wood']),([['yes'],['not']],[])],
    2467:[([[[0,1],[1,2],[1,3],[3,4]],3,[-2,4,2,-4,6]],6),([[[0,1]],1,[-7280,2350]],-7280)],
    2498:[([[0,2,5,6,7]],5),([[0,3,9]],9)],
}


def fixture(pid):
    return ''.join('Input: '+', '.join(f'{key} = {json.dumps(value)}' for key,value in zip(o.PARAMETERS[pid],args))+
                   '\nOutput: '+json.dumps(answer)+'\nExplanation: Synthetic transcription.\n' for args,answer in EXAMPLES[pid]).encode()


class Queue04Oracles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw={pid:fixture(pid) for pid in o.IDS}
        with patch.dict(o.STATEMENT_SHA256,{pid:q.sha(raw) for pid,raw in cls.raw.items()}):
            cls.built={pid:o.build_cases(pid,cls.raw[pid]) for pid in o.IDS}

    def rejected(self,pid,rows):
        for args in rows:
            with self.subTest(pid=pid,args=str(args)[:120]),self.assertRaises(ValueError):
                o.validate(pid,args)

    def test_examples_reference_and_no_effects(self):
        for pid,rows in EXAMPLES.items():
            for args,want in rows:
                before=deepcopy(args)
                self.assertTrue(q.exact(o.expected(pid,args),want))
                self.assertEqual(args,before)

    def test_exact_identity_and_arity(self):
        for pid,args in [(True,[]),(2375.0,['I']),(2355,[]),(2408,[]),(9999,[]),(2375,('I',)),(2375,[]),(2375,['I','D'])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        self.assertEqual(set(o.QUEUE_IDS),set(o.IDS)|set(o.BLOCKED))
        self.assertFalse(set(o.IDS)&set(o.BLOCKED))

    def test_pattern_full_domain_and_rejections(self):
        self.rejected(2375,[[''],['I'*9],['i'],['Ｉ'],['ID '],[True],[None]])
        for pattern in product('ID',repeat=8):o.validate(2375,[''.join(pattern)])

    def test_digit_domain_unicode_and_leading_zero(self):
        self.rejected(2384,[[''],['0'*100001],['١'],['９'],['-1'],[123],['1.0']])
        o.validate(2384,['0'*100000]);o.validate(2384,['00009'])
        self.assertEqual(o.expected(2384,['00000']),'0')
        self.assertEqual(o.expected(2384,['000909']),'900009')

    def test_scalar_exact_types_and_bounds(self):
        self.rejected(2396,[[3],[100001],[True],[4.0],['4'],[None]])
        self.rejected(2443,[[-1],[100001],[False],[0.0],['0']])
        o.validate(2396,[100000]);o.validate(2443,[0]);o.validate(2443,[100000])
        self.assertTrue(o.expected(2443,[0]))

    def test_grid_full_rectangle_domain(self):
        self.rejected(2428,[[[]],[[[0]*3]*2],[[[0]*2]*3],[[[0]*3,[0]*4,[0]*3]],
                            [[[0]*3,[0]*3,[0,0,-1]]],[[[0]*3,[0]*3,[0,0,1000001]]],
                            [[[0]*3,[0]*3,[0,0,True]]],[[[0]*151]*3],[[[0]*3]*151]])
        o.validate(2428,[[[1000000]*150 for _ in range(150)]])

    def test_query_bitcount_order_type_domain(self):
        self.rejected(2438,[[0,[[0,0]]],[1000000001,[[0,0]]],[True,[[0,0]]],[3,[]],
                            [3,[[1,0]]],[3,[[0,2]]],[3,[[False,1]]],[3,[[0.0,1]]],[3,[[0,1,1]]],
                            [3,[[0,1]]*100001]])
        o.validate(2438,[1000000000,[[0,12]]]);o.validate(2438,[1,[[0,0]]*100000])

    def test_similar_arrays_reachability_not_just_equal_lengths(self):
        self.rejected(2449,[[[],[]],[[1],[2]],[[1,3],[2,2]],[[1,2],[1]],[[0,2],[0,2]],
                            [[1000001],[1000001]],[[True],[1]],[[1.0],[1]]])
        o.validate(2449,[[2]*100000,[2]*100000])
        o.validate(2449,[[1,1000000],[1000000,1]])
        self.assertEqual(o.expected(2449,[[2,8],[4,6]]),1)

    def test_dictionary_length_alphabet_order_duplicates(self):
        self.rejected(2452,[[[],['a']],[['a'],[]],[[''],['']],[['a'],['aa']],[['A'],['a']],
                            [['é'],['a']],[['a'*101],['a'*101]],[['a']*101,['a']],[[1],['a']]])
        o.validate(2452,[['z'*100]*100,['a'*100]*100])
        self.assertEqual(o.expected(2452,[['abc','xxx','abc','abz'],['abc']]),['abc','abc','abz'])

    def test_tree_full_domain_cycle_connectivity_types(self):
        self.rejected(2467,[[[],1,[0]],[[[0,1]],0,[0,0]],[[[0,1]],2,[0,0]],
                            [[[0,1]],True,[0,0]],[[[0,0]],1,[0,0]],[[[0,2]],1,[0,0]],
                            [[[0,1],[1,0]],1,[0,0,0]],[[[0,1]],1,[0,1]],[[[0,1]],1,[0,10002]],
                            [[[0,1]],1,[False,0]],[[[0,1],[1,2],[2,0]],1,[0,0,0,0]]])
        n=100000;o.validate(2467,[[[0,i] for i in range(1,n)],n-1,[0]*n])
        self.assertEqual(o.expected(2467,[[[0,1],[1,2]],2,[-2,-4,8]]),-4)

    def test_stones_full_domain_strictness_and_endpoint(self):
        self.rejected(2498,[[[]],[[0]],[[1,2]],[[0,0]],[[0,2,1]],[[0,1000000001]],[[False,1]],[[0,1.0]]])
        o.validate(2498,[[0]+list(range(999900002,1000000001))])
        self.assertEqual(o.expected(2498,[[0,1]]),1)

    def test_reference_budget_is_not_full_domain(self):
        for pid,args in [(2384,['1'*10]),(2396,[513]),(2428,[[[0]*11 for _ in range(10)]]),
                         (2438,[256,[[0,0]]]),(2449,[[1]*9,[1]*9]),(2452,[['a'*13],['a'*13]]),
                         (2467,[[[0,i] for i in range(1,13)],1,[0]*13]),(2498,[list(range(9))])]:
            o.validate(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)

    def test_pattern_reference_matches_all_short_nine_digit_search(self):
        for length in range(1,4):
            possibilities={}
            for digits in permutations('123456789',length+1):
                pattern=''.join('I' if a<b else 'D' for a,b in zip(digits,digits[1:]))
                possibilities.setdefault(pattern,''.join(digits))
            for pattern,answer in possibilities.items():self.assertEqual(o.expected(2375,[pattern]),answer)

    def test_reverse_sum_arithmetic_reference_against_string_enumeration(self):
        reached={x+int(str(x)[::-1]) for x in range(100001)}
        for case in self.built[2443][0]:self.assertEqual(case['expected'],case['args'][0] in reached)

    def test_coin_reference_against_distinct_subset_sums(self):
        for mask in range(1,256):
            subset=[2**i for i in range(8) if mask>>i&1]
            self.assertEqual(o._minimum_coin_decompositions()[sum(subset)],tuple(subset))
        for case in self.built[2438][0]:
            n,queries=case['args'];powers=[1<<i for i in range(30) if n>>i&1]
            answer=[]
            for a,b in queries:
                value=1
                for p in powers[a:b+1]:value*=p
                answer.append(value%o.MOD)
            self.assertEqual(case['expected'],answer)

    def test_similar_assignment_against_bounded_operation_bfs(self):
        for start in product((1,2,3),repeat=3):
            seen={tuple(start):0};ready=[tuple(start)]
            for state in ready:
                if seen[state]==3:continue
                for i,j in permutations(range(3),2):
                    nxt=list(state);nxt[i]+=2;nxt[j]-=2
                    if min(nxt)<1:continue
                    nxt=tuple(nxt)
                    if nxt not in seen:seen[nxt]=seen[state]+1;ready.append(nxt)
            targets={tuple(sorted(state)) for state in seen}
            for target in targets:
                minimum=min(depth for state,depth in seen.items() if tuple(sorted(state))==target)
                self.assertEqual(o.expected(2449,[list(start),list(target)]),minimum)

    def test_edit_subsets_against_hamming(self):
        for case in self.built[2452][0]:
            a,b=case['args']
            self.assertEqual(case['expected'],[w for w in a if any(sum(x!=y for x,y in zip(w,v))<=2 for v in b)])

    def test_frog_all_tours_against_partition_monotone_legs(self):
        # Independent restricted-route witness plus lower bound from cuts with
        # one interior vertex: optimal max of consecutive two-step gaps.
        for case in self.built[2498][0]:
            stones=case['args'][0]
            want=stones[-1] if len(stones)==2 else max(stones[i+2]-stones[i] for i in range(len(stones)-2))
            self.assertEqual(case['expected'],want)

    def test_frozen_populations_and_transport(self):
        for pid,(cases,categories) in self.built.items():
            self.assertEqual(len(cases),o.CASE_COUNT[pid]);self.assertEqual(len(categories),len(cases))
            self.assertEqual(q.sha(q.encoded(cases)),o.CASES_SHA256[pid]);self.assertLessEqual(len(q.encoded(cases)),q.MAX_FILE)
            self.assertTrue(any('exhaustive' in label for label in categories))
            for _,batch in q.batches(cases):
                self.assertLessEqual(len(batch),32);self.assertLessEqual(len(q.encoded(q.packet(batch))),q.MAX_PACKET)
                self.assertNotIn('expected',q.packet(batch)['calls'][0])
                for language in ('python','javascript'):self.assertLessEqual(o.expected_observation_bytes(batch,language),q.LIMITS['max_output_bytes'])

    def test_missing_or_changed_definition_fails_closed(self):
        for pid in o.IDS:
            with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid])
            pin={pid:q.sha(self.raw[pid])}
            with patch.dict(o.STATEMENT_SHA256,pin):
                with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid]+b' ')
                with self.assertRaises(ValueError):o.public_examples(pid,self.raw[pid].decode())
        with self.assertRaises(ValueError):o.public_examples(2355,b'')

    def test_typed_numeric_effect_and_alias_obligations(self):
        case={'args':[[1,2]],'expected':[3],'compare':'return'}
        record={'result':[3],'result_type':'list','args_before':[[1,2]],'args_after':[[1,2]],'alias_edges':[]}
        self.assertIsNone(q.compare(case,record,'python'))
        for patch_value,reason in [({'result':[3.0]},'result_value'),({'result':[True]},'result_value'),
                                   ({'args_after':[[2,1]]},'input_effects'),({'alias_edges':[[0,0]]},'return_aliases')]:
            self.assertEqual(q.compare(case,dict(record,**patch_value),'python'),reason)


if __name__ == '__main__':unittest.main()
