"""Definition-derived host references. Never imports a candidate program."""
from collections import Counter,defaultdict,deque
from fractions import Fraction
from functools import lru_cache
from itertools import combinations,permutations,product
from bisect import bisect_left
import heapq,math
MOD=1000000007
IDS=(853,856,858,866,869,870,874,877,878,881,885,886,888,890,891,892,893,898,905,907,909,910,915,916,918,921,923,926,930,931,935,937,939,940,945,947,948,949,950,954,957,961,962,966,967,970,973,974,978,983)
ARITY={853:3,858:2,870:2,874:2,878:3,881:2,885:4,886:2,888:2,890:2,909:1,910:2,916:2,923:2,930:2,948:2,957:2,966:2,967:2,970:3,973:2,974:2,983:2}

def integer(x,low,high):return type(x)is int and low<=x<=high

def array(x,low,high,lo=1,hi=100000):return type(x)is list and lo<=len(x)<=hi and all(integer(v,low,high)for v in x)

def text(x,alphabet,lo=1,hi=100000):return type(x)is str and lo<=len(x)<=hi and set(x)<=set(alphabet)

def matrix(x,low,high,lo=1,hi=100):return type(x)is list and lo<=len(x)<=hi and all(array(r,low,high,len(x),len(x))for r in x)

