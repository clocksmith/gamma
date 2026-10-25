"""Independent definition-level oracles for pinned public statement snapshots.

Full-domain validators are separate from finite test evidence. No candidate import.
"""
from functools import lru_cache
from itertools import combinations
from math import gcd
IDS=(3894,3898,3903,3908,3912,3917,3921,3925,3931,3936,4000,4006,4010,4020,4024,4030)
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(x,a,b,lo,hi):return type(x)is list and lo<=len(x)<=hi and all(integer(v,a,b)for v in x)
def string(x,chars,lo,hi):return type(x)is str and lo<=len(x)<=hi and all(c in chars for c in x)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered arguments required')
 good=False
 if pid==3894:good=len(args)==1 and integer(args[0],0,1000)
 elif pid==3898 and len(args)==1:
  m=args[0];n=len(m)if type(m)is list else 0
  good=1<=n<=100 and all(ints(r,0,1,n,n)for r in m)and all(m[i][i]==0 for i in range(n))and all(m[i][j]==m[j][i]for i in range(n)for j in range(n))
 elif pid==3903:good=len(args)==2 and ints(args[0],0,10**9,1,100)and integer(args[1],0,10**9)
 elif pid==3908:good=len(args)==2 and integer(args[0],0,100000)and integer(args[1],0,9)
 elif pid in(3912,3917,3925):good=len(args)==1 and ints(args[0],1,100,1,100)
 elif pid==3921:good=len(args)==1 and type(args[0])is list and 1<=len(args[0])<=1000 and all(type(x)is str and x in ('0','1','2','3','4','6','W','WD','NB')for x in args[0])
 elif pid==3931:good=len(args)==1 and string(args[0],'0123456789',2,100)
 elif pid==3936:good=len(args)==1 and ints(args[0],0,100,1,100)
 elif pid==4000:good=len(args)==2 and integer(args[0],1,5)and integer(args[1],0,100)
 elif pid==4006:good=len(args)==1 and string(args[0],'01',1,100)
 elif pid==4010:good=len(args)==1 and ints(args[0],1,100000,2,2000)
 elif pid==4020:good=len(args)==2 and integer(args[0],1,100)and ints(args[1],0,args[0]-1,1,100)
 elif pid==4024 and len(args)==2:
  ds,t=args;good=type(ds)is list and 1<=len(ds)<=100 and ints(t,-25,25,2,2)and all(type(r)is list and len(r)==3 and integer(r[0],-25,25)and integer(r[1],-25,25)and integer(r[2],1,100)for r in ds)
 elif pid==4030:good=len(args)==1 and string(args[0],'abcdefghijklmnopqrstuvwxyz',1,100)
 if not good:raise ValueError('outside pinned statement domain')
@lru_cache(None)
def digit_table(n):
 # Exhaust all possible values, not the candidate's positional greedy rule.
 table={}
 for v in range(10**n):table[sum(map(int,str(v)))]=v
 return table
@lru_cache(None)
def zero_swaps_small(bits):
 target=tuple(sorted(bits,reverse=True));q=[(bits,0)];seen={bits}
 for state,d in q:
  if state==target:return d
  for i,j in combinations(range(len(bits)),2):
   if state[i]==state[j]:continue
   nxt=list(state);nxt[i],nxt[j]=nxt[j],nxt[i];nxt=tuple(nxt)
   if nxt not in seen:seen.add(nxt);q.append((nxt,d+1))
def expected(pid,args):
 validate(pid,args)
 if pid==3894:return {0:'Green',30:'Orange',**{t:'Red'for t in range(31,91)}}.get(args[0],'Invalid')
 if pid==3898:
  m=args[0];answer=[0]*len(m)
  for i,j in combinations(range(len(m)),2):
   if m[i][j]:answer[i]+=1;answer[j]+=1
  return answer
 if pid==3903:
  xs,k=args;return next((i for i in range(len(xs))if all(a-b<=k for a in xs[:i+1]for b in xs[i:])),-1)
 if pid==3908:
  n,x=args;digits=[]
  while n:digits.append(n%10);n//=10
  if not digits:digits=[0]
  return x in digits and digits[-1]!=x
 if pid==3912:
  xs=args[0];return [x for i,x in enumerate(xs)if all(x>v for v in xs[:i])or all(x>v for v in xs[i+1:])]
 if pid==3917:
  xs=args[0];return [sum((x+y)%2==1 for y in xs[i+1:])for i,x in enumerate(xs)]
 if pid==3921:
  events=args[0];positions=[i for i,x in enumerate(events)if x=='W'];end=positions[9]+1 if len(positions)>=10 else len(events);used=events[:end]
  return [sum({'0':0,'1':1,'2':2,'3':3,'4':4,'6':6,'WD':1,'NB':1,'W':0}[x]for x in used),used.count('W')]
 if pid==3925:return args[0]+list(reversed(args[0]))
 if pid==3931:return all(int(b) in range(max(0,int(a)-2),min(9,int(a)+2)+1)for a,b in zip(args[0],args[0][1:]))
 if pid==3936:
  bits=tuple(int(x!=0)for x in args[0])
  if len(bits)<=8:return zero_swaps_small(bits)
  # Each wrongly placed zero must cross the boundary; matching each with a
  # wrongly placed nonzero is a constructive equal lower/upper bound.
  target=sorted(bits,reverse=True);return sum(a!=b for a,b in zip(bits,target))//2
 if pid==4000:return digit_table(args[0]).get(args[1],-1)
 if pid==4006:
  s=args[0];return sum(any(s[:n].count('1')==sum((i+start)%2 for i in range(n))for start in(0,1))for n in range(1,len(s)+1))
 if pid==4010:
  xs=args[0]
  # Distinct index multiplicity retained. Independent stdlib gcd, not candidate gcd.
  return max(a*b//(gcd(a,b)**2)for a,b in combinations(xs,2))
 if pid==4020:
  _,requests=args;return sum(sum(1 for _ in range(min(a,b),max(a,b)))for a,b in zip([0]+requests,requests))
 if pid==4024:
  ds,t=args;valid=[(abs(x-t[0])+abs(y-t[1]),i)for i,(x,y,r)in enumerate(ds)if abs(x-t[0])+abs(y-t[1])<=r];return min(valid)[1]if valid else-1
 bits=''.join(format(ord(c),'08b')for c in args[0]);return bits==bits[::-1]
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind=type(want).__name__;types={'python':{'list':'list','int':'int','bool':'bool','str':'str'},'javascript':{'list':'object','int':'number','bool':'boolean','str':'string'}}
 if record.get('result_type')!=types[language][kind]:return False,'result_type'
 if not exact(record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
