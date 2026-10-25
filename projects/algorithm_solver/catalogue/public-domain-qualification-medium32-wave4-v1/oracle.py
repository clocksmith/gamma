"""Official-domain gates and independent bounded truth; never import candidates."""
from itertools import permutations
from collections import Counter
IDS=(2170,2186,2256,2433,2587,2597,2602,2860)
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(x,a,b,n=100000):return type(x)is list and 1<=len(x)<=n and all(integer(y,a,b)for y in x)
def word(x):return type(x)is str and 1<=len(x)<=200000 and all('a'<=c<='z'for c in x)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered argument list required')
 ok=False
 if pid==2170:ok=len(args)==1 and ints(args[0],1,100000)
 elif pid==2186:ok=len(args)==2 and all(word(x)for x in args)
 elif pid==2256:ok=len(args)==1 and ints(args[0],0,100000)
 elif pid==2433:ok=len(args)==1 and ints(args[0],0,1000000)
 elif pid==2587:ok=len(args)==1 and ints(args[0],-1000000,1000000)
 elif pid==2597:ok=len(args)==2 and ints(args[0],1,1000,18)and integer(args[1],1,1000)
 elif pid==2602:ok=len(args)==2 and all(ints(x,1,10**9)for x in args)
 elif pid==2860:ok=len(args)==1 and type(args[0])is list and ints(args[0],0,len(args[0])-1)
 if not ok:raise ValueError('outside reviewed official domain')

def expected(pid,args):
 validate(pid,args);a=args[0]
 if pid==2170:
  if len(set(a))==1:return len(a)//2
  if len(a)>100:raise ValueError('bounded distinct-target enumeration')
  choices=set(a)|{100001,100002}
  return min(sum(v!=(x if i%2==0 else y)for i,v in enumerate(a))for x in choices for y in choices if x!=y)
 if pid==2186:
  # Match equal characters in sorted strings; unmatched occurrences need appends.
  x,y=sorted(a),sorted(args[1]);i=j=matched=0
  while i<len(x)and j<len(y):
   if x[i]==y[j]:matched+=1;i+=1;j+=1
   elif x[i]<y[j]:i+=1
   else:j+=1
  return len(x)+len(y)-2*matched
 if pid==2256:
  if len(set(a))==1:return 0
  if len(a)>500:raise ValueError('bounded independent slice sums')
  return min(range(len(a)),key=lambda i:abs(sum(a[:i+1])//(i+1)-(sum(a[i+1:])//(len(a)-i-1)if i+1<len(a)else 0)))
 if pid==2433:
  # Solve each of20 binary triangular prefix systems independently.
  result=[0]*len(a)
  for bit in range(20):
   parity=0
   for i,prefix in enumerate(a):
    current=(prefix>>bit)&1
    if current!=parity:result[i]|=1<<bit
    parity=current
  return result
 if pid==2587:
  if all(x<=0 for x in a):return 0
  if all(x>=0 for x in a):return len(a) # at least one positive from previous branch
  if len(a)>8:raise ValueError('bounded order enumeration')
  best=0
  for order in set(permutations(a)):
   total=score=0
   for x in order:total+=x;score+=total>0
   best=max(best,score)
  return best
 if pid==2597:
  k=args[1];n=len(a);conflicts=[sum(1<<j for j in range(n)if abs(a[i]-a[j])==k)for i in range(n)]
  good=bytearray(1<<n);good[0]=1;count=0
  for mask in range(1,1<<n):
   low=mask&-mask;i=low.bit_length()-1;rest=mask^low
   if good[rest]and not rest&conflicts[i]:good[mask]=1;count+=1
  return count
 if pid==2602:
  counts=Counter(a);queries=args[1]
  if len(counts)*len(set(queries))>2000000:raise ValueError('bounded direct absolute differences')
  truth={q:sum(abs(v-q)*n for v,n in counts.items())for q in set(queries)}
  return [truth[q]for q in queries]
 if pid==2860:
  n=len(a)
  if n>16:
   if len(set(a))==1:return 1+(a[0]>0)
   raise ValueError('bounded selected-index enumeration')
  return sum(all((mask.bit_count()>v if mask>>i&1 else mask.bit_count()<v)for i,v in enumerate(a))for mask in range(1<<n))
 raise ValueError('unsupported id')
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind='list'if pid in(2433,2602)else'int';types={'python':{'list':'list','int':'int'},'javascript':{'list':'object','int':'number'}}
 if record.get('result_type')!=types[language][kind]or not exact(record.get('result'),want):return False,'typed_result'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
