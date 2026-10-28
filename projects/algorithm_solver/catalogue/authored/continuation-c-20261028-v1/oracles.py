"""Independent bounded references frozen before candidate authoring; no candidate imports."""
from collections import Counter, deque
from functools import lru_cache
from itertools import combinations, product
import random

IDS=(3675,3679,3689,3690,3691,3693,3694,3698,3699,3700)
MOD=1000000007


def integer(v,lo,hi):return type(v) is int and lo<=v<=hi


def array(v,lo,hi,minimum,maximum):return type(v) is list and minimum<=len(v)<=maximum and all(integer(x,lo,hi) for x in v)


def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:raise ValueError('fixed exact identity and argument list')
    arity={3675:1,3679:3,3689:2,3690:2,3691:2,3693:2,3694:2,3698:1,3699:3,3700:3}[pid]
    if len(args)!=arity:raise ValueError('argument count')
    if pid==3675:ok=type(args[0]) is str and 1<=len(args[0])<=500000 and all('a'<=c<='z' for c in args[0])
    elif pid==3679:ok=array(args[0],1,100000,1,100000) and integer(args[1],1,len(args[0])) and integer(args[2],1,args[1])
    elif pid in (3689,3691):ok=array(args[0],0,10**9,1,50000) and integer(args[1],1,100000 if pid==3689 else min(100000,len(args[0])*(len(args[0])+1)//2))
    elif pid==3690:ok=array(args[0],-100000,100000,2,6) and array(args[1],-100000,100000,len(args[0]),len(args[0])) and Counter(args[0])==Counter(args[1])
    elif pid==3693:ok=integer(args[0],1,100000) and array(args[1],1,10000,args[0],args[0])
    elif pid==3694:ok=type(args[0]) is str and 1<=len(args[0])<=100000 and set(args[0])<=set('UDLR') and integer(args[1],1,len(args[0]))
    elif pid==3698:ok=array(args[0],1,100000,2,100000)
    else:ok=integer(args[0],3,2000 if pid==3699 else 10**9) and integer(args[1],1,1999 if pid==3699 else 74) and integer(args[2],args[1]+1,2000 if pid==3699 else 75)
    if not ok:raise ValueError('outside complete pinned official domain')


def expected(pid,args):
    validate(pid,args)
    if pid==3675:
        s=args[0];letters=set(s)
        if len(letters)>3:raise ValueError('explicit letter-state BFS budget')
        mask=sum(1<<(ord(c)-97) for c in letters);queue=deque([(mask,0)]);seen={mask}
        while queue:
            state,d=queue.popleft()
            if state==1:return d
            for c in range(26):
                if state>>c&1:
                    nxt=(state^(1<<c))|(1<<((c+1)%26))
                    if nxt not in seen:seen.add(nxt);queue.append((nxt,d+1))
    if pid==3679:
        a,w,m=args;n=len(a)
        if n>14:raise ValueError('all keep/discard subsets budget')
        best=0
        for mask in range(1<<n):
            if mask.bit_count()<=best:continue
            valid=True
            for end in range(n):
                counts=Counter(a[i] for i in range(max(0,end-w+1),end+1) if mask>>i&1)
                if any(v>m for v in counts.values()):valid=False;break
            if valid:best=mask.bit_count()
        return n-best
    if pid in (3689,3691):
        a,k=args
        if len(a)>40:raise ValueError('all distinct subarray values budget')
        values=[max(a[l:r])-min(a[l:r]) for l in range(len(a)) for r in range(l+1,len(a)+1)]
        if pid==3689:
            # Literal selection with replacement, after enumerating all subarray values.
            return sum(max(values) for _ in range(k))
        return sum(sorted(values,reverse=True)[:k])
    if pid==3690:
        start,target=map(tuple,args)
        # Adjacent block rotations, independently expressed without remove/reinsert.
        queue=deque([(start,0)]);seen={start};n=len(start)
        while queue:
            state,d=queue.popleft()
            if state==target:return d
            for a,b,c in combinations(range(n+1),3):
                nxt=state[:a]+state[b:c]+state[a:b]+state[c:]
                if nxt not in seen:seen.add(nxt);queue.append((nxt,d+1))
    if pid==3693:
        n,costs=args
        if n>18:raise ValueError('all legal staircase paths budget')
        @lru_cache(None)
        def paths(i):
            if i==n:return 0
            return min(costs[j-1]+(j-i)**2+paths(j) for j in range(i+1,min(n,i+3)+1))
        return paths(0)
    if pid==3694:
        s,k=args
        if len(s)>200:raise ValueError('literal deletion and simulation budget')
        points=set()
        for i in range(len(s)-k+1):
            x=y=0
            for c in s[:i]+s[i+k:]:
                if c=='U':y+=1
                elif c=='D':y-=1
                elif c=='L':x-=1
                else:x+=1
            points.add((x,y))
        return len(points)
    if pid==3698:
        a=args[0]
        if len(a)>200:raise ValueError('literal split verification budget')
        differences=[]
        for k in range(1,len(a)):
            if all(a[i]<a[i+1] for i in range(k-1)) and all(a[i]>a[i+1] for i in range(k,len(a)-1)):
                differences.append(abs(sum(a[:k])-sum(a[k:])))
        return min(differences,default=-1)
    n,l,r=args;width=r-l+1
    if width==2:return 2  #Only the two alternating strings; valid for full length domain.
    if n>8 or width**n>500000:raise ValueError('literal zigzag array enumeration budget')
    total=0
    for a in product(range(l,r+1),repeat=n):
        if any(a[i]==a[i+1] for i in range(n-1)):continue
        if any(a[i]<a[i+1]<a[i+2] or a[i]>a[i+1]>a[i+2] for i in range(n-2)):continue
        total+=1
    return total%MOD


def matches(pid,args,answer,wanted=None):
    value=expected(pid,args)
    return type(answer) is type(value) and answer==value


PUBLIC_EXAMPLES={3675:[(['yz'],2),(['a'],0)],3679:[([[1,2,1,3,1],4,2],0),([[1,2,3,3,3,4],3,2],1)],3689:[([[1,3,2],2],4),([[4,2,5,1],3],12)],3690:[([[3,1,2],[1,2,3]],1),([[1,1,2,3,4,5],[5,4,3,2,1,1]],3)],3691:[([[1,3,2],2],4),([[4,2,5,1],3],12)],3693:[([4,[1,2,3,4]],13),([4,[5,1,6,2]],11),([3,[9,8,3]],12)],3694:[(['LUL',1],2),(['UDLR',4],1),(['UU',1],1)],3698:[([[1,3,2]],2),([[1,2,4,3]],4),([[3,1,2]],-1)],3699:[([3,4,5],2),([3,1,3],10)],3700:[([3,4,5],2),([3,1,3],10)]}


def build_cases(pid):
    if type(pid) is not int or pid not in IDS:raise ValueError('fixed identity')
    rng=random.Random(20261028000+pid);out=[];seen=set()
    import json
    def add(args,category,want=None):
        validate(pid,args);key=json.dumps(args,separators=(',',':'))
        if key in seen:return
        seen.add(key);value=expected(pid,args)
        if want is not None and (type(want) is not type(value) or want!=value):raise ValueError('official example/reference disagreement')
        out.append({'args':args,'expected':value,'compare':'return','category':category})
    for args,want in PUBLIC_EXAMPLES[pid]:add(args,'official-numeric-example',want)
    for _ in range(30):
        if pid==3675:args=[''.join(rng.choices(rng.sample('abcxyz',rng.randrange(1,4)),k=rng.randrange(1,8)))]
        elif pid==3679:
            n=rng.randrange(1,11);w=rng.randrange(1,n+1);args=[[rng.randrange(1,5) for _ in range(n)],w,rng.randrange(1,w+1)]
        elif pid in (3689,3691):
            n=rng.randrange(1,12);args=[[rng.randrange(20) for _ in range(n)],rng.randrange(1,20 if pid==3689 else min(20,n*(n+1)//2)+1)]
        elif pid==3690:
            a=[rng.randrange(-2,4) for _ in range(rng.randrange(2,7))];b=a[:];rng.shuffle(b);args=[a,b]
        elif pid==3693:
            n=rng.randrange(1,15);args=[n,[rng.randrange(1,30) for _ in range(n)]]
        elif pid==3694:
            n=rng.randrange(1,20);args=[''.join(rng.choices('UDLR',k=n)),rng.randrange(1,n+1)]
        elif pid==3698:args=[[rng.randrange(1,20) for _ in range(rng.randrange(2,20))]]
        else:
            n=rng.randrange(3,7);l=rng.randrange(1,4);args=[n,l,l+rng.randrange(1,4)]
        add(args,'seeded-bounded-independent-reference')
    if pid==3675:add(['z'*500000],'maximum-length-single-state-cycle',1)
    elif pid==3679:add([[100000]*10,10,1],'bounded-duplicate-windows-numeric-maximum',9)
    elif pid==3689:add([[0,10**9],100000],'maximum-value-times-maximum-repetition',10**14)
    elif pid==3691:add([[0,10**9],3],'all-three-distinct-subarrays',10**9)
    elif pid==3690:add([[-100000,0,100000],[100000,0,-100000]],'extreme-integer-permutation')
    elif pid==3693:add([18,[10000]*18],'bounded-maximum-jump-prices')
    elif pid==3694:add(['UDLR'*50,200],'bounded-entire-string-deletion',1)
    elif pid==3698:add([[100000,100000]],'strict-equality-singleton-sides',0)
    elif pid==3699:add([2000,1999,2000],'maximum-n-and-values-width-two-certificate',2)
    else:add([10**9,74,75],'maximum-n-and-values-width-two-certificate',2)
    return out


cases=build_cases
