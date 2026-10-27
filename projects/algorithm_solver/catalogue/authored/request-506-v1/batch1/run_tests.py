"""Bounded public-example and independently derived oracle tests; no hidden cases."""
import collections, copy, functools, importlib.util, itertools, json, math, random, subprocess, time
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
R=random.Random(50601);cases=[]
def add(i,args,expected,kind='independent_oracle'):
    cases.append(dict(id=i,args=args,expected=expected,kind=kind))
manifest=json.loads((BASE/'batch1/manifest.json').read_text())
for row in manifest:
    for args,expected in row['examples']:add(row['problem_id'],args,expected,'documented_example')
class Node:
    def __init__(self,val):self.val=val;self.next=None;self.left=None;self.right=None

def linked(a):
    head=None
    for v in reversed(a):n=Node(v);n.next=head;head=n
    return head

def tree(a):
    if not a or a[0] is None:return None
    root=Node(a[0]);q=[root];i=1
    for n in q:
        for side in ['left','right']:
            if i<len(a) and a[i] is not None:
                t=Node(a[i]);setattr(n,side,t);q.append(t)
            i+=1
    return root

def flat(root):
    q=[root];out=[]
    for n in q:
        out.append(n.val if n else None)
        if n:q.extend([n.left,n.right])
    while out and out[-1] is None:out.pop()
    return out
