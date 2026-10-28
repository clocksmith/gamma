"""Independent public-definition references for exact batch08 identities.

Host references only. No candidate source, delivered expectations, protected cases,
or cross-language agreement is used to produce expected outputs.
"""
import math,re,heapq
from bisect import bisect_left
from collections import Counter,deque
from functools import lru_cache
from itertools import combinations,product
from fractions import Fraction
IDS=(1002,1003,1004,1006,1007,1010,1011,1013,1014,1015,1016,1017,1020,1023,1024,1027,1029,1030,1031,1033,1034,1035,1037,1041,1042,1043,1048,1049,1052,1053,1057,1060,1061,1063,1066,1072,1073,1074,1079,1081,1087,1089,1090,1091,1093,1094,1104,1105,1109,1111,1114)
RESTRICTED={1057,1060,1063,1066,1087}
FUNCTIONAL=tuple(p for p in IDS if p not in RESTRICTED|{1114})

def require(condition):
 if not condition:raise ValueError('case outside pinned generated-case domain')
def integer(v,lo,hi):require(type(v)is int and lo<=v<=hi)
def array(x,lo,hi,lower,upper):
 require(type(x)is list);integer(len(x),lo,hi)
 for v in x:integer(v,lower,upper)
def text(s,lo,hi,alphabet):require(type(s)is str and lo<=len(s)<=hi and set(s)<=set(alphabet))
def matrix(x,m,n,lo,hi):
 require(type(x)is list);integer(len(x),1,m);require(type(x[0])is list);integer(len(x[0]),1,n)
 for row in x:array(row,len(x[0]),len(x[0]),lo,hi)
def vps(s):
 level=peak=0
 for ch in s:
  level+=1 if ch=='('else-1
  if level<0:return None
  peak=max(peak,level)
 return peak if level==0 else None

