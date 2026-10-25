"""Independent statement-definition oracles. Never import candidate code."""
from collections import Counter, deque
from itertools import combinations, product
IDS=(1248,1319,1338,1400,1466,1471,1482,1540)
def integer(x,lo,hi):return type(x)is int and lo<=x<=hi
def ints(xs,lo,hi,nlo,nhi):return type(xs)is list and nlo<=len(xs)<=nhi and all(integer(x,lo,hi)for x in xs)
def letters(s):return type(s)is str and 1<=len(s)<=100000 and all('a'<=c<='z'for c in s)
def graph(n,edges,tree=False):
 if not integer(n,2 if tree else 1,50000 if tree else 100000)or type(edges)is not list:return False
 if tree:
  if len(edges)!=n-1:return False
 elif not 1<=len(edges)<=min(n*(n-1)//2,100000):return False
 if not all(ints(e,0,n-1,2,2)and e[0]!=e[1]for e in edges):return False
 if len({tuple(sorted(e))for e in edges})!=len(edges):return False
 if tree:
  adj=[[]for _ in range(n)]
  for u,v in edges:adj[u].append(v);adj[v].append(u)
  seen={0};q=[0]
  for u in q:
   for v in adj[u]:
    if v not in seen:seen.add(v);q.append(v)
  if len(seen)!=n:return False
 return True

def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered positional arguments required')
 ok=False
 if pid==1248:ok=len(args)==2 and ints(args[0],1,100000,1,50000)and integer(args[1],1,len(args[0]))
 elif pid==1319:ok=len(args)==2 and graph(args[0],args[1])
 elif pid==1338:ok=len(args)==1 and ints(args[0],1,100000,2,100000)and len(args[0])%2==0
 elif pid==1400:ok=len(args)==2 and letters(args[0])and integer(args[1],1,100000)
 elif pid==1466:ok=len(args)==2 and graph(args[0],args[1],True)
 elif pid==1471:ok=len(args)==2 and ints(args[0],-100000,100000,1,100000)and integer(args[1],1,len(args[0]))
 elif pid==1482:ok=len(args)==3 and ints(args[0],1,10**9,1,100000)and integer(args[1],1,10**6)and integer(args[2],1,len(args[0]))
 elif pid==1540:ok=len(args)==3 and letters(args[0])and letters(args[1])and integer(args[2],0,10**9)
 if not ok:raise ValueError('outside pinned official domain')

def expected(pid,args):
 validate(pid,args)
 if pid==1248:
  xs,k=args;p=[-1]+[i for i,x in enumerate(xs)if x%2]+[len(xs)]
  return sum((p[i]-p[i-1])*(p[i+k]-p[i+k-1])for i in range(1,len(p)-k))
 if pid==1319:
  n,edges=args
  if len(edges)<n-1:return -1
  adj=[[]for _ in range(n)]
  for u,v in edges:adj[u].append(v);adj[v].append(u)
  seen=set();components=0
  for first in range(n):
   if first in seen:continue
   components+=1;seen.add(first);queue=[first]
   for u in queue:
    for v in adj[u]:
     if v not in seen:seen.add(v);queue.append(v)
  return components-1
 if pid==1338:
  xs=args[0];hist=Counter(Counter(xs).values());remaining=len(xs)//2;answer=0
  # Coverage lower bound: no t selected values can remove more than the t
  # largest multiplicities. Histogram buckets attain that bound, without the
  # candidate's per-value frequency sort.
  for frequency in range(len(xs),0,-1):
   take=min(hist.get(frequency,0),(remaining+frequency-1)//frequency)
   answer+=take;remaining-=take*frequency
   if remaining<=0:return answer
 if pid==1400:
  s,k=args;odd=sum(v%2 for v in Counter(s).values())
  # Each odd class needs a center; pairs can attach or split into additional
  # nonempty palindromes, attaining every count through len(s).
  return max(1,odd)<=k<=len(s)
 if pid==1466:
  n,edges=args;adj=[[]for _ in range(n)]
  for u,v in edges:adj[u].append(v);adj[v].append(u)
  parent=[-1]*n;parent[0]=0;queue=[0]
  for u in queue:
   for v in adj[u]:
    if parent[v]<0:parent[v]=u;queue.append(v)
  return sum(parent[v]==u for u,v in edges)
 if pid==1471:
  xs,k=args;center=sorted(xs)[(len(xs)-1)//2]
  return sorted(xs,key=lambda x:(-abs(x-center),-x))[:k]
 if pid==1482:
  blooms,m,k=args;n=len(blooms)
  if m*k>n:return -1
  # Day-ordered activation, not binary search/greedy scanning. Active adjacent
  # components each contribute floor(size/k) disjoint bouquets.
  parent=list(range(n));size=[1]*n;active=[False]*n;total=0
  def root(x):
   while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
   return x
  for i in sorted(range(n),key=lambda i:blooms[i]):
   active[i]=True;total+=1//k
   for j in(i-1,i+1):
    if 0<=j<n and active[j]:
     a,b=root(i),root(j)
     if a==b:continue
     total-=size[a]//k+size[b]//k
     if size[a]<size[b]:a,b=b,a
     parent[b]=a;size[a]+=size[b];total+=size[a]//k
   if total>=m:return blooms[i]
  raise AssertionError('activation must eventually satisfy feasible request')
 if pid==1540:
  s,t,k=args
  if len(s)!=len(t):return False
  demand=Counter((ord(b)-ord(a))%26 for a,b in zip(s,t))
  # Moves partition into disjoint residue classes. Every nonzero demand can
  # be matched iff that residue has enough distinct move numbers.
  return all(demand[r]<=max(0,(k-r)//26+1)for r in range(1,26))
 raise ValueError('unknown identity')

def brute(pid,args):
 """Small exhaustive definition controls; no candidate implementation involved."""
 validate(pid,args)
 if pid==1248:
  xs,k=args;return sum(sum(v%2 for v in xs[i:j])==k for i in range(len(xs))for j in range(i+1,len(xs)+1))
 if pid==1338:
  xs=args[0];values=set(xs)
  for n in range(1,len(values)+1):
   if any(sum(x in chosen for x in xs)>=len(xs)//2 for chosen in combinations(values,n)):return n
 if pid==1400:
  s,k=args
  if k>len(s):return False
  # Assign character positions to labelled nonempty bags; each bag can be
  # permuted into a palindrome iff at most one character count is odd.
  for assignment in product(range(k),repeat=len(s)):
   if len(set(assignment))!=k:continue
   bags=[Counter()for _ in range(k)]
   for c,b in zip(s,assignment):bags[b][c]+=1
   if all(sum(v%2 for v in bag.values())<=1 for bag in bags):return True
  return False
 if pid==1466:
  n,edges=args
  for changes in range(len(edges)+1):
   for chosen in combinations(range(len(edges)),changes):
    chosen=set(chosen);rev=[[]for _ in range(n)]
    for i,(u,v)in enumerate(edges):
     if i in chosen:u,v=v,u
     rev[v].append(u)
    seen={0};queue=[0]
    for u in queue:
     for v in rev[u]:
      if v not in seen:seen.add(v);queue.append(v)
    if len(seen)==n:return changes
 if pid==1471:
  xs,k=args;center=sorted(xs)[(len(xs)-1)//2]
  choices=list(combinations(range(len(xs)),k))
  chosen=max(choices,key=lambda c:sorted(((abs(xs[i]-center),xs[i])for i in c),reverse=True))
  return [xs[i]for i in chosen]
 if pid==1482:
  xs,m,k=args
  for day in sorted(set(xs)):
   starts=[i for i in range(len(xs)-k+1)if all(x<=day for x in xs[i:i+k])]
   if any(all(a+k<=b for a,b in zip(choice,choice[1:]))for choice in combinations(starts,m)):return day
  return -1
 if pid==1540:
  s,t,k=args
  if len(s)!=len(t):return False
  wanted=[(ord(b)-ord(a))%26 for a,b in zip(s,t)if a!=b]
  match={}
  def assign(i,seen):
   for move in range(1,k+1):
    if move%26!=wanted[i]or move in seen:continue
    seen.add(move)
    if move not in match or assign(match[move],seen):match[move]=i;return True
   return False
  return all(assign(i,set())for i in range(len(wanted)))
 if pid==1319:
  n,edges=args;initial=frozenset(tuple(sorted(e))for e in edges)
  def connected(es):
   reach={0}
   while True:
    nxt=reach|{v for u,v in es if u in reach}|{u for u,v in es if v in reach}
    if nxt==reach:return len(reach)==n
    reach=nxt
  queue=deque([(initial,0)]);seen={initial};all_edges=set(combinations(range(n),2))
  while queue:
   state,d=queue.popleft()
   if connected(state):return d
   for remove in state:
    for insert in all_edges-state:
     nxt=frozenset((state-{remove})|{insert})
     if nxt not in seen:seen.add(nxt);queue.append((nxt,d+1))
  return -1
 raise ValueError('no brute control')

def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b

def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 types={'python':{'list':'list','int':'int','bool':'bool'},'javascript':{'list':'object','int':'number','bool':'boolean'}}
 if record.get('result_type')!=types[language][type(want).__name__]:return False,'result_type'
 actual=record.get('result')
 if pid==1471:
  if type(actual)is not list or not all(type(x)is int for x in actual)or not exact(sorted(actual),sorted(want)):return False,'result_multiset'
 elif not exact(actual,want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