mods={}
def pycall(i,args):
    if i not in mods:
        spec=importlib.util.spec_from_file_location('candidate'+str(i),BASE/'python'/f'{i}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);mods[i]=m
    args=copy.deepcopy(args)
    if i in (2095,2130):args[0]=linked(args[0])
    if i in (2265,2415):args[0]=tree(args[0])
    answer=mods[i].solve(*args)
    if i==2095:
        out=[]
        while answer:out.append(answer.val);answer=answer.next
        return out
    if i==2415:return flat(answer)
    return answer

for _ in range(40):
    n=R.randint(1,8);a=[R.randint(0,9) for _ in range(n)]
    add(2110,[a],sum(all(a[t]-a[t+1]==1 for t in range(l,r)) for l in range(n) for r in range(l,n)))
    add(2348,[a],sum(not any(a[l:r+1]) for l in range(n) for r in range(l,n)))
    add(2640,[a],[sum(a[:j+1])+sum(max(a[:i+1]) for i in range(j+1)) for j in range(n)])
    add(2095,[a],a[:n//2]+a[n//2+1:])
    even=a+a;add(2130,[even],max(even[i]+even[-1-i] for i in range(n)))
    aa=[R.randint(-5,9) for _ in range(n)];add(2219,[aa],max([sum(aa[:j]) for j in range(1,n+1)]+[sum(aa[j:]) for j in range(n)]))
    b=[R.randrange(2) for _ in range(n)];c=[R.randrange(2) for _ in range(n)]
    add(1983,[b,c],max([0]+[r-l for l in range(n) for r in range(l+1,n+1) if sum(b[l:r])==sum(c[l:r])]))
    k=R.randrange(5);add(3202,[a,k+1],max(len(s) for mask in range(1,1<<n) if (s:=[a[i] for i in range(n) if mask>>i&1]) and len({(s[i]+s[i+1])%(k+1) for i in range(len(s)-1)})<=1))
    positive=[x+1 for x in a];cost=R.randrange(8)
    add(2786,[positive,cost],max(sum(s)-cost*sum((s[i]%2)!=(s[i+1]%2) for i in range(len(s)-1)) for mask in range(1<<max(0,n-1)) for s in [[positive[0]]+[positive[i+1] for i in range(n-1) if mask>>i&1]]))
    digits=[R.randint(10,99) for _ in range(n)]
    add(3153,[digits],sum(sum(x!=y for x,y in zip(str(digits[i]),str(digits[j]))) for i in range(n) for j in range(i)))
    coordinates=[[R.randrange(8),R.randrange(8)] for _ in range(n)];k=R.randrange(8)
    add(2857,[coordinates,k],sum((coordinates[i][0]^coordinates[j][0])+(coordinates[i][1]^coordinates[j][1])==k for i in range(n) for j in range(i)))
    d=R.randint(1,7);add(2964,[positive,d],sum(sum(t)%d==0 for t in itertools.combinations(positive,3)))
    bits=R.randint(1,5);nums=[R.randrange(1<<bits) for _ in range(n)]
    add(3141,[nums,bits],[max((v^u).bit_count() for u in nums) for v in nums])
    # Exact exhaustive choices of triple flips (each operation need be applied at most once).
    add(3191,[b],min([sum(mask>>j&1 for j in range(max(0,n-2))) for mask in range(1<<max(0,n-2)) if all((b[i]+sum(mask>>j&1 for j in range(max(0,i-2),min(i+1,n-2))))%2 for i in range(n))] or [-1]))
    # All interval partitions are an oracle for minimal resize waste.
    k=R.randrange(n)
    best=10**9
    for mask in range(1<<(n-1)):
        if mask.bit_count()>k:continue
        starts=[0]+[i+1 for i in range(n-1) if mask>>i&1]+[n]
        best=min(best,sum((r-l)*max(positive[l:r])-sum(positive[l:r]) for l,r in zip(starts,starts[1:])))
    add(1959,[positive,k],best)
    # Exhaustive merged segment partition, including zeros and too-large singletons.
    limit=R.randint(1,20);best=n
    for mask in range(1<<(n-1)):
        starts=[0]+[i+1 for i in range(n-1) if mask>>i&1]+[n]
        if all(r-l==1 or math.prod(a[l:r])<=limit for l,r in zip(starts,starts[1:])):best=min(best,len(starts)-1)
    add(2892,[a,limit],best)
    limit=R.randint(0,5);candies=R.randint(0,15)
    add(2927,[candies,limit],sum(x+y+z==candies for x in range(limit+1) for y in range(limit+1) for z in range(limit+1)))
    amount=R.randint(1,35)
    add(3183,[amount],sum(x+2*y+4*z+6*w==amount for x in range(amount+1) for y in range(amount//2+1) for z in range(3) for w in range(amount//6+1)))
    s=''.join(R.choice('abcde') for _ in range(n));vals=[(ord(x)-96)//3+1 for x in s]
    add(2950,[s],sum(sum(vals[l:r])%(r-l)==0 for l in range(n) for r in range(l+1,n+1)))
    count=R.randint(1,4)
    add(2067,[s,count],sum(set(collections.Counter(s[l:r]).values())=={count} for l in range(n) for r in range(l+1,n+1)))
    add(2981,[s],max([r-l for l in range(n) for r in range(l+1,n+1) if len(set(s[l:r]))==1 and sum(s.startswith(s[l:r],i) for i in range(n))>=3] or [-1]))
    run=[]
    for ch,g in itertools.groupby(s):
        length=len(list(g))
        while length:take=min(9,length);run.append(str(take)+ch);length-=take
    add(3163,[s],''.join(run))
    pat=R.choice('abc');other=R.choice('abc');k=R.randrange(n)
    add(3006,[s,pat,other,k],[i for i in range(n) if s.startswith(pat,i) and any(abs(i-j)<=k and s.startswith(other,j) for j in range(n))])
    lo=R.randint(1,5);hi=R.randint(lo,9);one=R.randint(1,3);zero=R.randint(1,3)
    @functools.lru_cache(None)
    def construct(t):
        return (lo<=len(t)<=hi)+sum(construct(t+c) for c in ['1'*one,'0'*zero] if len(t+c)<=hi)
    add(2533,[lo,hi,one,zero],construct(''))
    target=R.randrange(12);types=[[R.randint(1,4),R.randint(1,5)] for _ in range(R.randint(1,4))]
    add(2585,[target,types],sum(sum(c*t[1] for c,t in zip(choice,types))==target for choice in itertools.product(*(range(t[0]+1) for t in types))))
    x=R.randint(1,30);length=R.randint(1,15);sup=[v for v in range(x,2048) if v&x==x]
    add(3133,[length,x],sup[length-1])
    skills=R.sample(range(1,100),max(2,n));k=R.randint(1,12);queue=list(range(len(skills)));wins=0;last=None
    while wins<k:
        u,v=queue[:2];winner=u if skills[u]>skills[v] else v;loser=v if winner==u else u
        queue=[winner]+queue[2:]+[loser];wins=wins+1 if winner==last else 1;last=winner
    add(3175,[skills,k],last)
    nrows=R.randint(1,4);ncols=R.randint(1,3);grid=[[R.randrange(4) for _ in range(ncols)] for _ in range(nrows)]
    add(3122,[grid],min(sum(grid[i][j]!=v[j] for i in range(nrows) for j in range(ncols)) for v in itertools.product(range(10),repeat=ncols) if all(v[j]!=v[j+1] for j in range(ncols-1))))
    # Enumerate digit permutations; short inputs bound work.
    number=''.join(str(R.randrange(4)) for _ in range(R.randint(1,6)));pal=[]
    for length in range(1,len(number)+1):
        for t in set(itertools.permutations(number,length)):
            if t==t[::-1] and (length==1 or t[0]!='0'):pal.append(int(''.join(t)))
    add(2384,[number],str(max(pal)))
    # Anti-palindrome brute permutations verify the lexicographic construction.
    even=''.join(R.choice('abc') for _ in range(2*R.randint(1,4)))
    add(3088,[even],min([''.join(t) for t in set(itertools.permutations(even)) if all(t[j]!=t[-1-j] for j in range(len(t)//2))] or ['-1']))
    nums=[R.randint(1,5) for _ in range(R.randint(1,7))];queries=[R.randint(1,5) for _ in range(R.randint(1,6))]
    @functools.lru_cache(None)
    def ends(t,i):
        if not t or i==len(queries):return i
        choices=[i]
        if t[0]>=queries[i]:choices.append(ends(t[1:],i+1))
        if t[-1]>=queries[i]:choices.append(ends(t[:-1],i+1))
        return max(choices)
    best=max(ends(tuple(nums[j] for j in range(len(nums)) if mask>>j&1),0) for mask in range(1<<len(nums)))
    add(3018,[nums,queries],best)


for _ in range(30):
    # Endpoints partition the painting, and exact color-set identity matters.
    endpoints=sorted(R.sample(range(1,15),R.randint(2,8)));segments=[]
    for color in R.sample(range(1,30),R.randint(1,7)):
        l,r=sorted(R.sample(endpoints,2));segments.append([l,r,color])
    boundaries=sorted({x for seg in segments for x in seg[:2]});expected=[]
    for l,r in zip(boundaries,boundaries[1:]):
        color=sum(c for a,b,c in segments if a<=l and r<=b)
        if color:expected.append([l,r,color])
    add(1943,[segments],expected)
    words=[''.join(R.choice('abc') for _ in range(3)) for _ in range(6)];dictionary=[''.join(R.choice('abc') for _ in range(3)) for _ in range(4)]
    add(2452,[words,dictionary],[w for w in words if any(sum(x!=y for x,y in zip(w,d))<=2 for d in dictionary)])
    n=R.randint(1,8);queries=[[R.randrange(n),R.randint(1,4)] for _ in range(12)];colors=[0]*n;expected=[]
    for i,c in queries:
        colors[i]=c;expected.append(sum(colors[j]!=0 and colors[j]==colors[j+1] for j in range(n-1)))
    add(2672,[n,queries],expected)
    num=R.randint(1,50);t=R.randint(1,50);add(2769,[num,t],num+sum(2 for _ in range(t)))
    strings=[''.join(R.choice('ab') for _ in range(R.randint(1,3))) for _ in range(3)]
    answer=None
    for length in range(max(map(len,strings)),sum(map(len,strings))+1):
        possibilities=[''.join(x) for x in itertools.product('ab',repeat=length) if all(s in ''.join(x) for s in strings)]
        if possibilities:answer=min(possibilities);break
    add(2800,strings,answer)
    n=R.randint(1,7);offers=[]
    for j in range(R.randint(1,7)):
        l=R.randrange(n);r=R.randrange(l,n);offers.append([l,r,R.randint(1,10)])
    best=0
    for mask in range(1<<len(offers)):
        chosen=[v for j,v in enumerate(offers) if mask>>j&1]
        if all(a[1]<b[0] or b[1]<a[0] for a,b in itertools.combinations(chosen,2)):best=max(best,sum(x[2] for x in chosen))
    add(2830,[n,offers],best)
    arr=[R.randint(1,6) for _ in range(R.randint(1,5))];target=R.randint(1,6)
    # Enumerate every possible adjusted array in the bounded value domain.
    best=min(sum(abs(x-y) for x,y in zip(arr,b)) for b in itertools.product(range(1,7),repeat=len(arr)) if sorted(b)[len(b)//2]==target)
    add(3107,[arr,target],best)
    arr=[R.randint(1,100) for _ in range(8)]+[2];primes=[i for i,x in enumerate(arr) if x>=2 and all(x%d for d in range(2,math.isqrt(x)+1))]
    add(3115,[arr],primes[-1]-primes[0])
    k=R.randint(1,50);d1=R.randrange(10);d2=R.randrange(10);valid=[]
    for length in range(1,11):
        for digits in itertools.product(sorted({str(d1),str(d2)}),repeat=length):
            if digits[0]=='0':continue
            v=int(''.join(digits))
            if k<v<=2147483647 and v%k==0:valid.append(v)
        if valid:break
    add(1999,[k,d1,d2],min(valid) if valid else -1)
    n=R.randint(3,8);cycle=R.randint(3,n);edges=[[i,(i+1)%cycle] for i in range(cycle)]
    for i in range(cycle,n):edges.append([i,R.randrange(i)])
    graph=[[] for _ in range(n)]
    for u,v in edges:graph[u].append(v);graph[v].append(u)
    distances=[]
    for start in range(n):
        q=collections.deque([(start,0)]);seen={start}
        while q:
            v,d=q.popleft()
            if v<cycle:distances.append(d);break
            for w in graph[v]:
                if w not in seen:seen.add(w);q.append((w,d+1))
    add(2204,[n,edges],distances)
    n=R.randint(1,7);regular=[R.randint(1,10) for _ in range(n)];express=[R.randint(1,10) for _ in range(n)];fee=R.randint(1,10);expected=[]
    for stop in range(1,n+1):
        best=10**9
        for bits in itertools.product((0,1),repeat=stop):
            cost=sum(express[j] if b else regular[j] for j,b in enumerate(bits))+fee*sum(b and (j==0 or not bits[j-1]) for j,b in enumerate(bits))
            best=min(best,cost)
        expected.append(best)
    add(2361,[regular,express,fee],expected)
    n=R.randint(2,6);roads=[];distance=[[0 if i==j else 10**6 for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(i):
            if R.randrange(2):
                w=R.randint(1,10);roads.append([i+1,j+1,w]);distance[i][j]=distance[j][i]=w
    for k in range(n):
        for i in range(n):
            for j in range(n):distance[i][j]=min(distance[i][j],distance[i][k]+distance[k][j])
    costs=[R.randint(1,50) for _ in range(n)];k=R.randint(1,5)
    add(2473,[n,roads,costs,k],[min(costs[j]+(k+1)*distance[i][j] for j in range(n)) for i in range(n)])
    n=R.randint(1,15);covered=set();ranges=[]
    for j in range(R.randint(0,6)):
        l=R.randrange(n);r=R.randrange(l,n);ranges.append([l,r]);covered.update(range(l,r+1))
    missing=sorted(set(range(n))-covered);expected=[]
    for _,g in itertools.groupby(enumerate(missing),lambda t:t[1]-t[0]):
        chunk=[t[1] for t in g];expected.append([chunk[0],chunk[-1]])
    add(2655,[n,ranges],expected)
    # Bellman-Ford on expanded layered graph, not a heap/Dijkstra oracle.
    n=R.randint(2,6);edges=[[i-1,i,R.randint(1,8)] for i in range(1,n)]
    for i in range(n):
        for j in range(i-1):
            if R.randrange(3)==0:edges.append([i,j,R.randint(1,8)])
    k=R.randint(0,3);start=R.randrange(n);end=R.randrange(n);distance={(i,h):10**9 for i in range(n) for h in range(k+1)};distance[start,0]=0
    for __ in range(n*(k+1)):
        for u,v,w in edges:
            for u,v in [(u,v),(v,u)]:
                for h in range(k+1):
                    distance[v,h]=min(distance[v,h],distance[u,h]+w)
                    if h<k:distance[v,h+1]=min(distance[v,h+1],distance[u,h])
    add(2714,[n,edges,start,end,k],min(distance[end,h] for h in range(k+1)))
    s=''.join(R.choice('abc') for _ in range(8));power=R.randint(1,1000000000);mod=R.randint(1,1000000000);k=R.randint(1,len(s));start=R.randrange(len(s)-k+1)
    hashes=[sum((ord(s[i+j])-96)*pow(power,j,mod) for j in range(k))%mod for i in range(len(s)-k+1)]
    add(2156,[s,power,mod,k,hashes[start]],s[hashes.index(hashes[start]):hashes.index(hashes[start])+k])
    source=''.join(R.choice('abc12') for _ in range(8));sub=''.join(R.choice('abc12') for _ in range(R.randint(1,4)));maps=[list(R.sample('abc12',2)) for _ in range(5)]
    options=[{ch}|{y for x,y in maps if x==ch} for ch in sub]
    add(2301,[source,sub,maps],any(''.join(t) in source for t in itertools.product(*options)))
    a=[R.randrange(6) for _ in range(4)];b=[R.randrange(6) for _ in range(4)];k1=R.randrange(4);k2=R.randrange(4);diff=tuple(abs(x-y) for x,y in zip(a,b));states={diff}
    for j in range(k1+k2):
        states|={v[:i]+(v[i]-1,)+v[i+1:] for v in states for i in range(len(v)) if v[i]}
    add(2333,[a,b,k1,k2],min(sum(v*v for v in state) for state in states))
    n=R.randint(1,1000);powers=[1<<i for i in range(n.bit_length()) if n>>i&1];queries=[]
    for j in range(6):
        l=R.randrange(len(powers));r=R.randrange(l,len(powers));queries.append([l,r])
    add(2438,[n,queries],[math.prod(powers[l:r+1])%1000000007 for l,r in queries])
    words=[''.join(R.choice('abc') for _ in range(R.randint(1,3))) for _ in range(R.randint(1,7))];strings={words[0]}
    for word in words[1:]:strings={joined for s in strings for joined in [s+word[int(s[-1]==word[0]):],word+s[int(word[-1]==s[0]):]]}
    add(2746,[words],min(map(len,strings)))
    # Exhaustive action histories (decrement, mark, or idle).
    nums=[R.randrange(3) for _ in range(R.randint(1,3))];changes=[R.randint(1,len(nums)) for _ in range(R.randint(1,7))];states={(tuple(nums),0)};answer=-1
    for second,ix in enumerate(changes,1):
        nxt=set(states)
        for v,marked in states:
            if not v[ix-1]:nxt.add((v,marked|(1<<(ix-1))))
            for j in range(len(v)):
                if v[j]:nxt.add((v[:j]+(v[j]-1,)+v[j+1:],marked))
        states=nxt
        if any(mask==(1<<len(nums))-1 for _,mask in states):answer=second;break
    add(3048,[nums,changes],answer)

for _ in range(30):
    # An exhaustive mapping oracle for small alphanumeric pattern windows.
    board=[[R.randrange(4) for _ in range(3)] for _ in range(3)];pattern=[''.join(R.choice('ab01') for _ in range(2)) for _ in range(2)];answer=[-1,-1]
    for top in range(2):
        for left in range(2):
            cells=[(pattern[r][c],board[top+r][left+c]) for r in range(2) for c in range(2)]
            valid=all(not ch.isdigit() or int(ch)==v for ch,v in cells) and all((ch==other)==(v==w) for ch,v in cells for other,w in cells)
            if valid and answer==[-1,-1]:answer=[top,left]
    add(3078,[board,pattern],answer)
    operations=['StockPrice'];arguments=[[]];expected=[None];prices={}
    for j in range(35):
        if not prices or R.randrange(2):
            timestamp=R.randint(1,10);price=R.randint(1,100);operations.append('update');arguments.append([timestamp,price]);prices[timestamp]=price;expected.append(None)
        else:
            op=R.choice(['current','minimum','maximum']);operations.append(op);arguments.append([]);expected.append(prices[max(prices)] if op=='current' else min(prices.values()) if op=='minimum' else max(prices.values()))
    add(2034,[operations,arguments],expected)
    # Binary rooted parent tree; delete each vertex and enumerate components.
    n=R.randint(2,12);parents=[-1];children=collections.Counter()
    for i in range(1,n):
        choices=[j for j in range(i) if children[j]<2];p=R.choice(choices);parents.append(p);children[p]+=1
    graph=[[] for _ in parents]
    for i,p in enumerate(parents[1:],1):graph[i].append(p);graph[p].append(i)
    scores=[]
    for cut in range(n):
        seen={cut};sizes=[]
        for start in range(n):
            if start in seen:continue
            stack=[start];seen.add(start);size=0
            while stack:
                v=stack.pop();size+=1
                for w in graph[v]:
                    if w not in seen:seen.add(w);stack.append(w)
            sizes.append(size)
        scores.append(math.prod(sizes))
    add(2049,[parents],scores.count(max(scores)))
    ops=['ATM'];args=[[]];expected=[None];cash=[0]*5;denoms=[20,50,100,200,500]
    for j in range(25):
        if R.randrange(2):
            deposit=[R.randrange(4) for _ in range(5)];ops.append('deposit');args.append([deposit]);cash=[x+y for x,y in zip(cash,deposit)];expected.append(None)
        else:
            amount=R.randint(1,150)*10;ops.append('withdraw');args.append([amount]);remaining=amount;take=[0]*5
            # Deliberately explicit one-note-at-a-time greedy oracle.
            for i in range(4,-1,-1):
                while take[i]<cash[i] and remaining>=denoms[i]:take[i]+=1;remaining-=denoms[i]
            if remaining:expected.append([-1])
            else:cash=[x-y for x,y in zip(cash,take)];expected.append(take)
    add(2241,[ops,args],expected)
    depth=R.randint(1,4);vals=[R.randint(0,20) for _ in range((1<<depth)-1)];expected=[]
    for level in range(depth):
        row=vals[(1<<level)-1:(1<<(level+1))-1];expected.extend(row[::-1] if level%2 else row)
    add(2415,[vals],expected)
    def descendants(i):
        if i>=len(vals):return []
        return [vals[i]]+descendants(2*i+1)+descendants(2*i+2)
    add(2265,[vals],sum(vals[i]==sum(descendants(i))//len(descendants(i)) for i in range(len(vals))))
    n=R.randint(1,5);m=R.randint(1,6);seats=[[False]*m for _ in range(n)];ops=['BookMyShow'];args=[[n,m]];expected=[None]
    for j in range(30):
        op=R.choice(['gather','scatter']);k=R.randint(1,n*m);limit=R.randrange(n);ops.append(op);args.append([k,limit]);out=[] if op=='gather' else False
        if op=='gather':
            found=False
            for r in range(limit+1):
                for c in range(m-k+1):
                    if not any(seats[r][c:c+k]):
                        for x in range(c,c+k):seats[r][x]=True
                        out=[r,c];found=True;break
                if found:break
        else:
            free=[(r,c) for r in range(limit+1) for c in range(m) if not seats[r][c]]
            if len(free)>=k:
                for r,c in free[:k]:seats[r][c]=True
                out=True
        expected.append(out)
    add(2286,[ops,args],expected)
    n=R.randint(1,15);memory=[0]*n;ops=['Allocator'];args=[[n]];expected=[None]
    for j in range(30):
        mid=R.randint(1,5)
        if R.randrange(3):
            size=R.randint(1,n);ops.append('allocate');args.append([size,mid]);index=next((i for i in range(n-size+1) if not any(memory[i:i+size])),-1)
            if index>=0:memory[index:index+size]=[mid]*size
            expected.append(index)
        else:
            ops.append('freeMemory');args.append([mid]);expected.append(memory.count(mid));memory=[0 if v==mid else v for v in memory]
    add(2502,[ops,args],expected)
    words=R.sample([''.join(t) for t in itertools.product('abc',repeat=2)],R.randint(1,8));groups=[R.randint(1,3) for _ in words];best=0
    for mask in range(1<<len(words)):
        chosen=[i for i in range(len(words)) if mask>>i&1]
        if all(groups[i]!=groups[j] and sum(a!=b for a,b in zip(words[i],words[j]))==1 for i,j in zip(chosen,chosen[1:])):best=max(best,len(chosen))
    add(2901,[words,groups],{'optimal_length':best})
    n=R.randint(2,8);edges=[[i,R.randrange(i)] for i in range(1,n)];coins=[R.randrange(20) for _ in range(n)];k=R.randrange(10);parents={v:u for v,u in edges};best=-10**9
    for mask in range(1<<n):
        total=0
        for i in range(n):
            ancestor=i;shift=0
            while ancestor:
                ancestor=parents[ancestor];shift+=(mask>>ancestor)&1
            total+=(coins[i]>>(shift+1)) if mask>>i&1 else (coins[i]>>shift)-k
        best=max(best,total)
    add(2920,[edges,coins,k],best)

def matches(c,got):
    if c['id']==2901 and isinstance(c['expected'],dict):
        words,groups=c['args']
        if not isinstance(got,list) or len(got)!=c['expected']['optimal_length'] or any(w not in words for w in got):return False
        indices=[words.index(w) for w in got]
        return all(i<j and groups[i]!=groups[j] and len(words[i])==len(words[j]) and sum(a!=b for a,b in zip(words[i],words[j]))==1 for i,j in zip(indices,indices[1:]))
    return got==c['expected']

if __name__=='__main__':
    started=time.time();fail=[]
    for c in cases:
        try:
            got=pycall(c['id'],c['args'])
            if not matches(c,got):fail.append([c,'python',got])
        except Exception as e:fail.append([c,'python exception',repr(e)])
    result=subprocess.run(['node',str(BASE/'batch1/runner.js')],input=json.dumps(cases),text=True,capture_output=True,check=True)
    js=json.loads(result.stdout)
    for c,got in zip(cases,js):
        if not matches(c,got):fail.append([c,'javascript',got])
    report={'seed':50601,'case_count':len(cases),'language_assertions':2*len(cases),'elapsed_seconds':time.time()-started,'by_id':{},'failures':fail}
    for c in cases:
        d=report['by_id'].setdefault(str(c['id']),{});d[c['kind']]=d.get(c['kind'],0)+1
    (BASE/'batch1/test-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'assertions':2*len(cases),'failures':fail[:10]},indent=2))
    raise SystemExit(bool(fail))
