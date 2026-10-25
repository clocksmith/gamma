"""Definition-level host truth; no candidate imports; unsupported large cases reject."""
from collections import Counter
from decimal import Decimal,localcontext
from itertools import permutations,combinations
from functools import lru_cache
import math
IDS=(1515,1521,1542,1585,1713,2111,2127)
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(xs,a,b,lo=1,hi=100000):return type(xs)is list and lo<=len(xs)<=hi and all(integer(x,a,b)for x in xs)
def digits(s):return type(s)is str and 1<=len(s)<=100000 and all('0'<=c<='9'for c in s)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered argument list required')
 ok=False
 if pid==1515:ok=len(args)==1 and type(args[0])is list and 1<=len(args[0])<=50 and all(ints(p,0,100,2,2)for p in args[0])
 elif pid==1521:ok=len(args)==2 and ints(args[0],1,1000000)and integer(args[1],0,10000000)
 elif pid==1542:ok=len(args)==1 and digits(args[0])
 elif pid==1585:ok=len(args)==2 and digits(args[0])and digits(args[1])and len(args[0])==len(args[1])
 elif pid==1713:ok=len(args)==2 and ints(args[0],1,10**9)and ints(args[1],1,10**9)and len(set(args[0]))==len(args[0])
 elif pid==2111:ok=len(args)==2 and type(args[0])is list and ints(args[0],1,len(args[0]))and integer(args[1],1,len(args[0]))
 elif pid==2127:ok=len(args)==1 and type(args[0])is list and ints(args[0],0,len(args[0])-1,2)and all(i!=v for i,v in enumerate(args[0]))
 if not ok:raise ValueError('outside reviewed official domain or blocked ID')
