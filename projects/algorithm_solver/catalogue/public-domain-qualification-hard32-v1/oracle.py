"""Independent host oracles; no candidate imports or execution."""
from itertools import product
from functools import lru_cache
from fractions import Fraction
from math import factorial
import re
IDS=(798,801,899,913,928,972,1397,1434)
MOD=1000000007
RATIONAL=re.compile(r'(0|[1-9][0-9]{0,3})(?:\.([0-9]{0,4})(?:\(([0-9]{1,4})\))?)?\Z',re.ASCII)
def require(ok):
 if not ok:raise ValueError('outside reviewed official domain')
def integer(x,lo,hi):return type(x)is int and lo<=x<=hi
def ints(x,lo,hi):return type(x)is list and all(integer(v,lo,hi)for v in x)
def letters(x):return type(x)is str and bool(x)and all('a'<=c<='z'for c in x)
def validate(pid,args):
 require(pid in IDS and type(args)is list)
 require(len(args)=={798:1,801:2,899:2,913:1,928:2,972:2,1397:4,1434:1}[pid])
 if pid==798:
  a=args[0];require(type(a)is list and 1<=len(a)<=100000 and ints(a,0,len(a)-1))
 elif pid==801:
  a,b=args;require(type(a)is list and type(b)is list and 2<=len(a)==len(b)<=100000 and ints(a,0,200000)and ints(b,0,200000))
  # Existence predicate only, not the minimum-swap cost oracle.
  possible={0,1}
  for i in range(1,len(a)):
   possible={s for s in(0,1)if any((a[i-1],b[i-1])[t]<(a[i],b[i])[s]and(b[i-1],a[i-1])[t]<(b[i],a[i])[s]for t in possible)}
  require(bool(possible))
 elif pid==899:require(letters(args[0])and len(args[0])<=1000 and integer(args[1],1,len(args[0])))
 elif pid==913:
  g=args[0];require(type(g)is list and 3<=len(g)<=50);n=len(g)
  for i,row in enumerate(g):require(ints(row,0,n-1)and 1<=len(row)<n and len(set(row))==len(row)and i not in row)
  require(all(i in g[j]for i,row in enumerate(g)for j in row))
  # 'Can always move' concerns reachable nonterminal play, not every vertex:
  # official example 2 has node 1 adjacent only to hole, unreachable by cat.
  seen={(1,2,0)};todo=[(1,2,0)]
  for m,c,t in todo:
   if m==0 or m==c:continue
   children=([(j,c,1)for j in g[m]]if t==0 else[(m,j,0)for j in g[c]if j!=0])
   require(bool(children))
   for state in children:
    if state not in seen:seen.add(state);todo.append(state)
 elif pid==928:
  g,initial=args;require(type(g)is list and 2<=len(g)<=300);n=len(g)
  require(all(ints(row,0,1)and len(row)==n for row in g));require(all(g[i][i]==1 and all(g[i][j]==g[j][i]for j in range(n))for i in range(n)))
  require(ints(initial,0,n-1)and 1<=len(initial)<n and len(set(initial))==len(initial))
 elif pid==972:require(all(type(x)is str and RATIONAL.fullmatch(x)for x in args))
 elif pid==1397:
  n,a,b,e=args;require(integer(n,1,500)and all(letters(x)for x in(a,b,e))and len(a)==len(b)==n and a<=b and 1<=len(e)<=50)
 else:
  h=args[0];require(type(h)is list and 1<=len(h)<=10);require(all(ints(row,1,40)and 1<=len(row)<=40 and len(set(row))==len(row)for row in h))
def rational(text):
 """Sum place-value geometric series, using exact Fraction throughout."""
 whole,prefix,repeat=RATIONAL.fullmatch(text).groups();v=Fraction(int(whole))
 for i,c in enumerate(prefix or ''):v+=Fraction(int(c),10**(i+1))
 if repeat:
  cycle=sum((Fraction(int(c),10**(len(prefix)+i+1))for i,c in enumerate(repeat)),Fraction())
  v+=cycle/(1-Fraction(1,10**len(repeat)))
 return v
