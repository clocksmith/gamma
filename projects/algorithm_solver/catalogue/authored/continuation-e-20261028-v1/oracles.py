"""Independent source-free bounded references; full domains are separate from work bounds."""
from collections import Counter,deque
from itertools import permutations,product,combinations
import random

IDS=(3723,3724,3727,3728,3729,3732,3734,3737,3738,3739)


def integer(v,lo,hi):return type(v) is int and lo<=v<=hi


def array(v,lo,hi,minimum,maximum):return type(v) is list and minimum<=len(v)<=maximum and all(integer(x,lo,hi) for x in v)


def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:raise ValueError('fixed exact identity and ordered args')
    arity=1 if pid in (3727,3728,3732,3738) else 2
    if len(args)!=arity:raise ValueError('argument count')
    a=args[0]
    if pid==3723:ok=integer(a,1,200000) and integer(args[1],1,2000000)
    elif pid==3724:ok=array(a,1,100000,1,100000) and array(args[1],1,100000,len(a)+1,len(a)+1)
    elif pid==3727:ok=array(a,-40000,40000,1,100000)
    elif pid==3728:ok=array(a,-10**9,10**9,3,100000)
    elif pid==3729:ok=array(a,1,10**9,1,100000) and all(x<=y for x,y in zip(a,a[1:])) and integer(args[1],1,10**9)
    elif pid==3732:ok=array(a,-100000,100000,3,100000)
    elif pid==3734:ok=type(a) is str and 1<=len(a)<=300 and all('a'<=c<='z' for c in a) and type(args[1]) is str and len(args[1])==len(a) and all('a'<=c<='z' for c in args[1])
    elif pid in (3737,3739):ok=array(a,1,10**9,1,1000 if pid==3737 else 100000) and integer(args[1],1,10**9)
    else:ok=array(a,-10**9,10**9,1,100000)
    if not ok:raise ValueError('outside full pinned official domain')


def expected(pid,args):
    validate(pid,args)
    a=args[0]
    if pid==3723:
        digits,total=args
        if total>9*digits:return ''
        if total==9*digits:return '9'*digits
        if digits>5:raise ValueError('full decimal digit tuple budget')
        best=None
        for row in product(range(10),repeat=digits):
            if not row[0] or sum(row)!=total:continue
            key=(sum(x*x for x in row),row)
            if best is None or key>best:best=key
        return '' if best is None else ''.join(map(str,best[1]))
    if pid==3724:
        start,target=map(tuple,args)
        if len(start)==1:
            x,y=start[0],target[0];z=target[-1]
            #Convex piecewise-linear path cost changes slope only at x,y,z.
            return 1+min(abs(x-copy)+abs(copy-y)+abs(copy-z) for copy in (x,y,z))
        if len(start)>3 or max(start+target)>9:raise ValueError('complete unit-operation array-state budget')
        low,high=min(start+target),max(start+target)
        queue=deque([(start,0)]);seen={start}
        while queue:
            state,d=queue.popleft()
            if state==target:return d
            moves=[]
            for i,x in enumerate(state):
                for step in (-1,1):
                    if low<=x+step<=high:moves.append(state[:i]+(x+step,)+state[i+1:])
            if len(state)<len(target):moves.extend(state+(x,) for x in state)
            for row in moves:
                if row not in seen:seen.add(row);queue.append((row,d+1))
    if pid==3727:
        if len(a)>8:raise ValueError('all permutation score budget')
        return max(sum((1 if i%2==0 else -1)*v*v for i,v in enumerate(row)) for row in permutations(a))
    if pid==3728:
        if len(a)>80:raise ValueError('all interval interior sum budget')
        return sum(a[l]==a[r]==sum(a[l+1:r]) for l in range(len(a)) for r in range(l+2,len(a)))
    if pid==3729:
        k=args[1]
        if len(a)>60:raise ValueError('literal subarray sequence set budget')
        return len({tuple(a[l:r]) for l in range(len(a)) for r in range(l+1,len(a)+1) if sum(a[l:r])%k==0})
    if pid==3732:
        if len(a)>10:raise ValueError('all replacement endpoints and index triples budget')
        best=-10**30
        for i in range(len(a)):
            for v in (-100000,100000):
                row=a[:];row[i]=v
                best=max(best,max(row[x]*row[y]*row[z] for x,y,z in combinations(range(len(row)),3)))
        return best
    if pid==3734:
        target=args[1];counts=Counter(a)
        if sum(v%2 for v in counts.values())>1:return ''
        if len(counts)==1:return a if a>target else ''
        if len(a)>8:raise ValueError('full permutation/palindrome filter budget')
        return min((''.join(row) for row in set(permutations(a)) if row==row[::-1] and ''.join(row)>target),default='')
    if pid in (3737,3739):
        target=args[1]
        if all(x==target for x in a):return len(a)*(len(a)+1)//2
        if target not in a:return 0
        if len(a)>60:raise ValueError('literal subarray majority count budget')
        return sum(a[l:r].count(target)*2>r-l for l in range(len(a)) for r in range(l+1,len(a)+1))
    if len(set(a))==1:return len(a)
    if len(a)>14:raise ValueError('all relevant replacement values and intervals budget')
    best=1
    for i in range(len(a)):
        #Any feasible interval of replacement values contains a neighbor value;
        #the complete input value set therefore supplies an optimum witness.
        for v in set(a):
            row=a[:];row[i]=v;run=0;previous=None
            for x in row:
                run=run+1 if previous is not None and previous<=x else 1
                best=max(best,run);previous=x
    return best


