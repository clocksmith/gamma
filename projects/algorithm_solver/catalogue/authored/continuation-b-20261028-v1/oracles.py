"""Source-blind, bounded independent references; not qualification evidence."""
from collections import deque
from functools import lru_cache
from heapq import heappop, heappush
from itertools import combinations, product
from math import prod
import random

IDS = (3650,3651,3652,3653,3655,3659,3660,3661,3666,3669)
MOD = 1000000007
REFERENCE_DESIGN_SHA256 = '67187f529af31b4b660995ced4ebc2dbf64e7c19b8f9c76c2b2a0abd4b98e55e'


def integer(x, low, high):
    return type(x) is int and low <= x <= high


def integers(a, low, high, minimum=1, maximum=100000):
    return type(a) is list and minimum <= len(a) <= maximum and all(integer(x,low,high) for x in a)


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:
        raise ValueError('fixed exact identity and ordered arguments required')
    count = {3650:2,3651:2,3652:3,3653:2,3655:2,3659:2,3660:1,3661:3,3666:2,3669:2}[pid]
    if len(args) != count: raise ValueError('argument count')
    if pid == 3650:
        n, edges = args
        ok = integer(n,2,50000) and type(edges) is list and 1 <= len(edges) <= 100000 and all(type(e) is list and len(e)==3 and integer(e[0],0,n-1) and integer(e[1],0,n-1) and integer(e[2],1,1000) for e in edges)
    elif pid == 3651:
        grid,k=args
        ok = type(grid) is list and 2 <= len(grid) <= 80 and type(grid[0]) is list and 2 <= len(grid[0]) <= 80 and all(integers(row,0,10000,len(grid[0]),len(grid[0])) for row in grid) and integer(k,0,10)
    elif pid == 3652:
        prices,strategy,k=args
        ok = integers(prices,1,100000,2) and integers(strategy,-1,1,len(prices),len(prices)) and integer(k,2,len(prices)) and k%2==0
    elif pid in (3653,3655):
        a,queries=args; maximum=1000 if pid==3653 else 100000
        ok = integers(a,1,10**9,1,maximum) and type(queries) is list and 1 <= len(queries) <= maximum and all(type(q) is list and len(q)==4 and integer(q[0],0,len(a)-1) and integer(q[1],q[0],len(a)-1) and integer(q[2],1,len(a)) and integer(q[3],1,100000) for q in queries)
    elif pid == 3659:
        a,k=args;ok=integers(a,1,100000) and integer(k,1,len(a))
    elif pid == 3660:
        ok=integers(args[0],1,10**9)
    elif pid == 3661:
        robots,distance,walls=args
        ok=integers(robots,1,10**9) and len(set(robots))==len(robots) and integers(distance,1,100000,len(robots),len(robots)) and integers(walls,1,10**9) and len(set(walls))==len(walls)
    elif pid == 3666:
        s,k=args;ok=type(s) is str and 1 <= len(s) <= 100000 and set(s)<=set('01') and integer(k,1,len(s))
    else:
        n,k=args
        ok=integer(n,4,100000) and integer(k,2,5)
        if ok:
            divisors=sum(n%d==0 for d in range(1,int(n**0.5)+1))*2-(int(n**0.5)**2==n)
            ok=k<divisors
    if not ok: raise ValueError('outside pinned complete official domain')


