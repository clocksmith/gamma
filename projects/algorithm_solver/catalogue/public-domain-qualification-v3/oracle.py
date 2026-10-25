"""Independent bounded oracles; full domain validation is not universal proof."""
from itertools import permutations
IDS=(802,871,875,1438,1547,2246,2406,2416)
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(x,a,b,lo,hi):return type(x)is list and lo<=len(x)<=hi and all(integer(v,a,b)for v in x)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered arguments')
 good=False
 if pid==802 and len(args)==1:
  g=args[0];n=len(g)if type(g)is list else 0
  good=1<=n<=10000 and all(ints(r,0,n-1,0,n)and r==sorted(set(r))for r in g)and 1<=sum(map(len,g))<=40000
 elif pid==871 and len(args)==3:
  t,f,ss=args;good=integer(t,1,10**9)and integer(f,1,10**9)and type(ss)is list and len(ss)<=500 and all(type(r)is list and len(r)==2 and integer(r[0],1,t-1)and integer(r[1],1,10**9-1)for r in ss)and all(a[0]<b[0]for a,b in zip(ss,ss[1:]))
 elif pid==875 and len(args)==2:good=ints(args[0],1,10**9,1,10000)and integer(args[1],len(args[0]),10**9)
 elif pid==1438 and len(args)==2:good=ints(args[0],1,10**9,1,100000)and integer(args[1],0,10**9)
 elif pid==1547 and len(args)==2:
  n,cs=args;good=integer(n,2,10**6)and ints(cs,1,n-1,1,min(n-1,100))and len(set(cs))==len(cs)
 elif pid==2246 and len(args)==2:
  p,s=args;n=len(p)if type(p)is list else 0
  good=1<=n<=100000 and type(p[0])is int and p[0]==-1 and all(integer(x,0,n-1)for x in p[1:])and type(s)is str and len(s)==n and all('a'<=c<='z'for c in s)
  if good:
   children=[[]for _ in p]
   for i in range(1,n):children[p[i]].append(i)
   seen={0};q=[0]
   for x in q:
    for y in children[x]:
     if y in seen:good=False;break
     seen.add(y);q.append(y)
   good=good and len(seen)==n
 elif pid==2406 and len(args)==1:
  rows=args[0];good=type(rows)is list and 1<=len(rows)<=100000 and all(type(r)is list and len(r)==2 and integer(r[0],1,10**6)and integer(r[1],r[0],10**6)for r in rows)
 elif pid==2416 and len(args)==1:
  ws=args[0];good=type(ws)is list and 1<=len(ws)<=1000 and all(type(w)is str and 1<=len(w)<=1000 and all('a'<=c<='z'for c in w)for w in ws)
 if not good:raise ValueError('outside declared domain')
def expected(pid,args):
 validate(pid,args)
 if pid==802:
  g=args[0];state=[0]*len(g);safe=[False]*len(g)
  for start in range(len(g)):
   if state[start]:continue
   stack=[(start,0)];state[start]=1
   while stack:
    v,k=stack[-1]
    if k==len(g[v]):safe[v]=all(safe[w]for w in g[v]);state[v]=2;stack.pop();continue
    w=g[v][k];stack[-1]=(v,k+1)
    if state[w]==0:state[w]=1;stack.append((w,0))
  return [i for i,x in enumerate(safe)if x]
 if pid==871:
  target,fuel,stations=args;reach=[fuel]+[-1]*len(stations)
  for i,(position,gas)in enumerate(stations):
   for stops in range(i,-1,-1):
    if reach[stops]>=position:reach[stops+1]=max(reach[stops+1],reach[stops]+gas)
  return next((i for i,v in enumerate(reach)if v>=target),-1)
 if pid==875:
  piles,h=args
  if len(set(piles))==1:
   hours=h//len(piles);return (piles[0]+hours-1)//hours
  if max(piles)>10000:raise ValueError('bounded speed enumeration oracle')
  return next(k for k in range(1,max(piles)+1)if sum((p+k-1)//k for p in piles)<=h)
 if pid==1438:
  xs,limit=args
  if len(xs)>100:
   if len(set(xs))==1:return len(xs)
   if xs==list(range(1,len(xs)+1)):return min(len(xs),limit+1)
   if xs==[1,10**9]*(len(xs)//2):return len(xs)if limit>=10**9-1 else 1
   raise ValueError('bounded window enumeration oracle')
  return max(j-i for i in range(len(xs))for j in range(i+1,len(xs)+1)if max(xs[i:j])-min(xs[i:j])<=limit)
 if pid==1547:
  n,cuts=args
  if cuts==list(range(1,n)):
   depth=(n-1).bit_length();return n*depth-((1<<depth)-n)
  if len(cuts)>7:raise ValueError('bounded cut-order enumeration oracle')
  best=10**20
  for order in permutations(cuts):
   ends=[0,n];cost=0
   for cut in order:
    lo=max(x for x in ends if x<cut);hi=min(x for x in ends if x>cut);cost+=hi-lo;ends.append(cut)
   best=min(best,cost)
  return best
 if pid==2246:
  parent,s=args;g=[[]for _ in parent]
  for i,p in enumerate(parent[1:],1):
   if s[i]!=s[p]:g[i].append(p);g[p].append(i)
  seen=set();best=1
  def far(start,mark=False):
   q=[(start,-1,1)];last=(start,1)
   for x,p,d in q:
    if mark:seen.add(x)
    if d>last[1]:last=(x,d)
    q.extend((y,x,d+1)for y in g[x]if y!=p)
   return last
  for i in range(len(parent)):
   if i not in seen:best=max(best,far(far(i,True)[0])[1])
  return best
 if pid==2406:
  rows=args[0]
  if len(rows)>200:
   if len({tuple(r)for r in rows})==1:return len(rows)
   if rows==[[2*i+1,2*i+1]for i in range(len(rows))]:return 1
   raise ValueError('bounded overlap oracle')
  return max(sum(a<=point<=b for a,b in rows)for point in {a for a,b in rows})
 ws=args[0]
 if len(set(ws))==1:return [len(ws)*len(ws[0])]*len(ws)
 if sum(map(len,ws))>10000:raise ValueError('bounded pairwise prefix oracle')
 def lcp(a,b):
  n=0
  for x,y in zip(a,b):
   if x!=y:break
   n+=1
  return n
 return [sum(lcp(w,v)for v in ws)for w in ws]
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind='list'if pid in(802,2416)else'int'
 allowed={'python':{'list':'list','int':'int'},'javascript':{'list':'object','int':'number'}}
 if record.get('result_type')!=allowed[language][kind]:return False,'result_type'
 if not exact(record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
