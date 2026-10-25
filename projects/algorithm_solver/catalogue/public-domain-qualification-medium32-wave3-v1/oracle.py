"""Independent public-domain host oracles; no submitted-source imports.

Official validators cover the declared full domains. Some expensive truth
oracles intentionally reject unsupported large fixtures, never fabricate truth.
"""
from functools import lru_cache
from itertools import permutations
from collections import Counter
IDS=(1894,1911,1921,1953,1976,2079,2131,2135)
MOD=10**9+7

def integer(x,lo,hi):return type(x)is int and lo<=x<=hi
def ints(x,lo,hi,n=100000):return type(x)is list and 1<=len(x)<=n and all(integer(v,lo,hi)for v in x)
def word(x,lo=1,hi=26):return type(x)is str and lo<=len(x)<=hi and all('a'<=c<='z'for c in x)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered argument list required')
 ok=False
 if pid==1894:ok=len(args)==2 and ints(args[0],1,100000)and integer(args[1],1,10**9)
 elif pid==1911:ok=len(args)==1 and ints(args[0],1,100000)
 elif pid==1921:ok=len(args)==2 and ints(args[0],1,100000)and ints(args[1],1,100000)and len(args[0])==len(args[1])
 elif pid==1953:ok=len(args)==1 and ints(args[0],1,10**9)
 elif pid==1976:
  if len(args)==2 and integer(args[0],1,200)and type(args[1])is list:
   n,roads=args;ok=n-1<=len(roads)<=n*(n-1)//2;seen=set();g=[[]for _ in range(n)]
   for r in roads:
    if type(r)is not list or len(r)!=3 or not integer(r[0],0,n-1)or not integer(r[1],0,n-1)or r[0]==r[1]or not integer(r[2],1,10**9):ok=False;break
    u,v,_=r;key=tuple(sorted((u,v)))
    if key in seen:ok=False;break
    seen.add(key);g[u].append(v);g[v].append(u)
   if ok:
    visited={0};todo=[0]
    for u in todo:
     for v in g[u]:
      if v not in visited:visited.add(v);todo.append(v)
    ok=len(visited)==n
 elif pid==2079:ok=len(args)==2 and ints(args[0],1,10**6,1000)and integer(args[1],max(args[0]),10**9)
 elif pid==2131:ok=len(args)==1 and type(args[0])is list and 1<=len(args[0])<=100000 and all(word(x,2,2)for x in args[0])
 elif pid==2135:ok=len(args)==2 and all(type(xs)is list and 1<=len(xs)<=50000 and all(word(x)and len(set(x))==len(x)for x in xs)for xs in args)
 if not ok:raise ValueError('outside reviewed official domain')

def expected(pid,args):
 validate(pid,args)
 if pid==1894:
  a,k=args
  if len(set(a))==1:return (k//a[0])%len(a)
  if k>200000:raise ValueError('bounded direct consumption oracle')
  i=0
  while k>=a[i]:k-=a[i];i=(i+1)%len(a)
  return i
 if pid==1911:
  a=args[0]
  if len(a)<=16:
   return max(sum(v if j%2==0 else -v for j,v in enumerate([a[i]for i in range(len(a))if mask>>i&1]))for mask in range(1,1<<len(a)))
  if all(x<=y for x,y in zip(a,a[1:]))or all(x>=y for x,y in zip(a,a[1:])):return max(a)
  if len(a)%2==0 and a==[100000,1]*(len(a)//2):return (len(a)//2)*99999+1
  raise ValueError('bounded subsequence oracle')
 if pid==1921:
  d,s=args;n=len(d)
  if n>12:
   if all(x>=n*y for x,y in zip(d,s)):return n
   if all(x<=y for x,y in zip(d,s)):return 1
   raise ValueError('bounded shot-order oracle')
  @lru_cache(None)
  def shots(mask):
   t=mask.bit_count()
   if any(d[i]<=t*s[i]for i in range(n)if not mask>>i&1):return 0
   return max((1+shots(mask|1<<i)for i in range(n)if not mask>>i&1),default=0)
  return shots(0)
 if pid==1953:
  a=args[0]
  if sum(a)<=20:
   @lru_cache(None)
   def go(left,last):
    best=0
    for i,v in enumerate(left):
     if v and i!=last:
      rest=list(left);rest[i]-=1;best=max(best,1+go(tuple(rest),i))
    return best
   return go(tuple(a),-1)
  if len(a)==1:return 1
  if len(set(a))==1:return sum(a) # round-robin schedule, at least two projects
  biggest=max(a);others=sum(a)-biggest
  if biggest>others:return 2*others+1 # separator lower/upper bound coincide
  raise ValueError('bounded schedule oracle')
 if pid==1976:
  n,roads=args;inf=10**30;d=[[inf]*n for _ in range(n)]
  for i in range(n):d[i][i]=0
  for u,v,w in roads:d[u][v]=d[v][u]=w
  for k in range(n):
   for i in range(n):
    via=d[i][k]
    for j in range(n):d[i][j]=min(d[i][j],via+d[k][j])
  ways=[0]*n;ways[0]=1;g=[[]for _ in range(n)]
  for u,v,w in roads:
   if d[0][u]+w==d[0][v]:g[u].append(v)
   if d[0][v]+w==d[0][u]:g[v].append(u)
  for u in sorted(range(n),key=lambda i:d[0][i]):
   for v in g[u]:ways[v]=(ways[v]+ways[u])%MOD
  return ways[-1]
 if pid==2079:
  plants,cap=args;position=-1;water=cap;steps=0
  for i,need in enumerate(plants):
   if water<need:steps+=position+1;position=-1;water=cap
   steps+=i-position;position=i;water-=need
  return steps
 if pid==2131:
  a=args[0];n=len(a)
  if n<=7:
   for size in range(n,0,-1):
    for chosen in permutations(range(n),size):
     s=''.join(a[i]for i in chosen)
     if s==s[::-1]:return 2*size
   return 0
  c=Counter(a)
  if len(c)==1:
   w=a[0];return 2*n if w==w[::-1]else 0
  if set(c)=={'ab','ba'}:return 4*min(c['ab'],c['ba'])
  raise ValueError('bounded concatenation oracle')
 if pid==2135:
  starts={frozenset(x)for x in args[0]};targets=Counter(frozenset(x)for x in args[1])
  if len(starts)*len(targets)>2000000:raise ValueError('bounded independent subset oracle')
  return sum(count for t,count in targets.items()if any(len(t)==len(s)+1 and s<t for s in starts))
 raise ValueError('unsupported id')

def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b

def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 if record.get('result_type')!=('int'if language=='python'else'number')or not exact(record.get('result'),want):return False,'typed_result'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
