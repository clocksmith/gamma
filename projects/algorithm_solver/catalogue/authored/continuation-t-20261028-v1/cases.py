"""T source-free prospective cases; premium membership retained as exclusions."""
import importlib.util
import json
from pathlib import Path
from itertools import product
import random
S=importlib.util.spec_from_file_location('gamma_t_cases_refs',Path(__file__).with_name('oracles.py'));o=importlib.util.module_from_spec(S);S.loader.exec_module(o)
IDS=o.IDS

def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def linked(values,order=None):
    order=list(range(len(values))) if order is None else order;nexts=[None]*len(values)
    for i,j in zip(order,order[1:]):nexts[i]=j
    return {'values':values,'next':nexts,'head':order[0] if order else None}
def balanced(values):
    n=len(values);left=[None]*n;right=[None]*n
    def build(lo,hi):
        if lo>=hi:return None
        m=(lo+hi)//2;left[m]=build(lo,m);right[m]=build(m+1,hi);return m
    root=build(0,n);return {'values':values,'left':left,'right':right,'root':root}
def chain(values,right=True):
    n=len(values);nexts=[i+1 if i+1<n else None for i in range(n)]
    return {'values':values,'left':[None]*n if right else nexts,'right':nexts if right else [None]*n,'root':0 if n else None}
def build_cases():
    data={pid:[] for pid in IDS};seen={pid:set() for pid in IDS};rng=random.Random(2026102831)
    def add(pid,args,category):
        raw=encoded(args)
        if raw in seen[pid]:return
        seen[pid].add(raw);data[pid].append({'args':args,'expected':o.expected(pid,args),'category':category})
    for n in range(31):add(226,[balanced([i%3-1 for i in range(n)])],'small-original-pool-mirror')
    for right in (False,True):add(226,[chain([i-50 for i in range(100)],right)],'maximum100-skew-mirror')
    for _ in range(48):
        n=rng.randint(1,100);p=balanced([rng.randint(-100,100) for _ in range(n)])
        for i in range(n):
            if rng.randrange(2):p['left'][i],p['right'][i]=p['right'][i],p['left'][i]
        add(226,[p],'seeded-mirror-topology')
    for n in range(1,13):
        for k in range(1,n+1):add(230,[balanced(list(range(n))),k],'exhaustive-small-k')
    for k in (1,5000,10000):add(230,[balanced(list(range(10000))),k],'maximum10000-BST')
    add(230,[chain(list(range(10000))),10000],'maximum-depth-kth-smallest')
    for n in range(7):
        for choices in product(('push','pop'),repeat=n):
            ops=['MyQueue'];rows=[[]];size=0
            for name in choices:
                if name=='pop' and size==0:break
                ops.append(name);rows.append([size%3+1] if name=='push' else[]);size+=(name=='push')-(name=='pop');ops.append('empty');rows.append([])
                if size:ops.append('peek');rows.append([])
            else:add(232,[ops,rows],'exhaustive-valid-small-queue-traces')
    for _ in range(48):
        ops=['MyQueue'];rows=[[]];size=0
        for _ in range(100):
            name=rng.choice(('push','pop','peek','empty')) if size else rng.choice(('push','empty'));ops.append(name);rows.append([rng.randint(1,9)] if name=='push' else[]);size+=(name=='push')-(name=='pop')
        add(232,[ops,rows],'maximum100-stack-only-queue-behavior')
    numbers=list(range(1001))+[rng.randint(0,10**9) for _ in range(128)]
    for exponent in range(1,10):numbers.extend(n for n in (10**exponent-1,10**exponent,10**exponent+1) if n<=10**9)
    for n in numbers:add(233,[n],'decimal-exhaustive-seeded-and-place-boundaries')
    for n in range(1,8):
        for values in product((0,1),repeat=n):add(234,[linked(list(values))],'exhaustive-small-palindrome-restoration')
    for _ in range(32):
        n=rng.randint(1,100);add(234,[linked([rng.randrange(10) for _ in range(n)],rng.sample(range(n),n))],'permuted-original-pool-restoration')
    add(234,[linked([1]*100000)],'maximum100000-palindrome-restoration');add(234,[linked([1]*99999+[2])],'maximum100000-false-still-restored')
    for pid in (235,236):
        for n in range(2,9):
            values=list(range(n)) if pid==235 else rng.sample(range(-100,101),n);p=balanced(values)
            for a in range(n):
                for b in range(n):
                    if a!=b:add(pid,[p,a,b],'exhaustive-original-LCA-objectpairs')
        for _ in range(32):
            n=rng.randint(10,150);values=sorted(rng.sample(range(-100000,100001),n));p=balanced(values)
            if pid==236:
                rng.shuffle(p['values'])
                for i in range(n):
                    if rng.randrange(2):p['left'][i],p['right'][i]=p['right'][i],p['left'][i]
            a,b=rng.sample(range(n),2);add(pid,[p,a,b],'seeded-LCA-originalobjects')
        p=balanced(list(range(-50000,50000)));add(pid,[p,0,99999],'maximum100000-LCA-root');add(pid,[p,p['root'],0],'maximum-LCA-is-actual-root-and-p')
        values=list(range(100000)) if pid==235 else list(range(99999,-1,-1));add(pid,[chain(values),99998,99999],'maximum100000-depth-LCA-no-recursion')
    for n in range(2,11):
        p=linked(list(range(n)))
        for target in range(n-1):add(237,[p,target],'all-small-only-target-deletions')
    for _ in range(32):
        n=rng.randint(2,100);order=rng.sample(range(n),n);target=rng.choice(order[:-1]);add(237,[linked(rng.sample(range(-1000,1001),n),order),target],'permuted-copy-next-identity')
    for target in (0,998):add(237,[linked(list(range(-500,500))),target],'maximum1000-node-only-copy-next')
    return data
