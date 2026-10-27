"""Bounded, deterministic development tests. No hidden judge or qualification."""
import importlib.util,json,random,subprocess,time,math,itertools,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
CASES=json.loads((HERE/'public-examples.json').read_text());rng=random.Random(3061)
def add(i,a,e,kind='independent_bruteforce'):CASES.append(dict(id=i,args=a,expected=e,kind=kind))
for _ in range(45):
 n=rng.randint(1,8);a=[rng.randint(1,12) for _ in range(n)];b=[rng.randint(1,12) for _ in range(n)]
 add(2321,[a,b],max([sum(a),sum(b)]+[max(sum(a[:l]+b[l:r]+a[r:]),sum(b[:l]+a[l:r]+b[r:])) for l in range(n) for r in range(l+1,n+1)]))
 add(2972,[a],sum(all(v[i]<v[i+1] for i in range(len(v)-1)) for l in range(n) for r in range(l+1,n+1) for v in [a[:l]+a[r:]]))
 k=rng.randint(1,n);add(2941,[a,k],max(sum(a[l:r])*math.gcd(*a[l:r]) for l in range(n) for r in range(l+k,n+1)))
 add(3101,[[v%2 for v in a]],sum(all(a[i]%2!=a[i+1]%2 for i in range(l,r-1)) for l in range(n) for r in range(l+1,n+1)))
 add(2909,[a],min([a[i]+a[j]+a[k] for i in range(n) for j in range(i+1,n) for k in range(j+1,n) if a[i]<a[j]>a[k]] or [-1]))
 best=0
 for mask in range(1<<n):
  picked=[a[i] for i in range(n) if mask>>i&1]
  if all(abs(x-y)>2 or x==y for x in picked for y in picked):best=max(best,sum(picked))
 add(3186,[a],best)
 states={0}
 for v in sorted(a):states|={s+v for s in list(states) if s<v}
 add(3180,[a],max(states))
 x=[rng.randint(1,n) for _ in range(max(n,2))];y=[rng.randint(1,n) for _ in x];_,i,j=min((abs(x[i]-x[j])+abs(y[i]-y[j]),i,j) for i in range(len(x)) for j in range(i+1,len(x)))
 add(2613,[x,y],[i,j])
 aa=[v%4 for v in a];bb=[v%4 for v in b];total=0
 for l in range(n):
  for r in range(l+1,n+1):
   total+=sum(sum(aa[i] if mask>>(i-l)&1 else -bb[i] for i in range(l,r))==0 for mask in range(1<<(r-l)))
 add(2143,[aa,bb],total)
 ban=list(set(v%20+1 for v in a));limit=rng.randint(1,20);budget=rng.randint(1,80);s=count=0
 for v in range(1,limit+1):
  if v not in ban and s+v<=budget:s+=v;count+=1
 add(2557,[ban,limit,budget],count)
 present=[v%6 for v in a];future=[v%10 for v in b];budget=rng.randint(0,20)
 add(2291,[present,future,budget],max(sum(future[i]-present[i] for i in range(n) if mask>>i&1) for mask in range(1<<n) if sum(present[i] for i in range(n) if mask>>i&1)<=budget))
 vals=[v-6 for v in a];scores=[]
 for mask in range(1<<max(0,n-1)):
  sign=1;s=vals[0]
  for i in range(1,n):
   sign=1 if mask>>(i-1)&1 else -sign;s+=sign*vals[i]
  scores.append(s)
 add(3196,[vals],max(scores))
 # Full enumeration of allowed disjoint tree pairs.
 if n>=2:
  par=[-1]+[rng.randrange(i) for i in range(1,n)];edges=[[i,par[i]] for i in range(1,n)];sub=[{i} for i in range(n)]
  for i in range(n-1,0,-1):sub[par[i]]|=sub[i]
  sums=[sum(a[j] for j in s) for s in sub];ans=max([sums[i]^sums[j] for i in range(n) for j in range(i) if not sub[i]&sub[j]]or[0]);add(2479,[n,edges,a],ans)
  ss=''.join(rng.choice('abc') for _ in range(n));masks=[0]*n
  for i in range(1,n):masks[i]=masks[par[i]]^(1<<(ord(ss[i])-97))
  add(2791,[par,ss],sum((masks[i]^masks[j]).bit_count()<=1 for i in range(n) for j in range(i)))
 # Mutating-character query naive scan.
 s=''.join(rng.choice('abc') for _ in range(n));qs=''.join(rng.choice('abc') for _ in range(8));ix=[rng.randrange(n) for _ in qs];v=list(s);outs=[]
 for ch,i in zip(qs,ix):
  v[i]=ch;outs.append(max(len(list(group)) for _,group in itertools.groupby(v)))
 add(2213,[s,qs,ix],outs)
 # Positive array operation scheduling, enumerate all allocation counts via BFS small domain.
 nums=[v%7+1 for v in a[:3]];x=rng.randint(2,6);y=rng.randint(1,x-1);states={tuple(nums)};steps=0
 while not any(max(v)<=0 for v in states):
  states={tuple(max(0,v[j]- (x if j==i else y)) for j in range(len(v))) for v in states for i in range(len(v))};steps+=1
 add(2702,[nums,x,y],steps)
 # Sparse interval count vs literal integer union.
 ops=['CountIntervals'];args=[[]];out=[None];seen=set()
 for __ in range(8):
  l=rng.randint(1,30);r=rng.randint(l,35);ops+=['add','count'];args+=[[l,r],[]];seen.update(range(l,r+1));out+=[None,len(seen)]
 add(2276,[ops,args],out)

