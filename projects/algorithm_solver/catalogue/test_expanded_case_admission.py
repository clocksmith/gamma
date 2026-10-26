"""Adversarial-domain regressions and independently enumerated small answers."""
from collections import deque
import itertools
import random

import pytest

from . import expanded_case_admission as a


def test_rejects_impossible_promises_and_keeps_original_payloads():
    fixtures=[
        (1282,[[2,2,2]],'divisible'),
        (1376,[3,0,[-1,2,1],[0,0,0]],'reachable'),
        (1376,[2,0,[-1,0],[1,1]],'without subordinates'),
        (1462,[3,[[0,1],[1,0]],[[0,2]]],'no cycles'),
        (2097,[[[1,2],[3,4]]],'Euler trail'),
        (2097,[[[1,2],[2,1],[3,4],[4,3]]],'connected'),
        (2122,[[1,2]],'recovery'),
        (1992,[[[1,1],[1,0]]],'rectangle'),
        (2193,['abc'],'palindrome'),
        (2197,[[99991,99991*2]],'integer in'),
        (2463,[[0,1],[[2,1]]],'capacity'),
        (1968,[[1,1,2]],'distinct'),
        (2331,[{'__tree_node__':[1,0,1]}],'internal operators'),
        (2458,[{'__tree_node__':[1,2,3]},[1]],'exclude tree root'),
        (2646,[2,[[0,1]],[2,3],[[0,1]]],'even'),
    ]
    for pid,args,reason in fixtures:
        original={'args':args,'expected':None,'compare':'return'}
        decision=a.admit_case(pid,original)
        assert decision['status']=='rejected-domain'
        assert reason in decision['reason']
        assert decision['original']==original and decision['original'] is not original
        assert 'case' not in decision


def test_game_history_cannot_continue_after_winner():
    valid=[[0,0],[1,0],[0,1],[1,1],[0,2]]
    assert a.expected(1275,[valid])=='A'
    with pytest.raises(a.DomainError,match='game ends'):a.validate(1275,[valid+[[2,2]]])
    with pytest.raises(a.DomainError,match='unique'):a.validate(1275,[[[0,0],[0,0]]])


def test_pinned_integer_domains_do_not_inherit_historical_uint32_assumptions():
    a.validate(190,[2**31-2])
    with pytest.raises(a.DomainError):a.validate(190,[2**31])
    with pytest.raises(a.DomainError,match='even'):a.validate(190,[1])
    with pytest.raises(a.DomainError):a.validate(191,[0])
    with pytest.raises(a.DomainError):a.validate(258,[2**60])
    with pytest.raises(a.DomainError):a.validate(258,[True])
    assert a.expected(171,['FXSHRXW'])==2**31-1
    with pytest.raises(a.DomainError):a.validate(171,['FXSHRXX'])


def test_ascii_and_decimal_domains_follow_statements():
    a.validate(205,['\x00\n','a\r'])
    with pytest.raises(a.DomainError):a.validate(205,['é','a'])
    a.validate(1870,[[1],1.01])
    with pytest.raises(a.DomainError,match='decimal'):a.validate(1870,[[1],1.001])
    a.validate(2469,[0]);a.validate(2469,[999.99])
    with pytest.raises(a.DomainError):a.validate(2469,[float('nan')])
    with pytest.raises(a.DomainError):a.validate(2469,[True])
    with pytest.raises(a.DomainError):a.validate(2469,[1.001])


def test_clock_and_price_grammar_not_just_array_lengths():
    for pid,args in [(1736,['2?:7?']),(2224,['23:60','23:59']),
                     (1604,[['a'],['24:00']]),(2288,['$01',10]),
                     (2288,['$0',10]),(2042,['word 0 2'])]:
        with pytest.raises(a.DomainError):a.validate(pid,args)
    assert a.expected(2288,['a $100 $1e5 $ $9999999999',13])=='a $87.00 $1e5 $ $8699999999.13'
    assert a.expected(1736,['??:??'])=='23:59'
    assert a.expected(1604,[['a','a','a'],['08:00','08:30','09:00']])==['a']


def test_grouping_and_euler_promises_accept_valid_nonunique_inputs():
    a.validate(1282,[[2,2,2,2]])
    a.validate(2097,[[[1,2],[2,1],[1,3],[3,1]]])
    a.validate(2097,[[[1,2],[2,3]]])
    decision=a.admit_case(1282,{'args':[[2,2,2,2]],'expected':[[0,1],[2,3]],'compare':'return'})
    assert decision['status']=='domain-valid-oracle-unreviewed'
    assert 'case' not in decision


def test_paired_recovery_existence_matches_full_small_witness_set():
    possible=set()
    for originals in itertools.product(range(1,8),repeat=2):
        for k in range(1,7):
            values=sorted([x-k for x in originals]+[x+k for x in originals])
            if min(values)>=1 and max(values)<=8:possible.add(tuple(values))
    for values in itertools.combinations_with_replacement(range(1,9),4):
        assert (a._recover_pair_witness(list(values)) is not None)==(values in possible)


