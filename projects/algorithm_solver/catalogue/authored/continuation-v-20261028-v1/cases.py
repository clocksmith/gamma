"""V HOST-ONLY fixtures. NEVER copy host_api_fixture/expected into child input.
No API proxy/child harness is implemented here; reviewed profiles remain pending.
"""
import importlib.util
import json
from pathlib import Path
from itertools import product
import random
S=importlib.util.spec_from_file_location('gamma_v_cases_oracles',Path(__file__).with_name('oracles.py'));o=importlib.util.module_from_spec(S);S.loader.exec_module(o)
IDS=o.IDS

def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def build_cases():
    rng=random.Random(2026102833);data={pid:[] for pid in IDS};seen={pid:set() for pid in IDS}
    def add(pid,args,fixture,category):
        key=encoded([args,fixture])
        if key in seen[pid]:return
        seen[pid].add(key);row={'args':args,'expected':o.expected(pid,args,fixture),'category':category}
        if fixture is not None:row['host_api_fixture']=fixture
        data[pid].append(row)
    for n in range(10000):add(273,[n],None,'exhaustive-canonical-English-small')
    for n in (10000,10001,100000,100001,1000000,1000001,1001000,1000000000,1000000001,2**31-1):add(273,[n],None,'scale-boundary-English')
    for _ in range(128):add(273,[rng.randrange(2**31)],None,'seeded-full-int32-English')
    for n in range(1,65):
        for bad in range(1,n+1):add(278,[n],{'first_bad':bad},'all-small-monotone-oracle-boundaries')
    for exponent in range(1,32):
        for n in (2**exponent-1,2**exponent,2**exponent+1):
            if n>2**31-1:continue
            for bad in (1,n,(n+1)//2):add(278,[n],{'first_bad':bad},'oracle-overflow-and-log-budget-boundary')
    for _ in range(64):
        n=rng.randint(1,2**31-1);add(278,[n],{'first_bad':rng.randint(1,n)},'seeded-large-host-oracle')
    marker=o.ITERATOR_MARKER
    for n in range(1,4):
        for values in product((1,2),repeat=n):
            for calls in range(5):
                for ops in product(('peek','next','hasNext'),repeat=calls):
                    cursor=0
                    for op in ops:
                        if op in ('peek','next') and cursor>=n:break
                        cursor+=op=='next'
                    else:add(284,[['PeekingIterator',*ops],[[marker]]+[[] for _ in ops]],{'iterator0':list(values)},'exhaustive-valid-small-opaque-iterator-traces')
    for _ in range(32):
        n=rng.randint(1,1000);values=[rng.randint(1,1000) for _ in range(n)];ops=['PeekingIterator'];rows=[[marker]];cursor=0
        for _ in range(1000):
            op=rng.choice(('peek','next','hasNext')) if cursor<n else 'hasNext';ops.append(op);rows.append([]);cursor+=op=='next'
        add(284,[ops,rows],{'iterator0':values},'maximum1000-calls-opaque-interface')
    for n in (1,999,1000):
        values=list(range(1,n+1));ops=['next']*n+(['hasNext'] if n<1000 else[]);add(284,[['PeekingIterator',*ops],[[marker]]+[[] for _ in ops]],{'iterator0':values},'opaque-exhaustion-and-max-values')
    return data
