"""Private independent-case generation, file-local imports."""
import importlib.util
from pathlib import Path
import itertools
import random
_spec=importlib.util.spec_from_file_location('gamma_o_case_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain

def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==3909:
        for _ in range(100):args.append([sorted(rng.sample(range(1,40),rng.randrange(1,6)))+[100]+sorted(rng.sample(range(1,40),rng.randrange(1,6)),reverse=True)])
    elif pid==3910:
        for n in range(1,10):
            for _ in range(15):args.append([[rng.randrange(2) for _ in range(n)],[[i,j] for i in range(n) for j in range(i+1,n) if rng.randrange(3)==0]])
    elif pid==3913:
        args=[[''.join(rng.choice('aeioubcdf') for _ in range(rng.randrange(1,100)))] for _ in range(150)]+[['uoiea'],['leetcode']]
    elif pid==3914:args=[[[*v]] for n in range(1,5) for v in itertools.product([1,2,3],repeat=n)]
    elif pid==3915:
        args=[[[*v],k] for n in range(1,6) for v in itertools.product([1,2,3],repeat=n) for k in range(1,n+1)]
        args += [[[rng.randrange(1,100001) for _ in range(14)],rng.randrange(1,15)] for _ in range(20)]
    elif pid==3918:args=[[n] for n in range(1,1001)]
    elif pid==3919:
        for _ in range(100):
            n=rng.randrange(2,16);nums=sorted(rng.sample(range(-100,101),n));args.append([nums,[[i,j] for i in range(n) for j in range(n)]])
    elif pid==3926:
        args=[[['a-b a--b ','a-','b'],['a-b','a','b']],[['-cat dog- mouse'],['cat','dog','mouse','cat-dog']]]
        for _ in range(100):
            s=''.join(rng.choice('abc --') for _ in range(rng.randrange(1,100)));cuts=sorted(set([0,len(s)]+[rng.randrange(len(s)+1) for _ in range(8)]));args.append([[s[a:b] for a,b in zip(cuts,cuts[1:])],['a','b','c','a-b','ab','abc','a-b-c']])
    elif pid==3932:args=[[l,r,k] for l,r in [(0,0),(0,1),(0,100),(1,9),(8,30),(9990,10000)] for k in range(1,31)]
    elif pid==3934:args=[[[*v]] for n in range(1,9) for v in itertools.product([1,2],repeat=n)]+[[[rng.randrange(1,10) for _ in range(50)]] for _ in range(50)]
    elif pid==3937:args=[[[rng.randrange(1,1000000001) for _ in range(rng.randrange(1,20))],k] for k in range(2,16) for _ in range(15)]
    elif pid==3941:args=[[''.join(rng.choice('abcABC012!@#$') for _ in range(rng.randrange(1,100)))] for _ in range(100)]
    elif pid==3942:args=[[[*v]] for n in range(1,7) for v in itertools.permutations(range(n))]
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if include_maximum:
        extra=[]
        if pid==3909:extra=[([list(range(1,50001))+[100000]+list(range(49999,0,-1))],0)]
        if pid==3910:extra=[([[0]*13,[[i,j] for i in range(13) for j in range(i+1,13)]],8191),([[1]*13,[[i,j] for i in range(13) for j in range(i+1,13)]],4095)]
        if pid==3913:extra=[(['a'*100000],'a'*100000)]
        if pid==3914:extra=[([[10**9,1]*50000],49999999950000)]
        if pid==3915:extra=[([[1,100000]*50000,1],5000050000),([[1]*100000,100000],1)]
        if pid==3918:extra=[([1000],76127)]
        if pid==3919:extra=[([list(range(100000)),[[0,99999],[99999,0]]],[99999,99999])]
        if pid==3926:extra=[([['a-']*50000,['a-'*49999+'a','a']],[1,0])]
        if pid==3932:extra=[([0,10**9,1],1000000001),([0,10**9,30],2)]
        if pid==3934:extra=[([[1]*100000],100000),([[1,2]*50000],99998)]
        if pid==3937:extra=[([[10**9]*100,100],50)]
        if pid==3941:extra=[([('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$'*1516)[:100000]],128)]
        if pid==3942:extra=[([list(range(1,100000))+[0]],3),([list(range(99999,-1,-1))],1)]
        for a,expected in extra:validate_domain(pid,a);rows.append({'args':a,'expected':expected,'category':'analytic-maximum','isolate':True})
    return rows