def test_lcm_final_bound_is_checked_and_merge_order_agrees():
    # Individually valid even values merge to an LCM exceeding the final bound.
    with pytest.raises(a.DomainError,match='final non-coprime'):
        a.validate(2197,[[99998,99994]])
    def outcomes(values):
        results=set()
        for i in range(len(values)-1):
            if a.gcd(values[i],values[i+1])>1:
                results|=outcomes(values[:i]+(a.lcm(values[i],values[i+1]),)+values[i+2:])
        return results or {values}
    for values in itertools.product(range(1,7),repeat=4):
        result=tuple(a.expected(2197,[list(values)]))
        assert outcomes(values)=={result}


def test_good_subsets_match_direct_index_subset_products():
    rng=random.Random(1994)
    for _ in range(200):
        values=[rng.randrange(1,31) for _ in range(rng.randrange(1,11))];want=0
        for mask in range(1,1<<len(values)):
            product=1
            for i,v in enumerate(values):
                if mask>>i&1:product*=v
            if product==1:continue
            remaining=product;good=True;divisor=2
            while divisor*divisor<=remaining:
                exponent=0
                while remaining%divisor==0:remaining//=divisor;exponent+=1
                if exponent>1:good=False;break
                divisor+=1
            want+=good
        assert a.expected(1994,[values])==want
    decision=a.admit_case(1994,{'args':[[1,2,3,4]],'expected':6.0,'compare':'return'})
    assert decision['case']['expected']==6 and type(decision['case']['expected']) is int
    assert decision['status']=='oracle-corrected'


def test_bracket_swap_answer_matches_complete_bfs():
    for n in (2,4,6,8):
        strings={''.join(chars) for chars in itertools.product('[]',repeat=n) if chars.count('[')==n//2}
        def balanced(s):
            level=0
            for c in s:
                level+=1 if c=='[' else -1
                if level<0:return False
            return level==0
        distance={s:0 for s in strings if balanced(s)};queue=deque(distance)
        while queue:
            s=queue.popleft()
            for i,j in itertools.combinations(range(n),2):
                if s[i]==s[j]:continue
                row=list(s);row[i],row[j]=row[j],row[i];following=''.join(row)
                if following not in distance:distance[following]=distance[s]+1;queue.append(following)
        for s in strings:assert a.expected(1963,[s])==distance[s]


def test_discount_and_temperature_use_independent_exact_arithmetic():
    assert a.expected(2303,[[[3,50],[7,10],[12,25]],10])==2.65
    assert a.agrees(2469,a.expected(2469,[36.5]),[309.65,97.7])
    assert not a.agrees(2469,a.expected(2469,[36.5]),[True,97.7])
    assert a.agrees(1491,a.expected(1491,[[1000,2000,3000]]),2000)


def test_lattice_union_matches_direct_point_membership():
    rng=random.Random(2249)
    for _ in range(100):
        circles=[[rng.randrange(2,8),rng.randrange(2,8),rng.randrange(1,3)] for _ in range(4)]
        want=sum(any((x-cx)**2+(y-cy)**2<=r*r for cx,cy,r in circles) for x in range(11) for y in range(11))
        assert a.expected(2249,[circles])==want


def test_mutation_palindrome_and_bit_minimization_match_exhaustion():
    rng=random.Random(1946)
    for _ in range(150):
        s=''.join(str(rng.randrange(4)) for _ in range(5));mapping=[rng.randrange(10) for _ in range(10)]
        choices=[s]+[s[:i]+''.join(str(mapping[int(c)]) for c in s[i:j])+s[j:] for i in range(len(s)) for j in range(i+1,len(s)+1)]
        assert a.expected(1946,[s,mapping])==max(choices)
    for s,t in itertools.product(('abca','acba','abab','abba','aaaa'),repeat=2):
        want=any((s[:i]+t[i:])==(s[:i]+t[i:])[::-1] or (t[:i]+s[i:])==(t[:i]+s[i:])[::-1] for i in range(5))
        assert a.expected(1616,[s,t])==want
    for x in range(1,64):
        for y in range(1,16):
            want=min((v for v in range(1,128) if v.bit_count()==y.bit_count()),key=lambda v:v^x)
            assert a.expected(2429,[x,y])==want


def test_microwave_cost_considers_leading_zero_variants():
    def brute(start,move,push,target):
        costs=[]
        for value in range(10000):
            if value//100*60+value%100!=target:continue
            for width in range(max(1,len(str(value))),5):
                digits=str(value).zfill(width);finger=str(start);cost=0
                for digit in digits:cost+=push+(digit!=finger)*move;finger=digit
                costs.append(cost)
        return min(costs)
    for start,move,push,target in [(0,3,2,1),(9,7,4,99),(1,8,2,60),(0,1,9,600),(9,2,3,6039)]:
        assert a.expected(2162,[start,move,push,target])==brute(start,move,push,target)


def test_output_order_and_numeric_policies_do_not_drop_duplicates():
    assert not a.agrees(1604,['a','b'],['b','a'])
    assert a.agrees(2032,[1,2],[2,1])
    assert not a.agrees(2032,[1,2],[2,1,1])
    assert a.agrees(2215,[[1,2],[3]],[[2,1],[3]])
    assert not a.agrees(2215,[[1,2],[3]],[[3],[1,2]])
    assert a.agrees(1491,2.0,2)
    assert not a.agrees(1491,2.0,True)