def expected(pid,args):
    validate(pid,args)
    if pid == 3650:
        n,edges=args
        if n>8 or len(edges)>24: raise ValueError('simple-path reference budget')
        adjacency=[[] for _ in range(n)]
        for u,v,w in edges: adjacency[u].append((v,w));adjacency[v].append((u,2*w))
        def visit(u,seen):
            if u==n-1:return 0
            return min((w+visit(v,seen|{v}) for v,w in adjacency[u] if v not in seen),default=float('inf'))
        result=visit(0,{0});return -1 if result==float('inf') else result
    if pid == 3651:
        grid,k=args;m,n=len(grid),len(grid[0])
        if m*n>16 or k>3:raise ValueError('explicit state-graph budget')
        distances={(0,0):0};heap=[(0,0,0)]
        while heap:
            cost,p,t=heappop(heap)
            if distances[p,t]!=cost:continue
            if p==m*n-1:return cost
            i,j=divmod(p,n);moves=[]
            if i+1<m:moves.append((p+n,t,grid[i+1][j]))
            if j+1<n:moves.append((p+1,t,grid[i][j+1]))
            if t<k:
                moves.extend((q,t+1,0) for q in range(m*n) if grid[q//n][q%n]<=grid[i][j])
            for q,u,w in moves:
                if cost+w<distances.get((q,u),float('inf')):distances[q,u]=cost+w;heappush(heap,(cost+w,q,u))
    if pid == 3652:
        prices,strategy,k=args
        if len(prices)>30:raise ValueError('literal interval budget')
        rows=[strategy[:]]
        for start in range(len(prices)-k+1):rows.append(strategy[:start]+[0]*(k//2)+[1]*(k//2)+strategy[start+k:])
        return max(sum(x*y for x,y in zip(prices,row)) for row in rows)
    if pid in (3653,3655):
        a,queries=args
        if len(a)*len(queries)>10000:raise ValueError('index-query incidence budget')
        values=[a[i]*prod(v for l,r,k,v in queries if l<=i<=r and (i-l)%k==0)%MOD for i in range(len(a))]
        result=0
        for v in values:result^=v
        return result
    if pid == 3659:
        a,k=args
        if len(a)>10:raise ValueError('group-placement budget')
        if len(a)%k:return False
        @lru_cache(None)
        def visit(i,groups):
            if i==len(a):return all(len(g)==k for g in groups)
            for j,g in enumerate(groups):
                if len(g)<k and a[i] not in g:
                    nxt=list(groups);nxt[j]=tuple(sorted(g+(a[i],)));nxt=tuple(sorted(nxt))
                    if visit(i+1,nxt):return True
            return False
        return visit(0,tuple(() for _ in range(len(a)//k)))
    if pid == 3660:
        a=args[0];n=len(a)
        if n>30:raise ValueError('all-pair reachability budget')
        out=[]
        for start in range(n):
            seen={start};todo=[start]
            for i in todo:
                for j in range(n):
                    if j not in seen and ((j>i and a[j]<a[i]) or (j<i and a[j]>a[i])):seen.add(j);todo.append(j)
            out.append(max(a[i] for i in seen))
        return out
    if pid == 3661:
        robots,distance,walls=args
        if len(robots)>12 or len(walls)>30:raise ValueError('orientation and obstacle reference budget')
        answer=0
        for directions in product((-1,1),repeat=len(robots)):
            destroyed=set()
            for p,d,direction in zip(robots,distance,directions):
                for wall in walls:
                    if wall==p:destroyed.add(wall)
                    elif 0<(wall-p)*direction<=d and not any(0<(other-p)*direction<(wall-p)*direction for other in robots):destroyed.add(wall)
            answer=max(answer,len(destroyed))
        return answer
    if pid == 3666:
        s,k=args;n=len(s)
        if n>9:raise ValueError('explicit bitmask reference budget')
        mask=sum((c=='1')<<i for i,c in enumerate(s));target=(1<<n)-1;todo=deque([(mask,0)]);seen={mask}
        moves=[sum(1<<i for i in indices) for indices in combinations(range(n),k)]
        while todo:
            mask,d=todo.popleft()
            if mask==target:return d
            for move in moves:
                nxt=mask^move
                if nxt not in seen:seen.add(nxt);todo.append((nxt,d+1))
        return -1
    n,k=args
    if n>1000:raise ValueError('ordered factor enumeration reference budget')
    @lru_cache(None)
    def tuples(value,slots):
        if slots==1:return ((value,),)
        return tuple((factor,)+rest for factor in range(1,value+1) if value%factor==0 for rest in tuples(value//factor,slots-1))
    return min(max(row)-min(row) for row in tuples(n,k))


def accepts(pid,args,answer):
    try:
        validate(pid,args)
    except (ValueError, TypeError, IndexError):
        return False
    if pid == 3669:
        if type(answer) is not list or len(answer)!=args[1] or any(type(v) is not int or v<1 for v in answer) or prod(answer)!=args[0]:return False
        return max(answer)-min(answer)==expected(pid,args)
    wanted=expected(pid,args)
    def equal(a,b):
        return type(a) is type(b) and (len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b)) if type(a) is list else a==b)
    return equal(answer,wanted)


def _seeded_cases(pid):
    rng=random.Random(2026102800+pid);out=[]
    for _ in range(24):
        if pid==3650:
            n=rng.randrange(2,7);args=[n,[[rng.randrange(n),rng.randrange(n),rng.randrange(1,10)] for _ in range(rng.randrange(1,12))]]
        elif pid==3651:args=[[[rng.randrange(7) for _ in range(rng.randrange(2,4))] for _ in range(2)],rng.randrange(3)];args[0]=[row[:2] for row in args[0]]
        elif pid==3652:
            n=rng.randrange(2,10);args=[[rng.randrange(1,20) for _ in range(n)],[rng.randrange(-1,2) for _ in range(n)],2*rng.randrange(1,n//2+1)]
        elif pid in (3653,3655):
            n=rng.randrange(1,15);queries=[]
            for _ in range(rng.randrange(1,15)):
                l=rng.randrange(n);queries.append([l,rng.randrange(l,n),rng.randrange(1,n+1),rng.choice((1,2,99991,100000))])
            args=[[rng.randrange(1,10**9+1) for _ in range(n)],queries]
        elif pid==3659:
            n=rng.randrange(1,9);args=[[rng.randrange(1,5) for _ in range(n)],rng.randrange(1,n+1)]
        elif pid==3660:args=[[rng.randrange(1,8) for _ in range(rng.randrange(1,20))]]
        elif pid==3661:
            n=rng.randrange(1,7);args=[rng.sample(range(1,25),n),[rng.randrange(1,12) for _ in range(n)],rng.sample(range(1,25),rng.randrange(1,12))]
        elif pid==3666:
            n=rng.randrange(1,9);args=[''.join(rng.choices('01',k=n)),rng.randrange(1,n+1)]
        else:args=[rng.choice((12,24,36,60,100)),rng.choice((2,3))]
        out.append({'args':args,'expected':expected(pid,args),'comparison_policy':'optimal-factor-witness' if pid==3669 else 'exact'})
    return out


PUBLIC_NUMERIC_EXAMPLES = {3650: [([4, [[0, 1, 3], [3, 1, 1], [2, 3, 4], [0, 2, 2]]], 5), ([4, [[0, 2, 1], [2, 1, 1], [1, 3, 1], [2, 3, 3]]], 3)], 3651: [([[[1, 3, 3], [2, 5, 4], [4, 3, 5]], 2], 7), ([[[1, 2], [2, 3], [3, 4]], 1], 9)], 3652: [([[4, 2, 8], [-1, 0, 1], 2], 10), ([[5, 4, 3], [1, 1, 0], 2], 9)], 3653: [([[1, 1, 1], [[0, 2, 1, 4]]], 4), ([[2, 3, 1, 5, 4], [[1, 4, 2, 3], [0, 2, 1, 2]]], 31)], 3659: [([[1, 2, 3, 4], 2], True), ([[3, 5, 2, 2], 2], True), ([[1, 5, 2, 3], 3], False)], 3660: [([[2, 1, 3]], [2, 2, 3]), ([[2, 3, 1]], [3, 3, 3])], 3661: [([[4], [3], [1, 10]], 1), ([[10, 2], [5, 1], [5, 2, 7]], 3), ([[1, 2], [100, 1], [10]], 0)], 3666: [(['110', 1], 1), (['0101', 3], 2), (['101', 2], -1)], 3669: [([100, 2], 0), ([44, 3], 9)], 3655: [([[1, 1, 1], [[0, 2, 1, 4]]], 4), ([[2, 3, 1, 5, 4], [[1, 4, 2, 3], [0, 2, 1, 2]]], 31)]}


def cases(pid):
    """Bounded host-only cases: official numeric examples and independent controls.

    For3669 expected is an optimal RANGE scalar, not an arbitrary selected list.
    The runner must separately declare list result type and call accepts().
    No scalar/expected data belongs in candidate packets.
    """
    if type(pid) is not int or pid not in IDS:
        raise ValueError('fixed exact problem identity required')
    controls = {
        3650: [[2,[[0,1,1000]]],[2,[[1,0,1000]]],[2,[[0,0,1]]]],
        3651: [[[[0,0],[0,0]],0],[[[10000,0],[0,10000]],3],[[[10000,10000],[10000,10000]],0]],
        3652: [[[100000]*30,[-1]*30,30],[[1,100000],[1,1],2]],
        3653: [[[1000000000]*20,[[0,19,1,100000]]*20],[[1]*1000,[[0,999,1000,100000]]]],
        3655: [[[1000000000]*20,[[0,19,1,100000]]*20],[[1]*1000,[[0,999,1000,100000]]]],
        3659: [[[100000]*10,1],[[100000]*10,10],[list(range(1,11)),10]],
        3660: [[[1000000000,1,1000000000]],[[1]*30],[list(range(30,0,-1))]],
        3661: [[[1,1000000000],[100000,100000],[1,2,999999999,1000000000]],[[5],[1],[5]]],
        3666: [['0'*9,9],['1'*9,9],['0'+'1'*8,8]],
        3669: [[1000,5],[4,2],[840,5]],
    }
    rows,seen=[],set()
    import json
    def add(args,category,wanted=None):
        validate(pid,args)
        key=json.dumps(args,sort_keys=True,separators=(',',':'))
        if key in seen:return
        seen.add(key)
        result=expected(pid,args)
        if wanted is not None and (type(result) is not type(wanted) or result!=wanted):
            raise ValueError('independent oracle/public example mismatch')
        rows.append({'args':args,'expected':result,'comparison_policy':'optimal-factor-witness' if pid==3669 else 'exact','category':category})
    for args,wanted in PUBLIC_NUMERIC_EXAMPLES[pid]:add(args,'official-numeric-example',wanted)
    for row in _seeded_cases(pid):add(row['args'],'seeded-bounded-independent-reference')
    for args in controls[pid]:add(args,'bounded-domain-and-exact-numeric-edge')
    return rows


def build_cases(pid):
    return cases(pid)
