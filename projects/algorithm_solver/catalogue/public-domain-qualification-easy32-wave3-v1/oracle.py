"""Independent bounded oracles for owner Easy32 wave3."""
from itertools import combinations
IDS=(2138,2248,2351,2383,2432,2475,2500,2506)
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(xs,a,b,lo,hi):return type(xs)is list and lo<=len(xs)<=hi and all(integer(x,a,b)for x in xs)
def word(s,lo,hi):return type(s)is str and lo<=len(s)<=hi and all('a'<=c<='z'for c in s)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered arguments required')
 good=False
 if pid==2138:good=len(args)==3 and word(args[0],1,100)and integer(args[1],1,100)and word(args[2],1,1)
 elif pid==2248 and len(args)==1:
  xs=args[0];good=type(xs)is list and 1<=len(xs)<=1000 and all(ints(row,1,1000,1,1000)and len(set(row))==len(row)for row in xs)and sum(map(len,xs))<=1000
 elif pid==2351:good=len(args)==1 and word(args[0],2,100)and len(set(args[0]))<len(args[0])
 elif pid==2383:good=len(args)==4 and integer(args[0],1,100)and integer(args[1],1,100)and ints(args[2],1,100,1,100)and ints(args[3],1,100,len(args[2]),len(args[2]))
 elif pid==2432 and len(args)==2:
  n,logs=args;good=integer(n,2,500)and type(logs)is list and 1<=len(logs)<=500 and all(type(row)is list and len(row)==2 and integer(row[0],0,n-1)and integer(row[1],1,500)for row in logs)and all(a[0]!=b[0]and a[1]<b[1]for a,b in zip(logs,logs[1:]))
 elif pid==2475:good=len(args)==1 and ints(args[0],1,1000,3,100)
 elif pid==2500 and len(args)==1:
  g=args[0];m=len(g)if type(g)is list else 0;n=len(g[0])if m and type(g[0])is list else 0
  good=1<=m<=50 and 1<=n<=50 and all(ints(row,1,100,n,n)for row in g)
 elif pid==2506:good=len(args)==1 and type(args[0])is list and 1<=len(args[0])<=100 and all(word(s,1,100)for s in args[0])
 if not good:raise ValueError('outside official declared domain')
def expected(pid,args):
 validate(pid,args)
 if pid==2138:
  s,k,fill=args;padded=s+fill*((-len(s))%k);return [''.join(padded[j]for j in range(i,i+k))for i in range(0,len(padded),k)]
 if pid==2248:return sorted(set.intersection(*(set(row)for row in args[0])))
 if pid==2351:
  s=args[0];return s[min(i for i in range(1,len(s))if s[i]in s[:i])]
 if pid==2383:
  e,x,es,xs=args
  # Every opponent imposes an independent lower bound on initial stats.
  # Taking their maxima is both necessary and sufficient for all strict tests.
  energy=max(0,max(1+sum(es[:i+1])-e for i in range(len(es))))
  experience=max(0,max(1+xs[i]-sum(xs[:i])-x for i in range(len(xs))))
  return energy+experience
 if pid==2432:
  _,logs=args;ends=[0]+[t for _,t in logs];pairs=[(ends[i+1]-ends[i],logs[i][0])for i in range(len(logs))];return min(pairs,key=lambda p:(-p[0],p[1]))[1]
 if pid==2475:return sum(len({a,b,c})==3 for a,b,c in combinations(args[0],3))
 if pid==2500:
  rows=[row[:]for row in args[0]];answer=0
  while rows[0]:
   removed=[]
   for row in rows:largest=max(row);removed.append(largest);row.remove(largest)
   answer+=max(removed)
  return answer
 return sum(set(a)==set(b)for a,b in combinations(args[0],2))
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 types={'python':{'list':'list','int':'int','str':'str'},'javascript':{'list':'object','int':'number','str':'string'}}
 if record.get('result_type')!=types[language][type(want).__name__]:return False,'result_type'
 if not exact(record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
