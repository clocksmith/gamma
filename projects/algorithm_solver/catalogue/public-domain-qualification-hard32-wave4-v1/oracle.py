"""Independent public-domain finite oracles, authored before source inspection."""
from math import gcd
from itertools import product
from functools import lru_cache
IDS=(2709,2781,2953,3003,3041,3093,3130)
MOD=1000000007
FACT=[1]*2001
for i in range(1,len(FACT)):FACT[i]=FACT[i-1]*i%MOD
INV=[1]*2001;INV[-1]=pow(FACT[-1],MOD-2,MOD)
for i in range(2000,0,-1):INV[i-1]=INV[i]*i%MOD
def choose(n,r):return 0 if r<0 or n<r or n<0 else FACT[n]*INV[r]%MOD*INV[n-r]%MOD
def integer(x,a,b):return type(x)is int and a<=x<=b
def word(x,n=100000):return type(x)is str and 1<=len(x)<=n and all('a'<=c<='z'for c in x)
def ints(x,a,b):return type(x)is list and 1<=len(x)<=100000 and all(integer(v,a,b)for v in x)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered args required')
 ok=False
 if pid==2709:ok=len(args)==1 and ints(args[0],1,100000)
 elif pid==2781:ok=len(args)==2 and word(args[0])and type(args[1])is list and 1<=len(args[1])<=100000 and all(word(x,10)for x in args[1])
 elif pid==2953:ok=len(args)==2 and word(args[0])and integer(args[1],1,len(args[0]))
 elif pid==3003:ok=len(args)==2 and word(args[0],10000)and integer(args[1],1,26)
 elif pid==3041:ok=len(args)==1 and ints(args[0],1,1000000)
 elif pid==3093:ok=len(args)==2 and all(type(a)is list and 1<=len(a)<=10000 and all(word(s,5000)for s in a)and sum(map(len,a))<=500000 for a in args)
 elif pid==3130:ok=len(args)==3 and all(integer(x,1,1000)for x in args)
 if not ok:raise ValueError('outside reviewed official domain')
@lru_cache(None)
def compositions(n,r,limit):
 if r<1 or r>n or n>r*limit:return 0
 return sum((-1 if j%2 else 1)*choose(r,j)*choose(n-j*limit-1,r-1)for j in range(min(r,(n-r)//limit)+1))%MOD
@lru_cache(None)
def stable(z,o,limit):
 # Runs alternate: equal positive run counts have two starting bits;
 # counts differing by one have one starting bit. Inclusion-exclusion counts
 # bounded positive compositions independently of binary last-bit DP.
 total=0
 for r in range(1,max(z,o)+1):
  total+=2*compositions(z,r,limit)*compositions(o,r,limit)
  total+=compositions(z,r+1,limit)*compositions(o,r,limit)
  total+=compositions(z,r,limit)*compositions(o,r+1,limit)
 return total%MOD

def expected(pid,args):
 validate(pid,args);a=args[0]
 if pid==2709:
  if len(a)>500:
   if len(set(a))==1:return a[0]>1
   raise ValueError('bounded pairwise GCD connectivity')
  seen={0};todo=[0]
  while todo:
   i=todo.pop()
   for j,v in enumerate(a):
    if j not in seen and gcd(a[i],v)>1:seen.add(j);todo.append(j)
  return len(seen)==len(a)
 if pid==2781:
  forbidden=set(args[1]);n=len(a)
  if n>100:
   if len(set(a))!=1:raise ValueError('bounded substring enumeration')
   lengths=[len(s)for s in forbidden if set(s)=={a[0]}]
   return min(n,min(lengths)-1)if lengths else n
  return max(j-i for i in range(n+1)for j in range(i,n+1)if all(s not in a[i:j]for s in forbidden))
 if pid==2953:
  k=args[1];n=len(a)
  if len(set(a))==1:return n-k+1
  if n>100:raise ValueError('bounded interval enumeration')
  count=0
  for i in range(n):
   freq={}
   for j in range(i,n):
    if j>i and abs(ord(a[j])-ord(a[j-1]))>2:break
    freq[a[j]]=freq.get(a[j],0)+1
    count+=all(v==k for v in freq.values())
  return count
 if pid==3003:
  k=args[1];n=len(a)
  if k==26:return 1
  if n>40:
   if len(set(a))==1:return min(n,3)if k==1 else 1
   if k==1 and all(a[i]!=a[i-1]for i in range(1,n)):return n
   raise ValueError('bounded all-letter replacement enumeration')
  def partitions(s):
   start=0;count=0
   while start<len(s):
    end=start
    while end<len(s)and len(set(s[start:end+1]))<=k:end+=1
    count+=1;start=end
   return count
  return max(partitions(a[:i]+chr(c)+a[i+1:])for i in range(n)for c in range(97,123))
 if pid==3041:
  n=len(a)
  if n>12:
   if len(set(a))==1:return min(n,2)
   ordered=sorted(a)
   if all(ordered[i]==ordered[i-1]+1 for i in range(1,n)):return n
   if all(ordered[i]>=ordered[i-1]+3 for i in range(1,n)):return 1
   raise ValueError('bounded modification-mask enumeration')
  best=0
  for bits in product((0,1),repeat=n):
   values=set(x+b for x,b in zip(a,bits))
   for x in values:
    if x-1 not in values:
     end=x
     while end in values:end+=1
     best=max(best,end-x)
  return best
 if pid==3093:
  first={}
  for i,s in enumerate(a):first.setdefault(s,i)
  queries=args[1]
  if sum(len(s)for s in first)*len(set(queries))>2000000:raise ValueError('bounded pairwise suffix comparisons')
  def suffix(s,t):
   n=0
   while n<min(len(s),len(t))and s[-n-1]==t[-n-1]:n+=1
   return n
  answers={q:min(first.values(),key=lambda i:(-suffix(a[i],q),len(a[i]),i))for q in set(queries)}
  return[answers[q]for q in queries]
 if pid==3130:return stable(*args)
 raise ValueError('unsupported')
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind='bool'if pid==2709 else'list'if pid==3093 else'int';types={'python':{'bool':'bool','list':'list','int':'int'},'javascript':{'bool':'boolean','list':'object','int':'number'}}
 if record.get('result_type')!=types[language][kind]or not exact(record.get('result'),want):return False,'typed_result'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
