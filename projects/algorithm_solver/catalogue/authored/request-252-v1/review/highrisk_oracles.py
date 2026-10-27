"""Independent bounded development oracles for seven admitted IDs.

Not hidden judge qualification. Expected outputs never sent to candidate runner.
"""
import collections, functools, itertools, json, math, random
from decimal import Decimal, localcontext
SEED=25203539
RNG=random.Random(SEED)
MOD=10**9+7

def palindrome(s,k):
    c=collections.Counter(s); half={x:n//2 for x,n in c.items()}; n=sum(half.values()); ways=math.factorial(n)
    for v in half.values(): ways//=math.factorial(v)
    if k>ways:return ''
    out=[]
    while n:
        for ch in sorted(half):
            if not half[ch]:continue
            count=ways*half[ch]//n
            if k>count:k-=count
            else:out.append(ch);half[ch]-=1;ways=count;n-=1;break
    left=''.join(out);return left+''.join(ch for ch,v in c.items() if v%2)+left[::-1]

def query_product(nums,k,queries):
    nums=nums[:]; out=[]
    for i,v,start,x in queries:
        nums[i]=v;prod=1;count=0
        for val in nums[start:]:
            prod=prod*val%k;count+=prod==x
        out.append(count)
    return out

def magical(m,k,nums):
    total=0
    for seq in itertools.product(range(len(nums)),repeat=m):
        if sum(1<<x for x in seq).bit_count()==k:
            total+=math.prod(nums[x] for x in seq)
    return total%MOD

@functools.lru_cache(None)
def all_matchings(n):
    # Every set of disjoint transpositions, including the empty matching.
    def rec(left):
        if not left:yield ();return
        x=left[0]
        yield from rec(left[1:])
        for j in range(1,len(left)):
            y=left[j]
            for suffix in rec(left[1:j]+left[j+1:]):yield ((x,y),)+suffix
    return tuple(rec(tuple(range(n))))

def segment_transform(a,b):
    best=len(a)
    for reverse in (False,True):
        src=list(a[::-1] if reverse else a)
        for matching in all_matchings(len(a)):
            now=src[:]
            for i,j in matching:now[i],now[j]=now[j],now[i]
            best=min(best,int(reverse)+len(matching)+sum(x!=y for x,y in zip(now,b)))
    return best

def transform(a,b):
    dp=[0]+[len(a)]*len(a)
    for end in range(1,len(a)+1):
        dp[end]=min(dp[start]+segment_transform(a[start:end],b[start:end]) for start in range(end))
    return dp[-1]

def xor_subtrees(par,vals,queries):
    n=len(par); kids=[[] for _ in range(n)]
    for i,p in enumerate(par):
        if p>=0:kids[p].append(i)
    path={0:vals[0]}; todo=[0]
    for u in todo:
        for v in kids[u]:path[v]=path[u]^vals[v];todo.append(v)
    out=[]
    for u,k in queries:
        allnodes=[u]
        for v in allnodes:allnodes.extend(kids[v])
        values=sorted({path[v] for v in allnodes});out.append(values[k-1] if k<=len(values) else -1)
    return out

def spanning(n,edges,k):
    mandatory={i for i,e in enumerate(edges) if e[3]}
    best=-1
    for selected in itertools.combinations(range(len(edges)),n-1):
        if not mandatory.issubset(selected):continue
        visited={0}
        for _ in range(n):
            for i in selected:
                u,v,*_=edges[i]
                if u in visited or v in visited:visited.update([u,v])
        if len(visited)<n:continue
        optional=[i for i in selected if not edges[i][3]]
        for count in range(min(k,len(optional))+1):
            for upgraded in itertools.combinations(optional,count):
                strength=min(edges[i][2]*(2 if i in upgraded else 1) for i in selected)
                best=max(best,strength)
    return best

def clipped_reachable(X,Y,circles):
    # Independent geometric feasibility via exhaustive intersection witnesses.
    with localcontext() as ctx:
        ctx.prec=70
        D=Decimal; X=D(X);Y=D(Y);cs=[tuple(map(D,c)) for c in circles]
        def inside(p,c):return (p[0]-c[0])**2+(p[1]-c[1])**2<=c[2]**2+D('1e-55')
        def inrect(p):return -D('1e-55')<=p[0]<=X+D('1e-55') and -D('1e-55')<=p[1]<=Y+D('1e-55')
        corners=[(D(0),D(0)),(D(0),Y),(X,D(0)),(X,Y)]
        if any(inside(corners[0],c) or inside(corners[-1],c) for c in cs):return False
        def boundary(c):
            x,y,r=c;pts=[]
            for xx in [D(0),X]:
                rem=r*r-(xx-x)**2
                if rem>=0:
                    root=rem.sqrt()
                    pts.extend(p for p in [(xx,y-root),(xx,y+root)] if inrect(p))
            for yy in [D(0),Y]:
                rem=r*r-(yy-y)**2
                if rem>=0:
                    root=rem.sqrt()
                    pts.extend(p for p in [(x-root,yy),(x+root,yy)] if inrect(p))
            return pts
        b=[boundary(c) for c in cs]
        def overlap(i,j):
            c=cs[i];e=cs[j]
            candidates=corners+[c[:2],e[:2]]+b[i]+b[j]
            dx=e[0]-c[0];dy=e[1]-c[1];sq=dx*dx+dy*dy
            if sq:
                dist=sq.sqrt();r=c[2];s=e[2]
                if abs(r-s)<=dist<=r+s:
                    a=(r*r-s*s+sq)/(2*dist);h2=r*r-a*a
                    h=max(D(0),h2).sqrt();mx=c[0]+a*dx/dist;my=c[1]+a*dy/dist
                    candidates += [(mx+h*dy/dist,my-h*dx/dist),(mx-h*dy/dist,my+h*dx/dist)]
            return any(inrect(p) and inside(p,c) and inside(p,e) for p in candidates)
        N=len(cs);adj=[[] for _ in range(N+2)]
        def connect(i,j):adj[i].append(j);adj[j].append(i)
        for i,c in enumerate(cs):
            # Segment intersection via endpoint or circle/side boundary witness.
            if any(inside(p,c) for p in [corners[0],corners[1],corners[3]]) or any(p[0]==0 or p[1]==Y for p in b[i]):connect(i,N)
            if any(inside(p,c) for p in [corners[0],corners[2],corners[3]]) or any(p[1]==0 or p[0]==X for p in b[i]):connect(i,N+1)
            for j in range(i):
                if overlap(i,j):connect(i,j)
        seen={N};todo=[N]
        for u in todo:
            for v in adj[u]:
                if v not in seen:seen.add(v);todo.append(v)
        return N+1 not in seen

def cases_for(pid):
    cases=[]
    def add(args,expected=None,kind='random_oracle'):
        functions={3235:clipped_reachable,3518:palindrome,3525:query_product,3539:magical,3579:transform,3590:xor_subtrees,3600:spanning}
        cases.append({'args':args,'expected':functions[pid](*args) if expected is None else expected,'kind':kind})
    if pid==3518:
        for length in range(1,7):
            for _ in range(10):
                half=''.join(RNG.choice('abc') for _ in range(length));mid=RNG.choice(['','a','b']);s=half+mid+half[::-1]
                count=len(set(itertools.permutations(half)))
                for k in range(1,min(count,30)+2):add([s,k])
        for half in ['a'*4998+'bc','a'*2500+'b'*2500,('abcdefghijklmnopqrstuvwxyz'*193)[:5000]]:
            for k in [1,2,999999,1000000]:add([half+half[::-1],k],kind='large_exact_integer_oracle')
    elif pid==3525:
        for _ in range(300):
            n=RNG.randrange(1,22);k=RNG.randrange(1,6);nums=[RNG.randrange(1,10**9+1) for _ in range(n)]
            q=[[RNG.randrange(n),RNG.randrange(1,10**9+1),RNG.randrange(n),RNG.randrange(k)] for _ in range(RNG.randrange(1,25))];add([nums,k,q])
    elif pid==3539:
        for _ in range(180):
            n=RNG.randrange(1,6);m=RNG.randrange(1,7);k=RNG.randrange(1,m+1);nums=[RNG.choice([1,2,99999999,100000000,RNG.randrange(1,10**8+1)]) for _ in range(n)];add([m,k,nums])
        for m in range(1,31):
            for k in [1,m]:add([m,k,[100000000]],pow(100000000,m,MOD) if m.bit_count()==k else 0,'single_index_exact')
    elif pid==3579:
        for n in range(1,8):
            for _ in range(25):add([''.join(RNG.choice('abc') for _ in range(n)),''.join(RNG.choice('abc') for _ in range(n))])
        add(['abcdef','fedabc'],2,'public_example')
    elif pid==3590:
        for _ in range(250):
            n=RNG.randrange(1,30);old=[-1]+[RNG.randrange(i) for i in range(1,n)];perm=[0]+RNG.sample(list(range(1,n)),n-1);par=[-1]*n
            for i in range(1,n):par[perm[i]]=perm[old[i]]
            vals=[RNG.randrange(0,15) for _ in range(n)];q=[[RNG.randrange(n),RNG.randrange(1,n+2)] for _ in range(30)];add([par,vals,q])
        n=50000;add([[-1]+list(range(n-1)),[0]*n,[[0,1],[0,2],[n-1,1]]],[0,-1,0],'deep_chain_no_recursion')
    elif pid==3600:
        for _ in range(300):
            n=RNG.randrange(2,7);pairs=list(itertools.combinations(range(n),2));RNG.shuffle(pairs);edges=[[u,v,RNG.randrange(1,15),int(RNG.random()<.2)] for u,v in pairs[:RNG.randrange(1,min(len(pairs),9)+1)]];add([n,edges,RNG.randrange(n+1)])
    elif pid==3235:
        add([3,4,[[2,1,1]]],True,'public_example');add([4,4,[[5,5,1]]],True,'public_example')
        for _ in range(1000):
            X=RNG.randrange(3,15);Y=RNG.randrange(3,15);cs=[[RNG.randrange(1,26),RNG.randrange(1,26),RNG.randrange(1,16)] for _ in range(RNG.randrange(1,7))];add([X,Y,cs])
        for X,Y,cs in [(10**9,10**9,[[1,500000000,500000000]]),(10**9,10**9,[[500000000,500000000,499999999]]),(999999999,1000000000,[[999999999,999999999,1]])]:add([X,Y,cs],kind='large_exact_geometry')
    return cases

def add_geometry_cases(cases):
    rng = random.Random(3235001)
    extra = []
    while len(extra) < 2000:
        width, height = rng.randint(3, 30), rng.randint(3, 30)
        circles = []
        for _ in range(rng.randint(2, 8)):
            x, y = rng.randint(1, 2 * width), rng.randint(1, 2 * height)
            radius = rng.randint(1, max(width, height))
            if x*x + y*y <= radius*radius or (x-width)**2 + (y-height)**2 <= radius*radius:
                continue
            circles.append([x, y, radius])
        if len(circles) < 2:
            continue
        args = [width, height, circles]
        extra.append({'args': args, 'expected': clipped_reachable(*args),
                      'kind': 'endpoint_uncovered_clipped_geometry'})
    for args, expected in [([5, 5, [[3, 11, 6], [11, 3, 6]]], True),
                           ([10, 10, [[3, 7, 3], [7, 3, 3]]], False)]:
        assert clipped_reachable(*args) == expected
        extra.append({'args': args, 'expected': expected,
                      'kind': 'outside_intersection_or_barrier_fixture'})
    return cases + extra


def maximum_cases():
    n = 100000
    queries = [[i*7 % n, 1, i*13 % n, i % 5] for i in range(20000)]
    magic = pow(10**8, 30, MOD)
    for x in range(21, 51):
        magic = magic * x % MOD
    return [
        (3525, [[1]*n, 5, queries],
         [n-q[2] if q[3] == 1 else 0 for q in queries],
         '100000 elements and 20000 persistent queries; all-ones closed form'),
        (3539, [30, 30, [10**8]*50], magic,
         '50 indices and m=k=30; falling-factorial distinct-index closed form'),
        (3579, ['a'*100, 'b'*100], 100,
         '100 uniform mismatches; no improving swap or reversal'),
    ]
