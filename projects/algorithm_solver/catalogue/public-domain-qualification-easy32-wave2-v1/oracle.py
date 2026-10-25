"""Definition-level independent host oracles, never candidate imports."""
from itertools import permutations
from collections import Counter
IDS=(1880,1893,1897,1952,2000,2011,2094,2108)
def integer(x,a,b):return type(x)is int and a<=x<=b
def string(s,alphabet,lo,hi):return type(s)is str and lo<=len(s)<=hi and all(c in alphabet for c in s)
def words(xs):return type(xs)is list and 1<=len(xs)<=100 and all(string(x,'abcdefghijklmnopqrstuvwxyz',1,100)for x in xs)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered arguments required')
 good=False
 if pid==1880:good=len(args)==3 and all(string(x,'abcdefghij',1,8)for x in args)
 elif pid==1893 and len(args)==3:
  rs,l,r=args;good=integer(l,1,50)and integer(r,l,50)and type(rs)is list and 1<=len(rs)<=50 and all(type(x)is list and len(x)==2 and integer(x[0],1,50)and integer(x[1],x[0],50)for x in rs)
 elif pid in(1897,2108):good=len(args)==1 and words(args[0])
 elif pid==1952:good=len(args)==1 and integer(args[0],1,10000)
 elif pid==2000:good=len(args)==2 and string(args[0],'abcdefghijklmnopqrstuvwxyz',1,250)and string(args[1],'abcdefghijklmnopqrstuvwxyz',1,1)
 elif pid==2011:good=len(args)==1 and type(args[0])is list and 1<=len(args[0])<=100 and all(type(x)is str and x in('++X','X++','--X','X--')for x in args[0])
 elif pid==2094:good=len(args)==1 and type(args[0])is list and 3<=len(args[0])<=100 and all(integer(x,0,9)for x in args[0])
 if not good:raise ValueError('outside official declared domain')
def expected(pid,args):
 validate(pid,args)
 if pid==1880:
  decode=lambda s:int(''.join(str('abcdefghij'.index(c))for c in s))
  return decode(args[0])+decode(args[1])==decode(args[2])
 if pid==1893:
  rs,l,r=args;return set(range(l,r+1))<=set().union(*(set(range(a,b+1))for a,b in rs))
 if pid==1897:
  # Necessity: each final string consumes equal copies of every letter.
  # Sufficiency: distribute each letter's copies equally; arbitrary moves allow it.
  xs=args[0];allchars=''.join(xs);return all(allchars.count(c)%len(xs)==0 for c in set(allchars))
 if pid==1952:return sum(args[0]%d==0 for d in range(1,args[0]+1))==3
 if pid==2000:
  word,ch=args
  if ch not in word:return word
  stop=next(i for i,c in enumerate(word)if c==ch);return ''.join(word[stop-i]if i<=stop else word[i]for i in range(len(word)))
 if pid==2011:return sum({'++X':1,'X++':1,'--X':-1,'X--':-1}[x]for x in args[0])
 if pid==2094:
  xs=args[0]
  if len(xs)<=8:return sorted({100*a+10*b+c for a,b,c in permutations(xs,3)if a and c%2==0})
  available=Counter(xs);return [v for v in range(100,1000,2)if not (Counter(map(int,str(v)))-available)]
 return next((word for word in args[0]if word==word[::-1]),'')
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 types={'python':{'list':'list','int':'int','bool':'bool','str':'str'},'javascript':{'list':'object','int':'number','bool':'boolean','str':'string'}}
 if record.get('result_type')!=types[language][type(want).__name__]:return False,'result_type'
 if not exact(record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
