"""Failure-oriented admission tests and independent small exhaustive oracles."""
import itertools
import random

import pytest

from . import imported_case_admission as admission


def test_rejects_known_invalid_domains_without_mutating_or_losing_originals():
    fixtures = [
        (68, [['abcdefgh'], 3], 'words[i].length <= maxWidth'),
        (1256, [2**61-1], 'integer in [0, 1000000000]'),
        (1639, [['ab', 'a'], 'a'], 'same length'),
        (3074, [[10,20,30],[15,10,25]], 'redistribution must be possible'),
        (3114, ['??:??:'], 's.length'),
        (3132, [[1,2,3,4,5,6],[2,3]], 'nums2.length'),
        (3132, [[1,2,3,4],[0,1000]], 'reachable'),
        (1734, [[2,2]], 'permutation'),
        (2965, [[[1,1],[1,2]]], 'exactly one duplicated'),
        (3167, ['a01'], 'without leading zeros'),
        (3004, [[[0,1],[0,1]],[1,1,1]], 'without cycles'),
    ]
    for pid,args,reason in fixtures:
        original={'args':args,'expected':None,'compare':'return'}
        decision=admission.admit_case(pid,original)
        assert decision['status']=='rejected-domain'
        assert reason in decision['reason']
        assert decision['original']==original
        assert decision['original'] is not original
        assert 'case' not in decision


def test_supported_domain_boundaries_and_non_unique_outputs_are_not_invented():
    admission.validate(3004,[[],[1]])
    admission.validate(3004,[[[0,1],[1,2]],[1,2,2]])
    admission.validate(1554,[[]])
    admission.validate(1554,[['']])
    admission.validate(1610,[[[0,0]],0,[0,0]])
    admission.validate(3114,['11:59'])
    admission.validate(2450,['0',1])
    admission.validate(68,[['a!'],2])
    decision=admission.admit_case(2733,{'args':[[1,2,3,4]],'expected':2,'compare':'return'})
    assert decision['status']=='domain-valid-oracle-unreviewed'
    assert 'case' not in decision  # "any" middle element needs a property checker.
    with pytest.raises(admission.DomainError): admission.validate(660,[True])
    with pytest.raises(admission.DomainError): admission.validate(660,[1.0])
    with pytest.raises(admission.DomainError): admission.validate(999999,[[1]])


def test_expectation_repairs_are_computed_not_coerced():
    original={'args':[9],'expected':'999999','compare':'return'}
    decision=admission.admit_case(660,original)
    assert decision['case']['expected']==10
    assert decision['original']['expected']=='999999'
    assert original['expected']=='999999'
    assert decision['status']=='oracle-corrected'
    result=admission.admit_case(2450,{'args':['11111',1],'expected':32.0,'compare':'return'})
    assert result['case']['expected']==32 and type(result['case']['expected']) is int
    right_shift=admission.admit_case(2855,{'args':[[3,1,2]],'expected':1,'compare':'return'})
    assert right_shift['case']['expected']==2


def test_remove_nine_matches_direct_enumeration():
    sequence=[i for i in range(1,8000) if '9' not in str(i)]
    for n,want in enumerate(sequence,1):
        assert admission.expected(660,[n])==want


def test_flip_rank_matches_complete_reachability():
    for n in range(1,8):
        for k in range(1,n+1):
            masks=[((1<<k)-1)<<i for i in range(n-k+1)]
            reachable={0}
            for mask in masks:
                reachable |= {x^mask for x in reachable}
            assert admission.expected(2450,['0'*n,k])==len(reachable)


def test_deletion_translation_matches_enumerating_deleted_positions():
    rng=random.Random(6824)
    for n in range(3,9):
        for _ in range(40):
            source=[rng.randrange(10) for _ in range(n)]
            deleted=set(rng.sample(range(n),2))
            target=[v+3 for i,v in enumerate(source) if i not in deleted]
            possible=[]
            for removed in itertools.combinations(range(n),2):
                remaining=sorted(v for i,v in enumerate(source) if i not in removed)
                ordered=sorted(target); deltas=[y-x for x,y in zip(remaining,ordered)]
                if len(set(deltas))==1: possible.append(deltas[0])
            assert admission.expected(3132,[source,target])==min(possible)


def test_right_shifts_match_direct_repeated_operation():
    for n in range(1,7):
        for values in itertools.permutations(range(1,n+1)):
            state=list(values); want=-1
            for turns in range(n):
                if state==sorted(values): want=turns; break
                state=[state[-1]]+state[:-1]
            assert admission.expected(2855,[list(values)])==want


def test_cut_cost_matches_all_individual_cut_orders():
    for h,v in [([1],[2]),([1,4],[3,2]),([1,1],[1,1]),([],[2,1]),([5,1,2],[7])]:
        events=[('h',i) for i in range(len(h))]+[('v',i) for i in range(len(v))]
        costs=[]
        for order in itertools.permutations(events):
            hp=vp=1; total=0
            for direction,index in order:
                if direction=='h': total+=h[index]*vp; hp+=1
                else: total+=v[index]*hp; vp+=1
            costs.append(total)
        assert admission.expected(3218,[len(h)+1,len(v)+1,h,v])==min(costs)


def test_bst_reordering_matches_full_small_permutation_groups():
    def shape(values):
        if not values: return None
        return values[0],shape([v for v in values[1:] if v<values[0]]),shape([v for v in values[1:] if v>values[0]])
    for n in range(1,7):
        groups={}
        for values in itertools.permutations(range(1,n+1)):
            groups.setdefault(shape(values),[]).append(values)
        for values in groups.values():
            assert admission.expected(1569,[list(values[0])])==len(values)-1