# Further bounded independent models cover every nonconstructive contract.
for trial in range(35):
 n=rng.randint(2,7);a=[rng.randint(1,9) for _ in range(n)]
 # Small minimax grid routes, directly score second robot's route.
 grid=[a,[rng.randint(1,9) for _ in a]];best=10**9
 for first in range(n):
  remaining=[grid[0][:],grid[1][:]]
  for j in range(first+1):remaining[0][j]=0
  for j in range(first,n):remaining[1][j]=0
  best=min(best,max(sum(remaining[0][:j+1])+sum(remaining[1][j:]) for j in range(n)))
 add(2017,[grid],best)
 # Inorder-level serialized complete tree, descendants enumerated independently.
 values=[rng.randint(0,5) for _ in range(n)]
 desc=lambda i:([i]+desc(2*i+1)+desc(2*i+2)) if i<n else []
 add(1973,[values],sum(values[i]==sum(values[j] for j in desc(i)[1:]) for i in range(n)))
 levels={}
 for i,v in enumerate(values):levels.setdefault((i+1).bit_length(),[]).append(v)
 add(3157,[values],min(levels,key=lambda d:(sum(levels[d]),d)))
 add(2773,[values],n.bit_length()-1)
 inp=sorted([rng.randint(-20,20) for _ in range(n)],key=abs);add(2046,[inp],sorted(inp))
 queries=[rng.randint(1,n) for _ in range(8)];on=set()
 for q in queries:
  for v in range(1,n+1):
   k=v
   while k>q:k//=2
   if k==q:
    if v in on:on.remove(v)
    else:on.add(v)
 add(2445,[n,queries],len(on))
 # All simple paths, tiny weighted graph.
 edges=[[i,j,rng.randint(0,9)] for i in range(n) for j in range(i) if rng.random()<.4];k=rng.randint(1,n);g=[[] for _ in range(n)]
 for u,v,w in edges:g[u].append((v,w));g[v].append((u,w))
 def paths(u,seen,t,cost):
  if t==0:return cost
  return max([paths(v,seen|{v},t-1,cost+w) for v,w in g[u] if v not in seen]or[-1])
 add(2247,[n,edges,k],max(paths(u,{u},k,0) for u in range(n)))
 # Move minimum to front and maximum to back via literal adjacent swaps.
 v=a[:];steps=0
 while v[0]!=min(v):
  i=v.index(min(v));v[i-1],v[i]=v[i],v[i-1];steps+=1
 while v[-1]!=max(v):
  i=len(v)-1-v[::-1].index(max(v));v[i],v[i+1]=v[i+1],v[i];steps+=1
 add(2340,[a],steps)
 # Semi-repetitive substring enumeration.
 st=''.join(str(v%3) for v in a);add(2730,[st],max(r-l for l in range(n) for r in range(l+1,n+1) if sum(st[i]==st[i+1] for i in range(l,r-1))<=1))
 # Every retained digit subsequence.
 st=''.join(str(v%10) for v in a);add(2844,[st],min(n-len(t) for mask in range(1<<n) for t in [''.join(st[i] for i in range(n) if mask>>i&1)] if (int(t) if t else 0)%25==0))
 # Mountain sequences brute-force all heights for tiny bounded caps.
 caps=[v%3+1 for v in a[:5]];best=0
 for v in itertools.product(*(range(1,c+1) for c in caps)):
  if any(all(v[i]<=v[i+1] for i in range(p)) and all(v[i]>=v[i+1] for i in range(p,len(v)-1)) for p in range(len(v))):best=max(best,sum(v))
 add(2865,[caps],best)
 # Remove adjacent conflicts: maximal independent set in path of original bad edges.
 st=''.join(chr(97+v%5) for v in a);add(2957,[st],min(mask.bit_count() for mask in range(1<<n) if all(abs(ord(st[i])-ord(st[i+1]))>1 or mask>>i&1 or mask>>(i+1)&1 for i in range(n-1))))
 # Prefix rectangle sum from scratch; pairwise reachable grid score.
 grid=[[rng.randint(0,9) for _ in range(3)] for _ in range(3)];k=rng.randint(0,45)
 add(3070,[grid,k],sum(sum(grid[x][y] for x in range(r+1) for y in range(c+1))<=k for r in range(3) for c in range(3)))
 add(3148,[grid],max(grid[r][c]-grid[x][y] for r in range(3) for c in range(3) for x in range(r+1) for y in range(c+1) if (r,c)!=(x,y)))
 add(2428,[grid],sum(grid[0])+grid[1][1]+sum(grid[2]))
 grid=[[v%2 for v in row] for row in grid];add(3128,[grid],sum(grid[r][c]*grid[r][x]*grid[y][c] for r in range(3) for c in range(3) for x in range(3) for y in range(3) if x!=c and y!=r))
 days=rng.randint(1,20);meet=[sorted([rng.randint(1,days),rng.randint(1,days)]) for _ in range(5)]
 add(3169,[days,meet],sum(not any(l<=d<=r for l,r in meet) for d in range(1,days+1)))
 road=''.join('x' if v%2 else '.' for v in a);budget=rng.randint(0,10);best=0
 for mask in range(1<<n):
  if any(mask>>i&1 and road[i]!='x' for i in range(n)):continue
  cost=mask.bit_count()+sum(mask>>i&1 and (i==0 or not(mask>>(i-1)&1)) for i in range(n))
  if cost<=budget:best=max(best,mask.bit_count())
 add(3119,[road,budget],best)
 # Public integer history semantics; each -1 walks back within its consecutive run.
 inp=[v if v%3 else -1 for v in a];hist=[];back=0;out=[]
 for v in inp:
  if v!=-1:hist.append(v);back=0
  else:back+=1;out.append(hist[-back] if back<=len(hist) else -1)
 add(2899,[inp],out)
 # Range-frequency stateful adapter.
 ops=['RangeFreqQuery'];args=[[a]];out=[None]
 for __ in range(5):
  l=rng.randrange(n);r=rng.randrange(l,n);v=rng.randint(1,9);ops.append('query');args.append([l,r,v]);out.append(a[l:r+1].count(v))
 add(2080,[ops,args],out)
 # Two-edge parity augmentation, enumerate all absent edges.
 ed=[[i+1,j+1] for i in range(n) for j in range(i) if rng.random()<.3];have={tuple(sorted(e)) for e in ed};missing=[(i,j) for i in range(1,n+1) for j in range(i+1,n+1) if (i,j) not in have];ok=False
 for added in [()]+[(e,) for e in missing]+list(itertools.combinations(missing,2)):
  deg=[0]*(n+1)
  for u,v in ed+list(added):deg[u]+=1;deg[v]+=1
  if all(d%2==0 for d in deg):ok=True;break
 add(2508,[n,ed],ok)
 # Reachability champion, independent of direct indegree implementation.
 ed=[[i,j] for i in range(n) for j in range(i+1,n) if rng.random()<.3];reach=[{i} for i in range(n)]
 for i in range(n-1,-1,-1):
  for u,v in ed:
   if u==i:reach[i]|=reach[v]
 winners=[i for i in range(n) if len(reach[i])==n];add(2924,[n,ed],winners[0] if len(winners)==1 else -1)
 # Rectangles exhaustive breakpoint DP.
 pts=[[v,rng.randint(0,9)] for v in a];w=rng.randint(0,4);xs=sorted(set(a));dp=[0]*(len(xs)+1)
 for i in range(len(xs)-1,-1,-1):
  j=i
  while j<len(xs) and xs[j]-xs[i]<=w:j+=1
  dp[i]=1+dp[j]
 add(3111,[pts,w],dp[0])
 word=''.join(chr(97+v%3) for v in a);k=1;add(3137,[word,k],len(word)-max(word.count(ch) for ch in set(word)))
