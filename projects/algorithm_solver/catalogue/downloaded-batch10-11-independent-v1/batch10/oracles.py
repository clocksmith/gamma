"""Independent host references for batch ten; no candidate imports."""
from collections import Counter
from functools import lru_cache
from fractions import Fraction
from itertools import permutations,combinations
import math,re
DEFINITION_BLOCKED={1427}
MANDATORY_FAILURES={}
@lru_cache(None)
def palindrome_removals(s):
 if not s:return 0
 best=len(s)
 for mask in range(1,1<<len(s)):
  word=''.join(c for i,c in enumerate(s)if mask>>i&1)
  if word==word[::-1]:best=min(best,1+palindrome_removals(''.join(c for i,c in enumerate(s)if not(mask>>i&1))))
 return best
@lru_cache(None)
def frog_min(s):
 # Assign each character to any existing compatible frog or a new frog.
 if not s:return 0
 states={((),0)}
 for c in s:
  next_states=set()
  for active,peak in states:
   if c=='c':next_states.add((tuple(sorted(active+(1,))),max(peak,len(active)+1)))
   else:
    stage='croak'.index(c)
    for i,v in enumerate(active):
     if v==stage:
      new=active[:i]+active[i+1:]+(()if stage==4 else(stage+1,));next_states.add((tuple(sorted(new)),peak))
  states=next_states
 return min([peak for active,peak in states if not active]or[-1])
def expected(pid,a):
 x=a[0]
 if pid==1311:
  watched,friends,start,level=a;n=len(friends);d=[[0 if i==j else 10**6 for j in range(n)]for i in range(n)]
  for i,row in enumerate(friends):
   for j in row:d[i][j]=1
  for k in range(n):
   for i in range(n):
    for j in range(n):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
  counts=Counter(v for i,row in enumerate(watched)if d[start][i]==level for v in row);return sorted(counts,key=lambda v:(counts[v],v))
 if pid==1314:
  k=a[1];return [[sum(x[u][v]for u in range(len(x))for v in range(len(x[0]))if abs(u-r)<=k and abs(v-c)<=k)for c in range(len(x[0]))]for r in range(len(x))]
 if pid==1328:
  values=[]
  for i in range(len(x)):
   for c in 'abcdefghijklmnopqrstuvwxyz':
    if c==x[i]:continue
    s=x[:i]+c+x[i+1:]
    if s!=s[::-1]:values.append(s)
  return min(values)if values else''
 if pid==1329:
  result=[row[:]for row in x]
  for r,c in [(0,c)for c in range(len(x[0]))]+[(r,0)for r in range(1,len(x))]:
   cells=[]
   while r<len(x)and c<len(x[0]):cells.append((r,c));r+=1;c+=1
   # Rank by specification over one diagonal, using frequency counting.
   counts=Counter(x[r][c]for r,c in cells);values=[v for v in range(1,101)for _ in range(counts[v])]
   for (r,c),v in zip(cells,values):result[r][c]=v
  return result
 if pid==1332:return palindrome_removals(x)
 if pid==1344:
  ticks=(60*(x%12)-11*a[1])%720;return float(Fraction(min(ticks,720-ticks),2))
 if pid==1375:
  on=set();answer=0
  for v in x:
   on.add(v);answer+=on==set(range(1,len(on)+1))
  return answer
 if pid==1386:
  n,reserved=a;reserved=set(map(tuple,reserved));answer=0
  groups=[set(range(start,start+4))for start in range(1,8)if all(not(start<=aisle<start+3)or aisle-start==1 for aisle in (3,7))]
  for row in range(1,n+1):
   valid=[g for g in groups if not any((row,s)in reserved for s in g)];answer+=max([0]+[len(combo)for k in range(1,len(valid)+1)for combo in combinations(valid,k)if sum(map(len,combo))==len(set().union(*combo))])
  return answer
 if pid==1394:return max([v for v in set(x)if x.count(v)==v]or[-1])
 if pid==1402:return max([0]+[sum(i*v for i,v in enumerate(order,1))for n in range(1,len(x)+1)for order in permutations(x,n)])
 if pid==1410:
  mapping={'&quot;':'"','&apos;':"'",'&amp;':'&','&gt;':'>','&lt;':'<','&frasl;':'/'}
  return re.sub(r'&(?:quot|apos|amp|gt|lt|frasl);',lambda m:mapping[m[0]],x)
 if pid==1418:
  foods=sorted({r[2]for r in x});tables=sorted({int(r[1])for r in x});return [['Table']+foods]+[[str(t)]+[str(sum(int(row[1])==t and row[2]==f for row in x))for f in foods]for t in tables]
 if pid==1419:return frog_min(x)
 if pid==1427:
  values=list(x)
  for direction,amount in a[1]:
   for _ in range(amount%len(values)):
    if direction:values.insert(0,values.pop())
    else:values.append(values.pop(0))
  return ''.join(values)
 if pid==1433:
  y=a[1];thresholds='abcdefghijklmnopqrstuvwxyz'
  return all(sum(v>=c for v in x)>=sum(v>=c for v in y)for c in thresholds)or all(sum(v>=c for v in y)>=sum(v>=c for v in x)for c in thresholds)
 if pid==1442:
  def xor(v):
   n=0
   for c in v:n^=c
   return n
  return sum(xor(x[i:j])==xor(x[j:k+1])for i in range(len(x))for j in range(i+1,len(x))for k in range(j,len(x)))
 raise ValueError(pid)
def exact(a,b):
 return type(a)is type(b)and(len(a)==len(b)and all(exact(l,r)for l,r in zip(a,b))if type(a)is list else a==b)
def matches(pid,args,value,want):
 if pid==1344:return type(value)in(int,float)and math.isfinite(value)and -1e-5<=value<=180+1e-5 and abs(value-want)<=1e-5
 return exact(value,want)
def compare(pid,args,want,row,lang):
 if 'error'in row:return False,'candidate_error'
 types={'python':{list:'list',int:'int',bool:'bool',str:'str'},'javascript':{list:'object',int:'number',bool:'boolean',str:'string'}}
 if pid==1344:
  if row.get('result_type')not in(('int','float')if lang=='python'else('number',)):return False,'result_type'
 elif row.get('result_type')!=types[lang][type(want)]:return False,'result_type'
 if not matches(pid,args,row.get('result'),want):return False,'result_value'
 if not exact(row.get('args_before'),args)or not exact(row.get('args_after'),args):return False,'input_effects'
 if row.get('alias_edges')!=[]:return False,'mutable_alias'
 return True,None