def test_kth_paths_match_lexicographic_enumeration():
    for row in range(1,5):
        for col in range(1,5):
            paths=sorted(set(''.join(p) for p in itertools.permutations('V'*row+'H'*col)))
            for k,want in enumerate(paths,1):
                assert admission.expected(1643,[[row,col],k])==want


def test_text_justification_preserves_width_and_greedy_last_line():
    assert admission.expected(68,[['This','is','an','example','of','text','justification.'],16])==[
        'This    is    an','example  of text','justification.  ']
    assert admission.expected(68,[['a','b','c','d'],4])==['a  b','c d ']
    assert admission.expected(68,[['a'],3])==['a  ']


def test_public_examples_parser_preserves_inline_strings_and_rejects_wrong_oracle():
    raw=b'<p>Example 1:</p><pre><strong>Input:</strong> s = "<em>100</em>"\n<strong>Output:</strong> "1"</pre><p>Constraints:</p>'
    assert admission.public_examples(2710,raw)==[{'args':['100'],'expected':'1','compare':'return'}]
    with pytest.raises(ValueError,match='disagrees'):
        admission.public_examples(2710,raw.replace(b'"1"</pre>',b'"wrong"</pre>'))
    with pytest.raises(ValueError,match='no public example'):
        admission.public_examples(2710,b'<p>Statement without examples</p>')


def test_output_contract_specific_facts():
    # Exactly one hour is excluded; midnight does not wrap.
    assert admission.expected(2933,[[['a','0000'],['a','0030'],['a','0100'],['b','2350'],['b','0005'],['b','0010']]])==[]
    assert admission.expected(2933,[[['a','0000'],['a','0030'],['a','0059']]])==['a']
    assert admission.expected(3194,[[1,2,3,4]])==2.5
    assert admission.expected(3114,['??:??'])=='11:59'
    assert admission.expected(2802,[6])=='77'
    assert admission.expected(3167,['a3b1a1c2'])=='a4b1c2'


def test_tree_padding_is_transport_but_orphan_nodes_and_bad_bsts_are_not():
    short={'__tree_node__':[4,2,6,1,3]}
    padded={'__tree_node__':[4,2,6,1,3,None,None,None,None,None,None,None]}
    assert admission.tree_nodes(short,2,100,0,100000,bst=True)==admission.tree_nodes(padded,2,100,0,100000,bst=True)
    admission.validate(1305,[None,{'__tree_node__':[]}])
    with pytest.raises(admission.DomainError,match='orphan'):
        admission.validate(783,[{'__tree_node__':[2,None,None,1]}])
    with pytest.raises(admission.DomainError,match='BST'):
        admission.validate(1382,[{'__tree_node__':[1,2,3,4,5,6,7]}])
    with pytest.raises(admission.DomainError,match='BST'):
        admission.validate(783,[{'__tree_node__':[5,2,8,None,6]}])
    with pytest.raises(admission.DomainError,match='parent value exceeds'):
        admission.validate(998,[{'__tree_node__':[4,1,5]},6])
    with pytest.raises(admission.DomainError,match='exists'):
        admission.validate(2385,[{'__tree_node__':[1,2,3]},4])
    with pytest.raises(admission.DomainError,match='leading zeros'):
        admission.validate(2816,[{'__list_node__':[0,1]}])


def test_graph_and_folder_promises_are_checked_before_admission():
    admission.validate(2196,[[[1,2,1],[1,2,1]]])
    fixtures=[
        (2196,[[[1,2,1],[1,2,0]]],'one parent'),
        (1489,[4,[[0,1,1],[2,3,1]]],'connected'),
        (1377,[3,[[1,2],[2,1]],1,2],'at most one edge'),
        (1548,[3,[[0,1],[0,1]],['AAA','BBB','CCC'],['AAA']],'at most one edge'),
        (1948,[[['a','b']]],'parent'),
        (1948,[[['a'],['a']]],'same folder'),
        (2196,[[[1,2,1],[1,3,1]]],'one left'),
        (2196,[[[1,2,1],[3,4,1],[4,3,1]]],'single rooted tree'),
        (1901,[[[1,1],[2,3]]],'adjacent'),
        (1008,[[5,2,6,1]],'preorder'),
        (1203,[2,1,[0,0],[[0],[]]],'itself'),
        (1301,[['ES','XS']],'only top-left'),
    ]
    for pid,args,reason in fixtures:
        with pytest.raises(admission.DomainError,match=reason): admission.validate(pid,args)


def test_subset_sum_existence_matches_complete_small_array_universes():
    rng=random.Random(1982)
    for n,limit in [(1,5),(2,4),(3,3),(4,2)]:
        possible=set()
        for values in itertools.product(range(-limit,limit+1),repeat=n):
            sums=[0]
            for x in values: sums+=[s+x for s in sums]
            if min(sums)>=-limit and max(sums)<=limit: possible.add(tuple(sorted(sums)))
            assert admission.recoverable_subset_sums(n,sums)
        for _ in range(500):
            sums=sorted([0]+[rng.randrange(-limit,limit+1) for _ in range(2**n-1)])
            assert admission.recoverable_subset_sums(n,sums)==(tuple(sums) in possible)
    with pytest.raises(admission.DomainError,match='full subset-sum'):
        admission.validate(1982,[2,[0,1,1,3]])