def geometric(positions):
 """50-digit analytic optimum for declared finite fixture families, NOT ternary search.
 Median on a line; opposite-pair triangle lower bound; majority-point triangle
 bound; three-point Fermat/120-degree formula. Unsupported geometry rejects.
 """
 with localcontext()as ctx:
  ctx.prec=50;p=[tuple(map(Decimal,x))for x in positions];n=len(p)
  def distance(a,b):return sum((x-y)**2 for x,y in zip(a,b)).sqrt()
  counts=Counter(p)
  for center,count in counts.items():
   if 2*count>=n:return str(sum((distance(x,center)for x in p),Decimal()))
  a=p[0];b=next((x for x in p if x!=a),a)
  if all((x[0]-a[0])*(b[1]-a[1])==(x[1]-a[1])*(b[0]-a[0])for x in p):
   center=sorted(p)[n//2];return str(sum((distance(x,center)for x in p),Decimal()))
  center=tuple(sum(x[i]for x in p)/n for i in(0,1))
  if all(counts[(2*center[0]-x[0],2*center[1]-x[1])]==count for x,count in counts.items()):return str(sum((distance(x,center)for x in p),Decimal()))
  if n==3:
   side2=[sum((x-y)**2 for x,y in zip(p[i],p[j]))for i,j in((1,2),(0,2),(0,1))]
   for i in range(3):
    others=[side2[j]for j in range(3)if j!=i]
    if side2[i]>=sum(others)+(others[0]*others[1]).sqrt():return str(sum((distance(p[i],x)for x in p),Decimal()))
   twice_area=abs((p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[1][1]-p[0][1])*(p[2][0]-p[0][0]))
   return str(((sum(side2)+2*Decimal(3).sqrt()*twice_area)/2).sqrt())
  raise ValueError('unsupported host geometry: analytic certified families only')
@lru_cache(maxsize=512)
def reachable(s):
 seen={s};todo=[s]
 for x in todo:
  for i in range(len(x)-1):
   if x[i]>x[i+1]:
    y=x[:i]+x[i+1]+x[i]+x[i+2:]
    if y not in seen:seen.add(y);todo.append(y)
 return frozenset(seen)
def expected(pid,args):
 validate(pid,args)
 if pid==1515:return {'analytic_decimal':geometric(args[0]),'oracle_absolute_uncertainty':'1e-35','official_absolute_tolerance':'1e-5'}
 if pid==1521:
  a,t=args
  if len(set(a))==1:return abs(a[0]-t)
  if len(a)>200:
   if t in a:return 0
   if t==0 and any(x&y==0 for x,y in zip(a,a[1:])):return 0
   raise ValueError('bounded interval oracle')
  best=10**20
  for i in range(len(a)):
   v=a[i]
   for j in range(i,len(a)):v&=a[j];best=min(best,abs(v-t))
  return best
 if pid==1542:
  s=args[0]
  if sum(v%2 for v in Counter(s).values())<=1:return len(s)
  if len(s)>200:raise ValueError('bounded substring enumeration oracle')
  best=1
  for i in range(len(s)):
   counts=Counter()
   for j in range(i,len(s)):
    counts[s[j]]+=1
    if sum(v%2 for v in counts.values())<=1:best=max(best,j-i+1)
  return best
 if pid==1585:
  s,t=args
  if Counter(s)!=Counter(t):return False
  if s==t or t==''.join(sorted(s)):return True
  if s==''.join(sorted(s)):return False
  if len(s)>8:raise ValueError('bounded adjacent-inversion reachability oracle')
  return t in reachable(s)
 if pid==1713:
  a,b=args
  if a==b:return 0
  if not set(a)&set(b):return len(a)
  if b==a[::-1]:return len(a)-1
  if len(a)*len(b)>40000:raise ValueError('bounded LCS table oracle')
  previous=[0]*(len(b)+1)
  for x in a:
   current=[0]
   for j,y in enumerate(b):current.append(previous[j]+1 if x==y else max(previous[j+1],current[-1]))
   previous=current
  return len(a)-previous[-1]
 if pid==2111:
  a,k=args
  if all(a[i-k]<=a[i]for i in range(k,len(a))):return 0
  if all(a[i-k]>a[i]for i in range(k,len(a))):return len(a)-k
  if len(a)>200:raise ValueError('bounded quadratic subsequence oracle')
  result=0
  for start in range(k):
   seq=a[start::k];dp=[]
   for i,x in enumerate(seq):dp.append(1+max((dp[j]for j in range(i)if seq[j]<=x),default=0))
   result+=len(seq)-max(dp)
  return result
 f=args[0];n=len(f)
 if n>8:
  if f==list(range(1,n))+[0]:return n
  if all(f[f[i]]==i for i in range(n)):return n
  if f[:2]==[1,0]and all(x==0 for x in f[2:]):return 3
  if f==[1,0]+list(range(1,n-1)):return n
  raise ValueError('bounded circular seating enumeration oracle')
 for size in range(n,1,-1):
  for chosen in combinations(range(n),size):
   for tail in permutations(chosen[1:]):
    seating=(chosen[0],)+tail
    if all(f[x]in(seating[i-1],seating[(i+1)%size])for i,x in enumerate(seating)):return size
 raise AssertionError('finite functional graph contains a cycle')
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 result=record.get('result')
 if pid==1515:
  if record.get('result_type')!=('float'if language=='python'else'number')or type(result)not in(int,float)or (language=='python'and type(result)is not float)or not math.isfinite(result):return False,'finite_numeric_type'
  # Conservatively shrink official acceptance by the analytic oracle guard.
  with localcontext()as ctx:
   ctx.prec=1200
   actual=Decimal.from_float(result)if type(result)is float else Decimal(result)
   if abs(actual-Decimal(want['analytic_decimal']))>Decimal('1e-5')-Decimal('1e-35'):return False,'official_absolute_tolerance'
 else:
  kind='bool'if pid==1585 else'int';types={'python':{'bool':'bool','int':'int'},'javascript':{'bool':'boolean','int':'number'}}
  if record.get('result_type')!=types[language][kind]:return False,'result_type'
  if not exact(result,want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
