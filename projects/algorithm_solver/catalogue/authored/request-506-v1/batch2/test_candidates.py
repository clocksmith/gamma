"""Bounded public-contract candidate checks. No admission or hidden judge claims."""
import json, importlib.util, subprocess, random, itertools, math, heapq, hashlib, copy, sys
sys.dont_write_bytecode=True
from pathlib import Path
from collections import Counter, deque
ROOT=Path(__file__).resolve().parents[1]; HERE=Path(__file__).resolve().parent
records=json.loads((HERE/'cases.json').read_text()); tests=[]; rng=random.Random(50602)
def add(i,args,want,kind='independent_oracle'):tests.append(dict(id=i,args=args,expected=want,kind=kind))
for r in records:
    for args,want in r['cases']:add(r['id'],args,want,'public_example_or_hand_checked')
for _ in range(35):
    a=[rng.randrange(1,10) for _ in range(rng.randrange(1,9))];n=len(a)
    add(1950,[a],[max(min(a[i:i+k]) for i in range(n-k+1)) for k in range(1,n+1)])
    add(2221,[a],sum(math.comb(n-1,i)*x for i,x in enumerate(a))%10)
    add(2393,[a],sum(all(a[k]<a[k+1] for k in range(i,j)) for i in range(n) for j in range(i,n)))
    sums=[sum(a[i] for i in range(n) if mask>>i&1) for mask in range(1<<n)];v=0
    for x in sums:v|=x
    add(2505,[a],v)
    add(2789,[a],None)
    cache={}
    def merge(t):
        if t in cache:return cache[t]
        best=max(t)
        for i in range(len(t)-1):
            if t[i]<=t[i+1]:best=max(best,merge(t[:i]+(t[i]+t[i+1],)+t[i+2:]))
        cache[t]=best;return best
    tests[-1]['expected']=merge(tuple(a))
    add(2863,[a],max([j-i+1 for i in range(n) for j in range(i+1,n) if a[i]>a[j]] or [0]))
    add(2908,[a],min([a[i]+a[j]+a[k] for i in range(n) for j in range(i+1,n) for k in range(j+1,n) if a[i]<a[j]>a[k]] or [-1]))
    add(3063,[a],list(Counter(a).values()))
    add(3185,[a],sum((a[i]+a[j])%24==0 for i in range(n) for j in range(i+1,n)))
    b=a[:];rounds=0
    while True:
        c=[x for i,x in enumerate(b) if i==0 or b[i-1]<=x]
        if len(c)==len(b):break
        rounds+=1;b=c
    add(2289,[a],rounds)
    b=rng.sample(range(1,40),n)
    add(2832,[b],[max(j-i+1 for i in range(k+1) for j in range(k,n) if max(b[i:j+1])==b[k]) for k in range(n)])
    bits=[rng.randrange(2) for _ in a]
    add(3096,[bits],next((i for i in range(1,n) if sum(2*x-1 for x in bits[:i])>sum(2*x-1 for x in bits[i:])), -1))
    add(2750,[bits],sum(all(sum(bits[l:r])==1 for l,r in zip([0]+[i+1 for i in range(n-1) if mask>>i&1],[i+1 for i in range(n-1) if mask>>i&1]+[n])) for mask in range(1<<max(0,n-1))))
    b=[rng.randrange(1,10) for _ in a];best=1
    for mask in range(1<<n):
        c=[b[i] if mask>>i&1 else a[i] for i in range(n)];run=1
        for i in range(1,n):run=run+1 if c[i]>=c[i-1] else 1;best=max(best,run)
    add(2771,[a,b],best)
    k=rng.randrange(1,5);b=[rng.randrange(1,10) for _ in range(5)]
    add(3164,[a,b,k],sum(x%(y*k)==0 for x in a for y in b))
    x,y,z=rng.randrange(256),rng.randrange(256),rng.randrange(9)
    add(2939,[x,y,z],max((x^v)*(y^v) for v in range(1<<z))%1000000007)
    n1=rng.randrange(1,8);kk=rng.randrange(1,8)
    add(3179,[n1,kk],math.comb(n1+kk-1,kk)%1000000007)
    coins=rng.sample(range(1,15),rng.randrange(1,5));kk=rng.randrange(1,30)
    add(3116,[coins,kk],[x for x in range(1,kk*min(coins)+1) if any(x%c==0 for c in coins)][kk-1])
    num=rng.randrange(1000);add(2443,[num],any(x+int(str(x)[::-1])==num for x in range(num+1)))
    num=rng.randrange(1,100);v=num;answer=num
    for x in range(num,-1,-1):
        v&=x
        if v==0:answer=x;break
    add(3125,[num],answer)
    s=''.join(rng.choice('abc') for _ in a);t=''.join(rng.choice('abc') for _ in b)
    l=max([j-i for i in range(len(s)) for j in range(i+1,len(s)+1) if s[i:j] in t] or [0]);add(3135,[s,t],len(s)+len(t)-2*l)
    q=[[rng.randrange(n),rng.randrange(n)] for _ in range(5)];q=[sorted(x) for x in q]
    add(2955,[s,q],[sum(s[i]==s[j] for i in range(l,r+1) for j in range(i,r+1)) for l,r in q])
    c=[rng.randrange(1,10) for _ in range(3)];u=[rng.randrange(1,10) for _ in c];ss=[rng.randrange(1,10) for _ in c];m=[rng.randrange(1,10) for _ in c]
    add(3155,[c,u,ss,m],[max(t for t in range(cc+1) if t*uu<=mm+(cc-t)*sv) for cc,uu,sv,mm in zip(c,u,ss,m)])
    arr=[rng.randrange(1,100) for _ in a];pals=[v for v in range(1,1000) if str(v)==str(v)[::-1]]
    add(2967,[arr],min(sum(abs(v-x) for x in arr) for v in pals))
