"""Source-free independent bounded references including official native traces."""
from itertools import product
from collections import deque,Counter
from heapq import heappush,heappop
import random
IDS=(3871,3872,3873,3876,3877,3878,3881,3885,3889,3890)
MOD=1000000007

def integer(x,l,h):return type(x) is int and l<=x<=h

def array(x,l,h,mn,mx):return type(x) is list and mn<=len(x)<=mx and all(integer(v,l,h) for v in x)

def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b

def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=(3 if pid==3881 else 2 if pid in (3877,3885) else 1):raise ValueError('Fixed identity and ordered args')
    a=args[0]
    if pid==3871:ok=integer(a,1,10**15)
    elif pid==3872:ok=array(a,1,100000,4,100000)
    elif pid==3873:ok=type(a) is list and 1<=len(a)<=100000 and all(array(p,-10**9,10**9,2,2) for p in a) and len({tuple(p) for p in a})==len(a)
    elif pid==3876:ok=array(a,1,10**9,1,100000) and len(set(a))==len(a)
    elif pid==3877:ok=array(a,0,10000,1,40) and integer(args[1],0,10000)
    elif pid==3878:ok=array(a,0,10**9,1,100000)
    elif pid==3881:ok=integer(a,1,100000) and integer(args[1],0,a-1) and integer(args[2],0,a-1)
    elif pid==3885:
        operations,rows=args
        ok=type(operations) is list and type(rows) is list and 1<=len(operations)<=100001 and len(rows)==len(operations) and operations[0]=='EventManager' and type(rows[0]) is list and len(rows[0])==1
        if ok:
            events=rows[0][0];ok=type(events) is list and 1<=len(events)<=100000 and all(array(e,1,10**9,2,2) for e in events) and len({e[0] for e in events})==len(events)
        if ok:
            active=dict(events);heap=[(-p,i) for i,p in events];from heapq import heapify;heapify(heap)
            for operation,row in zip(operations[1:],rows[1:]):
                if type(operation) is not str or type(row) is not list:ok=False;break
                if operation=='updatePriority':
                    if not array(row,1,10**9,2,2) or row[0] not in active:ok=False;break
                    active[row[0]]=row[1];heappush(heap,(-row[1],row[0]))
                elif operation=='pollHighest':
                    if row:ok=False;break
                    while heap:
                        p,i=heappop(heap)
                        if active.get(i)==-p:del active[i];break
                else:ok=False;break
    elif pid==3889:ok=type(a) is str and 1<=len(a)<=500000 and set(a)<=set('abcdefghijklmnopqrstuvwxyz0123456789')
    else:ok=integer(a,1,10**9)
    if not ok:raise ValueError('Outside exact official domain')

