"""Private case generator with explicit official angle tolerance."""
import importlib.util
from pathlib import Path
import itertools
import random
_spec=importlib.util.spec_from_file_location('gamma_n_case_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain

def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==3891:args=[[[*v]] for n in range(3,6) for v in itertools.product([1,2,3],repeat=n)]
    elif pid==3895:args=[[[rng.randrange(1,10**6+1) for _ in range(30)],d] for d in range(10) for _ in range(10)]+[[[1000000,101010,1],0]]
    elif pid==3896:args=[[[*v]] for n in range(1,5) for v in itertools.product([1,2,3,4,5],repeat=n)]+[[[rng.randrange(1,1001) for _ in range(50)]] for _ in range(30)]
    elif pid==3897:
        for n in range(1,7):
            for _ in range(20):
                pairs=[rng.choice([(0,1),(1,0),(1,1),(2,1),(1,2),(3,0),(0,3),(3,3)]) for _ in range(n)];args.append([[a for a,b in pairs],[b for a,b in pairs]])
    elif pid==3899:args=[[[*v]] for v in itertools.product([1,2,3,5,10,999,1000],repeat=3)]
    elif pid==3900:args=[[''.join(v)] for n in range(1,10) for v in itertools.product('01',repeat=n)]
    elif pid==3901:
        for n in range(2,9):
            for _ in range(20):args.append([[rng.randrange(1,20) for _ in range(n)],rng.randrange(1,8),[[rng.randrange(n),rng.randrange(1,30)] for _ in range(10)]])
        args += [[[6,10,15],1,[[0,6],[1,10],[2,15]]],[[2,3],1,[[0,2],[1,3]]],[[2,2],2,[[0,2]]]]
    elif pid==3904:
        args=[[[*v],k] for n in range(1,5) for v in itertools.product([0,2,5],repeat=n) for k in [0,1,3,5]]
    elif pid==3905:
        for n,m in [(1,1),(1,8),(8,1),(3,3),(5,7)]:
            for _ in range(20):
                cells=rng.sample(range(n*m),rng.randrange(1,n*m+1));args.append([n,m,[[cell//m,cell%m,rng.randrange(1,10**6+1)] for cell in cells]])
        args += [[3,3,[[0,0,1],[2,2,2]]],[3,3,[[0,1,3],[1,1,5]]]]
    elif pid==3906:
        paths=sorted({''.join(v) for v in itertools.permutations('DDDRRR')})
        for path in paths:
            args += [[8,110,path],[123456789,123456800,path],[rng.randrange(1,9*10**15-100),0,path]]
        for row in args:
            if row[1]==0:row[1]=row[0]+rng.randrange(100)
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if pid==3899:
        for row in rows:row['comparison']={'kind':'absolute-finite-float-array','absolute_tolerance':1e-5,'ordered':True}
    if include_maximum:
        extra=[]
        if pid==3891:extra=[([[1]*100000],49999)]
        if pid==3895:extra=[([[1000000]*1000,0],6000)]
        if pid==3896:extra=[([[1,2]*50000],150000)]
        if pid==3897:extra=[([[10000]*20,[0]*20],(pow(2,200000,10**9+7)-1)%(10**9+7)),([[0]*20,[10000]*20],0)]
        if pid==3900:extra=[(['1'+'0'*99998+'1'],4),(['01'*50000],100000)]
        if pid==3901:extra=[([[1]*50000,1,[[i,2] for i in range(50000)]],49999)]
        if pid==3904:extra=[([[10**9]+[0]*99999,0],-1)]
        if pid==3905:extra=[([1,100000,[[0,0,1],[0,99999,2]]],[[1]*50000+[2]*50000])]
        if pid==3906:extra=[([1,9*10**15,'DDDRRR'],11438999999999),([9*10**15,9*10**15,'RRRDDD'],0)]
        for a,expected in extra:validate_domain(pid,a);rows.append({'args':a,'expected':expected,'category':'analytic-maximum','isolate':True})
    return rows
