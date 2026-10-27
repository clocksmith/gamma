"""Public examples plus deterministic independently derived small-input oracles.
No hidden tests, judge access, admission, or soundness qualification.
"""
import collections, copy, functools, hashlib, heapq, importlib.util, itertools, json, math, random, subprocess, time, sys, datetime
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
R=random.Random(50604)
CASES=collections.defaultdict(list)
def case(i,a,e,kind='independent_small_oracle'): CASES[i].append((a,e,kind))
def subsets(a):
 for mask in range(1<<len(a)):yield [a[i] for i in range(len(a)) if mask>>i&1]
def runs(s):return all(not(s[i]==s[i+1]==s[i+2]) for i in range(len(s)-2))
def path_dist(n,edges):
 d=[[0 if i==j else 10**12 for j in range(n)] for i in range(n)]
 for u,v,*w in edges:d[u][v]=d[v][u]=min(d[u][v],w[0] if w else 1)
 for k in range(n):
  for i in range(n):
   for j in range(n):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
 return d

def build():
 for rec in json.load(open(ROOT/'batch4/manifest.json')):
  for a,e in rec['cases']:case(rec['problem_id'],a,e,'public_example')
 for rep in range(25):
  n=R.randint(3,7);a=[R.randint(1,6) for _ in range(n)];s=''.join(R.choices('abc',k=n))
  valid=[''.join(t) for t in subsets(s) if runs(t)]
  # Greedy should attain the independently enumerated optimal subsequence length.
  best=max(map(len,valid));candidate=''.join(c for c,g in itertools.groupby(s) for _ in range(min(2,len(list(g)))))
  assert len(candidate)==best;case(1957,[s],candidate)
  v=[R.randrange(i+1) for i in range(n)];counts=[0]*n;seen=set();room=day=0
  while len(seen)<n:
   seen.add(room)
   if len(seen)==n:break
   counts[room]+=1;room=v[room] if counts[room]%2 else (room+1)%n;day+=1
  case(1997,[v],day)
  cps=[i for i in range(1,n-1) if (a[i]>a[i-1] and a[i]>a[i+1]) or (a[i]<a[i-1] and a[i]<a[i+1])]
  ds=[y-x for x,y in itertools.combinations(cps,2)];case(2058,[a], [min(ds),max(ds)] if ds else [-1,-1])
  stones=[0]+sorted(R.sample(range(1,30),n-1));best=10**9
  for mask in range(1<<(n-2)):
   p=[0]+[i for i in range(1,n-1) if mask>>(i-1)&1]+[n-1];q=[0]+[i for i in range(1,n-1) if not mask>>(i-1)&1]+[n-1]
   best=min(best,max(stones[y]-stones[x] for z in (p,q) for x,y in zip(z,z[1:])))
  case(2498,[stones],best)
  # Any two changed elements can be placed within the range of unchanged values.
  best=min(max(b)-min(b) for inds in itertools.combinations(range(n),n-2) for b in [[a[i] for i in inds]])
  case(2567,[a],best)
  small=a[:4];q=collections.deque([(tuple(small),0)]);seen={tuple(small)};ans=-1
  while q:
   state,d=q.popleft()
   if all(x==1 for x in state):ans=d;break
   for i in range(len(state)-1):
    g=math.gcd(state[i],state[i+1])
    for j in (i,i+1):
     t=list(state);t[j]=g;t=tuple(t)
     if t not in seen:seen.add(t);q.append((t,d+1))
  case(2654,[small],ans)
  bits=''.join(R.choices('01',k=5));start=int(bits,2);dist={start:0};h=[(0,start)]
  while h:
   cost,st=heapq.heappop(h)
   if cost!=dist[st]:continue
   if st in (0,31):break
   for k in range(1,6):
    for mask in ((1<<k)-1,((1<<k)-1)<<(5-k)):
     t=st^mask;c=cost+k
     if c<dist.get(t,10**9):dist[t]=c;heapq.heappush(h,(c,t))
  case(2712,[bits],cost)
  m,z=R.randint(2,5),R.randint(2,5);cells=R.sample([(i,j) for i in range(m) for j in range(z)],R.randint(0,m*z));C=set(cells);hist=[0]*5
  for i in range(m-1):
   for j in range(z-1):hist[sum((x,y) in C for x in (i,i+1) for y in (j,j+1))]+=1
  case(2768,[m,z,cells],hist)
  t=R.randint(0,7);case(2798,[a,t],len([x for x in a if x>=t]))
  groups=R.choices([0,1],k=n);words=[chr(97+i) for i in range(n)];selected=[words[i] for i in range(n) if i==0 or groups[i]!=groups[i-1]]
  longest=max(len(t) for t in subsets(list(range(n))) if all(groups[x]!=groups[y] for x,y in zip(t,t[1:])))
  assert len(selected)==longest;case(2900,[words,groups],selected)
  k=R.randint(1,n);case(2962,[a,k],sum(a[i:j].count(max(a))>=k for i in range(n) for j in range(i+1,n+1)))
  aa=a[:6];bb=R.choices(range(1,8),k=6);aa=(aa*2)[:6]
  case(3002,[aa,bb],max(len(set(x)|set(y)) for x in itertools.combinations(aa,3) for y in itertools.combinations(bb,3)))
  word=s;cur=list(word)
  while cur:
   old=cur[:];seen=set();cur=[c for c in cur if c in seen or not(seen.add(c) is None)]
  case(3039,[word],''.join(old))
  counts=list(collections.Counter(s).values());k=R.randint(0,3);best=len(s)
  for kept in itertools.product(*(range(c+1) for c in counts)):
   nz=[c for c in kept if c]
   if not nz or max(nz)-min(nz)<=k:best=min(best,len(s)-sum(kept))
  case(3085,[s,k],best)
  st=''.join(R.choices('aByXxAbC',k=n));case(3121,[st],sum(c in st and c.upper() in st and max(i for i,x in enumerate(st) if x==c)<st.index(c.upper()) for c in 'abcxyz'))
  case(3138,[s],next(k for k in range(1,n+1) if n%k==0 and len({tuple(sorted(s[i:i+k])) for i in range(0,n,k)})==1))
  queries=[sorted(R.choices(range(n),k=2)) for _ in range(5)];case(3152,[a,queries],[all(a[i]%2!=a[i+1]%2 for i in range(l,r)) for l,r in queries])
  queries=[[R.randrange(5),R.randint(1,6)] for _ in range(10)];balls={};out=[]
  for b,c in queries:balls[b]=c;out.append(len(set(balls.values())))
  case(3160,[4,queries],out)
  st='';remaining=0
  for _ in range(10):
   c='*' if remaining and R.random()<.3 else R.choice('abc');st+=c;remaining+=-1 if c=='*' else 1
  states={''}
  for c in st:
   if c!='*':states={x+c for x in states}
   else:states={x[:j]+x[j+1:] for x in states for j,ch in enumerate(x) if ch==min(x)}
  case(3170,[st],min(states))
  reach={0}
  for _ in range(n):reach|={v+x for v in reach for x in a if x>v}
  case(3181,[a],max(reach))
  case(3201,[a],max(len(t) for t in subsets(a) if len({(x+y)%2 for x,y in zip(t,t[1:])})<=1))
  grid=[R.choices('XY.',k=3) for _ in range(3)];ans=0
  for i in range(3):
   for j in range(3):
    flat=[grid[x][y] for x in range(i+1) for y in range(j+1)];ans+=flat.count('X')>0 and flat.count('X')==flat.count('Y')
  case(3212,[grid],ans)
  lights=[[R.randint(-5,5),R.randint(0,4)] for _ in range(4)];lo=min(x-r for x,r in lights);hi=max(x+r for x,r in lights)
  case(2021,[lights],max(range(lo,hi+1),key=lambda p:sum(abs(p-x)<=r for x,r in lights)))
  case(2083,[s],sum(s[i]==s[j] for i in range(n) for j in range(i,n)))
  k=R.randint(0,n);case(2107,[a,k],max(len(set(a[:i]+a[i+k:])) for i in range(n-k+1)))
  damage=a;armor=R.randint(0,7);case(2214,[damage,armor],1+min(sum(damage[:i]+damage[i+1:])+max(0,x-armor) for i,x in enumerate(damage)))
  lights=[[R.randrange(n),R.randrange(n)] for _ in range(4)];req=R.choices(range(6),k=n)
  case(2237,[n,lights,req],sum(sum(abs(p-x)<=r for x,r in lights)>=req[p] for p in range(n)))
  short=[R.randrange(4) for _ in range(5)];best=min(sum(abs(x-y) for x,y in zip(short,b)) for b in itertools.product(range(4),repeat=5) if list(b)==sorted(b) or list(b)==sorted(b,reverse=True))
  case(2263,[short],best)
  edges=[[R.randrange(i),i] for i in range(1,n)];d=path_dist(n,edges);queries=[R.sample(range(n),3) for _ in range(4)]
  case(2277,[n,edges,queries],[min((i for i in range(n) if d[u][i]+d[i][v]==d[u][v]),key=lambda i:d[w][i]) for u,v,w in queries])
  peaks=[[R.randrange(6),R.randint(1,5)] for _ in range(5)]
  case(2345,[peaks],sum(not any(j!=i and y+abs(x-u)<=v for j,(u,v) in enumerate(peaks)) for i,(x,y) in enumerate(peaks)))
  books=[R.randrange(5) for _ in range(5)];best=0
  for l in range(5):
   for r in range(l+1,6):
    best=max(best,max((sum(t) for t in itertools.product(*(range(1,b+1) for b in books[l:r])) if all(x<y for x,y in zip(t,t[1:]))),default=0))
  case(2355,[books],best)
  tree=[[-1,-1]]+[[R.randrange(i),R.randint(-3,8)] for i in range(1,n)];best=0
  for chosen in subsets(list(range(1,n))):
   ends=[v for i in chosen for v in (i,tree[i][0])]
   if len(ends)==len(set(ends)):best=max(best,sum(tree[i][1] for i in chosen))
  case(2378,[tree],best)
  price=R.choices(range(1,9),k=5);taste=R.choices(range(1,8),k=5);money=R.randint(0,15);coupons=R.randrange(4);best=0
  for st in itertools.product(range(3),repeat=5):
   if st.count(2)<=coupons and sum(price[i]//(2 if x==2 else 1) for i,x in enumerate(st) if x)<=money:best=max(best,sum(taste[i] for i,x in enumerate(st) if x))
  case(2431,[price,taste,money,coupons],best)
  nums=R.sample(range(1,15),n);k=R.randint(1,5);case(2638,[nums,k],sum(all(abs(x-y)!=k for x,y in itertools.combinations(t,2)) for t in subsets(nums)))
  directed=[[i,j,R.randint(1,9)] for i in range(n) for j in range(n) if i!=j and R.random()<.2];dd=[[0 if i==j else 10**9 for j in range(n)] for i in range(n)]
  for u,v,w in directed:dd[u][v]=w
  for mid in range(n):
   for i in range(n):
    for j in range(n):dd[i][j]=min(dd[i][j],dd[i][mid]+dd[mid][j])
  marked=R.sample(range(n),2);src=R.randrange(n);ans=min(dd[src][x] for x in marked);case(2737,[n,directed,src,marked],ans if ans<10**9 else -1)
  rooks=[[R.randrange(n),R.randrange(n)] for _ in range(n)]
  ans=sum(min(sum(abs(rooks[i][axis]-p[i]) for i in range(n)) for p in itertools.permutations(range(n))) for axis in (0,1));case(3189,[rooks],ans)
  num=''.join(R.choices('01234',k=n))
  @functools.lru_cache(None)
  def ways(pos,last):
   if pos==len(num):return 1
   if num[pos]=='0':return 0
   return sum(ways(j,int(num[pos:j])) for j in range(pos+1,len(num)+1) if int(num[pos:j])>=last)
  case(1977,[num],ways(0,0))
  labels=R.choices(range(4),k=n);case(2782,[n,labels],len(set(labels)))
  prices=R.choices(range(1,20),k=n);queries=[[R.randrange(20),R.randint(1,n)] for _ in range(5)]
  case(2819,[prices,queries],[min(sum(p if p<=k else 2*k-p for p in t) for t in itertools.combinations(prices,m)) for k,m in queries])
  grid=[[R.choice([-1,1,2,3]) for _ in range(3)] for _ in range(3)];ans=0
  for x in range(3):
   for y in range(3):
    if grid[x][y]<0:continue
    seen={(x,y)};q=[(x,y)]
    for u,v in q:
     for p,t in ((u-1,v),(u+1,v),(u,v-1),(u,v+1)):
      if 0<=p<3 and 0<=t<3 and grid[p][t]>0 and (p,t) not in seen:seen.add((p,t));q.append((p,t))
    ans+=sum(grid[u][v] for u in range(3) for v in range(3) if grid[u][v]>0 and (u,v) not in seen)
  case(2852,[grid],ans)
  words=R.sample([a+b for a in 'abcd' for b in 'abc'],8);aa=sorted(words[:4]);bb=sorted(words[4:])
  @functools.lru_cache(None)
  def win(last,player):return any(not win(w,1-player) for w in (aa if player==0 else bb) if w>last and ord(w[0])-ord(last[0]) in (0,1))
  case(2868,[aa,bb],not win(aa[0],1))
  m,z=R.randint(2,4),R.randint(2,4);k=R.randint(1,6);src=[R.randint(1,m),R.randint(1,z)];dst=[R.randint(1,m),R.randint(1,z)];dp={tuple(src):1}
  for _ in range(k):
   nxt=collections.Counter()
   for (x,y),v in dp.items():
    for i in range(1,m+1):
     if i!=x:nxt[i,y]+=v
    for j in range(1,z+1):
     if j!=y:nxt[x,j]+=v
   dp=nxt
  case(2912,[m,z,k,src,dst],dp.get(tuple(dst),0))
  edges=[[R.randrange(i),i] for i in range(1,n)];values=a;parent={v:u for u,v in edges};internal={u for u,v in edges};paths=[]
  for leaf in range(n):
   if leaf in internal:continue
   path=[leaf]
   while path[-1]:path.append(parent[path[-1]])
   paths.append(set(path))
  case(2925,[edges,values],max(sum(values[i] for i in chosen) for chosen in subsets(list(range(n))) if all(p-set(chosen) for p in paths)))
  st=''.join(R.choices('abec',k=n));k=R.randint(1,8);case(2949,[st,k],sum((v:=sum(c in 'aeiou' for c in st[i:j]))*2==j-i and v*v%k==0 for i in range(n) for j in range(i+1,n+1)))
  vals=R.choices(range(1,15),k=n)+[1,2,3];nvals=len(vals);case(3073,[vals],max((vals[i]-vals[j]+vals[k] for i,j,k in itertools.combinations(range(nvals),3) if vals[i]<vals[j]<vals[k]),default=0))
  zero,one,lim=R.randint(1,4),R.randint(1,4),R.randint(1,4);case(3129,[zero,one,lim],sum(len(t)==zero and all(len(list(g))<=lim for _,g in itertools.groupby([0 if i in t else 1 for i in range(zero+one)])) for t in itertools.combinations(range(zero+one),zero)))
  grid=[R.choices([0,1],k=3) for _ in range(3)];ones=[(i,j) for i in range(3) for j in range(3) if grid[i][j]];best=len(ones)
  for kept in subsets(ones):
   if all(abs(x-u)+abs(y-v)!=1 for (x,y),(u,v) in itertools.combinations(kept,2)):best=min(best,len(ones)-len(kept))
  case(2123,[grid],best)
  ed=[[i,j,R.randint(1,6)] for i in range(n) for j in range(i+1,n) if R.random()<.4];dis=R.choices(range(1,15),k=n);d=[10**9]*n;d[0]=0
  for _ in range(n):
   for u,v,w in ed:
    if d[u]+w<dis[v]:d[v]=min(d[v],d[u]+w)
    if d[v]+w<dis[u]:d[u]=min(d[u],d[v]+w)
  case(3112,[n,ed,dis],[x if x<10**9 else -1 for x in d])
 for rep in range(15):
  n=R.randint(0,1000);balanced=[]
  # Construct balanced integers from digit multisets instead of increment-and-test.
  for digits in subsets(list(range(1,8))):
   chars=''.join(str(d)*d for d in digits)
   if 1<=len(chars)<=4:balanced.extend(int(''.join(p)) for p in set(itertools.permutations(chars)))
  case(2048,[n],min(x for x in balanced if x>n))
  a=R.choices(range(3,10),k=4);b=a[:]
  for _ in range(3):
   i,j=R.sample(range(4),2)
   if b[i]>2:b[i]-=2;b[j]+=2
  R.shuffle(b);cost=min(sum(abs(x-y) for x,y in zip(a,p)) for p in itertools.permutations(b) if all((x-y)%2==0 for x,y in zip(a,p)))//4
  case(2449,[a,b],cost)
  # Nine distinct letters: exactly one must occupy a second press position.
  counts=R.choices(range(1,6),k=9);word=''.join(chr(97+i)*c for i,c in enumerate(counts));case(3016,[word],sum(counts)+min(counts))
  st=''.join(R.choices('abcyz',k=3));k=R.randint(0,7)
  case(3106,[st,k],min(''.join(t) for t in itertools.product('abcdefghijklmnopqrstuvwxyz',repeat=3) if sum(min(abs(ord(x)-ord(y)),26-abs(ord(x)-ord(y))) for x,y in zip(st,t))<=k))
  pts=R.sample([(i,j) for i in range(3) for j in range(3)],R.randint(1,6));m=len(pts);lines=[1<<i for i in range(m)]
  for i,j in itertools.combinations(range(m),2):
   x,y=pts[i];u,v=pts[j];lines.append(sum(1<<k for k,(p,q) in enumerate(pts) if (p-x)*(v-y)==(q-y)*(u-x)))
  q=collections.deque([(0,0)]);seen={0}
  while q:
   mask,d=q.popleft()
   if mask==(1<<m)-1:break
   for line in lines:
    z=mask|line
    if z not in seen:seen.add(z);q.append((z,d+1))
  case(2152,[pts],d)
  w=R.randint(1,5);h=R.randint(1,3);bricks=sorted(R.sample(range(1,w+1),R.randint(1,w)));rows=[]
  def tile(pos,seams):
   if pos==w:rows.append(set(seams));return
   for b in bricks:
    if pos+b<=w:tile(pos+b,seams+([pos+b] if pos+b<w else []))
  tile(0,[]);case(2184,[h,w,bricks],sum(all(not (a&b) for a,b in zip(wall,wall[1:])) for wall in itertools.product(rows,repeat=h)))
  ops=['TextEditor'];args=[[]];out=[None];text='';cursor=0
  for _ in range(25):
   op=R.choice(['addText','deleteText','cursorLeft','cursorRight']);arg=''.join(R.choices('abc',k=R.randint(1,4))) if op=='addText' else R.randrange(8)
   ops.append(op);args.append([arg])
   if op=='addText':text=text[:cursor]+arg+text[cursor:];cursor+=len(arg);out.append(None)
   elif op=='deleteText':n=min(arg,cursor);text=text[:cursor-n]+text[cursor:];cursor-=n;out.append(n)
   else:cursor=max(0,cursor-arg) if op=='cursorLeft' else min(len(text),cursor+arg);out.append(text[max(0,cursor-10):cursor])
  case(2296,[ops,args],out)
  m,n=R.randint(1,5),R.randint(1,5);vals=list(range(R.randint(1,m*n)));cells=[];top,left,bottom,right=0,0,m-1,n-1
  while top<=bottom and left<=right:
   cells.extend((top,j) for j in range(left,right+1));top+=1
   cells.extend((i,right) for i in range(top,bottom+1));right-=1
   if top<=bottom:cells.extend((bottom,j) for j in range(right,left-1,-1));bottom-=1
   if left<=right:cells.extend((i,left) for i in range(bottom,top-1,-1));left+=1
  grid=[[-1]*n for _ in range(m)]
  for val,(i,j) in zip(vals,cells):grid[i][j]=val
  case(2326,[m,n,vals],grid)
  vals=R.sample(range(1,100),7);best=0
  for lev in (vals[:1],vals[1:3],vals[3:]):
   q=collections.deque([(tuple(lev),0)]);seen={tuple(lev)}
   while q:
    state,d=q.popleft()
    if list(state)==sorted(state):best+=d;break
    for i,j in itertools.combinations(range(len(lev)),2):
     z=list(state);z[i],z[j]=z[j],z[i];z=tuple(z)
     if z not in seen:seen.add(z);q.append((z,d+1))
  case(2471,[vals],best)
  value=R.randint(1,4);k=R.randint(1,5);stream=R.choices(range(1,5),k=20)
  case(2526,[['DataStream']+['consec']*20,[[value,k]]+[[x] for x in stream]],[None]+[i+1>=k and all(x==value for x in stream[i-k+1:i+1]) for i in range(20)])
  ops=['FrequencyTracker'];args=[[]];out=[None];bag=[]
  for _ in range(25):
   op=R.choice(['add','deleteOne','hasFrequency']);x=R.randint(1,5);ops.append(op);args.append([x])
   if op=='add':bag.append(x);out.append(None)
   elif op=='deleteOne':
    if x in bag:bag.remove(x)
    out.append(None)
   else:out.append(any(bag.count(v)==x for v in set(bag)))
  case(2671,[ops,args],out)
  p,q=R.sample([2,3,5,7,11],2);possible={p*i+q*j for i in range(q+1) for j in range(p+1)};case(2979,[p,q],max(x for x in range(p*q) if x not in possible))
 # SQL transcript checks deletion holes, malformed inserts, bad names/indices and ID monotonicity.
 case(2408,[['SQL','ins','ins','ins','rmv','ins','sel','sel','exp','sel','rmv','exp'],[[['t'],[1]],['t',['a']],['t',[]],['bad',['x']],['t',1],['t',['b']],['t',1,1],['t',2,1],['t'],['t',2,2],['missing',1],['missing']]],[None,True,False,False,None,True,'<null>','b',['2,b'],'<null>',None,[]])
 case(2431,[[0,0,2],[5,3,9],0,1],8,'zero_cost_edge')
 # Selected boundary/numeric regressions; expected results independently count simple structures.
 case(2123,[[[1]*40 for _ in range(40)]],800,'structured_edge')
 case(2912,[1000000000,1000000000,2,[1,1],[1,1]],1999999998%1000000007,'numeric_edge')
 case(2638,[list(range(1,101,2)),2],32951280099,'structured_edge') # independent-set path F52
 case(3112,[2,[[0,1,3],[0,1,2]],[1,2]],[0,-1],'strict_deadline_edge')
 case(1977,['1'*30],5604,'structured_edge') # integer partitions of 30
 case(3181,[[1,49999,50000]],99999,'numeric_edge')

def main():
 start=time.monotonic();build();counts={};jobs=[]
 for i,cases in sorted(CASES.items()):
  spec=importlib.util.spec_from_file_location('candidate_'+str(i),ROOT/'python'/f'{i}.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  for args,expected,kind in cases:
   actual=mod.solve(*copy.deepcopy(args))
   assert actual==expected,(i,'python',args,expected,actual)
   jobs.append([i,args,expected])
  counts[str(i)]=dict(collections.Counter(kind for _,_,kind in cases))
 runner="const fs=require('fs'),root=process.argv[1],jobs=JSON.parse(fs.readFileSync(0,'utf8'));for(const [id,args,expected] of jobs){const actual=require(root+'/javascript/'+id+'.js')(...args);if(JSON.stringify(actual)!==JSON.stringify(expected)){console.error(JSON.stringify({id,args,expected,actual}));process.exit(1);}}console.log(JSON.stringify({passed:jobs.length}));"
 proc=subprocess.run(['node','-e',runner,str(ROOT)],input=json.dumps(jobs),text=True,capture_output=True,timeout=120)
 assert proc.returncode==0,proc.stderr
 expected={r['problem_id'] for r in json.load(open(ROOT/'batch4/manifest.json'))};assert set(CASES)==expected
 assert all(any(k!='public_example' for _,_,k in cases) for cases in CASES.values())
 receipt={'schema':'gamma.authored-candidate-tests.v1','batch':4,'seed':50604,'ids':len(CASES),'pairs':len(jobs),'language_executions':2*len(jobs),'per_id':counts,'node':proc.stdout.strip(),'duration_seconds':round(time.monotonic()-start,3),'qualification':'not_qualified','limitations':['Finite public and independently generated local tests only.','No hidden judge, protected corpus, models, admission, frozen confirmation, or official acceptance.','Adapter representations tested; native linked-list/tree/oracle integration not tested.']}
 receipt.update(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),base_commit='62f8d1e2b375ab1c576a412be06adeddb5bcbffe',test_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),python_version=sys.version.split()[0],node_version=subprocess.check_output(['node','--version'],text=True).strip(),candidate_hashes={str(i):{lang:hashlib.sha256((ROOT/lang/f'{i}.{ext}').read_bytes()).hexdigest() for lang,ext in [('javascript','js'),('python','py')]} for i in CASES})
 (ROOT/'batch4/test-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
