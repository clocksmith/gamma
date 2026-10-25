"""Independent public mathematical predicates/oracles; no candidate imports."""
import math
from collections import Counter,deque
from itertools import combinations
IDS=(120,931,955,988,1005,1007,1071,1106,1122,1160,1170,1514,1942,2192)
def need(condition,message='official domain violation'):
 if not condition:raise ValueError(message)
def integer(x):return type(x)is int
def ints(a,lo,hi,nlo,nhi):return type(a)is list and nlo<=len(a)<=nhi and all(integer(x)and lo<=x<=hi for x in a)
def word(s,n,upper=False):return type(s)is str and 1<=len(s)<=n and all(('A'<=c<='Z')if upper else('a'<=c<='z')for c in s)
def boolean_expression(s):
 need(type(s)is str and 1<=len(s)<=20000)
 # Explicit grammar frames: operator, child values, whether child is required.
 frames=[];root=None;i=0
 def emit(value):
  nonlocal root
  if frames:
   need(frames[-1][2]);frames[-1][1].append(value);frames[-1][2]=False
  else:need(root is None);root=value
 while i<len(s):
  c=s[i]
  if c in 'tf':emit(c=='t');i+=1
  elif c in '!&|':
   need((not frames and root is None)or(frames and frames[-1][2]));need(i+1<len(s)and s[i+1]=='(');frames.append([c,[],True]);i+=2
  elif c==',':need(bool(frames)and not frames[-1][2]);frames[-1][2]=True;i+=1
  elif c==')':
   need(bool(frames)and not frames[-1][2]);op,values,_=frames.pop();need(op!='!'or len(values)==1)
   emit(not values[0]if op=='!'else all(values)if op=='&'else any(values));i+=1
  else:raise ValueError('invalid Boolean grammar')
 need(not frames and root is not None);return root

def tree_arrays(tag):
 need(type(tag)is dict and set(tag)=={'__tree_node__'})
 a=tag['__tree_node__'];need(type(a)is list and bool(a)and a[0]is not None and a[-1]is not None)
 need(all(x is None or integer(x)and 0<=x<=25 for x in a))
 parents=[-1];values=[a[0]];children=[[]];position=1;cursor=0
 while cursor<len(values):
  for _ in range(2):
   if position<len(a):
    x=a[position];position+=1
    if x is not None:children[cursor].append(len(values));parents.append(cursor);values.append(x);children.append([])
  cursor+=1
 need(position==len(a),'orphan BFS nodes');need(1<=len(values)<=8500)
 return values,parents,children

