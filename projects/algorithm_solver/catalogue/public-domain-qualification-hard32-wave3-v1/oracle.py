"""Independent finite public-domain oracles; no candidate imports or execution."""
from itertools import product
from heapq import heappush,heappop
IDS=(2132,2267,2290,2426,2565,2569,2573,2663)
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(x,a,b,lo=1,hi=100000):return type(x)is list and lo<=len(x)<=hi and all(integer(v,a,b)for v in x)
def word(x):return type(x)is str and 1<=len(x)<=100000 and all('a'<=v<='z'for v in x)
def matrix(x,a,b,maxcells):
 return type(x)is list and 1<=len(x)<=100000 and type(x[0])is list and 1<=len(x[0])<=100000 and len(x)*len(x[0])<=maxcells and all(type(r)is list and len(r)==len(x[0])and all(integer(v,a,b)for v in r)for r in x)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered args required')
 ok=False
 if pid==2132:ok=len(args)==3 and matrix(args[0],0,1,200000)and all(integer(x,1,100000)for x in args[1:])
 elif pid==2267:
  if len(args)==1:
   x=args[0];ok=type(x)is list and 1<=len(x)<=100 and type(x[0])is list and 1<=len(x[0])<=100 and all(type(r)is list and len(r)==len(x[0])and all(type(v)is str and v in('(',')')for v in r)for r in x)
 elif pid==2290:ok=len(args)==1 and matrix(args[0],0,1,100000)and len(args[0])*len(args[0][0])>=2 and args[0][0][0]==args[0][-1][-1]==0
 elif pid==2426:ok=len(args)==3 and ints(args[0],-10000,10000,2)and ints(args[1],-10000,10000,2)and len(args[0])==len(args[1])and integer(args[2],-10000,10000)
 elif pid==2565:ok=len(args)==2 and all(word(x)for x in args)
 elif pid==2569:
  if len(args)==3:
   a,b,qs=args;ok=ints(a,0,1)and ints(b,0,10**9)and len(a)==len(b)and type(qs)is list and 1<=len(qs)<=100000
   if ok:
    for q in qs:
     if type(q)is not list or len(q)!=3 or not integer(q[0],1,3):ok=False;break
     if q[0]==1:valid=integer(q[1],0,len(a)-1)and integer(q[2],q[1],len(a)-1)
     elif q[0]==2:valid=integer(q[1],0,10**6)and type(q[2])is int and q[2]==0
     else:valid=all(type(v)is int and v==0 for v in q[1:])
     if not valid:ok=False;break
 elif pid==2573:
  if len(args)==1:
   x=args[0];ok=matrix(x,0,1000,1000000)and len(x)<=1000 and len(x)==len(x[0])and all(v<=len(x)for r in x for v in r)
 elif pid==2663:ok=len(args)==2 and word(args[0])and integer(args[1],4,26)and all(ord(x)<97+args[1]for x in args[0])and beautiful(args[0])
 if not ok:raise ValueError('outside official domain')
def beautiful(s):return all(s[i]!=s[i-1]and(i<2 or s[i]!=s[i-2])for i in range(1,len(s)))
def lcp_matrix(s):
 n=len(s);out=[[0]*n for _ in s]
 for i in range(n):
  for j in range(n):
   k=0
   while i+k<n and j+k<n and s[i+k]==s[j+k]:k+=1
   out[i][j]=k
 return out