for n in range(1,8):
    add(2992,[n],sum(all(math.gcd(i+1,x)==1 for i,x in enumerate(p)) for p in itertools.permutations(range(1,n+1))))
for n in range(1,7):
    perms=list(itertools.permutations(range(1,n+1)))
    for rank in rng.sample(range(len(perms)),min(10,len(perms))):add(3109,[list(perms[rank])],rank)
for _ in range(20):
    n=rng.randrange(2,8);edges=[[i,j] for i in range(n) for j in range(i) if rng.random()<.25];s,t=rng.randrange(n),rng.randrange(n);seen={s}
    while True:
        nxt=seen|{b for a,b in edges if a in seen}|{a for a,b in edges if b in seen}
        if nxt==seen:break
        seen=nxt
    add(1971,[n,edges,s,t],t in seen)
    # Bank reference uses mathematical integer accounting.
    balance=[rng.randrange(1,100) for _ in range(4)];ops=['Bank'];args=[[balance[:]]];out=[None]
    for z in range(25):
        op=rng.choice(['deposit','withdraw','transfer']);a=rng.randrange(0,6);money=rng.randrange(1,150);b=rng.randrange(0,6)
        aa=[a,b,money] if op=='transfer' else [a,money];ok=1<=a<=4 and (op!='transfer' or 1<=b<=4) and (op=='deposit' or balance[a-1]>=money)
        if ok:
            balance[a-1]+=money if op=='deposit' else -money
            if op=='transfer':balance[b-1]+=money
        ops.append(op);args.append(aa);out.append(ok)
    add(2043,[ops,args],out)
    w,h=rng.randrange(2,7),rng.randrange(2,7);ops=['Robot'];args=[[w,h]];out=[None];x=y=direction=0;dirs=[(1,0),(0,1),(-1,0),(0,-1)];names=['East','North','West','South']
    for z in range(15):
        steps=rng.randrange(1,100)
        for step in range(steps):
            dx,dy=dirs[direction]
            if not(0<=x+dx<w and 0<=y+dy<h):direction=(direction+1)%4;dx,dy=dirs[direction]
            x+=dx;y+=dy
        ops+=['step','getPos','getDir'];args += [[steps],[],[]];out += [None,[x,y],names[direction]]
    add(2069,[ops,args],out)
    ops=['SmallestInfiniteSet'];args=[[]];out=[None];present=set(range(1,100))
    for z in range(35):
        if rng.random()<.6:v=min(present);present.remove(v);ops.append('popSmallest');args.append([]);out.append(v)
        else:v=rng.randrange(1,30);present.add(v);ops.append('addBack');args.append([v]);out.append(None)
    add(2336,[ops,args],out)
    ops=['NumberContainers'];args=[[]];out=[None];index={}
    for z in range(35):
        v=rng.randrange(1,5)
        if rng.random()<.7:i=rng.randrange(1,15);index[i]=v;ops.append('change');args.append([i,v]);out.append(None)
        else:ops.append('find');args.append([v]);out.append(min([i for i,x in index.items() if x==v] or [-1]))
    add(2349,[ops,args],out)
    n=10;ops=['LUPrefix'];args=[[n]];out=[None];seen=set()
    for i in rng.sample(range(1,n+1),n):
        seen.add(i);v=next((j-1 for j in range(1,n+1) if j not in seen),n);ops+=['upload','longest'];args += [[i],[]];out += [None,v]
    add(2424,[ops,args],out)
    pts=[];ops=['DetectSquares'];args=[[]];out=[None]
    for z in range(25):
        p=[rng.randrange(5),rng.randrange(5)]
        if rng.random()<.7:pts.append(p);ops.append('add');args.append([p]);out.append(None)
        else:
            x,y=p;c=Counter(map(tuple,pts));answer=0
            for a in range(5):
                if a==x:continue
                for b in [y+(a-x),y-(a-x)]:answer+=c[a,y]*c[x,b]*c[a,b]
            ops.append('count');args.append([p]);out.append(answer)
    add(2013,[ops,args],out)
    floor=''.join(rng.choice('01') for _ in range(7));k=rng.randrange(1,4);length=rng.randrange(1,5)
    add(2209,[floor,k,length],min(sum(v=='1' and not any(start<=i<start+length for start in starts) for i,v in enumerate(floor)) for starts in itertools.product(range(len(floor)),repeat=k)))
    tiles=[]
    for i in range(0,20,4):
        if rng.random()<.7:tiles.append([i,i+rng.randrange(3)])
    if not tiles:tiles=[[1,1]]
    whites={i for a,b in tiles for i in range(a,b+1)};length=rng.randrange(1,9)
    add(2271,[tiles,length],max(len(whites&set(range(i,i+length))) for i in range(-length,21)))
    n=3;qs=[[rng.randrange(2),rng.randrange(n),rng.randrange(9)] for _ in range(12)];grid=[[0]*n for _ in range(n)]
    for typ,i,v in qs:
        for j in range(n):
            if typ==0:grid[i][j]=v
            else:grid[j][i]=v
    add(2718,[n,qs],sum(map(sum,grid)))
    n=4;g=[[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i):g[i][j]=rng.randrange(2);g[j][i]=1-g[i][j]
    add(2923,[g],next(i for i in range(n) if sum(g[i])==n-1) if any(sum(row)==n-1 for row in g) else None)
    if tests[-1]['expected'] is None:tests.pop() # Contract guarantees a champion.
    arr=[rng.randrange(1,15) for _ in range(8)];qs=[[rng.randrange(8),rng.randrange(9)] for _ in range(8)];marked=set();answers=[]
    for i,k in qs:
        marked.add(i);marked.update(sorted((j for j in range(8) if j not in marked),key=lambda j:(arr[j],j))[:k]);answers.append(sum(v for j,v in enumerate(arr) if j not in marked))
    add(3080,[arr,qs],answers)
    points=rng.sample([(x,y) for x in range(-3,4) for y in range(-3,4)],8);labels=''.join(rng.choice('abcd') for _ in points)
    add(3143,[[list(p) for p in points],labels],max([len(tags) for d in range(4) if len(tags:=[labels[i] for i,p in enumerate(points) if max(map(abs,p))<=d])==len(set(tags))] or [0]))
    grid=[[rng.randrange(2) for _ in range(3)] for _ in range(3)];grid[0][0]=1
    add(3195,[grid],min((b-a+1)*(d-c+1) for a in range(3) for b in range(a,3) for c in range(3) for d in range(c,3) if all(a<=i<=b and c<=j<=d for i in range(3) for j in range(3) if grid[i][j])))
    team=[rng.randrange(2) for _ in range(7)];dist=rng.randrange(1,7);catchers=[i for i,x in enumerate(team) if x];free=[i for i,x in enumerate(team) if not x]
    def matching(i,used):
        if i==len(catchers):return 0
        return max([matching(i+1,used)]+[1+matching(i+1,used|{j}) for j in free if j not in used and abs(catchers[i]-j)<=dist])
    add(1989,[team,dist],matching(0,set()))
    words=['x'*rng.randrange(1,5) for _ in range(5)];limit=7;sentence=' '.join(words)
    def wrap(i):
        if i==len(words):return 0
        costs=[]
        for j in range(i+1,len(words)+1):
            width=sum(map(len,words[i:j]))+j-i-1
            if width<=limit:costs.append(0 if j==len(words) else (limit-width)**2+wrap(j))
        return min(costs)
    add(2052,[sentence,limit],wrap(0))
    nums=[2,5,7];states=[nums[:]];cur=nums[:];saved=[]
    for time in range(1,25):
        if (time-1)//len(nums)%2==0:saved.append(cur.pop(0))
        else:cur.append(saved.pop(0))
        states.append(cur[:])
    qs=[[rng.randrange(25),rng.randrange(5)] for _ in range(20)]
    add(2113,[nums,qs],[states[t][i] if i<len(states[t]) else -1 for t,i in qs])
    buckets=[rng.randrange(1,30) for _ in range(5)];loss=rng.randrange(100);ratio=1-loss/100;bs=sorted(buckets)
    for k in range(1,len(bs)+1):
        v=(sum(bs[:k])+ratio*sum(bs[k:]))/(k+ratio*(len(bs)-k))
        if bs[k-1]<=v and (k==len(bs) or v<=bs[k]):break
    add(2137,[buckets,loss],v)
    paint=[sorted(rng.sample(range(20),2)) for _ in range(8)];seen=set();ans=[]
    for l,r in paint:new=set(range(l,r));ans.append(len(new-seen));seen|=new
    add(2158,[paint],ans)
    vals=[rng.randrange(1,10) for _ in range(4)];eq=[['a','b'],['b','c'],['c','d'],['a','d']];ratios=[vals[0]/vals[1],vals[1]/vals[2],vals[2]/vals[3],vals[0]/vals[3]]
    add(2307,[eq,ratios],False);add(2307,[eq,ratios[:3]+[ratios[3]+1]],True)
    items=[[rng.randrange(1,20),2] for _ in range(4)];capacity=rng.randrange(1,10)
    add(2548,[items,capacity],-1 if capacity>8 else max(sum(items[i][0]*q[i]/2 for i in range(4)) for q in itertools.product(range(3),repeat=4) if sum(q)==capacity))
    nums=[rng.randrange(-5,6) for _ in range(6)]
    if sum(nums)<0:nums[-1]-=sum(nums)
    def valid(a):return all(sum(a[:i])>=0 for i in range(1,len(a)+1))
    add(2599,[nums],min(mask.bit_count() for mask in range(1<<len(nums)) if valid([v for i,v in enumerate(nums) if not mask>>i&1]+[v for i,v in enumerate(nums) if mask>>i&1])))
    y=[rng.randrange(1,8)]
    for i in range(6):y.append(rng.choice([x for x in range(1,8) if x!=y[-1]]))
    from fractions import Fraction
    levels={Fraction(v) for v in y}|{Fraction(a+b,2) for a,b in zip(sorted(set(y)),sorted(set(y))[1:])};maximum=0
    for level in levels:
        xs={Fraction(i)+(level-a)/(b-a) for i,(a,b) in enumerate(zip(y,y[1:])) if min(a,b)<=level<=max(a,b)};maximum=max(maximum,len(xs))
    add(3009,[y],maximum)

for _ in range(20):
    # Complete tree adapter with unique values, paths independently found by BFS.
    values=rng.sample(range(1,100),15);start,dest=rng.sample(values,2);adj={v:[] for v in values}
    for i in range(1,len(values)):
        p=(i-1)//2;adj[values[p]].append((values[i],'L' if i%2 else 'R'));adj[values[i]].append((values[p],'U'))
    q=deque([(start,'')]);seen={start}
    while q:
        u,path=q.popleft()
        if u==dest:break
        for v,d in adj[u]:
            if v not in seen:seen.add(v);q.append((v,path+d))
    add(2096,[values,start,dest],path)
    # Balanced BST level order from sorted unique values.
    ordered=sorted(values);nodes=deque([ordered]);tree=[]
    while nodes:
        row=nodes.popleft();mid=len(row)//2;tree.append(row[mid])
        if len(row)>1:nodes.append(row[:mid]);nodes.append(row[mid+1:])
    queries=[rng.randrange(110) for _ in range(10)]
    add(2476,[tree,queries],[[max([v for v in values if v<=x] or [-1]),min([v for v in values if v>=x] or [-1])] for x in queries])
    grid=[[rng.randrange(1,31) for _ in range(3)] for _ in range(3)];best=0
    def zeros(p):
        z=0
        while p%10==0:z+=1;p//=10
        return z
    for i in range(3):
        for j in range(3):
            for vi in range(3):
                for hj in range(3):
                    cells={(r,j) for r in range(min(i,vi),max(i,vi)+1)}|{(i,c) for c in range(min(j,hj),max(j,hj)+1)};product=math.prod(grid[r][c] for r,c in cells);best=max(best,zeros(product))
    add(2245,[grid],best)
    n=4;edges=[[i,j,rng.randrange(1,10)] for i in range(n) for j in range(n) if i!=j and rng.random()<.3];ops=['Graph'];args=[[n,copy.deepcopy(edges)]];out=[None];existing={(a,b) for a,b,w in edges}
    for z in range(12):
        available=[(i,j) for i in range(n) for j in range(n) if i!=j and (i,j) not in existing]
        if available and rng.random()<.4:
            a,b=rng.choice(available);edge=[a,b,rng.randrange(1,10)];edges.append(edge);existing.add((a,b));ops.append('addEdge');args.append([edge]);out.append(None)
        else:
            dist=[[0 if i==j else math.inf for j in range(n)] for i in range(n)]
            for a,b,w in edges:dist[a][b]=w
            for k in range(n):
                for i in range(n):
                    for j in range(n):dist[i][j]=min(dist[i][j],dist[i][k]+dist[k][j])
            a,b=rng.randrange(n),rng.randrange(n);ops.append('shortestPath');args.append([a,b]);out.append(-1 if math.isinf(dist[a][b]) else dist[a][b])
    add(2642,[ops,args],out)
    start=[1,1];target=[8,8];roads=[[rng.randrange(1,9),rng.randrange(1,9),rng.randrange(1,9),rng.randrange(1,9),rng.randrange(1,10)] for _ in range(4)];points=[start,target]+[r[:2] for r in roads]+[r[2:4] for r in roads];dist=[[abs(a[0]-b[0])+abs(a[1]-b[1]) for b in points] for a in points]
    for k,r in enumerate(roads):dist[k+2][k+6]=min(dist[k+2][k+6],r[4])
    for k in range(len(points)):
        for i in range(len(points)):
            for j in range(len(points)):dist[i][j]=min(dist[i][j],dist[i][k]+dist[k][j])
    add(2662,[start,target,roads],dist[0][1])
    n=3;grid=[[int(rng.random()<.25) for _ in range(n)] for _ in range(n)];grid[rng.randrange(n)][rng.randrange(n)]=1;thieves=[(i,j) for i in range(n) for j in range(n) if grid[i][j]];d=[[min(abs(i-a)+abs(j-b) for a,b in thieves) for j in range(n)] for i in range(n)];answer=0
    for threshold in range(2*n):
        seen={(0,0)} if d[0][0]>=threshold else set();q=list(seen)
        while q:
            i,j=q.pop()
            for a,b in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
                if 0<=a<n and 0<=b<n and (a,b) not in seen and d[a][b]>=threshold:seen.add((a,b));q.append((a,b))
        if (n-1,n-1) in seen:answer=threshold
    add(2812,[grid],answer)
    n=6;a=rng.randrange(1<<n);b=rng.randrange(1<<n);x=rng.randrange(1,8);ds={a:0};heap=[(0,a)]
    while heap:
        cost,mask=heapq.heappop(heap)
        if cost!=ds[mask]:continue
        if mask==b:break
        for i in range(n):
            for j in range(i+1,n):
                m=mask^(1<<i)^(1<<j);c=cost+min(x,1 if j==i+1 else x)
                if c<ds.get(m,math.inf):ds[m]=c;heapq.heappush(heap,(c,m))
    add(2896,[format(a,'06b'),format(b,'06b'),x],ds.get(b,-1))
    nums=[rng.choice([1,2,3,4,9,16]) for _ in range(8)];count=Counter(nums);best=1
    for mask in range(1,1<<len(nums)):
        chosen=sorted(nums[i] for i in range(len(nums)) if mask>>i&1)
        if len(chosen)%2==0:continue
        mid=len(chosen)//2;valid=True;base=chosen[0];pattern=[]
        for i in range(mid):pattern += [base,base];base*=base
        pattern.append(base)
        if sorted(pattern)==chosen:best=max(best,len(chosen))
    add(3020,[nums],best)
    enemy=[rng.randrange(1,6) for _ in range(3)];energy=rng.randrange(8);seen={(0,energy,0)};q=list(seen);best=0
    while q:
        mask,e,p=q.pop();best=max(best,p)
        for i,v in enumerate(enemy):
            if mask>>i&1:continue
            choices=[]
            if e>=v:choices.append((mask,e-v,p+1))
            if p>=1:choices.append((mask|1<<i,e+v,p))
            for state in choices:
                if state not in seen:seen.add(state);q.append(state)
    add(3207,[enemy,energy],best)
    vals=rng.sample(range(1,100),9);grid=[vals[i:i+3] for i in range(0,9,3)];memo={}
    def rank(i,j):
        if (i,j) not in memo:memo[i,j]=1+max([rank(i,c) for c in range(3) if grid[i][c]<grid[i][j]]+[rank(r,j) for r in range(3) if grid[r][j]<grid[i][j]]+[0])
        return memo[i,j]
    add(2371,[grid],[[rank(i,j) for j in range(3)] for i in range(3)])
for n in range(2,7):
    initial=[tuple(range(n)),tuple(list(range(1,n))+[0])];distance={s:0 for s in initial};q=deque(initial)
    while q:
        state=q.popleft();blank=state.index(0)
        for i in range(n):
            nxt=list(state);nxt[blank],nxt[i]=nxt[i],nxt[blank];nxt=tuple(nxt)
            if nxt not in distance:distance[nxt]=distance[state]+1;q.append(nxt)
    for state in rng.sample(list(distance),min(20,len(distance))):add(2459,[list(state)],distance[state])
for n in [1,9,10,20,37,100]:
    answer=0
    for x in range(1,n+1):
        s=str(x*x);good=False
        for mask in range(1<<(len(s)-1)):
            cuts=[0]+[i+1 for i in range(len(s)-1) if mask>>i&1]+[len(s)]
            if sum(int(s[a:b]) for a,b in zip(cuts,cuts[1:]))==x:good=True;break
        if good:answer+=x*x
    add(2698,[n],answer)
# Maximum-shape and precision regression checks, separately counted.
add(2043,[['Bank']+['deposit']*10000+['withdraw','withdraw'],[[[10**12]]]+[[1,10**12]]*10000+[[1,10**12],[1,10**12]]],[None]+[True]*10002,'numeric_edge')
add(3109,[list(range(100000,0,-1))],(math.factorial(100000)-1)%1000000007,'maximum_shape')
add(3125,[10**15],(1<<49)-1,'numeric_edge')
add(2505,[[10**9]*100000],(1<<47)-512,'numeric_edge')
add(2955,['a'*30000,[[0,29999]]],[30000*30001//2],'maximum_shape')
add(2832,[list(range(1,100001))],list(range(1,100001)),'maximum_shape')
add(2863,[list(range(100000,0,-1))],100000,'maximum_shape')
add(3135,['a'*1000,'a'*1000],0,'maximum_shape')

add(2096,[[1]+[v for i in range(2,100001) for v in (None,i)],1,100000],'R'*99999,'maximum_shape')
add(3116,[[25],2000000000],50000000000,'numeric_edge')
add(3164,[[1000000]*100000,[1]*100000,1],10000000000,'maximum_shape')
add(2209,['1'*1000,1000,1],0,'maximum_shape')
# Deterministic examples are separated from oracles, which compute expectations without candidates.
modules={}
for r in records:
    p=ROOT/'python'/f"{r['id']}.py";compile(p.read_text(),str(p),'exec')
    spec=importlib.util.spec_from_file_location('candidate_'+str(r['id']),p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);modules[r['id']]=module.solve
    subprocess.run(['node','--check',str(ROOT/'javascript'/f"{r['id']}.js")],check=True,capture_output=True)
def equal(a,b):
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):return abs(a-b)<=1e-5
    if type(a)!=type(b):return False
    if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b
node='''const fs=require('fs'),path=require('path'),root=process.argv[1];const rows=JSON.parse(fs.readFileSync(0,'utf8'));let result=rows.map(r=>{try{const before=JSON.stringify(r.args);const value=require(path.join(root,r.id+'.js'))(...r.args);return {value,mutated:before!==JSON.stringify(r.args)}}catch(e){return {error:String(e)}}});process.stdout.write(JSON.stringify(result));'''
js=json.loads(subprocess.run(['node','-e',node,str(ROOT/'javascript')],input=json.dumps(tests),text=True,capture_output=True,check=True).stdout)
fail=[];counts={r['id']:Counter() for r in records}
for t,j in zip(tests,js):
    try:
        arguments=copy.deepcopy(t['args']);p=modules[t['id']](*arguments);mutated=arguments!=t['args']
    except Exception as e:p={'error':repr(e)};mutated=False
    good=not mutated and not j.get('mutated') and equal(p,t['expected']) and 'value' in j and equal(j['value'],t['expected'])
    counts[t['id']][t['kind']]+=1;counts[t['id']]['cross_language_parity']+=int('value'in j and equal(p,j['value']))
    if not good:fail.append(dict(test=t,python=p,javascript=j,input_mutation_python=mutated))
(HERE/'test-results.json').write_text(json.dumps(dict(source_sha256={str(r['id']):{lang:hashlib.sha256((ROOT/lang/(str(r['id'])+ext)).read_bytes()).hexdigest() for lang,ext in [('python','.py'),('javascript','.js')]} for r in records}, test_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), fixtures_sha256=hashlib.sha256((HERE/'cases.json').read_bytes()).hexdigest(), syntax_checks={'python':len(records),'javascript':len(records)}, total_cases=len(tests),total_language_executions=len(tests)*2,failures=fail,per_id={str(i):dict(c) for i,c in counts.items()},scope='Public examples and bounded independently computed tests only; not hidden-judge or admission qualification.'),indent=2)+'\n')
print(json.dumps(dict(cases=len(tests),failures=len(fail),first_failures=fail[:10]),indent=2))
raise SystemExit(bool(fail))