def validate(pid,args):
 need(pid in IDS and type(args)is list)
 need(len(args)=={120:1,931:1,955:1,988:1,1005:2,1007:2,1071:2,1106:1,1122:2,1160:2,1170:2,1514:5,1942:2,2192:2}[pid])
 if pid in (120,931):
  a=args[0];limit=200 if pid==120 else 100;bound=10000 if pid==120 else 100
  need(type(a)is list and 1<=len(a)<=limit)
  for i,row in enumerate(a):need(ints(row,-bound,bound,i+1 if pid==120 else len(a),i+1 if pid==120 else len(a)))
 elif pid==955:
  a=args[0];need(type(a)is list and 1<=len(a)<=100 and all(word(x,100)for x in a));need(len({len(x)for x in a})==1)
 elif pid==988:tree_arrays(args[0])
 elif pid==1005:need(ints(args[0],-100,100,1,10000)and integer(args[1])and 1<=args[1]<=10000)
 elif pid==1007:need(all(ints(a,1,6,2,20000)for a in args)and len(args[0])==len(args[1]))
 elif pid==1071:need(all(word(s,1000,True)for s in args))
 elif pid==1106:boolean_expression(args[0])
 elif pid==1122:
  a,b=args;need(all(ints(x,0,1000,1,1000)for x in args));need(len(set(b))==len(b)and set(b)<=set(a))
 elif pid==1160:
  a,b=args;need(type(a)is list and 1<=len(a)<=1000 and all(word(x,100)for x in a)and word(b,100))
 elif pid==1170:need(all(type(a)is list and 1<=len(a)<=2000 and all(word(x,10)for x in a)for a in args))
 elif pid in (1514,2192):
  n,edges=args[:2];need(integer(n)and (2 if pid==1514 else 1)<=n<=(10000 if pid==1514 else 1000));need(type(edges)is list and len(edges)<=(20000 if pid==1514 else min(2000,n*(n-1)//2)))
  need(all(ints(e,0,n-1,2,2)and e[0]!=e[1]for e in edges));keys=[tuple(sorted(e))if pid==1514 else tuple(e)for e in edges];need(len(set(keys))==len(keys))
  if pid==1514:
   probs,start,end=args[2:];need(type(probs)is list and len(probs)==len(edges)and all(type(p)in(int,float)and math.isfinite(p)and 0<=p<=1 for p in probs));need(integer(start)and integer(end)and 0<=start<n and 0<=end<n and start!=end)
  else:
   indeg=[0]*n;adj=[[]for _ in range(n)]
   for x,y in edges:adj[x].append(y);indeg[y]+=1
   ready=deque(i for i in range(n)if indeg[i]==0);seen=0
   while ready:
    x=ready.popleft();seen+=1
    for y in adj[x]:
     indeg[y]-=1
     if indeg[y]==0:ready.append(y)
   need(seen==n,'DAG required')
 else:
  a,target=args;need(type(a)is list and 2<=len(a)<=10000 and integer(target)and 0<=target<len(a));need(all(ints(x,1,100000,2,2)and x[0]<x[1]for x in a));need(len({x[0]for x in a})==len(a))
 return True

def expected(pid,args):
 validate(pid,args)
 if pid in (120,931):
  a=args[0];cost=list(a[0])
  for row in a[1:]:
   cost=[x+min(cost[k]for k in (j-1,j)if 0<=k<len(cost))for j,x in enumerate(row)]if pid==120 else[x+min(cost[max(0,j-1):j+2])for j,x in enumerate(row)]
  return min(cost)
 if pid==955:
  a=args[0];m=len(a[0])
  # Exhaustive column-subset oracle for small width, independently known
  # structural formulas only for predeclared large boundary families.
  if m>12:
   if all(x==a[0]for x in a):return 0
   if all(len(set(x))==1 for x in a):return 0 if a==sorted(a)else m
   raise ValueError('oracle resource domain: unplanned large 955 case')
  for deleted in range(m+1):
   for keep in combinations(range(m),m-deleted):
    rows=[''.join(s[i]for i in keep)for s in a]
    if rows==sorted(rows):return deleted
 if pid==988:
  values,parents,children=tree_arrays(args[0]);best=None
  for leaf in range(len(values)):
   if children[leaf]:continue
   letters=[];i=leaf
   while i!=-1:letters.append(chr(97+values[i]));i=parents[i]
   value=''.join(letters)
   if best is None or value<best:best=value
  return best
 if pid==1005:
  a,k=args;counts=Counter(a)
  # Integer histogram mass transport, not sorted-array flipping.
  for v in range(-100,0):
   moved=min(k,counts[v]);counts[v]-=moved;counts[-v]+=moved;k-=moved
  total=sum(v*c for v,c in counts.items());least=min(abs(v)for v,c in counts.items()if c)
  return total-2*least*(k%2)
 if pid==1007:
  a,b=args;costs=[]
  for face in range(1,7):
   if all(x==face or y==face for x,y in zip(a,b)):costs.extend((sum(x!=face for x in a),sum(y!=face for y in b)))
  return min(costs,default=-1)
 if pid==1071:
  a,b=args
  for n in range(min(len(a),len(b)),0,-1):
   if len(a)%n==len(b)%n==0 and a[:n]*(len(a)//n)==a and a[:n]*(len(b)//n)==b:return a[:n]
  return ''
 if pid==1106:return boolean_expression(args[0])
 if pid==1122:
  a,b=args;priority={x:i for i,x in enumerate(b)};return sorted(a,key=lambda x:(0,priority[x])if x in priority else(1,x))
 if pid==1160:
  words,chars=args;return sum(len(w)for w in words if all(w.count(c)<=chars.count(c)for c in set(w)))
 if pid==1170:
  queries,words=args;f=lambda w:w.count(min(w));hist=Counter(map(f,words));return [sum(n for k,n in hist.items()if k>f(q))for q in queries]
 if pid==1514:
  n,edges,probs,start,end=args
  # Synchronous Bellman-Ford products, not candidate heap search. At most
  # n-1 edges suffice since every edge probability is in [0,1].
  values=[0.0]*n;values[start]=1.0
  for _ in range(n-1):
   new=values.copy()
   for (x,y),p in zip(edges,probs):new[x]=max(new[x],values[y]*p);new[y]=max(new[y],values[x]*p)
   if new==values:break
   values=new
  return values[end]
 if pid==1942:
  times,target=args;occupied={}
  for friend in sorted(range(len(times)),key=lambda i:times[i][0]):
   arrival,departure=times[friend];occupied={chair:leave for chair,leave in occupied.items()if leave>arrival};chair=0
   while chair in occupied:chair+=1
   if friend==target:return chair
   occupied[chair]=departure
 n,edges=args;reverse=[[]for _ in range(n)]
 for x,y in edges:reverse[y].append(x)
 answer=[]
 for end in range(n):
  seen=set();stack=reverse[end].copy()
  while stack:
   x=stack.pop()
   if x not in seen:seen.add(x);stack.extend(reverse[x])
  answer.append(sorted(seen))
 return answer

def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b

def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 got=record.get('result');kind='str'if pid in(988,1071)else'bool'if pid==1106 else'list'if pid in(1122,1170,2192)else'real'if pid==1514 else'int'
 allowed={'javascript':{'str':('string',),'bool':('boolean',),'list':('object',),'real':('number',),'int':('number',)},'python':{'str':('str',),'bool':('bool',),'list':('list',),'real':('int','float'),'int':('int',)}}
 if record.get('result_type')not in allowed[language][kind]:return False,'result_type'
 okay=type(got)in(int,float)and math.isfinite(got)and abs(got-want)<=1e-5 if pid==1514 else exact(got,want)
 if not okay:return False,'result_value'
 def input_equal(observed):
  if pid!=1514:return exact(observed,args)
  if type(observed)is not list or len(observed)!=5:return False
  if any(not exact(observed[i],args[i])for i in (0,1,3,4)):return False
  ps=observed[2]
  return type(ps)is list and len(ps)==len(args[2])and all(type(x)in(int,float)and math.isfinite(x)and x==y for x,y in zip(ps,args[2]))
 if not input_equal(record.get('args_before')):return False,'args_before'
 if not input_equal(record.get('args_after')):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
