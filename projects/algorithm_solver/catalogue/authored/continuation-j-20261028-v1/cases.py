"""Generate private exact expected cases from independent models."""
import itertools
import random
import importlib.util as _importlib_util
from pathlib import Path as _Path
_spec = _importlib_util.spec_from_file_location('gamma_continuation_j_oracles_' + __name__, _Path(__file__).with_name('oracles.py'))
_oracles = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_oracles)
reference = _oracles.reference
validate_domain = _oracles.validate_domain

def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==3819:
        args=[[[*v],k] for n in range(1,5) for v in itertools.product([-1,0,2],repeat=n) for k in [0,1,2,5]]
    elif pid==3820:
        for n in range(4,18):
            for _ in range(6):args.append([n,[[v,rng.randrange(v)] for v in range(1,n)],*rng.sample(range(n),3)])
        args += [[4,[[0,1],[0,2],[0,3]],1,2,3],[4,[[0,1],[1,2],[2,3]],0,3,2]]
    elif pid==3821:args=[[n,k] for k in range(1,8) for n in range(1,10)]+[[50,3],[100,4]]
    elif pid==3824:
        args=[[[*v]] for n in range(1,5) for v in itertools.product([1,3,7],repeat=n)]+[[[rng.randrange(1,101) for _ in range(30)]] for _ in range(60)]
    elif pid==3825:
        args=[[[*v]] for n in range(1,6) for v in itertools.product([0,1,2,3],repeat=n)]+[[[rng.randrange(10**9+1) for _ in range(12)]] for _ in range(30)]
    elif pid==3828:args=[[[*v]] for n in range(1,7) for v in itertools.product([1,2,3],repeat=n)]
    elif pid==3830:
        args=[[[*v]] for n in range(2,7) for v in itertools.product([1,2,3],repeat=n)]
        args += [[[rng.randrange(1,100001) for _ in range(20)]] for _ in range(30)]
    elif pid==3834:args=[[[*v]] for n in range(1,8) for v in itertools.product([1,2,4],repeat=n)]+[[[100000]*80]]
    elif pid==3835:
        args=[[[*v],k] for n in range(1,5) for v in itertools.product([1,2,4],repeat=n) for k in [0,1,4,10]]
        args += [[[rng.randrange(1,10**9+1) for _ in range(30)],rng.randrange(10**15)] for _ in range(30)]
    elif pid==3836:
        for n in range(1,7):
            for m in range(1,7):
                for _ in range(3):args.append([[rng.randrange(-9,10) for _ in range(n)],[rng.randrange(-9,10) for _ in range(m)],rng.randrange(1,min(n,m)+1)])
        args += [[[-10**6]*9,[10**6]*9,9],[[1,3,2],[4,5,1],2]]
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if include_maximum:
        extra=[]
        if pid==3819:extra=[([[-1,0]*50000,100000],[-1,0]*50000)]
        if pid==3820:extra=[([100000,[[0,v] for v in range(1,100000)],1,2,3],3)]
        if pid==3821:extra=[([50,1],2**49),([1,50],2**50-1)]
        if pid==3824:extra=[([[100000]*100000],2168)]
        if pid==3825:extra=[([[0]*100000],0),([list(range(1,100001,2))],50000)]
        if pid==3828:extra=[([[1]+[100000]*99998+[2]],2)]
        if pid==3830:extra=[([[1,2]*50000],100000),([[1]*100000],1)]
        if pid==3834:extra=[([[100000]*65536],[6553600000])]
        if pid==3835:extra=[([[10**9]*100000,0],5000050000),([[1,10**9]*50000,0],100000)]
        if pid==3836:extra=[([[10**6]*100,[10**6]*100,100],10**14),([[-10**6]*100,[10**6]*100,100],-10**14)]
        for a,expected in extra:validate_domain(pid,a);rows.append({'args':a,'expected':expected,'category':'analytic-maximum','isolate':True})
    return rows
