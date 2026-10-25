"""Prospective Hard10 independent finite oracles; candidates never imported."""
from functools import lru_cache
from itertools import product
IDS=(10,42,84,85,123,546,564,992,1074,1187)
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(x,a,b,n,m):return type(x)is list and n<=len(x)<=m and all(integer(v,a,b)for v in x)
def matrix(x,limit,cell):return type(x)is list and 1<=len(x)<=limit and type(x[0])is list and 1<=len(x[0])<=limit and all(type(r)is list and len(r)==len(x[0])and all(cell(v)for v in r)for r in x)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered arguments')
 okay=False
 if pid==10 and len(args)==2:
  s,p=args;okay=type(s)is str and 1<=len(s)<=20 and all('a'<=c<='z'for c in s)and type(p)is str and 1<=len(p)<=20 and all('a'<=c<='z'or c in'.*'for c in p)and all(i>0 and p[i-1]!='*'for i,c in enumerate(p)if c=='*')
 elif pid in(42,84,123,546)and len(args)==1:
  limits={42:(0,100000,20000),84:(0,10000,100000),123:(0,100000,100000),546:(1,100,100)};lo,hi,n=limits[pid];okay=ints(args[0],lo,hi,1,n)
 elif pid==85 and len(args)==1:okay=matrix(args[0],200,lambda v:type(v)is str and v in('0','1'))
 elif pid==564 and len(args)==1:
  s=args[0];okay=type(s)is str and 1<=len(s)<=18 and all('0'<=c<='9'for c in s)and s[0]!='0'
 elif pid==992 and len(args)==2:
  xs,k=args;n=len(xs)if type(xs)is list else 0;okay=ints(xs,1,n,1,20000)and integer(k,1,n)
 elif pid==1074 and len(args)==2:okay=matrix(args[0],100,lambda v:integer(v,-1000,1000))and integer(args[1],-10**8,10**8)
 elif pid==1187 and len(args)==2:okay=all(ints(x,0,10**9,1,2000)for x in args)
 if not okay:raise ValueError('outside declared official domain')
def expected(pid,args):
 validate(pid,args)
 if pid==10:
  # NFA epsilon closure over pattern atoms, not candidate rolling DP rows.
  text,pattern=args;atoms=[];i=0
  while i<len(pattern):
   star=i+1<len(pattern)and pattern[i+1]=='*';atoms.append((pattern[i],star));i+=2 if star else 1
  def closure(states):
   states=set(states);todo=list(states)
   for j in todo:
    if j<len(atoms)and atoms[j][1]and j+1 not in states:states.add(j+1);todo.append(j+1)
   return states
  states=closure({0})
  for char in text:states=closure({j if star else j+1 for j in states if j<len(atoms)for atom,star in[atoms[j]]if atom=='.'or atom==char})
  return len(atoms)in states
 if pid==42:
  xs=args[0];left=[];high=0
  for x in xs:high=max(high,x);left.append(high)
  high=0;answer=0
  for i in range(len(xs)-1,-1,-1):high=max(high,xs[i]);answer+=min(left[i],high)-xs[i]
  return answer
 if pid==84:
  xs=args[0]
  if len(set(xs))==1:return len(xs)*xs[0]
  if len(xs)>200:raise ValueError('bounded interval enumeration oracle')
  return max((j-i)*min(xs[i:j])for i in range(len(xs))for j in range(i+1,len(xs)+1))
 if pid==85:
  m=args[0];r=len(m);c=len(m[0])
  if all(x=='1'for row in m for x in row):return r*c
  if all(x=='0'for row in m for x in row):return 0
  if r*c>100:raise ValueError('bounded rectangle enumeration oracle')
  return max([0]+[(b-a)*(d-c0)for a in range(r)for b in range(a+1,r+1)for c0 in range(c)for d in range(c0+1,c+1)if all(m[i][j]=='1'for i in range(a,b)for j in range(c0,d))])
 if pid==123:
  xs=args[0];n=len(xs)
  # Separate prefix/suffix single-transaction optima, not four-state machine.
  pre=[0]*n;low=xs[0]
  for i,x in enumerate(xs):low=min(low,x);pre[i]=max(pre[i-1]if i else 0,x-low)
  high=xs[-1];suffix=answer=0
  for i in range(n-1,-1,-1):high=max(high,xs[i]);suffix=max(suffix,high-xs[i]);answer=max(answer,suffix+(pre[i-1]if i else 0))
  return answer
 if pid==546:
  xs=args[0]
  if len(set(xs))==1:return len(xs)**2
  if len(set(xs))==len(xs):return len(xs)
  if len(xs)>10:raise ValueError('bounded removal-sequence oracle')
  @lru_cache(None)
  def remove(seq):
   best=0
   for i in range(len(seq)):
    for j in range(i+1,len(seq)+1):
     if any(x!=seq[i]for x in seq[i:j]):break
     best=max(best,(j-i)**2+remove(seq[:i]+seq[j:]))
   return best
  return remove(tuple(xs))
 if pid==564:
  n=int(args[0]);s=str(n)
  # Enumerate outward for small values. Large boundary families have exact
  # nearest-neighbor proofs, avoiding candidate half-prefix generation.
  if n<=10000:
   for distance in range(1,20000):
    for value in(n-distance,n+distance):
     if value>=0 and str(value)==str(value)[::-1]:return str(value)
  if set(s)=={'9'}:return str(n+2)
  if s[0]=='1'and set(s[1:])=={'0'}:return str(n-1)
  if s=='1'+'0'*(len(s)-2)+'1':return str(n-2)
  raise ValueError('bounded nearest-integer oracle')
 if pid==992:
  xs,k=args;n=len(xs)
  if len(set(xs))==1:return n*(n+1)//2 if k==1 else 0
  if len(set(xs))==n:return n-k+1
  if n>100:raise ValueError('bounded subarray enumeration oracle')
  return sum(len(set(xs[i:j]))==k for i in range(n)for j in range(i+1,n+1))
 if pid==1074:
  m,t=args;r=len(m);c=len(m[0])
  if all(x==0 for row in m for x in row):return r*(r+1)*c*(c+1)//4 if t==0 else 0
  if r*c>100:raise ValueError('bounded submatrix enumeration oracle')
  return sum(sum(m[i][j]for i in range(a,b)for j in range(c0,d))==t for a in range(r)for b in range(a+1,r+1)for c0 in range(c)for d in range(c0+1,c+1))
 a,b=args
 if all(x<y for x,y in zip(a,a[1:])):return 0
 if len(a)>8:
  if len(set(a))==len(set(b))==1:return -1 if len(a)>2 or a[0]==b[0]else 1
  if a==[0]*len(a)and sorted(set(b))==list(range(len(a))):return len(a)-1
  raise ValueError('bounded replacement product oracle')
 best=len(a)+1
 for values in product(*[set([x,*b])for x in a]):
  if all(x<y for x,y in zip(values,values[1:])):best=min(best,sum(x!=y for x,y in zip(values,a)))
 return best if best<=len(a)else -1

def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind='bool'if pid==10 else'str'if pid==564 else'int';types={'python':{'bool':'bool','str':'str','int':'int'},'javascript':{'bool':'boolean','str':'string','int':'number'}}
 if record.get('result_type')!=types[language][kind]:return False,'result_type'
 if not exact(record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