def expected(pid,args):
 validate(pid,args);a=args[0]
 if pid==2132:
  m,n=len(a),len(a[0]);h,w=args[1:];covered=set()
  if m*n>400:
   if all(v==1 for row in a for v in row):return True
   if all(v==0 for row in a for v in row):return h<=m and w<=n
   raise ValueError('bounded placement oracle')
  for i in range(m-h+1):
   for j in range(n-w+1):
    cells=[(r,c)for r in range(i,i+h)for c in range(j,j+w)]
    if all(a[r][c]==0 for r,c in cells):covered.update(cells)
  return all(v or(r,c)in covered for r,row in enumerate(a)for c,v in enumerate(row))
 if pid==2267:
  m,n=len(a),len(a[0]);front={(0,0,0)}
  # Explicit reachable path states, tracking exact balance and rejecting negative prefixes.
  while front:
   nxt=set()
   for i,j,b in front:
    b+=1 if a[i][j]=='('else-1
    if b<0:continue
    if i==m-1 and j==n-1 and b==0:return True
    if i+1<m:nxt.add((i+1,j,b))
    if j+1<n:nxt.add((i,j+1,b))
   front=nxt
  return False
 if pid==2290:
  m,n=len(a),len(a[0]);d={(0,0):0};q=[(0,0,0)]
  while q:
   cost,i,j=heappop(q)
   if d[i,j]!=cost:continue
   if(i,j)==(m-1,n-1):return cost
   for r,c in((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
    if 0<=r<m and 0<=c<n and cost+a[r][c]<d.get((r,c),10**9):d[r,c]=cost+a[r][c];heappush(q,(d[r,c],r,c))
 if pid==2426:
  b,d=args[1:]
  if len(a)>500:
   if len(set(a))==len(set(b))==1:return len(a)*(len(a)-1)//2 if d>=0 else 0
   raise ValueError('bounded pair enumeration')
  return sum(a[i]-a[j]<=b[i]-b[j]+d for i in range(len(a))for j in range(i+1,len(a)))
 if pid==2565:
  t=args[1]
  if max(len(a),len(t))>100:
   if a==t:return 0
   if not set(a)&set(t):return len(t)
   raise ValueError('bounded removal enumeration')
  def subseq(s):
   it=iter(a);return all(any(x==c for x in it)for c in s)
  return min(j-i for i in range(len(t)+1)for j in range(i,len(t)+1)if subseq(t[:i]+t[j:]))
 if pid==2569:
  bits=a[:];values=args[1][:];out=[]
  if len(bits)*len(args[2])>2000000:
   # Independently evaluate no-flip case by exact linear superposition, not tree state.
   if any(q[0]==1 for q in args[2]):raise ValueError('bounded explicit updates')
   total=sum(values);ones=sum(bits)
   for op,x,y in args[2]:
    if op==2:total+=ones*x
    else:out.append(total)
   return out
  for op,x,y in args[2]:
   if op==1:
    for i in range(x,y+1):bits[i]=1-bits[i]
   elif op==2:
    for i in range(len(bits)):values[i]+=bits[i]*x
   else:out.append(sum(values))
  return out
 if pid==2573:
  n=len(a)
  if n>8:
   if all(a[i][j]==n-max(i,j)for i in range(n)for j in range(n)):return'a'*n
   if all(a[i][j]==(n-i if i==j else 0)for i in range(n)for j in range(n)):return ''.join(chr(97+i)for i in range(n))if n<=26 else''
   raise ValueError('bounded equality-partition enumeration')
  def strings(prefix,maxchar):
   if len(prefix)==n:yield prefix;return
   for c in range(min(25,maxchar+1)+1):yield from strings(prefix+chr(97+c),max(maxchar,c))
  for s in strings('',-1):
   if lcp_matrix(s)==a:return s
  return''
 if pid==2663:
  k=args[1]
  if len(a)>8:raise ValueError('bounded lexicographic enumeration')
  # Enumerate suffixes in order, pruning forbidden equalities, independent of greedy pivot repair.
  def walk(s):
   if len(s)==len(a):return s if s>a else None
   for c in map(chr,range(97,97+k)):
    t=s+c
    if t<a[:len(t)]or(c in s[-2:]):continue
    found=walk(t)
    if found is not None:return found
  return walk('')or''
 raise ValueError('unsupported')
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def integer_markers(x):
 if type(x)is list:return[integer_markers(v)for v in x]
 if type(x)is dict:
  if set(x)=={'__gamma_bigint_v1__'}and type(x['__gamma_bigint_v1__'])is str:
   s=x['__gamma_bigint_v1__'];v=int(s)
   if str(v)!=s:raise ValueError('noncanonical integer marker')
   return v
  raise ValueError('unexpected output object')
 if type(x)is int and abs(x)>9007199254740991:raise ValueError('unsafe untagged JS integer')
 return x
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind='bool'if pid in(2132,2267)else'list'if pid==2569 else'str'if pid in(2573,2663)else'int'
 types={'python':{'bool':'bool','list':'list','str':'str','int':'int'},'javascript':{'bool':'boolean','list':'object','str':'string','int':'number'}}
 result=record.get('result')
 if pid==2569 and language=='javascript':
  try:result=integer_markers(result)
  except(ValueError,TypeError):return False,'integer_encoding'
 if record.get('result_type')!=types[language][kind]or not exact(result,want):return False,'typed_result'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