def validate(pid,args):
 require(pid in FUNCTIONAL and type(args)is list);x=args[0]
 lengths={1002:1,1003:1,1004:2,1006:1,1007:2,1010:1,1011:2,1013:1,1014:1,1015:1,1016:2,1017:1,1020:1,1023:2,1024:2,1027:1,1029:1,1030:4,1031:3,1033:3,1034:4,1035:2,1037:1,1041:1,1042:2,1043:2,1048:1,1049:1,1052:3,1053:1,1061:3,1072:1,1073:2,1074:2,1079:1,1081:1,1089:1,1090:4,1091:1,1093:1,1094:2,1104:1,1105:2,1109:2,1111:1};require(len(args)==lengths[pid])
 if pid in(1002,1048):
  require(type(x)is list);integer(len(x),1,100 if pid==1002 else 1000)
  for w in x:text(w,1,100 if pid==1002 else 16,'abcdefghijklmnopqrstuvwxyz')
 elif pid==1003:text(x,1,20000,'abc')
 elif pid==1004:array(x,1,100000,0,1);integer(args[1],0,len(x))
 elif pid==1006:integer(x,1,10000)
 elif pid==1007:array(x,2,20000,1,6);array(args[1],len(x),len(x),1,6)
 elif pid==1010:array(x,1,60000,1,500)
 elif pid==1011:array(x,1,50000,1,500);integer(args[1],1,len(x))
 elif pid==1013:array(x,3,50000,-10000,10000)
 elif pid==1014:array(x,2,50000,1,1000)
 elif pid==1015:integer(x,1,100000)
 elif pid==1016:text(x,1,1000,'01');integer(args[1],1,10**9)
 elif pid==1017:integer(x,0,10**9)
 elif pid==1020:matrix(x,500,500,0,1)
 elif pid==1023:
  require(type(x)is list);integer(len(x),1,100)
  for q in x:text(q,1,100,'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
  text(args[1],1,100,'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
 elif pid==1024:
  require(type(x)is list);integer(len(x),1,100)
  for a,b in x:integer(a,0,100);integer(b,a,100)
  integer(args[1],1,100)
 elif pid==1027:array(x,2,1500,0,500)
 elif pid==1029:
  matrix(x,100,2,1,1000);require(len(x)%2==0 and len(x[0])==2)
 elif pid==1030:integer(x,1,100);integer(args[1],1,100);integer(args[2],0,x-1);integer(args[3],0,args[1]-1)
 elif pid==1031:array(x,2,1000,0,1000);integer(args[1],1,len(x)-1);integer(args[2],1,len(x)-args[1])
 elif pid==1033:
  for v in args:integer(v,1,100)
  require(len(set(args))==3)
 elif pid==1034:matrix(x,50,50,1,1000);integer(args[1],0,len(x)-1);integer(args[2],0,len(x[0])-1);integer(args[3],1,1000)
 elif pid==1035:array(x,1,500,1,2000);array(args[1],1,500,1,2000)
 elif pid==1037:matrix(x,3,2,0,100);require(len(x)==3 and len(x[0])==2)
 elif pid==1041:text(x,1,100,'GLR')
 elif pid==1042:
  integer(x,1,10000);require(type(args[1])is list);integer(len(args[1]),0,20000);deg=Counter()
  for a,b in args[1]:integer(a,1,x);integer(b,1,x);require(a!=b);deg.update((a,b))
  require(max(deg.values(),default=0)<=3)
 elif pid==1043:
  array(x,1,500,0,10**9);integer(args[1],1,len(x));require(expected(pid,args)<=2**31-1)
 elif pid==1049:array(x,1,30,1,100)
 elif pid==1052:array(x,1,20000,0,1000);array(args[1],len(x),len(x),0,1);integer(args[2],1,len(x))
 elif pid==1053:array(x,1,10000,1,10000)
 elif pid==1061:
  for s in args:text(s,1,1000,'abcdefghijklmnopqrstuvwxyz')
  require(len(x)==len(args[1]))
 elif pid==1072:matrix(x,300,300,0,1)
 elif pid==1073:
  for v in args:array(v,1,1000,0,1);require(len(v)==1 or v[0]==1)
 elif pid==1074:matrix(x,100,100,-1000,1000);integer(args[1],-10**8,10**8)
 elif pid==1079:text(x,1,7,'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
 elif pid==1081:text(x,1,1000,'abcdefghijklmnopqrstuvwxyz')
 elif pid==1089:array(x,1,10000,0,9)
 elif pid==1090:array(x,1,20000,0,20000);array(args[1],len(x),len(x),0,20000);integer(args[2],1,len(x));integer(args[3],1,len(x))
 elif pid==1091:matrix(x,100,100,0,1);require(len(x)==len(x[0]))
 elif pid==1093:array(x,256,256,0,10**9);require(1<=sum(x)<=10**9 and x.count(max(x))==1)
 elif pid==1094:
  require(type(x)is list);integer(len(x),1,1000)
  for a,b,c in x:integer(a,1,100);integer(b,0,999);integer(c,b+1,1000)
  integer(args[1],1,100000)
 elif pid==1104:integer(x,1,10**6)
 elif pid==1105:
  integer(args[1],1,1000);matrix(x,1000,2,1,1000);require(len(x[0])==2 and all(a<=args[1]for a,b in x))
 elif pid==1109:
  integer(args[1],1,20000);require(type(x)is list);integer(len(x),1,20000)
  for a,b,c in x:integer(a,1,args[1]);integer(b,a,args[1]);integer(c,1,10000)
 elif pid==1111:text(x,1,10000,'()');require(vps(x)is not None)


def negative_digits(n):
 # For an even bit width, toggling odd bits converts signed radix weights.
 width=2*((abs(n).bit_length()+3)//2+1);mask=sum(1<<i for i in range(1,width,2))
 return bin((n+mask)^mask)[2:]
def factor(n):
 out={};d=2
 while d*d<=n:
  while n%d==0:out[d]=out.get(d,0)+1;n//=d
  d+=1
 if n>1:out[n]=out.get(n,0)+1
 return out

def expected(pid,args):
 x=args[0]
 if pid==1002:
  c=Counter(x[0])
  for w in x[1:]:c&=Counter(w)
  return sorted(c.elements())
 if pid==1003:
  while 'abc'in x:x=x.replace('abc','')
  return not x
 if pid==1004:
  if len(x)>1000:require(len(set(x))==1);return len(x)if x[0]else min(len(x),args[1])
  return max([0]+[j-i for i in range(len(x))for j in range(i+1,len(x)+1)if x[i:j].count(0)<=args[1]])
 if pid==1006:
  answer=0
  for i,a in enumerate(range(x,0,-4)):
   term=a if a==1 else a*(a-1)if a==2 else a*(a-1)//(a-2)
   answer+=term if i==0 else-term
   if a>=4:answer+=a-3
  return answer
 if pid==1007:
  y=args[1];n=len(x)
  if n>15:
   if len(set(x))==1 or len(set(y))==1:return 0
   require(set(x)|set(y)=={1,2}and all(a!=b for a,b in zip(x,y)));return min(x.count(1),x.count(2))
  best=n+1
  for mask in range(1<<n):
   a=[y[i]if mask>>i&1 else x[i]for i in range(n)];b=[x[i]if mask>>i&1 else y[i]for i in range(n)]
   if len(set(a))==1 or len(set(b))==1:best=min(best,mask.bit_count())
  return-1 if best>n else best
 if pid==1010:
  if len(x)>1000:require(len(set(x))==1);return len(x)*(len(x)-1)//2 if 2*x[0]%60==0 else 0
  return sum((a+b)%60==0 for a,b in combinations(x,2))
 if pid==1011:
  if len(x)>100:require(len(set(x))==1);return((len(x)+args[1]-1)//args[1])*x[0]
  @lru_cache(None)
  def partition(i,d):
   if i==len(x):return 0
   if d==0:return math.inf
   return min(max(sum(x[i:j]),partition(j,d-1))for j in range(i+1,len(x)+1))
  return partition(0,args[1])
 if pid==1013:
  if len(x)>1000:require(len(set(x))==1);return x[0]==0 or len(x)%3==0
  return any(sum(x[:i])==sum(x[i:j])==sum(x[j:])for i in range(1,len(x)-1)for j in range(i+1,len(x)))
 if pid==1014:
  if len(x)>1000:require(len(set(x))==1);return 2*x[0]-1
  return max(x[i]+x[j]+i-j for i in range(len(x))for j in range(i+1,len(x)))
 if pid==1015:
  if math.gcd(x,10)!=1:return-1
  m=9*x;phi=m
  for p in factor(m):phi=phi//p*(p-1)
  order=phi
  for p in factor(phi):
   while order%p==0 and pow(10,order//p,m)==1:order//=p
  return order
 if pid==1016:
  values=set()
  for i in range(len(x)):
   value=0
   for j in range(i,min(len(x),i+args[1].bit_length())):
    value=value*2+int(x[j])
    if 1<=value<=args[1]:values.add(value)
  return len(values)==args[1]
 if pid==1017:return negative_digits(x)
 if pid==1020:
  m,n=len(x),len(x[0]);parent=list(range(m*n+1));outside=m*n
  def find(i):
   while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
   return i
  def union(a,b):parent[find(a)]=find(b)
  for i,row in enumerate(x):
   for j,v in enumerate(row):
    if not v:continue
    k=i*n+j
    if i in(0,m-1)or j in(0,n-1):union(k,outside)
    if i and x[i-1][j]:union(k,k-n)
    if j and x[i][j-1]:union(k,k-1)
  return sum(v and find(i*n+j)!=find(outside)for i,row in enumerate(x)for j,v in enumerate(row))
 if pid==1023:
  pattern='[a-z]*'+'[a-z]*'.join(map(re.escape,args[1]))+'[a-z]*'
  return[bool(re.fullmatch(pattern,q))for q in x]
 if pid==1024:
  distance={0:0};queue=deque([0])
  while queue:
   end=queue.popleft()
   if end>=args[1]:return distance[end]
   for a,b in x:
    if a<=end<b and b not in distance:distance[b]=distance[end]+1;queue.append(b)
  return-1
 if pid==1027:
  if len(x)>20:require(len(set(x))==1);return len(x)
  best=2
  for size in range(3,len(x)+1):
   if any(len({b-a for a,b in zip(v,v[1:])})==1 for v in combinations(x,size)):best=size
  return best
 if pid==1029:
  if len(x)>12:require(len(set(map(tuple,x)))==1);return len(x)//2*sum(x[0])
  return min(sum(x[i][0]if i in chosen else x[i][1]for i in range(len(x)))for chosen in map(set,combinations(range(len(x)),len(x)//2)))
 if pid==1030:return [[r,c]for r in range(x)for c in range(args[1])]
 if pid==1031:
  if len(x)>100:require(len(set(x))==1);return(args[1]+args[2])*x[0]
  a,b=args[1:];return max(sum(x[i:i+a])+sum(x[j:j+b])for i in range(len(x)-a+1)for j in range(len(x)-b+1)if i+a<=j or j+b<=i)
 if pid==1033:
  initial=tuple(sorted(args));queue=deque([(initial,0)]);seen={initial}
  while queue:
   (a,b,c),steps=queue.popleft()
   if c-a==2:return[steps,initial[2]-initial[0]-2]
   for nextstate in [tuple(sorted((b,c,p)))for p in range(a+1,c)if p!=b]+[tuple(sorted((a,b,p)))for p in range(a+1,c)if p!=b]:
    if nextstate not in seen:seen.add(nextstate);queue.append((nextstate,steps+1))
 if pid==1034:
  row,col,color=args[1:];component={(row,col)};queue=deque(component);m,n=len(x),len(x[0])
  while queue:
   a,b=queue.popleft()
   for c,d in((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
    if 0<=c<m and 0<=d<n and x[c][d]==x[row][col]and(c,d)not in component:component.add((c,d));queue.append((c,d))
  return[[color if(i,j)in component and any((a,b)not in component for a,b in((i-1,j),(i+1,j),(i,j-1),(i,j+1)))else v for j,v in enumerate(line)]for i,line in enumerate(x)]
 if pid==1035:
  y=args[1]
  if len(x)>15 or len(y)>15:
   if set(x).isdisjoint(y):return 0
   require(len(set(x)|set(y))==1);return min(len(x),len(y))
  if len(x)>len(y):x,y=y,x
  best=0
  for mask in range(1<<len(x)):
   seq=[v for i,v in enumerate(x)if mask>>i&1];index=0
   for v in y:
    if index<len(seq)and seq[index]==v:index+=1
   if index==len(seq):best=max(best,len(seq))
  return best
 if pid==1037:return sum(x[i][0]*x[(i+1)%3][1]-x[(i+1)%3][0]*x[i][1]for i in range(3))!=0
 if pid==1041:
  point=0j;direction=1j
  for _ in range(4):
   for ch in x:
    if ch=='G':point+=direction
    elif ch=='L':direction*=1j
    else:direction*=-1j
  return point==0
 if pid==1042:return x
 if pid==1043:
  if len(x)>20:require(len(set(x))==1);return len(x)*x[0]
  @lru_cache(None)
  def partitions(start):
   if start==len(x):return 0
   return max(max(x[start:end])*(end-start)+partitions(end)for end in range(start+1,min(len(x),start+args[1])+1))
  return partitions(0)
 if pid==1048:
  words=tuple(set(x))
  def predecessor(a,b):
   if len(b)!=len(a)+1:return False
   i=0
   for ch in b:
    if i<len(a)and a[i]==ch:i+=1
   return i==len(a)
  @lru_cache(None)
  def length(w):return 1+max([0]+[length(a)for a in words if predecessor(a,w)])
  return max(map(length,words))
 if pid==1049:
  def signed(values):
   sums=[0]
   for v in values:sums=[s+v for s in sums]+[s-v for s in sums]
   return sums
  left=signed(x[:len(x)//2]);right=sorted(signed(x[len(x)//2:]));best=sum(x)
  for v in left:
   pos=bisect_left(right,-v)
   for p in(pos-1,pos):
    if 0<=p<len(right):best=min(best,abs(v+right[p]))
  return best
 if pid==1052:
  y,minutes=args[1:]
  if len(x)>1000:
   require(len(set(x))==len(set(y))==1);return x[0]*(len(x)if y[0]==0 else minutes)
  return max(sum(v for i,v in enumerate(x)if y[i]==0 or start<=i<start+minutes)for start in range(len(x)-minutes+1))
 if pid==1053:
  if len(x)>100:
   if x==sorted(x):return list(x)
   require(x==sorted(x,reverse=True)and len(set(x))==len(x));return x[:-2]+x[-2:][::-1]
  possibilities=[]
  for i,j in combinations(range(len(x)),2):
   y=x[:];y[i],y[j]=y[j],y[i]
   if y<x:possibilities.append(y)
  return max(possibilities,default=x[:])
 if pid==1061:
  graph={c:{c}for c in'abcdefghijklmnopqrstuvwxyz'}
  for a,b in zip(x,args[1]):graph[a].add(b);graph[b].add(a)
  out={}
  for c in graph:
   reached={c};queue=list(reached)
   for u in queue:
    for v in graph[u]:
     if v not in reached:reached.add(v);queue.append(v)
   out[c]=min(reached)
  return''.join(out[c]for c in args[2])
 if pid==1072:
  if len(x[0])>10:require(all(row==x[0]or row==[1-v for v in x[0]]for row in x));return len(x)
  return max(sum(len({v^(mask>>i&1)for i,v in enumerate(row)})==1 for row in x)for mask in range(1<<len(x[0])))
 if pid==1073:
  value=sum(v*(-2)**i for arr in args for i,v in enumerate(arr[::-1]));return list(map(int,negative_digits(value)))
 if pid==1074:
  m,n=len(x),len(x[0]);target=args[1]
  if m*n>100:
   require(len({v for row in x for v in row})==1);value=x[0][0]
   return sum((m-a+1)*(n-b+1)for a in range(1,m+1)for b in range(1,n+1)if a*b*value==target)
  return sum(sum(x[i][j]for i in range(a,b)for j in range(c,d))==target for a in range(m)for b in range(a+1,m+1)for c in range(n)for d in range(c+1,n+1))
 if pid==1079:
  counts=list(Counter(x).values());return sum(math.factorial(sum(v))//math.prod(math.factorial(k)for k in v)for v in product(*(range(c+1)for c in counts))if sum(v))
 if pid==1081:
  remaining=set(x);answer='';start=0
  while remaining:
   end=min(x.rfind(c)for c in remaining)
   ch=min(c for c in x[start:end+1]if c in remaining);start=x.index(ch,start)+1;answer+=ch;remaining.remove(ch)
  return answer
 if pid==1089:return[v for a in x for v in([0,0]if a==0 else[a])][:len(x)]
 if pid==1090:
  labels,wanted,limit=args[1:]
  if len(x)>20:
   require(len(set(x))==1 and(len(set(labels))==1 or len(set(labels))==len(labels)));return x[0]*min(wanted,limit if len(set(labels))==1 else len(x))
  return max(sum(x[i]for i in chosen)for size in range(wanted+1)for chosen in combinations(range(len(x)),size)if max(Counter(labels[i]for i in chosen).values(),default=0)<=limit)
 if pid==1091:
  n=len(x)
  if x[0][0]or x[-1][-1]:return-1
  heap=[(1,0,0)];distance={(0,0):1}
  while heap:
   d,i,j=heapq.heappop(heap)
   if d!=distance[i,j]:continue
   if(i,j)==(n-1,n-1):return d
   for a,b in product((-1,0,1),repeat=2):
    u,v=i+a,j+b
    if(a or b)and 0<=u<n and 0<=v<n and x[u][v]==0 and d+1<distance.get((u,v),math.inf):distance[u,v]=d+1;heapq.heappush(heap,(d+1,u,v))
  return-1
 if pid==1093:
  bins=[i for i,v in enumerate(x)if v];total=sum(x);prefix=[];s=0
  for v in x:s+=v;prefix.append(s)
  low=bisect_left(prefix,(total+1)//2);high=bisect_left(prefix,total//2+1)
  return[bins[0],bins[-1],float(Fraction(sum(i*v for i,v in enumerate(x)),total)),float(Fraction(low+high,2)),x.index(max(x))]
 if pid==1094:return all(sum(a for a,b,c in x if b<=position<c)<=args[1]for position in range(1000))
 if pid==1104:
  level=x.bit_length()-1;index=(1<<(level+1))-1+(1<<level)-x if level%2 else x;path=[]
  while index:
   d=index.bit_length()-1;path.append((1<<(d+1))-1+(1<<d)-index if d%2 else index);index//=2
  return path[::-1]
 if pid==1105:
  width=args[1]
  if len(x)>20:require(len(set(map(tuple,x)))==1);return((len(x)*x[0][0]+width-1)//width)*x[0][1]if width%x[0][0]==0 else((len(x)+(width//x[0][0])-1)//(width//x[0][0]))*x[0][1]
  @lru_cache(None)
  def shelf(i):
   if i==len(x):return 0
   choices=[]
   for j in range(i+1,len(x)+1):
    if sum(a for a,b in x[i:j])<=width:choices.append(max(b for a,b in x[i:j])+shelf(j))
   return min(choices)
  return shelf(0)
 if pid==1109:
  n=args[1]
  if len(x)*n>100000:require(all(a==1 and b==n for a,b,c in x));return[sum(c for a,b,c in x)]*n
  return[sum(c for a,b,c in x if a<=i<=b)for i in range(1,n+1)]
 if pid==1111:return(vps(x)+1)//2
 raise ValueError('unregistered exact-identity reference')

def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b

def matches(pid,args,value,want):
 if pid==1002:return type(value)is list and all(type(v)is str and len(v)==1 for v in value)and Counter(value)==Counter(want)
 if pid==1030:
  if type(value)is not list or any(type(p)is not list or len(p)!=2 or any(type(v)is not int for v in p)for p in value):return False
  if Counter(map(tuple,value))!=Counter(map(tuple,want)):return False
  distances=[abs(a-args[2])+abs(b-args[3])for a,b in value];return distances==sorted(distances)
 if pid==1042:return type(value)is list and len(value)==args[0]and all(type(v)is int and 1<=v<=4 for v in value)and all(value[a-1]!=value[b-1]for a,b in args[1])
 if pid==1093:return type(value)is list and len(value)==5 and all(type(a)in(int,float)and math.isfinite(a)and abs(a-b)<=1e-5 for a,b in zip(value,want))
 if pid==1111:
  if type(value)is not list or len(value)!=len(args[0])or any(type(v)is not int or v not in(0,1)for v in value):return False
  depths=[vps(''.join(ch for ch,v in zip(args[0],value)if v==side))for side in(0,1)];return None not in depths and max(depths)==want
 return exact(value,want)

def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind=list if pid in(1042,1111)else type(want);types={'python':{list:'list',int:'int',bool:'bool',str:'str'},'javascript':{list:'object',int:'number',bool:'boolean',str:'string'}}
 if record.get('result_type')!=types[language][kind]:return False,'result_type'
 if not matches(pid,args,record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if record.get('alias_edges')!=[]:return False,'mutable_return_alias'
 return True,None
