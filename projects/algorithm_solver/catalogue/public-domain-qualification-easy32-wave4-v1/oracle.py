"""Independent definition-level finite oracles for owner Easy32 final wave."""
IDS=(2520,2566,2644,2739,2778,2828,2848,2917)
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(xs,a,b,lo,hi):return type(xs)is list and lo<=len(xs)<=hi and all(integer(x,a,b)for x in xs)
def word(s,lo,hi):return type(s)is str and lo<=len(s)<=hi and all('a'<=c<='z'for c in s)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered arguments required')
 good=False
 if pid==2520:good=len(args)==1 and integer(args[0],1,10**9)and '0'not in str(args[0])
 elif pid==2566:good=len(args)==1 and integer(args[0],1,10**8)
 elif pid==2644:good=len(args)==2 and all(ints(xs,1,10**9,1,1000)for xs in args)
 elif pid==2739:good=len(args)==2 and all(integer(x,1,100)for x in args)
 elif pid==2778:good=len(args)==1 and ints(args[0],1,50,1,50)
 elif pid==2828:good=len(args)==2 and type(args[0])is list and 1<=len(args[0])<=100 and all(word(s,1,10)for s in args[0])and word(args[1],1,100)
 elif pid==2848:good=len(args)==1 and type(args[0])is list and 1<=len(args[0])<=100 and all(type(r)is list and len(r)==2 and integer(r[0],1,100)and integer(r[1],r[0],100)for r in args[0])
 elif pid==2917:good=len(args)==2 and ints(args[0],0,2**31-1,1,50)and integer(args[1],1,len(args[0]))
 if not good:raise ValueError('outside official declared domain')
def expected(pid,args):
 validate(pid,args)
 if pid==2520:return sum(args[0]%int(c)==0 for c in str(args[0]))
 if pid==2566:
  s=str(args[0]);values=[int(s.replace(a,b))for a in '0123456789'for b in '0123456789'];return max(values)-min(values)
 if pid==2644:
  xs,ds=args;return min(ds,key=lambda d:(-len([x for x in xs if x%d==0]),d))
 if pid==2739:
  main,extra=args;used=0
  while main:
   main-=1;used+=1
   if used%5==0 and extra:extra-=1;main+=1
  return used*10
 if pid==2778:
  xs=args[0];divisors={d for d in range(1,len(xs)+1)if len(xs)//d*d==len(xs)};return sum(xs[d-1]**2 for d in divisors)
 if pid==2828:return ''.join(s[0]for s in args[0])==args[1]
 if pid==2848:return len(set().union(*(set(range(a,b+1))for a,b in args[0])))
 xs,k=args;bits=[format(x,'031b')for x in xs];return int(''.join('1'if sum(row[i]=='1'for row in bits)>=k else'0'for i in range(31)),2)
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 types={'python':{'int':'int','bool':'bool'},'javascript':{'int':'number','bool':'boolean'}}
 if record.get('result_type')!=types[language][type(want).__name__]:return False,'result_type'
 if not exact(record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
