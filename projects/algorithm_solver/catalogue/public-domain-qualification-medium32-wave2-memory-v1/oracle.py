"""Definition-level independent oracles; no incoming candidate imports."""
from collections import Counter
from functools import lru_cache
from itertools import combinations,permutations
IDS=(1567,1573,1630,1653,1743,1817,1877,1887)
MOD=1000000007
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(xs,a,b,lo,hi):return type(xs)is list and lo<=len(xs)<=hi and all(integer(x,a,b)for x in xs)
def letters(s,chars,lo,hi):return type(s)is str and lo<=len(s)<=hi and all(c in chars for c in s)
def path_graph(pairs):
 if type(pairs)is not list or not 1<=len(pairs)<=99999 or not all(ints(e,-100000,100000,2,2)and e[0]!=e[1]for e in pairs):return False
 edges={tuple(sorted(e))for e in pairs}
 if len(edges)!=len(pairs):return False
 adj={}
 for a,b in pairs:adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 if len(adj)!=len(pairs)+1 or sum(len(v)==1 for v in adj.values())!=2 or any(len(v)not in(1,2)for v in adj.values()):return False
 first=next(iter(adj));seen={first};todo=[first]
 for u in todo:
  for v in adj[u]:
   if v not in seen:seen.add(v);todo.append(v)
 return len(seen)==len(adj)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered arguments required')
 ok=False
 if pid==1567:ok=len(args)==1 and ints(args[0],-10**9,10**9,1,100000)
 elif pid==1573:ok=len(args)==1 and letters(args[0],'01',3,100000)
 elif pid==1630 and len(args)==3:
  xs,l,r=args
  ok=ints(xs,-100000,100000,2,500)and type(l)is list and type(r)is list and 1<=len(l)==len(r)<=500 and all(integer(a,0,len(xs)-1)and integer(b,0,len(xs)-1)and a<b for a,b in zip(l,r))
 elif pid==1653:ok=len(args)==1 and letters(args[0],'ab',1,100000)
 elif pid==1743:ok=len(args)==1 and path_graph(args[0])
 elif pid==1817 and len(args)==2:
  logs,k=args
  ok=type(logs)is list and 1<=len(logs)<=10000 and integer(k,1,100000)and all(type(e)is list and len(e)==2 and integer(e[0],0,10**9)and integer(e[1],1,100000)for e in logs)
  if ok:
   counts=Counter(u for u,t in set(map(tuple,logs)));ok=max(counts.values())<=k
 elif pid==1877:ok=len(args)==1 and ints(args[0],1,100000,2,100000)and len(args[0])%2==0
 elif pid==1887:ok=len(args)==1 and ints(args[0],1,50000,1,50000)
 if not ok:raise ValueError('outside pinned official domain')