def validate(pid,args):
 if pid not in IDS or type(args)is not list or len(args)!=ARITY.get(pid,1):raise ValueError('invalid identity or ordered positional ABI')
 x=args[0];good=False;lower='abcdefghijklmnopqrstuvwxyz';letters=lower+lower.upper()
 if pid==853:good=integer(x,1,10**6)and array(args[1],0,x-1,1,100000)and len(set(args[1]))==len(args[1])and array(args[2],1,10**6,len(args[1]),len(args[1]))
 elif pid==856:
  good=text(x,'()',2,50);balance=0
  if good:
   for c in x:
    balance+=1 if c=='('else-1
    if balance<0:good=False
   good=good and balance==0
 elif pid==858:good=integer(x,1,1000)and integer(args[1],1,x)
 elif pid==866:good=integer(x,1,10**8)
 elif pid==869:good=integer(x,1,10**9)
 elif pid==870:good=array(x,0,10**9,1,100000)and array(args[1],0,10**9,len(x),len(x))
 elif pid==874:
  good=array(x,-2,9,1,10000)and all(v not in(0,)for v in x)and type(args[1])is list and len(args[1])<=10000 and all(array(p,-30000,30000,2,2)for p in args[1])
 elif pid==877:good=array(x,1,500,2,500)and len(x)%2==0 and sum(x)%2==1
 elif pid==878:good=integer(x,1,10**9)and all(integer(v,2,40000)for v in args[1:])
 elif pid==881:good=integer(args[1],1,30000)and array(x,1,args[1],1,50000)
 elif pid==885:good=integer(x,1,100)and integer(args[1],1,100)and integer(args[2],0,x-1)and integer(args[3],0,args[1]-1)
 elif pid==886:good=integer(x,1,2000)and type(args[1])is list and len(args[1])<=10000 and all(array(e,1,x,2,2)and e[0]<e[1]for e in args[1])and len(set(map(tuple,args[1])))==len(args[1])
 elif pid==888:
  good=array(x,1,100000,1,10000)and array(args[1],1,100000,1,10000)and sum(x)!=sum(args[1])
  if good:
   delta=sum(x)-sum(args[1]);other=set(args[1]);good=delta%2==0 and any(a-delta//2 in other for a in x)
 elif pid==890:good=text(args[1],lower,1,20)and type(x)is list and 1<=len(x)<=50 and all(text(w,lower,len(args[1]),len(args[1]))for w in x)
 elif pid==891:good=array(x,1,100000,1,100000)
 elif pid==892:good=matrix(x,0,50,1,50)
 elif pid==893:good=type(x)is list and 1<=len(x)<=1000 and text(x[0],lower,1,20)and all(text(w,lower,len(x[0]),len(x[0]))for w in x)
 elif pid==898:good=array(x,0,10**9,1,50000)
 elif pid==905:good=array(x,0,5000,1,5000)
 elif pid==907:good=array(x,1,30000,1,30000)
 elif pid==909:good=matrix(x,-1,len(x)**2,2,20)and all(v==-1 or v>=1 for row in x for v in row)and x[-1][0]==-1 and (x[0][-1]if len(x)%2 else x[0][0])==-1
 elif pid==910:good=array(x,0,10000,1,10000)and integer(args[1],0,10000)
 elif pid==915:
  good=array(x,0,10**6,2,100000)
  if good:
   right=[0]*len(x);right[-1]=x[-1]
   for i in range(len(x)-2,-1,-1):right[i]=min(x[i],right[i+1])
   largest=x[0];found=False
   for i in range(len(x)-1):largest=max(largest,x[i]);found=found or largest<=right[i+1]
   good=found
 elif pid==916:good=all(type(v)is list and 1<=len(v)<=10000 and all(text(w,lower,1,10)for w in v)for v in args)and len(set(x))==len(x)
 elif pid==918:good=array(x,-30000,30000,1,30000)
 elif pid==921:good=text(x,'()',1,1000)
 elif pid==923:good=array(x,0,100,3,3000)and integer(args[1],0,300)
 elif pid==926:good=text(x,'01',1,100000)
 elif pid==930:good=array(x,0,1,1,30000)and integer(args[1],0,len(x))
 elif pid==931:good=matrix(x,-100,100,1,100)
 elif pid==935:good=integer(x,1,5000)
 elif pid==937:
  good=type(x)is list and 1<=len(x)<=100
  if good:
   for log in x:
    if type(log)is not str or not 3<=len(log)<=100 or '  'in log or log!=log.strip()or len(log.split(' '))<2:good=False;break
    ident,*content=log.split(' ')
    if not text(ident,letters+'0123456789',1,100)or not(all(text(w,lower,1,100)for w in content)or all(text(w,'0123456789',1,100)for w in content)):good=False;break
 elif pid in(939,947):good=type(x)is list and 1<=len(x)<=(500 if pid==939 else 1000)and all(array(p,0,40000 if pid==939 else 10000,2,2)for p in x)and len(set(map(tuple,x)))==len(x)
 elif pid==940:good=text(x,lower,1,2000)
 elif pid==945:
  good=array(x,0,100000,1,100000)
  if good:
   cursor=-1;cost=0
   for v in sorted(x):cursor=max(cursor+1,v);cost+=cursor-v
   good=cost<=2**31-1
 elif pid==948:good=array(x,0,9999,0,1000)and integer(args[1],0,9999)
 elif pid==949:good=array(x,0,9,4,4)
 elif pid==950:good=array(x,1,10**6,1,1000)and len(set(x))==len(x)
 elif pid==954:good=array(x,-100000,100000,2,30000)and len(x)%2==0
 elif pid==957:good=array(x,0,1,8,8)and integer(args[1],1,10**9)
 elif pid==961:
  good=array(x,0,10000,4,10000)and len(x)%2==0
  if good:
   counts=Counter(x);n=len(x)//2;good=len(counts)==n+1 and sum(v==n for v in counts.values())==1 and all(v in(1,n)for v in counts.values())
 elif pid==962:good=array(x,0,50000,2,50000)
 elif pid==966:good=all(type(v)is list and 1<=len(v)<=5000 and all(text(w,letters,1,7)for w in v)for v in args)
 elif pid==967:good=integer(x,2,9)and integer(args[1],0,9)
 elif pid==970:good=integer(x,1,100)and integer(args[1],1,100)and integer(args[2],0,10**6)
 elif pid==973:
  good=type(x)is list and 1<=len(x)<=10000 and all(array(p,-10000,10000,2,2)for p in x)and integer(args[1],1,len(x))
  if good:
   distances=sorted(p[0]*p[0]+p[1]*p[1]for p in x);k=args[1]
   if k<len(x)and distances[k-1]==distances[k]:good=len({tuple(p)for p in x if p[0]*p[0]+p[1]*p[1]==distances[k-1]})==1
 elif pid==974:good=array(x,-10000,10000,1,30000)and integer(args[1],2,10000)
 elif pid==978:good=array(x,0,10**9,1,40000)
 elif pid==983:good=array(x,1,365,1,365)and x==sorted(set(x))and array(args[1],1,1000,3,3)
 if good and pid==874:good=expected(pid,args)<2**31
 if not good:raise ValueError('outside pinned public domain')

def partition(xs):
 # Exhaustive splits for small cases; scalar scans for analytic large shapes.
 if len(xs)>1000:
  if all(v==xs[0]for v in xs):return 1
  if all(a<=b for a,b in zip(xs,xs[1:])):return 1
  if xs[0]==10**6 and xs[-1]==10**6 and all(v==0 for v in xs[1:-1]):return len(xs)-1
  raise ValueError('large partition reference unsupported')
 return next((i for i in range(1,len(xs))if max(xs[:i])<=min(xs[i:])),None)

def subsets(xs):
 for mask in range(1,1<<len(xs)):yield [v for i,v in enumerate(xs)if mask>>i&1]

def prime(n):
 return n>=2 and all(n%d for d in range(2,math.isqrt(n)+1))

def prime_palindrome(n):
 for length in range(len(str(n)),10):
  half=(length+1)//2;start=max(10**(half-1),int(str(n)[:half])if length==len(str(n))else 1)
  for prefix in range(start,10**half):
   s=str(prefix);v=int(s+s[-2::-1]if length%2 else s+s[::-1])
   if v>=n and prime(v):return v
 raise ValueError('oracle domain exhausted')

def spiral_rank(r,c):
 k=max(abs(r),abs(c))
 if not k:return 0
 start=(2*k-1)**2
 if c==k and r>-k:return start+r+k-1
 if r==k:return start+2*k+k-1-c
 if c==-k:return start+4*k+k-1-r
 return start+6*k+c+k-1

def bipartite(n,edges):
 parent=list(range(2*n));size=[1]*(2*n)
 def find(x):
  while parent[x]!=x:x=parent[x]
  return x
 def union(a,b):
  a,b=find(a),find(b)
  if a==b:return
  if size[a]<size[b]:a,b=b,a
  parent[b]=a;size[a]+=size[b]
 for a,b in edges:union(a-1,b-1+n);union(a-1+n,b-1)
 return all(find(i)!=find(i+n)for i in range(n))

def knight_count(n):
 coords={i+1:(i//3,i%3)for i in range(9)};coords[0]=(3,1)
 a=[[int(sorted((abs(coords[i][0]-coords[j][0]),abs(coords[i][1]-coords[j][1])))==[1,2])for j in range(10)]for i in range(10)]
 def multiply(x,y):return [[sum(x[i][k]*y[k][j]for k in range(10))%MOD for j in range(10)]for i in range(10)]
 result=[[int(i==j)for j in range(10)]for i in range(10)];power=n-1
 while power:
  if power&1:result=multiply(result,a)
  a=multiply(a,a);power//=2
 return sum(map(sum,result))%MOD

@lru_cache(None)
def prison_maps():
 maps=[tuple((~((s<<1)^(s>>1)))&0x7e for s in range(256))]
 for _ in range(30):maps.append(tuple(maps[-1][maps[-1][s]]for s in range(256)))
 return tuple(maps)

def expected(pid,args):
 x=args[0]
 if pid==853:
  target,positions,speeds=args
  if len(positions)>16:
   if len(set(speeds))==1:return len(positions)
   times={Fraction(target-p,s)for p,s in zip(positions,speeds)};assert len(times)==1;return 1
  times=[Fraction(target-p,s)for p,s in sorted(zip(positions,speeds))];n=len(times);best=n
  for mask in range(1<<(n-1)):
   count,start,valid=0,0,True
   for end in range(n):
    if end==n-1 or mask>>end&1:
     if max(times[start:end+1])>times[end]:valid=False;break
     count+=1;start=end+1
   if valid:best=min(best,count)
  return best
 if pid==856:
  depth,total=0,0
  for i,c in enumerate(x):
   depth+=1 if c=='('else-1
   if c==')'and x[i-1]=='(':total+=2**depth
  return total
 if pid==858:
  for k in range(1,x+1):
   height=k*args[1]
   if height%x==0:return 1 if k%2 and height//x%2 else 0 if k%2 else 2
 if pid==866:return prime_palindrome(x)
 if pid==869:return any(Counter(str(x))==Counter(str(2**k))for k in range(30))
 if pid==870:
  # Hall deficiency for nested neighborhoods b>=threshold.
  n=len(x);return n-max([0]+[sum(v>=t for v in args[1])-sum(v>t for v in x)for t in set(args[1])])
 if pid==874:
  position=0j;heading=1j;best=0
  for cmd in x:
   if cmd==-2:heading*=1j
   elif cmd==-1:heading*=-1j
   else:
    distances=[]
    for bx,by in args[1]:
     relative=(complex(bx,by)-position)/heading
     if relative.imag==0 and 0<relative.real<=cmd:distances.append(int(relative.real)-1)
    position+=heading*min([cmd]+distances);best=max(best,int(position.real**2+position.imag**2))
  return best
 if pid==877:return True
 if pid==878:
  n,a,b=args;l=math.lcm(a,b);period=sorted(set(range(a,l+1,a))|set(range(b,l+1,b)));q,r=divmod(n-1,len(period));return(q*l+period[r])%MOD
 if pid==881:
  if len(x)>16 and len(set(x))==1:return (len(x)+1)//2 if 2*x[0]<=args[1]else len(x)
  @lru_cache(None)
  def boats(mask):
   if not mask:return 0
   i=(mask&-mask).bit_length()-1;rest=mask^(1<<i)
   return 1+min([boats(rest)]+[boats(rest^(1<<j))for j in range(len(x))if rest>>j&1 and x[i]+x[j]<=args[1]])
  return boats((1<<len(x))-1)
 if pid==885:return sorted(([r,c]for r in range(x)for c in range(args[1])),key=lambda rc:spiral_rank(rc[0]-args[2],rc[1]-args[3]))
 if pid==886:return bipartite(x,args[1])
 if pid==888:return sorted([a,b]for a in set(x)for b in set(args[1])if 2*(a-b)==sum(x)-sum(args[1]))
 if pid==890:
  signature=lambda s:tuple(s.index(c)for c in s)
  return [w for w in x if signature(w)==signature(args[1])]
 if pid==891:
  if len(x)>20:
   counts=Counter(x)
   if len(counts)==1:return 0
   assert len(counts)==2
   lo,hi=sorted(counts);return(hi-lo)*(pow(2,counts[lo],MOD)-1)*(pow(2,counts[hi],MOD)-1)%MOD
  return sum(max(s)-min(s)for s in subsets(x))%MOD
 if pid==892:
  cubes={(r,c,z)for r,row in enumerate(x)for c,h in enumerate(row)for z in range(h)};directions=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
  return sum((r+dr,c+dc,z+dz)not in cubes for r,c,z in cubes for dr,dc,dz in directions)
 if pid==893:return len({tuple(Counter(w[parity::2])[chr(97+i)]for parity in range(2)for i in range(26))for w in x})
 if pid==898:
  if len(set(x))==1:return 1
  values=set()
  for i in range(len(x)):
   v=0
   for j in range(i,len(x)):v|=x[j];values.add(v)
  return len(values)
 if pid==905:return Counter(x)
 if pid==907:
  n=len(x)
  if len(set(x))==1:return x[0]*n*(n+1)//2%MOD
  if x==list(range(1,n+1))or x==list(range(n,0,-1)):return n*(n+1)*(n+2)//6%MOD
  return sum(min(x[i:j])for i in range(n)for j in range(i+1,n+1))%MOD
 if pid==909:
  n=len(x);goal=n*n;edges={}
  def cell(v):
   band,c=divmod(v-1,n);return n-1-band,c if band%2==0 else n-1-c
  for v in range(1,goal+1):
   edges[v]=set()
   for nxt in range(v+1,min(v+6,goal)+1):
    r,c=cell(nxt);edges[v].add(nxt if x[r][c]==-1 else x[r][c])
  reached={1};front={1};turn=0
  while front:
   if goal in front:return turn
   front=set().union(*(edges[v]for v in front))-reached;reached|=front;turn+=1
  return -1
 if pid==910:
  if len(set(x))==1:return 0
  return min(max(v)-min(v)for signs in product((-1,1),repeat=len(x))for v in [[n+sign*args[1]for n,sign in zip(x,signs)]])
 if pid==915:return partition(x)
 if pid==916:return [w for w in x if all(not(Counter(b)-Counter(w))for b in args[1])]
 if pid==918:
  if len(set(x))==1:return max(x[0],sum(x))
  return max(sum((x+x)[i:i+k])for i in range(len(x))for k in range(1,len(x)+1))
 if pid==921:
  while '()'in x:x=x.replace('()','')
  return len(x)
 if pid==923:
  if len(set(x))==1:return(math.comb(len(x),3)if 3*x[0]==args[1]else 0)%MOD
  return sum(sum(p)==args[1]for p in combinations(x,3))%MOD
 if pid==926:
  if len(x)>1000:
   if len(set(x))==1:return 0
   if x=='10'*(len(x)//2):return len(x)//2
   if x=='01'*(len(x)//2):return len(x)//2-1
   raise ValueError('large reference shape unsupported')
  return min(x[:i].count('1')+x[i:].count('0')for i in range(len(x)+1))
 if pid==930:
  if len(set(x))==1:
   if x[0]==0:return len(x)*(len(x)+1)//2 if args[1]==0 else 0
   return len(x)-args[1]+1 if 1<=args[1]<=len(x)else 0
  return sum(sum(x[i:j])==args[1]for i in range(len(x))for j in range(i+1,len(x)+1))
 if pid==931:
  if len(x)>8:
   values={v for row in x for v in row}
   if len(values)==1:return len(x)*x[0][0]
   assert all(v==(0 if r==c else 100)for r,row in enumerate(x)for c,v in enumerate(row));return 0
  @lru_cache(None)
  def paths(r,c):return x[r][c]if r==len(x)-1 else x[r][c]+min(paths(r+1,nc)for nc in range(max(0,c-1),min(len(x),c+2)))
  return min(paths(0,c)for c in range(len(x)))
 if pid==935:return knight_count(x)
 if pid==937:
  letters=[v for v in x if v.split(' ',1)[1][0].isalpha()];digits=[v for v in x if v not in letters]
  return sorted(letters,key=lambda s:(s.split(' ',1)[1],s.split(' ',1)[0]))+digits
 if pid==939:
  columns=defaultdict(set)
  for a,b in x:columns[a].add(b)
  areas=[]
  for a,b in combinations(columns,2):
   ys=sorted(columns[a]&columns[b]);areas += [abs(b-a)*(d-c)for c,d in zip(ys,ys[1:])]
  return min(areas,default=0)
 if pid==940:
  if len(set(x))==1:return len(x)
  if len(x)>20:
   assert x=='ab'*(len(x)//2);a,b=0,1
   for _ in range(len(x)+3):a,b=b,(a+b)%MOD
   return(a-2)%MOD
  return len({''.join(s)for s in subsets(x)})%MOD
 if pid==945:
  if len(x)>10:
   if len(set(x))==1:answer=len(x)*(len(x)-1)//2
   elif len(set(x))==len(x):answer=0
   else:
    assert x[:40000]==[0]*40000 and x[40000:]==list(range(40000,100000));answer=40000*39999//2
  else:
   original=sorted(x);answer=min(sum(slots)-sum(x)for slots in combinations(range(max(x)+len(x)),len(x))if all(a<=b for a,b in zip(original,slots)))
  assert answer<=2**31-1
  return answer
 if pid==947:
  remaining=set(map(tuple,x));components=0
  while remaining:
   components+=1;todo=[remaining.pop()]
   while todo:
    a,b=todo.pop();neighbors={p for p in remaining if p[0]==a or p[1]==b};remaining-=neighbors;todo.extend(neighbors)
  return len(x)-components
 if pid==948:
  if len(x)>10:
   assert len(set(x))==1
   return len(x)if x[0]==0 else min(len(x),args[1]//x[0])
  @lru_cache(None)
  def score(mask,power,points):
   best=points
   for i,v in enumerate(x):
    if not mask>>i&1:continue
    if power>=v:best=max(best,score(mask^(1<<i),power-v,points+1))
    if points:best=max(best,score(mask^(1<<i),power+v,points-1))
   return best
  return score((1<<len(x))-1,args[1],0)
 if pid==949:
  valid=[f'{h:02d}:{m:02d}'for h in range(24)for m in range(60)if Counter(f'{h:02d}{m:02d}')==Counter(map(str,x))]
  return max(valid,default='')
 if pid==950:
  q=deque()
  for v in sorted(x,reverse=True):
   if q:q.rotate(1)
   q.appendleft(v)
  return list(q)
 if pid==954:
  if len(x)>12:
   c=Counter(x)
   if set(c)=={0}:return True
   if set(c)=={1}:return False
   assert set(c)=={-1,-2};return c[-1]==c[-2]
  @lru_cache(None)
  def pairs(values):
   if not values:return True
   return any((values[0]==2*v or v==2*values[0])and pairs(values[1:i]+values[i+1:])for i,v in enumerate(values)if i)
  return pairs(tuple(x))
 if pid==957:
  state=sum(v<<i for i,v in enumerate(x));days=args[1];i=0
  while days:
   if days&1:state=prison_maps()[i][state]
   days//=2;i+=1
  return [(state>>i)&1 for i in range(8)]
 if pid==961:return max(Counter(x),key=Counter(x).get)
 if pid==962:
  if len(x)>1000:
   if x==sorted(x):return len(x)-1
   assert x==list(range(50000,0,-1));return 0
  return max([0]+[j-i for i in range(len(x))for j in range(i+1,len(x))if x[i]<=x[j]])
 if pid==966:
  out=[]
  def alike(a,b):return all(l==r or(l in'aeiou'and r in'aeiou')for l,r in zip(a.lower(),b.lower()))and len(a)==len(b)
  for q in args[1]:
   if q in x:out.append(q);continue
   lower=next((w for w in x if w.lower()==q.lower()),None)
   out.append(lower if lower is not None else next((w for w in x if alike(w,q)),''))
  return out
 if pid==967:
  counts=[0]+[1]*9
  for _ in range(x-1):counts=[sum(counts[d]for d in range(10)if abs(d-e)==args[1])for e in range(10)]
  return sum(counts)
 if pid==970:
  xs={x**i for i in range(21)if x**i<=args[2]};ys={args[1]**i for i in range(21)if args[1]**i<=args[2]}
  return sorted({a+b for a,b in product(xs,ys)if a+b<=args[2]})
 if pid==973:return sorted((p for p in x),key=lambda p:p[0]*p[0]+p[1]*p[1])[:args[1]]
 if pid==974:
  if len(set(x))==1:
   period=args[1]//math.gcd(abs(x[0]),args[1]);return sum(len(x)-m*period+1 for m in range(1,len(x)//period+1))
  return sum(sum(x[i:j])%args[1]==0 for i in range(len(x))for j in range(i+1,len(x)+1))
 if pid==978:
  if len(x)>1000:
   if len(set(x))==1:return 1
   if all((a<b) !=(b<c)and a!=b and b!=c for a,b,c in zip(x,x[1:],x[2:])):return len(x)
   assert x==sorted(x)and len(set(x))==len(x);return 2
  return max(j-i for i in range(len(x))for j in range(i+1,len(x)+1)if all(a!=b for a,b in zip(x[i:j],x[i+1:j]))and all((a<b)!=(b<c)for a,b,c in zip(x[i:j],x[i+1:j],x[i+2:j])))
 if pid==983:
  dist=[10**12]*(len(x)+1);dist[0]=0;heap=[(0,0)]
  while heap:
   cost,i=heapq.heappop(heap)
   if i==len(x):return cost
   if cost!=dist[i]:continue
   for duration,price in zip((1,7,30),args[1]):
    j=bisect_left(x,x[i]+duration)
    if cost+price<dist[j]:dist[j]=cost+price;heapq.heappush(heap,(cost+price,j))
 raise ValueError('unregistered independent oracle')

def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b

def matches(pid,args,value,want):
 if pid==870:return type(value)is list and all(type(v)is int for v in value)and Counter(value)==Counter(args[0])and sum(a>b for a,b in zip(value,args[1]))==want
 if pid==888:return type(value)is list and len(value)==2 and all(type(v)is int for v in value)and value in want
 if pid in(890,916):return type(value)is list and all(type(v)is str for v in value)and Counter(value)==Counter(want)
 if pid==905:
  if type(value)is not list or not all(type(v)is int for v in value)or Counter(value)!=want:return False
  seen_odd=False
  for v in value:
   if v%2:seen_odd=True
   elif seen_odd:return False
  return True
 if pid==967:return type(value)is list and len(value)==want and len(set(value))==len(value)and all(type(v)is int and len(str(v))==args[0]and v>=10**(args[0]-1)and all(abs(int(a)-int(b))==args[1]for a,b in zip(str(v),str(v)[1:]))for v in value)
 if pid==970:return type(value)is list and all(type(v)is int for v in value)and sorted(value)==want
 if pid==973:return type(value)is list and all(type(p)is list and len(p)==2 and all(type(v)is int for v in p)for p in value)and Counter(map(tuple,value))==Counter(map(tuple,want))
 return exact(value,want)

def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind=list if pid in(870,888,905,967)else type(want)
 types={'python':{list:'list',int:'int',bool:'bool',str:'str'},'javascript':{list:'object',int:'number',bool:'boolean',str:'string'}}
 if record.get('result_type')!=types[language][kind]:return False,'result_type'
 if not matches(pid,args,record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if record.get('alias_edges')!=[]:return False,'mutable_return_alias'
 return True,None
