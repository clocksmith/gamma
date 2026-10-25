"""Independent specification oracle and domain gate; never imports candidates."""
from collections import Counter
IDS=(153,645,674,832,833,916)
def integer(x):return type(x)is int
def lower(x,low,high):return type(x)is str and low<=len(x)<=high and all('a'<=c<='z'for c in x)
def validate(pid,args):
 if pid not in IDS or type(args)is not list:raise ValueError('unsupported problem/arguments')
 if len(args)!={153:1,645:1,674:1,832:1,833:4,916:2}[pid]:raise ValueError('argument arity')
 if pid in (153,645,674):
  a=args[0];limit=5000 if pid==153 else 10000
  if type(a)is not list or not (2 if pid==645 else 1)<=len(a)<=limit or not all(integer(x)for x in a):raise ValueError('integer array domain')
  if pid==153:
   if any(not -5000<=x<=5000 for x in a) or len(set(a))!=len(a):raise ValueError('rotated distinct numeric domain')
   smallest=a.index(min(a));unrotated=a[smallest:]+a[:smallest]
   if any(x>=y for x,y in zip(unrotated,unrotated[1:])):raise ValueError('not a rotated ascending array')
  elif pid==645:
   counts=Counter(a);n=len(a)
   if any(not 1<=x<=n for x in a) or sorted(counts.values())!=[1]*(n-2)+[2]:raise ValueError('exact one duplicate and one missing required')
  elif any(not -10**9<=x<=10**9 for x in a):raise ValueError('LCIS numeric bounds')
 elif pid==832:
  a=args[0]
  if type(a)is not list or not 1<=len(a)<=20 or any(type(row)is not list or len(row)!=len(a)or any(type(x)is not int or x not in (0,1)for x in row)for row in a):raise ValueError('square binary matrix required')
 elif pid==833:
  s,indices,sources,targets=args
  if not lower(s,1,1000) or any(type(x)is not list for x in (indices,sources,targets)) or not 1<=len(indices)<=100 or len({len(indices),len(sources),len(targets)})!=1:raise ValueError('replacement parallel-array bounds')
  if any(not integer(x)or not 0<=x<len(s)for x in indices) or any(not lower(x,1,50)for x in sources+targets):raise ValueError('replacement text/index domain')
  spans=sorted((i,i+len(src))for i,src in zip(indices,sources)if s[i:i+len(src)]==src)
  if any(left[1]>right[0]for left,right in zip(spans,spans[1:])):raise ValueError('successful simultaneous replacements overlap')
 else:
  a,b=args
  if any(type(x)is not list or not 1<=len(x)<=10000 or any(not lower(w,1,10)for w in x)for x in (a,b)) or len(set(a))!=len(a):raise ValueError('word-subset domain')
 return True

def expected(pid,args):
 validate(pid,args)
 if pid==153:return min(args[0])
 if pid==645:
  a=args[0];counts=Counter(a)
  return [next(x for x,n in counts.items()if n==2),next(x for x in range(1,len(a)+1)if x not in counts)]
 if pid==674:
  a=args[0];cuts=[0]+[i for i in range(1,len(a))if not a[i-1]<a[i]]+[len(a)]
  return max(right-left for left,right in zip(cuts,cuts[1:]))
 if pid==832:
  a=args[0];n=len(a)
  return [[1-a[i][n-1-j]for j in range(n)]for i in range(n)]
 if pid==833:
  s,indices,sources,targets=args
  # Apply independently selected original-coordinate intervals right-to-left;
  # unlike candidate left-to-right matching/scanning, earlier coordinates stay.
  matches=sorted(((i,src,dst)for i,src,dst in zip(indices,sources,targets)if s[i:i+len(src)]==src),reverse=True)
  result=s
  for index,source,target in matches:result=result[:index]+target+result[index+len(source):]
  return result
 words,requirements=args
 # Independently test every distinct requirement, without combining them into
 # the maximum-frequency vector used by the candidate algorithm.
 demands=[Counter(word)for word in sorted(set(requirements))]
 return [word for word in words if all(all(word.count(letter)>=count for letter,count in demand.items())for demand in demands)]

def exact(left,right):
 if type(left)is not type(right):return False
 if type(left)is list:return len(left)==len(right)and all(exact(x,y)for x,y in zip(left,right))
 if type(left)is dict:return left.keys()==right.keys()and all(exact(left[k],right[k])for k in left)
 return left==right

def compare(pid,args,want,record,language):
 """Local effect policy is explicit, prospective and independently adopted."""
 if 'error'in record:return False,'candidate_error'
 got=record.get('result');kind='int'if pid in (153,674)else'str'if pid==833 else'list'
 expected_type={'javascript':{'int':'number','str':'string','list':'object'},'python':{'int':'int','str':'str','list':'list'}}[language][kind]
 if record.get('result_type')!=expected_type:return False,'result_type'
 if pid==916:
  valid=type(got)is list and all(type(x)is str for x in got)and Counter(got)==Counter(want)
 else:valid=exact(got,want)
 if not valid:return False,'result_value'
 if not exact(record.get('args_before'),args):return False,'args_before'
 after=[want]if pid==832 else args
 if not exact(record.get('args_after'),after):return False,'input_effects'
 aliases=[['result','args.0']]if pid==832 else[]
 if not exact(record.get('alias_edges'),aliases):return False,'return_aliases'
 return True,None