def expected(pid,args):
 validate(pid,args)
 if pid==1567:
  xs=args[0];answer=0;start=0
  for stop in range(len(xs)+1):
   if stop<len(xs)and xs[stop]!=0:continue
   negative=[i for i in range(start,stop)if xs[i]<0]
   if len(negative)%2==0:answer=max(answer,stop-start)
   else:answer=max(answer,stop-negative[0]-1,negative[-1]-start)
   start=stop+1
  return answer
 if pid==1573:
  s=args[0];ones=s.count('1')
  if ones%3:return 0
  target=ones//3;prefix=0;eligible_first=0;answer=0
  # Count ordered cut positions by prefix sums. Process second cut before
  # registering that same position as a first cut: all3 parts stay nonempty.
  for cut in range(1,len(s)):
   prefix+=int(s[cut-1])
   if prefix==2*target:answer+=eligible_first
   if prefix==target:eligible_first+=1
  return answer%MOD
 if pid==1630:
  xs,l,r=args;out=[]
  for a,b in zip(l,r):
   values=sorted(xs[a:b+1]);diff=values[1]-values[0]
   out.append(all(y-x==diff for x,y in zip(values,values[1:])))
  return out
 if pid==1653:
  s=args[0];left_b=0;right_a=s.count('a');best=right_a
  for c in s:
   left_b+=c=='b';right_a-=c=='a';best=min(best,left_b+right_a)
  return best
 if pid==1743:
  pairs=args[0];adj={}
  for a,b in pairs:adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
  # Deliberately choose the LARGER endpoint; candidate chooses smaller. The
  # checker below validates the path relation, never our arbitrary orientation.
  result=[max(v for v,ns in adj.items()if len(ns)==1)];used=set(result)
  while len(result)<len(adj):
   nxt=next(v for v in adj[result[-1]]if v not in used);result.append(nxt);used.add(nxt)
  return result
 if pid==1817:
  logs,k=args;ordered=sorted(set(map(tuple,logs)));counts=[];last=None;total=0
  for user,time in ordered:
   if user!=last:
    if last is not None:counts.append(total)
    last=user;total=0
   total+=1
  counts.append(total);hist=Counter(counts)
  return [hist[j]for j in range(1,k+1)]
 if pid==1877:
  xs=sorted(args[0]);low=max(xs);high=2*max(xs)
  # Feasibility threshold: pair current largest with smallest. If even that
  # exceeds T, no partner can fit; exchange preserves feasibility otherwise.
  def feasible(t):return all(xs[i]+xs[-1-i]<=t for i in range(len(xs)//2))
  while low<high:
   middle=(low+high)//2
   if feasible(middle):high=middle
   else:low=middle+1
  return low
 if pid==1887:
  counts=Counter(args[0]);descending=sorted(counts,reverse=True);active=0;operations=0
  for value in descending[:-1]:active+=counts[value];operations+=active
  return operations
 raise ValueError('unknown ID')

def brute(pid,args):
 validate(pid,args)
 if pid==1567:
  xs=args[0];answer=0
  for start in range(len(xs)):
   sign=1
   for end in range(start,len(xs)):
    sign*=0 if xs[end]==0 else(1 if xs[end]>0 else-1)
    if sign>0:answer=max(answer,end-start+1)
  return answer
 if pid==1573:
  s=args[0];return sum(s[:a].count('1')==s[a:b].count('1')==s[b:].count('1')for a,b in combinations(range(1,len(s)),2))%MOD
 if pid==1630:
  xs,l,r=args;out=[]
  for a,b in zip(l,r):
   out.append(any(len({y-x for x,y in zip(p,p[1:])})==1 for p in permutations(xs[a:b+1])))
  return out
 if pid==1653:
  s=args[0]
  for removed in range(len(s)+1):
   for chosen in combinations(range(len(s)),removed):
    chosen=set(chosen);left=''.join(c for i,c in enumerate(s)if i not in chosen)
    if 'ba'not in left:return removed
 if pid==1743:
  pairs=args[0];nodes=set(x for e in pairs for x in e);edges={tuple(sorted(e))for e in pairs}
  return [list(p)for p in permutations(nodes)if {tuple(sorted(e))for e in zip(p,p[1:])}==edges]
 if pid==1817:
  logs,k=args;users=set(u for u,t in logs)
  amounts=[len({t for u,t in logs if u==user})for user in users]
  return [sum(n==j for n in amounts)for j in range(1,k+1)]
 if pid==1877:
  @lru_cache(None)
  def pair(xs):
   if not xs:return 0
   return min(max(xs[0]+xs[i],pair(xs[1:i]+xs[i+1:]))for i in range(1,len(xs)))
  return pair(tuple(args[0]))
 if pid==1887:
  xs=args[0][:];count=0
  while len(set(xs))>1:
   high=max(xs);next_high=max(x for x in xs if x<high);xs[xs.index(high)]=next_high;count+=1
  return count
 raise ValueError('unknown ID')
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 types={'python':{'list':'list','int':'int'},'javascript':{'list':'object','int':'number'}}
 if record.get('result_type')!=types[language][type(want).__name__]:return False,'result_type'
 actual=record.get('result')
 if pid==1743:
  pairs=args[0];nodes={x for e in pairs for x in e}
  if type(actual)is not list or not all(type(x)is int for x in actual)or len(actual)!=len(nodes)or set(actual)!=nodes or {tuple(sorted(e))for e in zip(actual,actual[1:])}!={tuple(sorted(e))for e in pairs}:return False,'restored_path_relation'
 elif not exact(actual,want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
