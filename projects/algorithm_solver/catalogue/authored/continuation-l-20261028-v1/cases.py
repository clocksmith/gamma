"""Private case generation from file-local independent references."""
import importlib.util
from pathlib import Path
import itertools
import random
_spec=importlib.util.spec_from_file_location('gamma_l_case_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain

def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==3855:args=[[l,r,k] for l in range(10) for r in range(l,10) for k in range(1,5)]
    elif pid==3857:args=[[n] for n in range(1,61)]
    elif pid==3858:
        for rows,cols in [(1,1),(1,5),(2,3),(4,3),(6,2)]:
            args += [[[[rng.randrange(1,100001) for _ in range(cols)] for _ in range(rows)]] for _ in range(30)]
    elif pid==3859:
        args=[[[*v],k,m] for n in range(1,6) for v in itertools.product([1,2],repeat=n) for k in range(1,min(n,3)+1) for m in range(1,min(n,3)+1)]
        args += [[[rng.randrange(1,8) for _ in range(30)],rng.randrange(1,8),rng.randrange(1,8)] for _ in range(100)]
    elif pid==3862:
        args=[[[*v]] for n in range(1,6) for v in itertools.product([1,2,3],repeat=n)]+[[[10**9]*100],[[1]*100]]
    elif pid==3863:args=[[''.join(v)] for n in range(1,7) for v in itertools.product('abc',repeat=n)]
    elif pid==3864:
        args=[[''.join(v),enc,flat] for n in range(1,7) for v in itertools.product('01',repeat=n) for enc,flat in [(1,1),(2,9),(9,2)]]
        args += [[''.join(rng.choice('01') for _ in range(16)),rng.randrange(1,100001),rng.randrange(1,100001)] for _ in range(30)]
    elif pid==3867:args=[[[*v]] for n in range(1,6) for v in itertools.product([1,2,3],repeat=n)]+[[[rng.randrange(1,101) for _ in range(30)]] for _ in range(60)]
    elif pid==3868:
        args=[[[*a],[*b]] for n in range(2,4) for a in itertools.product([1,2,3],repeat=n) for b in itertools.product([1,2,3],repeat=n)]
        args += [[[rng.randrange(1,5) for _ in range(6)],[rng.randrange(1,5) for _ in range(6)]] for _ in range(30)]
    elif pid==3869:
        args=[[n,n+50] for n in [1,8,9,90,99,100,1000,12340,123456788]]
        args += [[rng.randrange(1,10**15-100),0] for _ in range(70)]
        for row in args:
            if row[1]==0:row[1]=row[0]+rng.randrange(100)
        args += [[10**15-50,10**15]]
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if include_maximum:
        extra=[]
        if pid==3855:extra=[([0,0,10**9],0),([1,1,10**9],(pow(10,10**9,10**9+7)-1)*pow(9,-1,10**9+7)%(10**9+7))]
        if pid==3857:extra=[([500],124750)]
        if pid==3858:extra=[([[[100000] for _ in range(100000)]],100000)]
        if pid==3859:extra=[([[1]*100000,1,100000],1),([[1]*100000,1,1],5000050000),([[1,2]*50000,2,50000],1)]
        if pid==3862:extra=[([[1]*100000],1),([[10**9]*100000],-1)]
        if pid==3863:extra=[(['z'+'m'*99998+'a'],3),(['a'*100000],0)]
        if pid==3864:extra=[(['0'*100000,100000,100000],100000),(['1'*65536,100000,1],6553600000)]
        if pid==3867:extra=[([[10**9]*100000],5*10**13)]
        if pid==3868:extra=[([[1]*80000,[2]*80000],40000),([[1]*80000,[1]*80000],0)]
        if pid==3869:extra=[([10**15,10**15],1)]
        for a,expected in extra:validate_domain(pid,a);rows.append({'args':a,'expected':expected,'category':'analytic-maximum','isolate':True})
    return rows