def matches(pid,args,answer,wanted=None):
    want=expected(pid,args)
    return type(answer) is type(want) and answer==want


PUBLIC_EXAMPLES={3723:[([2,3],'30'),([2,17],'98'),([1,10],'')],3724:[([[2,8],[1,7,3]],4),([[1,3,6],[2,4,5,3]],4),([[2],[3,4]],3)],3727:[([[1,2,3]],12),([[1,-1,2,-2,3,-3]],16)],3728:[([[9,3,3,3,9]],2),([[1,2,3,4,5]],0),([[-4,4,0,0,-8,-4]],1)],3729:[([[1,2,3],3],3),([[2]*6,6],2)],3732:[([[-5,7,0]],3500000),([[-4,-2,-1,-3]],1200000),([[0,10,0]],0)],3734:[(['baba','abba'],'baab'),(['baba','bbaa'],''),(['abc','abb'],''),(['aac','abb'],'aca')],3737:[([[1,2,2,3],2],5),([[1]*4,1],10),([[1,2,3],4],0)],3738:[([[1,2,3,1,2]],4),([[2]*5],5)],3739:[([[1,2,2,3],2],5),([[1]*4,1],10),([[1,2,3],4],0)]}


def build_cases(pid):
    if type(pid) is not int or pid not in IDS:raise ValueError('fixed identity')
    rng=random.Random(202610280000+pid);rows=[];seen=set()
    import json
    def add(args,category,wanted=None):
        validate(pid,args);key=json.dumps(args,separators=(',',':'))
        if key in seen:return
        seen.add(key);want=expected(pid,args)
        if wanted is not None and (type(wanted) is not type(want) or wanted!=want):raise ValueError('public example/reference disagreement')
        rows.append({'args':args,'expected':want,'compare':'return','category':category})
    for args,want in PUBLIC_EXAMPLES[pid]:add(args,'official-numeric-example',want)
    for _ in range(24):
        if pid==3723:
            n=rng.randrange(1,5);args=[n,rng.randrange(1,9*n+5)]
        elif pid==3724:
            n=rng.randrange(1,4);args=[[rng.randrange(1,6) for _ in range(n)],[rng.randrange(1,6) for _ in range(n+1)]]
        elif pid==3727:args=[[rng.randrange(-5,6) for _ in range(rng.randrange(1,8))]]
        elif pid==3728:args=[[rng.randrange(-5,6) for _ in range(rng.randrange(3,16))]]
        elif pid==3729:args=[sorted(rng.randrange(1,8) for _ in range(rng.randrange(1,20))),rng.randrange(1,12)]
        elif pid==3732:args=[[rng.randrange(-10,11) for _ in range(rng.randrange(3,9))]]
        elif pid==3734:
            n=rng.randrange(1,9);args=[''.join(rng.choices('abc',k=n)),''.join(rng.choices('abc',k=n))]
        elif pid in (3737,3739):args=[[rng.randrange(1,5) for _ in range(rng.randrange(1,25))],rng.randrange(1,6)]
        else:args=[[rng.randrange(-10,11) for _ in range(rng.randrange(1,13))]]
        add(args,'seeded-bounded-independent-reference')
    if pid==3723:add([200000,2000000],'maximum-infeasible-digit-sum','');add([200000,1800000],'unique-all-nine-maximum-length','9'*200000)
    elif pid==3724:add([[1],[100000,100000]],'numeric-extreme-unit-path-append',100000)
    elif pid==3727:add([[40000,-40000,0]],'numeric-square-extrema',3200000000)
    elif pid==3728:add([[0]*20],'zero-interior-all-valid-lengths',171)
    elif pid==3729:add([[1000000000]*60,1000000000],'sorted-single-value-distinct-lengths',60)
    elif pid==3732:add([[100000,-100000,100000]],'numeric-triple-product-extreme',10**15)
    elif pid==3734:add(['z'*300,'a'*300],'unique-maximum-length-palindrome','z'*300)
    elif pid in (3737,3739):
        n=1000 if pid==3737 else 100000;add([[10**9]*n,10**9],'maximum-all-target-majority',n*(n+1)//2)
    else:add([[-10**9]*100000],'maximum-uniform-replacement-unnecessary',100000)
    return rows


cases=build_cases