def expected(pid,args):
    validate(pid,args);a=args[0]
    if pid==3871:
        return sum(max(0,min(a,10**d-1)-10**(d-1)+1)*((d-1)//3) for d in range(1,17))
    if pid==3872:
        if all(a[i]-a[i-1]==a[1]-a[0] for i in range(2,len(a))):return len(a)
        if len(a)>18:raise ValueError('Arithmetic interpolation reference budget')
        answer=2
        for l in range(len(a)):
            for r in range(l+2,len(a)+1):
                for changed in range(l,r):
                    fixed=[i for i in range(l,r) if i!=changed]
                    if len(fixed)<2:answer=max(answer,r-l);continue
                    i,j=fixed[:2];gap=a[j]-a[i]
                    if gap%(j-i):continue
                    d=gap//(j-i)
                    if all(a[t]==a[i]+(t-i)*d for t in fixed):answer=max(answer,r-l)
        return answer
    if pid==3873:
        if len(a)>12:
            if len({x for x,y in a})==1 or len({y for x,y in a})==1:return len(a)+1
            if len({x for x,y in a})==len(a) and len({y for x,y in a})==len(a):return min(2,len(a))+1
            raise ValueError('Added-point activation reference budget')
        points=set(map(tuple,a));xs={x for x,y in a};ys={y for x,y in a};xs.add(max(xs)+1);ys.add(max(ys)+1);best=1
        for x,y in product(xs,ys):
            if (x,y) in points:continue
            active={(x,y)};pending=[(x,y)]
            while pending:
                u,v=pending.pop()
                for p in points-active:
                    if p[0]==u or p[1]==v:active.add(p);pending.append(p)
            best=max(best,len(active))
        return best
    if pid==3876:
        if len(a)>300:
            if len({x%2 for x in a})==1:return True
            raise ValueError('Per-position allowed parity enumeration budget')
        common={0,1}
        for i,x in enumerate(a):common&={x%2}|{(x-y)%2 for j,y in enumerate(a) if i!=j and x-y>=1}
        return bool(common)
    if pid==3877:
        target=args[1]
        if len(set(a))==1:
            x=a[0]
            return next((removed for removed in range(len(a)+1) if (x if (len(a)-removed)%2 else 0)==target),-1)
        if len(a)>18:raise ValueError('XOR subset enumeration budget')
        best=len(a)+1
        for mask in range(1<<len(a)):
            value=0
            for i,x in enumerate(a):
                if mask>>i&1:value^=x
            if value==target:best=min(best,len(a)-mask.bit_count())
        return -1 if best>len(a) else best
    if pid==3878:
        if len(a)>100:
            if len(set(a))==1:return len(a)*(len(a)+1)//2
            raise ValueError('Literal OR interval reference budget')
        answer=0
        for l in range(len(a)):
            for r in range(l,len(a)):
                value=0
                for x in a[l:r+1]:value|=x
                answer+=value in a[l:r+1]
        return answer
    if pid==3881:
        n,pos,k=args
        if n>16:
            if k in (0,n-1):return 2
            if k in (1,n-2):return 2*(n-1)%MOD
            raise ValueError('Direction assignment reference budget')
        return sum(sum((i<pos and d=='L') or (i>pos and d=='R') for i,d in enumerate(directions))==k for directions in product('LR',repeat=n))%MOD
    if pid==3885:
        events=args[1][0][0]
        if len(events)*len(a)>1000000:raise ValueError('Literal active-event scan reference budget')
        active=dict(events);out=[None]
        for operation,row in zip(a[1:],args[1][1:]):
            if operation=='updatePriority':active[row[0]]=row[1];out.append(None)
            elif active:
                chosen=min(active,key=lambda event:(-active[event],event));out.append(chosen);del active[chosen]
            else:out.append(-1)
        return out
    if pid==3889:
        letters='abcdefghijklmnopqrstuvwxyz';digits='0123456789';pairs=set()
        for c in set(a):
            alphabet=digits if c in digits else letters;m=alphabet[-1-alphabet.index(c)];pairs.add(tuple(sorted((c,m))))
        return sum(abs(a.count(x)-a.count(y)) for x,y in pairs)
    # Sorted k-way merging of cube-sum rows, independent of candidate hash counts.
    heap=[];x=1
    while 2*x**3<=a:heappush(heap,(2*x**3,x,x));x+=1
    answer=[];previous=None;ways=0
    while heap:
        total,x,y=heappop(heap)
        if total!=previous:
            if ways>=2:answer.append(previous)
            previous=total;ways=0
        ways+=1;y+=1
        if x**3+y**3<=a:heappush(heap,(x**3+y**3,x,y))
    if ways>=2:answer.append(previous)
    return answer

def matches(pid,args,result,wanted=None):
    if wanted is None:wanted=expected(pid,args)
    return exact(result,wanted)

PUBLIC_EXAMPLES={3871:[([1002],3),([998],0)],3872:[([[9,7,5,10,1]],5),([[1,2,6,7]],3)],3873:[([[[1,1],[1,2],[2,2]]],4),([[[2,2],[1,1],[3,3]]],3),([[[2,3],[2,2],[1,1],[4,5]]],4)],3876:[([[1,4,7]],True),([[2,3]],False),([[4,6]],True)],3877:[([[1,2,3],2],1),([[2,4],1],-1),([[7],7],0)],3878:[([[4,2,3]],4),([[1,3,1]],6)],3881:[([3,1,0],2),([3,2,1],4),([1,0,0],2)],3885:[([['EventManager','pollHighest','updatePriority','pollHighest','pollHighest'],[[[[5,7],[2,7],[9,4]]],[],[9,7],[],[]]],[None,2,None,5,9]),([['EventManager','pollHighest','pollHighest','pollHighest'],[[[[4,1],[7,2]]],[],[],[]]],[None,7,4,-1])],3889:[(['ab1z9'],3),(['4m7n'],2),(['byby'],0)],3890:[([4104],[1729,4104]),([578],[])]}

def build_cases(pid):
    rng=random.Random(20261028+pid);rows=[{'args':args,'expected':value,'tag':'public example'} for args,value in PUBLIC_EXAMPLES[pid]];generated=[]
    for _ in range(24):
        n=rng.randint(1,8)
        if pid==3871:args=[rng.randint(1,10**15)]
        elif pid==3872:args=[[rng.randint(1,20) for _ in range(max(4,n))]]
        elif pid==3873:args=[list(map(list,rng.sample([(x,y) for x in range(4) for y in range(4)],n)))]
        elif pid==3876:args=[rng.sample(range(1,30),n)]
        elif pid==3877:args=[[rng.randint(0,15) for _ in range(n)],rng.randint(0,15)]
        elif pid==3878:args=[[rng.randint(0,31) for _ in range(n)]]
        elif pid==3881:args=[n,rng.randrange(n),rng.randrange(n)]
        elif pid==3885:
            events=[[i+1,rng.randint(1,8)] for i in range(n)];active=dict(events);operations=['EventManager'];params=[[events]]
            for _ in range(14):
                if active and rng.randrange(2):
                    i=rng.choice(list(active));p=rng.randint(1,8);active[i]=p;operations.append('updatePriority');params.append([i,p])
                else:
                    operations.append('pollHighest');params.append([])
                    if active:del active[min(active,key=lambda i:(-active[i],i))]
            args=[operations,params]
        elif pid==3889:args=[''.join(rng.choice('abmyz0198') for _ in range(n))]
        else:args=[rng.randint(1,100000)]
        generated.append(args)
    edges={3871:[[1],[999],[1000],[999999],[10**15]],3872:[[[5]*100000],[list(range(1,100001))],[[1,3,8,7,9]]],3873:[[[[i,i] for i in range(100000)]],[[[0,i] for i in range(100000)]]],3876:[[list(range(1,200000,2))],[list(range(2,200001,2))]],3877:[[[0]*40,0],[[10000]*40,10000],[[10000]*40,9999]],3878:[[[10**9]*100000],[[0]*100000]],3881:[[100000,0,0],[100000,99999,99999],[100000,50000,1]],3885:[[['EventManager','updatePriority','updatePriority','pollHighest','pollHighest','pollHighest'],[[[[2,10],[1,10]]],[1,1],[1,10],[],[],[]]],[['EventManager','pollHighest'],[[[[i+1,10**9] for i in range(100000)]],[]]]],3889:[['a'*500000],['az'*250000],['09'*250000]],3890:[[1],[1728],[1729],[10**9]]}[pid]
    seen={repr(row['args']) for row in rows}
    for args in generated+edges:
        key=repr(args)
        if key not in seen:seen.add(key);rows.append({'args':args,'expected':expected(pid,args),'tag':'seeded independent reference or boundary'})
    return rows
cases=build_cases
