"""Frozen core references plus independent native-mutation witnesses."""
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import string
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'references'))
import core_cases
import core_oracles as o

IDS=core_cases.IDS
NATIVE=(189,283,289,324,344)


def validate_native(pid,args):
    assert type(args)is list and len(args)==(2 if pid==189 else 1)
    x=args[0]
    if pid in (189,283,324):
        limit={189:100000,283:10000,324:50000}[pid]
        assert type(x)is list and 1<=len(x)<=limit and all(type(v)is int for v in x)
        assert all((0<=v<=5000) if pid==324 else -(2**31)<=v<2**31 for v in x)
        if pid==189:assert type(args[1])is int and 0<=args[1]<=100000
    elif pid==289:
        assert type(x)is list and 1<=len(x)<=25 and type(x[0])is list and 1<=len(x[0])<=25
        assert all(type(row)is list and len(row)==len(x[0]) and all(type(v)is int and v in (0,1) for v in row) for row in x)
    elif pid==344:
        assert type(x)is list and 1<=len(x)<=100000 and all(type(c)is str and len(c)==1 and 32<=ord(c)<=126 for c in x)
    else:raise ValueError('not a native mutation problem')


def post_matches(pid,args,post,want):
    if type(post)is not list or len(post)!=len(args):return False
    if pid==324:
        return o.matches(324,args,post[0],want)
    if not o.exact(post[0],want):return False
    return len(args)==1 or o.exact(post[1:],args[1:])


def build(statements):
    data=core_cases.build(statements);seen={pid:{json.dumps(c['args'],sort_keys=True,separators=(',',':')) for c in values} for pid,values in data.items()}
    def add(pid,args,category,want=None,isolate=False):
        if pid in NATIVE:validate_native(pid,args)
        key=json.dumps(args,sort_keys=True,separators=(',',':'))
        if key in seen[pid]:return
        seen[pid].add(key)
        data[pid].append({'args':args,'expected':o.expected(pid,args) if want is None else want,'category':category,'isolate':isolate})
    # Existing distinct-reviewer witnesses are still checked against independent core references.
    packet=json.loads((HERE/'references/review-witnesses.json').read_bytes())
    for case in packet['cases']:
        pid=case['problem_id']
        if 'expected'in case:want=case['expected']
        else:
            assert pid==386
            want=sorted(range(1,case['args'][0]+1),key=str)
            assert len(want)==case['expected_length'] and hashlib.sha256(json.dumps(want,separators=(',',':')).encode()).hexdigest()==case['expected_value_sha256']
        assert o.exact(o.expected(pid,case['args']),want)
        add(pid,case['args'],'existing-distinct-reviewer-witness',want)
    add(287,[list(range(1,100001))+[100000]],'maximum-selfcycle-native-value',100000,True)
    add(287,[list(range(1,100001))+[1]],'maximum-fullcycle-native-value',1,True)
    ranked=[[r*300+c-45000 for c in range(300)] for r in range(300)]
    duplicate=[[0]*300 for _ in range(300)]
    for rank in (1,45000,90000):
        add(378,[ranked,rank],'maximum-ranked-square-native-value',rank-1-45000,True)
        add(378,[duplicate,rank],'maximum-duplicate-square-native-value',0,True)
    rng=random.Random(2026102868)
    for n in range(1,5):
        for values in product((-1,0,2),repeat=n):
            for steps in {0,1,n-1,n,100000}:
                add(189,[list(values),steps],'exhaustive-small-native-rotation')
    for n in range(1,6):
        for values in product((-(2**31),0,2**31-1),repeat=n):
            add(283,[list(values)],'exhaustive-stable-zero-compaction-boundaries')
    for rows,cols in ((1,1),(1,2),(2,1),(2,2),(2,3),(3,2),(3,3)):
        for values in product((0,1),repeat=rows*cols):
            board=[list(values[r*cols:(r+1)*cols]) for r in range(rows)]
            add(289,[board],'exhaustive-simultaneous-finite-board-transition')
    for n in range(1,8):
        values=list(product((0,1,2),repeat=n))
        valid_bags={tuple(sorted(xs)) for xs in values if all((xs[i-1]<xs[i] if i%2 else xs[i-1]>xs[i]) for i in range(1,n))}
        # Validity is established by enumeration of a witness, not by running the supplied sorter.
        for xs in values:
            if tuple(sorted(xs))in valid_bags:add(324,[list(xs)],'all-small-inputs-with-independent-wiggle-witness')
    for n in range(1,5):
        for values in product(('a','Z',' '),repeat=n):add(344,[list(values)],'exhaustive-ascii-reversal-small')
    for code in range(32,127):
        add(344,[[chr(code)]],'every-printable-ascii-singleton')
        add(344,[[chr(code),'!',chr(158-code)]],'printable-ascii-reversal-pairs')
    for _ in range(60):
        size=rng.randint(1,80)
        vector=[rng.randint(-(2**31),2**31-1) for _ in range(size)]
        add(189,[vector,rng.randint(0,100000)],'signed32-random-native-rotation')
        add(283,[[v if rng.randrange(2) else 0 for v in vector]],'signed32-stable-zero-order')
        rows,cols=rng.randint(1,25),rng.randint(1,25)
        add(289,[[[rng.randrange(2) for _ in range(cols)] for _ in range(rows)]],'native-board-dimensions-and-density')
        # Distinct values always admit a strict wiggle ordering.
        add(324,[rng.sample(range(5001),size)],'native-unique-values-full-range')
        add(344,[[chr(rng.randint(32,126)) for _ in range(size)]],'native-random-printable-ascii')
    rotate=list(range(-50000,50000))
    add(189,[rotate,1],'maximum-native-one-step-rotation',[rotate[-1],*rotate[:-1]],True)
    add(189,[rotate,99999],'maximum-native-offset-rotation',rotate[1:]+rotate[:1],True)
    add(189,[rotate,100000],'maximum-native-noop-offset',rotate,True)
    zeroes=[0,-2**31,0,2**31-1]*2500
    add(283,[zeroes],'maximum-native-stable-zero-compaction',[v for v in zeroes if v]+[0]*5000,True)
    add(283,[[0]*10000],'maximum-native-all-zero-noop',[0]*10000,True)
    add(289,[[[1]*25 for _ in range(25)]],'maximum-dense-native-board',isolate=True)
    add(289,[[[0]*25 for _ in range(25)]],'maximum-empty-native-board',isolate=True)
    for n in (49999,50000):
        values=[0]*((n+1)//2)+[5000]*(n//2)
        add(324,[values],'maximum-duplicate-native-wiggle',sorted(values),True)
        shuffled=values[:];rng.shuffle(shuffled)
        add(324,[shuffled],'maximum-shuffled-native-wiggle',sorted(values),True)
    chars=[chr(32+i%95) for i in range(100000)]
    add(344,[chars],'maximum-native-ascii-reversal',list(reversed(chars)),True)
    for pid,values in data.items():
        assert len({json.dumps(c['args'],sort_keys=True,separators=(',',':')) for c in values})==len(values),('duplicate realized case',pid)
        for case in values:
            if pid in NATIVE:
                validate_native(pid,case['args'])
                case['requires_native_effect_change']=not post_matches(pid,case['args'],case['args'],case['expected'])
    assert all(any(c['requires_native_effect_change'] for c in data[pid]) for pid in NATIVE)
    return data
