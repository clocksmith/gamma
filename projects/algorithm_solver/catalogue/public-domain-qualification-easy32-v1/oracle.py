"""Independent finite oracles and official nonunique-output property checks."""
import re
IDS=(1317,1351,1470,1556,1598,1716,1800,1854)
def integer(x,a,b):return type(x)is int and a<=x<=b
def ints(x,a,b,lo,hi):return type(x)is list and lo<=len(x)<=hi and all(integer(v,a,b)for v in x)
def validate(pid,args):
 if type(args)is not list:raise ValueError('ordered arguments required')
 good=False
 if pid==1317:good=len(args)==1 and integer(args[0],2,10000)
 elif pid==1351 and len(args)==1:
  g=args[0];m=len(g)if type(g)is list else 0;n=len(g[0])if m and type(g[0])is list else 0
  good=1<=m<=100 and 1<=n<=100 and all(ints(r,-100,100,n,n)for r in g)and all(g[i][j]>=g[i][j+1]for i in range(m)for j in range(n-1))and all(g[i][j]>=g[i+1][j]for i in range(m-1)for j in range(n))
 elif pid==1470:good=len(args)==2 and integer(args[1],1,500)and ints(args[0],1,1000,2*args[1],2*args[1])
 elif pid==1556:good=len(args)==1 and integer(args[0],0,2**31-1)
 elif pid==1598:good=len(args)==1 and type(args[0])is list and 1<=len(args[0])<=1000 and all(type(x)is str and 2<=len(x)<=10 and (x in('../','./')or re.fullmatch('[a-z0-9]+/',x,re.ASCII))for x in args[0])
 elif pid==1716:good=len(args)==1 and integer(args[0],1,1000)
 elif pid==1800:good=len(args)==1 and ints(args[0],1,100,1,100)
 elif pid==1854:good=len(args)==1 and type(args[0])is list and 1<=len(args[0])<=100 and all(type(r)is list and len(r)==2 and integer(r[0],1950,2049)and integer(r[1],r[0]+1,2050)for r in args[0])
 if not good:raise ValueError('outside official declared domain')
def expected(pid,args):
 validate(pid,args)
 if pid==1317:return {'property':'positive-no-zero-pair-summing-to-n','n':args[0]}
 if pid==1351:return sum(v<0 for row in args[0]for v in row)
 if pid==1470:
  xs,n=args;return [xs[(i//2)+(n if i%2 else 0)]for i in range(2*n)]
 if pid==1556:return format(args[0],',d').replace(',','.')
 if pid==1598:
  stack=[]
  for op in args[0]:
   if op=='../':
    if stack:stack.pop()
   elif op!='./':stack.append(op[:-1])
  return len(stack)
 if pid==1716:
  monday=1;daily=1;total=0
  for day in range(args[0]):
   if day and day%7==0:monday+=1;daily=monday
   total+=daily;daily+=1
  return total
 if pid==1800:
  xs=args[0];return max(sum(xs[i:j])for i in range(len(xs))for j in range(i+1,len(xs)+1)if all(xs[k]<xs[k+1]for k in range(i,j-1)))
 logs=args[0];counts={year:sum(b<=year<d for b,d in logs)for year in range(1950,2050)}
 return min(counts,key=lambda y:(-counts[y],y))
def exact(a,b):
 if type(a)is not type(b):return False
 if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
 if type(a)is dict:return a.keys()==b.keys()and all(exact(a[k],b[k])for k in a)
 return a==b
def valid_no_zero_pair(n,result):
 return type(result)is list and len(result)==2 and all(type(v)is int and 0<v<n and '0'not in str(v)for v in result)and sum(result)==n
def compare(pid,args,want,record,language):
 if 'error'in record:return False,'candidate_error'
 kind='list'if pid in(1317,1470)else('str'if pid==1556 else'int')
 types={'python':{'list':'list','int':'int','str':'str'},'javascript':{'list':'object','int':'number','str':'string'}}
 if record.get('result_type')!=types[language][kind]:return False,'result_type'
 if pid==1317:
  if not exact(want,expected(pid,args))or not valid_no_zero_pair(args[0],record.get('result')):return False,'nonunique_result_property'
 elif not exact(record.get('result'),want):return False,'result_value'
 if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
 if not exact(record.get('alias_edges'),[]):return False,'return_aliases'
 return True,None
