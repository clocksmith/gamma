"""Definition-derived exact host oracles and freedom predicates; never import sources."""
from collections import Counter,deque,defaultdict
from functools import lru_cache
from fractions import Fraction
from itertools import combinations,product
import math,datetime
DEFINITION_BLOCKED=set()
MANDATORY_FAILURES={(1578,'javascript'):'Original writes caller cost array on descending equal-color runs; immutable input violated'}
MOD=1000000007

def subsets(a):
 for mask in range(1<<len(a)):yield [v for i,v in enumerate(a)if mask>>i&1]
@lru_cache(None)
def suffix_distances(n):
 d={0:0};q=deque([0])
 while q:
  x=q.popleft()
  for i in range(n):
   y=x^((1<<(n-i))-1)
   if y not in d:d[y]=d[x]+1;q.append(y)
 return d
@lru_cache(None)
def coins(values):
 if not values:return 0
 return max(sorted([values[i]for i in indices])[1]+coins(tuple(v for i,v in enumerate(values)if i not in indices))for indices in combinations(range(len(values)),3))
def balls_probability(balls):
 states={(0,0):1}
 for count in balls:
  nxt=defaultdict(int)
  for (taken,diff),ways in states.items():
   for take in range(count+1):nxt[taken+take,diff+int(take>0)-int(take<count)]+=ways*math.comb(count,take)
  states=nxt
 total=sum(balls);return float(Fraction(states.get((total//2,0),0),math.comb(total,total//2)))
def expected(pid,a):
 x=a[0]
 if pid==1458:
  return max(sum(l*r for l,r in zip(xs,ys))for xs in subsets(x)if xs for ys in subsets(a[1])if len(ys)==len(xs))
 if pid==1460:return Counter(x)==Counter(a[1])
 if pid==1461:return all(''.join(bits)in x for bits in product('01',repeat=a[1]))
 if pid==1467:return balls_probability(x)
 if pid==1475:return [v-next((w for w in x[i+1:]if w<=v),0)for i,v in enumerate(x)]
 if pid==1477:
  ranges=[(i,j)for i in range(len(x))for j in range(i+1,len(x)+1)if sum(x[i:j])==a[1]]
  return min([j-i+l-k for i,j in ranges for k,l in ranges if j<=k or l<=i]or[-1])
 if pid==1487:
  result=[]
  for name in x:
   if name not in result:result.append(name);continue
   k=1
   while name+'('+str(k)+')'in result:k+=1
   result.append(name+'('+str(k)+')')
  return result
 if pid==1488:
  states={frozenset()}
  for lake in x:
   if lake:states={s|{lake}for s in states if lake not in s}
   else:states={s-{lake}for s in states for lake in s}|states
  return bool(states)
 if pid==1492:
  divisors=sorted(v for v in range(1,x+1)if x%v==0);return divisors[a[1]-1]if a[1]<=len(divisors)else-1
 if pid==1493:
  answer=0
  for i in range(len(x)):
   current=0
   for v in x[:i]+x[i+1:]:
    current=current+1 if v else 0;answer=max(answer,current)
  return answer
 if pid==1498:return sum(bool(s)and min(s)+max(s)<=a[1]for s in subsets(x))%MOD
 if pid==1507:
  day,month,year=x.split();months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];return datetime.date(int(year),months.index(month)+1,int(day[:-2])).isoformat()
 if pid==1508:
  sums=sorted(sum(x[i:j])for i in range(len(x))for j in range(i+1,len(x)+1));return sum(sums[a[2]-1:a[3]])%MOD
 if pid==1512:return sum(l==r for i,l in enumerate(x)for r in x[i+1:])
 if pid==1514:
  n,edges,probs,start,end=a;graph=[[]for _ in range(n)]
  for (u,v),p in zip(edges,probs):graph[u].append((v,Fraction(str(p))));graph[v].append((u,Fraction(str(p))))
  best=Fraction(0);stack=[(start,1<<start,Fraction(1))]
  while stack:
   node,mask,prob=stack.pop()
   if node==end:best=max(best,prob);continue
   for nxt,p in graph[node]:
    if not(mask>>nxt&1):stack.append((nxt,mask|1<<nxt,prob*p))
  return float(best)
 if pid==1518:return x+(x-1)//(a[1]-1)
 if pid==1525:return sum(len(set(x[:i]))==len(set(x[i:]))for i in range(1,len(x)))
 if pid==1526:return sum(sum(v>=height and (i==0 or x[i-1]<height)for i,v in enumerate(x))for height in range(1,max(x)+1))
 if pid==1529:return suffix_distances(len(x))[int(x,2)]
 if pid==1545:
  n,k=a;flipped=False
  while n>1:
   mid=1<<(n-1)
   if k==mid:return str(int(not flipped))
   if k>mid:k=(1<<n)-k;flipped=not flipped
   n-=1
  return str(int(flipped))
 if pid==1546:
  dp=[0]*(len(x)+1)
  for end in range(1,len(x)+1):dp[end]=max([dp[end-1]]+[dp[start]+1 for start in range(end)if sum(x[start:end])==a[1]])
  return dp[-1]
 if pid==1552:return max(min(r-l for l,r in zip(sorted(s),sorted(s)[1:]))for s in combinations(x,a[1]))
 if pid==1558:return sum(v.bit_count()for v in x)+max([0]+[v.bit_length()-1 for v in x])
 if pid==1561:return coins(tuple(sorted(x)))
 if pid==1566:
  m,k=a[1:];return any(x[i:i+m]*k==x[i:i+m*k]for i in range(len(x)-m*k+1))
 if pid==1574:return min(j-i for i in range(len(x)+1)for j in range(i,len(x)+1)if all(l<=r for l,r in zip(x[:i]+x[j:],(x[:i]+x[j:])[1:])))
 if pid==1576:return None
 if pid==1578:
  cost=a[1];return min(sum(cost[i]for i in range(len(x))if not(mask>>i&1))for mask in range(1<<len(x))if all(l!=r for l,r in zip([c for i,c in enumerate(x)if mask>>i&1],[c for i,c in enumerate(x)if mask>>i&1][1:])))
 if pid==1592:
  words=x.split();spaces=x.count(' ')
  if len(words)==1:return words[0]+' '*spaces
  gap=max(g for g in range(spaces+1)if g*(len(words)-1)<=spaces);return (' '*gap).join(words)+' '*(spaces-gap*(len(words)-1))
 if pid==1594:
  rows,cols=len(x),len(x[0]);values=[];stack=[(0,0,x[0][0])]
  while stack:
   r,c,value=stack.pop()
   if r==rows-1 and c==cols-1:values.append(value)
   if r+1<rows:stack.append((r+1,c,value*x[r+1][c]))
   if c+1<cols:stack.append((r,c+1,value*x[r][c+1]))
  best=max(values);return -1 if best<0 else best%MOD
 if pid==1599:
  customers,fee,cost=a;prefix=[0]
  for v in customers:prefix.append(prefix[-1]+v)
  profits=[]
  for r in range(1,len(x)+(sum(x)+3)//4+1):
   boarded=min(prefix[min(t,len(x))]+4*(r-t)for t in range(r+1));profits.append(boarded*fee-r*cost)
  best=max(profits);return profits.index(best)+1 if best>0 else-1
 raise ValueError(pid)
def exact(a,b):return type(a)is type(b)and(len(a)==len(b)and all(exact(l,r)for l,r in zip(a,b))if type(a)is list else a==b)
def matches(pid,args,value,want):
 if pid in (1467,1514):return type(value)in(int,float)and math.isfinite(value)and -1e-5<=value<=1+1e-5 and abs(value-want)<=1e-5
 if pid==1488:
  if not want:return exact(value,[])
  if type(value)is not list or len(value)!=len(args[0])or any(type(v)is not int for v in value):return False
  full=set()
  for rain,dry in zip(args[0],value):
   if rain:
    if dry!=-1 or rain in full:return False
    full.add(rain)
   else:
    if dry<=0:return False
    full.discard(dry)
  return True
 if pid==1576:return type(value)is str and len(value)==len(args[0])and all('a'<=c<='z'and (old=='?'or old==c)for old,c in zip(args[0],value))and all(l!=r for l,r in zip(value,value[1:]))
 return exact(value,want)
def input_matches(pid,observed,args):
 if pid!=1514:return exact(observed,args)
 if type(observed)is not list or len(observed)!=5:return False
 if not all(exact(observed[i],args[i])for i in (0,1,3,4)):return False
 return type(observed[2])is list and len(observed[2])==len(args[2])and all(type(v)in(int,float)and math.isfinite(v)and v==w for v,w in zip(observed[2],args[2]))
def compare(pid,args,want,row,lang):
 if 'error'in row:return False,'candidate_error'
 kind=list if pid==1488 else str if pid==1576 else type(want)
 types={'python':{list:'list',int:'int',bool:'bool',str:'str'},'javascript':{list:'object',int:'number',bool:'boolean',str:'string'}}
 if pid in (1467,1514):
  if row.get('result_type')not in(('int','float')if lang=='python'else('number',)):return False,'result_type'
 elif row.get('result_type')!=types[lang][kind]:return False,'result_type'
 if not matches(pid,args,row.get('result'),want):return False,'result_value'
 if not input_matches(pid,row.get('args_before'),args)or not input_matches(pid,row.get('args_after'),args):return False,'input_effects'
 if row.get('alias_edges')!=[]:return False,'mutable_alias'
 return True,None