@lru_cache(maxsize=256)
def game(graph):
 """Synchronous least fixed point of winning attractors, no reverse-edge queue.
 Unlabelled closed remainder permits both players to avoid loss indefinitely;
 finite state repetition is precisely the official draw condition.
 """
 n=len(graph);states=[(m,c,t)for m in range(n)for c in range(1,n)for t in(0,1)]
 values={(m,c,t):(1 if m==0 else 2 if m==c else 0)for m,c,t in states}
 for _ in range(len(states)):
  following=values.copy()
  for m,c,t in states:
   if values[m,c,t]:continue
   children=([values[x,c,1]for x in graph[m]]if t==0 else[values[m,x,0]for x in graph[c]if x!=0])
   if t+1 in children:following[m,c,t]=t+1
   elif children and all(x==2-t for x in children):following[m,c,t]=2-t
  if following==values:return values[1,2,0]
  values=following
 raise AssertionError('finite attractor convergence bound')
def expected(pid,args):
 validate(pid,args)
 if pid==798:
  a=args[0];n=len(a)
  if len(set(a))==1:return 0
  if n>200:raise ValueError('host rotation enumeration bounded to 200 except constant family')
  return max(range(n),key=lambda k:sum(a[(i+k)%n]<=i for i in range(n)))
 if pid==801:
  a,b=args;n=len(a)
  if all(x<y for seq in(a,b)for x,y in zip(seq,seq[1:])):return 0
  if n>12:raise ValueError('host swap enumeration bounded to 12 except already-increasing family')
  scores=[]
  for mask in range(1<<n):
   x=[(a[i],b[i])[(mask>>i)&1]for i in range(n)];y=[(b[i],a[i])[(mask>>i)&1]for i in range(n)]
   if all(x[i]<x[i+1]and y[i]<y[i+1]for i in range(n-1)):scores.append(mask.bit_count())
  return min(scores)
 if pid==899:
  s,k=args
  if k==1:return min(s[i:]+s[:i]for i in range(len(s)))
  if len(s)>7:
   # First-two moves generate all permutations: rotations plus adjacent swaps.
   return ''.join(sorted(s))
  seen={s};todo=[s]
  for x in todo:
   for i in range(k):
    y=x[:i]+x[i+1:]+x[i]
    if y not in seen:seen.add(y);todo.append(y)
  return min(seen)
 if pid==913:return game(tuple(tuple(row)for row in args[0]))
 if pid==928:
  g,initial=args
  def infected(removed):
   reached=set(initial)-{removed};todo=list(reached)
   for i in todo:
    for j,edge in enumerate(g[i]):
     if edge and j!=removed and j not in reached:reached.add(j);todo.append(j)
   return len(reached)
  return min(initial,key=lambda i:(infected(i),i))
 if pid==972:return rational(args[0])==rational(args[1])
 if pid==1397:
  n,a,b,e=args
  if a==b:return int(e not in a)
  if a=='a'*n and b=='z'*n and len(e)==1:return pow(25,n,MOD)
  def rank(s):
   r=0
   for c in s:r=26*r+ord(c)-97
   return r
  lo,hi=rank(a),rank(b)
  if len(e)>n:return (hi-lo+1)%MOD
  if hi-lo>20000:raise ValueError('bounded lexical enumeration oracle')
  count=0
  for number in range(lo,hi+1):
   chars=[]
   for _ in range(n):number,d=divmod(number,26);chars.append(chr(97+d))
   count+=e not in ''.join(reversed(chars))
  return count%MOD
 # Partition-lattice inclusion-exclusion over PEOPLE, unlike candidate hat DP.
 hats=[set(row)for row in args[0]];n=len(hats)
 weights={}
 for mask in range(1,1<<n):
  members=[i for i in range(n)if mask>>i&1];common=set.intersection(*(hats[i]for i in members));k=len(members)
  weights[mask]=(-1)**(k-1)*factorial(k-1)*len(common)
 @lru_cache(None)
 def partitions(mask):
  if not mask:return 1
  first=mask&-mask;rest=mask^first;sub=rest;total=0
  while True:
   block=sub|first;total+=weights[block]*partitions(mask^block)
   if sub==0:return total
   sub=(sub-1)&rest
 return partitions((1<<n)-1)%MOD

def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind='bool'if pid==972 else'str'if pid==899 else'int'
 types={'python':{'bool':'bool','str':'str','int':'int'},'javascript':{'bool':'boolean','str':'string','int':'number'}}
 if record.get('result_type')!=types[language][kind]:return False,'result_type'
 if not exact(record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