# Exact exhaustive low-domain contracts.
for n in range(1,9):
 add(3211,[n],[''.join(s) for s in itertools.product('01',repeat=n) if '00' not in ''.join(s)])
for a in range(1,20):
 add(3032,[a,a+30],sum(all(str(v).count(c)==1 for c in str(v)) for v in range(a,a+31)))
for n in range(4,30):
 def digits(x,b):
  out=[]
  while x:out.append(x%b);x//=b
  return out
 add(2396,[n],all(digits(n,b)==digits(n,b)[::-1] for b in range(2,n-1)))
for pattern in ['I','D','ID','DI','IID','DDI','DID']:
 expected=next(''.join(map(str,p)) for p in itertools.permutations(range(1,len(pattern)+2)) if all((p[i]<p[i+1])==(ch=='I') for i,ch in enumerate(pattern)))
 add(2375,[pattern],expected)


for trial in range(25):
 n=rng.randint(2,7);par=[-1]+[rng.randrange(i) for i in range(1,n)]
 ancestors=[]
 for v in range(n):
  chain=[];u=par[v]
  while u>=0:chain.append(u);u=par[u]
  ancestors.append(chain)
 ops=['LockingTree'];args=[[par]];out=[None];locked={}
 for _ in range(20):
  op=rng.choice(['lock','unlock','upgrade']);v=rng.randrange(n);user=rng.randint(1,3);ops.append(op);args.append([v,user]);ok=False
  if op=='lock' and v not in locked:locked[v]=user;ok=True
  elif op=='unlock' and locked.get(v)==user:del locked[v];ok=True
  elif op=='upgrade' and v not in locked and not any(u in locked for u in ancestors[v]):
   children=[u for u in locked if v in ancestors[u]]
   if children:
    for u in children:del locked[u]
    locked[v]=user;ok=True
  out.append(ok)
 add(1993,[ops,args],out)
 pts=[[rng.randint(1,6),rng.randint(1,6)] for _ in range(n)];k=rng.randint(1,n)
 answer=next(t for t in range(15) if any(sum(abs(x-a)+abs(y-b)<=t for a,b in pts)>=k for x in range(-10,17) for y in range(-10,17)))
 add(1956,[pts,k],answer)
 # Bitset literal model.
 bits=[0]*n;ops=['Bitset'];args=[[n]];out=[None]
 for _ in range(25):
  op=rng.choice(['fix','unfix','flip','all','one','count','toString']);ops.append(op);i=rng.randrange(n);args.append([i] if op in ('fix','unfix') else [])
  if op=='fix':bits[i]=1;res=None
  elif op=='unfix':bits[i]=0;res=None
  elif op=='flip':bits=[1-v for v in bits];res=None
  elif op=='all':res=all(bits)
  elif op=='one':res=any(bits)
  elif op=='count':res=sum(bits)
  else:res=''.join(map(str,bits))
  out.append(res)
 add(2166,[ops,args],out)
 # Rank tracker naive sorted online state.
 ops=['SORTracker'];args=[[]];out=[None];seen=[];gets=0
 for i in range(12):
  name=chr(97+i);score=rng.randint(1,5);ops.append('add');args.append([name,score]);out.append(None);seen.append((-score,name))
  if rng.random()<.7:ops.append('get');args.append([]);out.append(sorted(seen)[gets][1]);gets+=1
 add(2102,[ops,args],out)
 # Food rating direct scans and lexicographic ties.
 foods=['f'+str(i) for i in range(n)];cuisines=['c'+str(i%2) for i in range(n)];ratings=[rng.randint(1,8) for _ in foods];state=ratings[:]
 ops=['FoodRatings'];args=[[foods,cuisines,ratings]];out=[None]
 for _ in range(20):
  if rng.random()<.5:
   i=rng.randrange(n);rating=rng.randint(1,8);ops.append('changeRating');args.append([foods[i],rating]);state[i]=rating;out.append(None)
  else:
   c=rng.choice(cuisines);ops.append('highestRated');args.append([c]);out.append(min(((-state[i],foods[i]) for i in range(n) if cuisines[i]==c))[1])
 add(2353,[ops,args],out)
 # Dictionary encryption by full enumeration.
 keys=list('abc');values=['aa','ab','aa'];dictionary=list(set(''.join(rng.choice(keys) for _ in range(3)) for _ in range(10)));mapping=dict(zip(keys,values));ops=['Encrypter'];args=[[keys,values,dictionary]];out=[None]
 for word in dictionary:
  enc=''.join(mapping[c] for c in word);ops+=['encrypt','decrypt'];args+=[[word],[enc]];out+=[enc,sum(''.join(mapping[c] for c in w)==enc for w in dictionary)]
 add(2227,[ops,args],out)
 # Alice enumerate all root-to-leaf paths; Bob direct ancestor chain.
 amount=[2*rng.randint(-5,5) for _ in range(n)];bob=rng.randrange(1,n);bt={};u=bob;t=0
 while u>=0:bt[u]=t;t+=1;u=par[u]
 children=[[i for i in range(1,n) if par[i]==u] for u in range(n)];scores=[]
 for leaf in range(n):
  if children[leaf]:continue
  path=list(reversed([leaf]+ancestors[leaf]));score=0
  for t,u in enumerate(path):
   if t<bt.get(u,10**9):score+=amount[u]
   elif t==bt.get(u):score+=amount[u]//2
  scores.append(score)
 add(2467,[[[i,par[i]] for i in range(1,n)],bob,amount],max(scores))
 # Valid binary tree preorder order, compare explicit DFS respecting first-child appearance.
 par=[-1];child=[[] for _ in range(n)]
 for i in range(1,n):
  p=rng.choice([j for j in range(i) if len(child[j])<2]);par.append(p);child[p].append(i)
 order=list(range(1,n));rng.shuffle(order);order=[0]+order;pos={v:i for i,v in enumerate(order)}
 def walk(u):return [u]+sum((walk(v) for v in sorted(child[u],key=pos.get)),[])
 add(2764,[[[u,par[u]] for u in order]],walk(0)==order)
 # Literal BFS between small numbers (independent wider fixed state domain).
 x=rng.randint(1,60);y=rng.randint(1,30);q=[x];dist={x:0}
 for u in q:
  if u==y:break
  nxt=[u-1,u+1]+([u//5] if u%5==0 else [])+([u//11] if u%11==0 else [])
  for v in nxt:
   if 0<=v<=150 and v not in dist:dist[v]=dist[u]+1;q.append(v)
 add(2998,[x,y],dist[y])
 # Array modulo operation game exhaustive canonical multisets.
 vals=tuple(sorted(rng.randint(1,5) for _ in range(rng.randint(1,5))));states={vals};q=[vals];best=len(vals)
 for v in q:
  best=min(best,len(v))
  for i in range(len(v)):
   for j in range(len(v)):
    if i!=j and v[i]>0 and v[j]>0:
     nxt=tuple(sorted([v[k] for k in range(len(v)) if k not in (i,j)]+[v[i]%v[j]]))
     if nxt not in states:states.add(nxt);q.append(nxt)
 add(3012,[list(vals)],best)
 # Question marks: exhaustive 26-letter assignments for <=2 unknowns.
 st=''.join(rng.choice('ab?') for _ in range(4))
 while st.count('?')>2:st=st.replace('?','a',1)
 opts=[]
 for repl in itertools.product('abcdefghijklmnopqrstuvwxyz',repeat=st.count('?')):
  it=iter(repl);v=''.join(next(it) if c=='?' else c for c in st);score=sum(v.count(c)*(v.count(c)-1)//2 for c in set(v));opts.append((score,v))
 add(3081,[st],min(opts)[1])
# Single chess piece geometry and two-piece exhaustive motion tuples.
for piece in ['rook','bishop','queen']:
 for r,c in [(1,1),(4,4),(8,3)]:
  expected=1+sum((piece in ('rook','queen') and (a==r or b==c) or piece in ('bishop','queen') and abs(a-r)==abs(b-c)) for a in range(1,9) for b in range(1,9) if (a,b)!=(r,c))
  add(2056,[[piece],[[r,c]]],expected)
# Water simulation in lockstep, no precomputed flood-arrival table.
for _ in range(30):
 m=n=4;land=[[rng.choice('....X*') for _ in range(n)] for _ in range(m)];land[0][0]='S';land[3][3]='D';wet={(r,c) for r in range(m) for c in range(n) if land[r][c]=='*'};front={(0,0)};seen=set(front);answer=-1
 def nb(p):
  r,c=p;return [(a,b) for a,b in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)] if 0<=a<m and 0<=b<n]
 for t in range(m*n+1):
  if (3,3) in front:answer=t;break
  wet|={p for w in list(wet) for p in nb(w) if land[p[0]][p[1]] not in 'XD'}
  front={p for v in front for p in nb(v) if p not in wet and p not in seen and land[p[0]][p[1]]!='X'};seen|=front
 add(2814,[land],answer)

# Numeric extremes and full-product check, without Python's integer string conversion limit.
add(2941,[[1000000]*10000,1],10**16,'numeric_boundary')
add(2557,[[],10**9,10**15],44721359,'numeric_boundary')
def product_oracle(l,r):
 v=math.prod(range(l,r+1));z=0
 while v%10==0:v//=10;z+=1
 if v<10**10:return f'{v}e{z}'
 chunks=[]
 while v:chunks.append(v%1000000000);v//=1000000000
 s=str(chunks[-1])+''.join(f'{x:09d}' for x in chunks[-2::-1]);return f'{s[:5]}...{s[-5:]}e{z}'
for l,r in [(1,10000),(9990,10000),(1,50),(25,80)]:add(2117,[l,r],product_oracle(l,r),'independent_exact_product')
modules={};counts={};start=time.monotonic()
for case in CASES:
 i=case['id']
 if i not in modules:
  spec=importlib.util.spec_from_file_location('candidate'+str(i),ROOT/'python'/f'{i}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);modules[i]=m
 actual=modules[i].solve(*case['args'])
 assert actual==case['expected'],(i,case['args'],actual,case['expected'])
 counts[i]=counts.get(i,0)+1
# Structural knight checks are independent of candidate ordering.
knights=[]
for m,n,r,c in [(1,1,0,0),(3,4,0,0),(5,5,0,0),(5,5,2,2)]:
 spec=importlib.util.spec_from_file_location('knight',ROOT/'python'/'2664.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 board=mod.solve(m,n,r,c);pos={board[i][j]:(i,j) for i in range(m) for j in range(n)}
 assert len(pos)==m*n and set(pos)==set(range(m*n)) and pos[0]==(r,c)
 assert all(sorted([abs(pos[i][0]-pos[i-1][0]),abs(pos[i][1]-pos[i-1][1])])==[1,2] for i in range(1,m*n))
 knights.append([m,n,r,c]);counts[2664]=counts.get(2664,0)+1
payload={'cases':CASES,'knights':knights}
js=r'''const fs=require('fs'),path=require('path');const p=JSON.parse(fs.readFileSync(0,'utf8'));const root=process.argv[1];const norm=x=>typeof x==='bigint'?x.toString():Array.isArray(x)?x.map(norm):x;for(const c of p.cases){let actual=require(path.join(root,'javascript',c.id+'.js'))(...c.args);const expected=typeof c.expected==='number'&&!Number.isSafeInteger(c.expected)?BigInt(c.expected).toString():c.expected;if(JSON.stringify(norm(actual))!==JSON.stringify(expected))throw Error(JSON.stringify([c.id,c.args,actual,expected],(_,v)=>typeof v==='bigint'?v.toString():v));}for(const [m,n,r,c]of p.knights){let b=require(path.join(root,'javascript','2664.js'))(m,n,r,c),pos=new Map();for(let i=0;i<m;i++)for(let j=0;j<n;j++)pos.set(b[i][j],[i,j]);if(pos.size!==m*n||JSON.stringify(pos.get(0))!==JSON.stringify([r,c]))throw Error('knight shape');for(let i=1;i<m*n;i++){let a=pos.get(i),b=pos.get(i-1),d=[Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1])].sort();if(JSON.stringify(d)!=='[1,2]')throw Error('knight edge');}}console.log(JSON.stringify({passed:p.cases.length+ p.knights.length}));'''
res=subprocess.run(['node','-e',js,str(ROOT)],input=json.dumps(payload),text=True,capture_output=True,timeout=60)
assert res.returncode==0,res.stderr
report={'kind':'development_only','seed':3061,'python_passed':len(CASES)+len(knights),'javascript':json.loads(res.stdout),'counts_by_id':counts,'elapsed_seconds':round(time.monotonic()-start,3),'limitations':'Public examples and independently authored bounded oracles only. Not hidden judge, admission, native interface qualification or confirmation.'}
(HERE/'test-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
