"""Independent HOST-ONLY development specifications; no source or hidden-test imports."""
import collections,itertools,math,random,re,functools,importlib.util
from pathlib import Path
SEED=202610204
NEW_IDS=[541,599,645,682,696,697,734,748,796,806,821,824,830,844,859,893,914,917,925,929,566,661,766,832,867,883,892,896,908,922,942,944,976,977,1005,1013,1018,1085,1086,1122]
DOMAINS={541:'Lowercase ASCII; nonempty text; positive k.',599:'Nonempty unique string lists with at least one common value; result order ignored.',645:'1..n with exactly one duplicate and one missing.',682:'Valid baseball operations; all sums within safe integers.',696:'Nonempty binary ASCII string.',697:'Nonempty integer array; shortest contiguous subarray retaining maximum frequency.',734:'ASCII word lists; symmetric nontransitive similarity pairs.',748:'ASCII plate; lowercase words with at least one completing word; first shortest.',796:'Nonempty lowercase ASCII strings.',806:'26 widths in1..10; nonempty lowercase ASCII text.',821:'ASCII text containing target.',824:'Nonempty ASCII words separated by one space.',830:'Lowercase ASCII groups length>=3; inclusive positions.',844:'ASCII letters and # backspaces.',859:'Nonempty lowercase ASCII strings; exactly one swap of distinct positions.',893:'Nonempty equal-length lowercase words; parity-permutation equivalence.',914:'Nonempty card integers; common group size>=2.',917:'ASCII printable text; reverse ASCII letters only.',925:'Nonempty lowercase ASCII names and typed text.',929:'Well-formed ASCII local@domain; periods and plus special only in local.',566:'Nonempty rectangular integer matrix; positive target dimensions.',661:'Nonempty rectangular grayscale matrix values0..255; floor neighborhood average.',766:'Nonempty rectangular integer matrix; constant top-left diagonals.',832:'Nonempty square binary matrix; input mutation permitted and recorded.',867:'Nonempty rectangular integer matrix transpose.',883:'Nonempty square nonnegative height matrix.',892:'Nonempty square nonnegative height matrix; exposed unit-cube faces.',896:'Nonempty integer array; nondecreasing or nonincreasing.',908:'Nonempty integer array, nonnegative integer adjustment.',922:'Even nonempty integer array with equal parity counts; mutation permitted; any valid multiset arrangement.',942:'Nonempty ASCII I/D; any matching permutation0..n.',944:'Nonempty equal-length lowercase ASCII rows.',976:'Positive integer sides; maximal valid triangle perimeter; retained source sorts input in place. Length1/2 are extra-domain robustness checks.',977:'Nondecreasing integers within[-10000,10000]; exact squared sorted result.',1005:'Integers[-100,100], positive k; exactly k sign flips; input preserved.',1013:'At least three integers; three nonempty contiguous equal-sum parts.',1018:'Nonempty bits; prefix divisibility by5 with bounded arithmetic.',1085:'Positive integers<=10000; even digit sum of minimum.',1086:'Positive IDs<=1000, scores0..100; at least five scores per ID; floor top5average.',1122:'Values0..1000; distinct priority array values all present; sorted nonpriority suffix.'}

def oracle(i,args):
 a=args[0]
 if i==541:
  k=args[1];return ''.join(a[j:j+k][::-1]+a[j+k:j+2*k] for j in range(0,len(a),2*k))
 if i==599:
  b=args[1];shared=set(a)&set(b);best=min(a.index(x)+b.index(x) for x in shared);return sorted(x for x in shared if a.index(x)+b.index(x)==best)
 if i==645:
  c=collections.Counter(a);return [next(x for x,n in c.items() if n==2),next(x for x in range(1,len(a)+1) if x not in c)]
 if i==682:
  stack=[]
  for x in a:
   if x=='C':stack.pop()
   elif x=='D':stack.append(2*stack[-1])
   elif x=='+':stack.append(sum(stack[-2:]))
   else:stack.append(int(x))
  return sum(stack)
 if i==696:return sum(len(set(a[j:k]))==2 and a[j:k].count('0')==a[j:k].count('1') and len(list(itertools.groupby(a[j:k])))==2 for j in range(len(a)) for k in range(j+2,len(a)+1,2))
 if i==697:
  c=collections.Counter(a);degree=max(c.values());return min(len(a)-1-a[::-1].index(x)-a.index(x)+1 for x in c if c[x]==degree)
 if i==734:
  b,pairs=args[1:];edges={tuple(x) for x in pairs}|{tuple(reversed(x)) for x in pairs};return len(a)==len(b) and all(x==y or (x,y) in edges for x,y in zip(a,b))
 if i==748:
  c=collections.Counter(x.lower() for x in a if x.isalpha());return min((x for x in args[1] if not c-collections.Counter(x)),key=len)
 if i==796:return len(a)==len(args[1]) and args[1] in a+a
 if i==806:
  line=1;size=0
  for c in args[1]:
   width=a[ord(c)-97]
   if size+width>100:line+=1;size=0
   size+=width
  return [line,size]
 if i==821:return [min(abs(j-k) for k,c in enumerate(a) if c==args[1]) for j in range(len(a))]
 if i==824:return ' '.join((w if w[0].lower() in 'aeiou' else w[1:]+w[0])+'ma'+'a'*(j+1) for j,w in enumerate(a.split(' ')))
 if i==830:
  out=[];pos=0
  for _,g in itertools.groupby(a):
   n=len(list(g))
   if n>=3:out.append([pos,pos+n-1])
   pos+=n
  return out
 if i==844:
  def reduce(s):
   while '#' in s:
    k=s.index('#');s=s[:max(0,k-1)]+s[k+1:]
   return s
  return reduce(a)==reduce(args[1])
 if i==859:
  return any(a[:j]+a[k]+a[j+1:k]+a[j]+a[k+1:]==args[1] for j in range(len(a)) for k in range(j+1,len(a)))
 if i==893:return len({(''.join(sorted(w[::2])),''.join(sorted(w[1::2]))) for w in a})
 if i==914:return functools.reduce(math.gcd,collections.Counter(a).values())>=2
 if i==917:
  letters=[c for c in a if c.isascii() and c.isalpha()][::-1];it=iter(letters);return ''.join(next(it) if c.isascii() and c.isalpha() else c for c in a)
 if i==925:
  x=[(c,len(list(g))) for c,g in itertools.groupby(a)];y=[(c,len(list(g))) for c,g in itertools.groupby(args[1])];return len(x)==len(y) and all(c==d and n<=m for (c,n),(d,m) in zip(x,y))
 if i==929:
  return len({(s.split('@')[0].split('+')[0].replace('.',''),s.split('@')[1]) for s in a})
 if i==566:
  nr,nc=args[1:];flat=sum(a,[]);return [flat[j:j+nc] for j in range(0,len(flat),nc)] if nr*nc==len(flat) else a
 if i==661:return [[sum(a[x][y] for x in range(max(0,j-1),min(len(a),j+2)) for y in range(max(0,k-1),min(len(a[0]),k+2)))//((min(len(a),j+2)-max(0,j-1))*(min(len(a[0]),k+2)-max(0,k-1))) for k in range(len(a[0]))] for j in range(len(a))]
 if i==766:return all(a[j][k]==a[j-1][k-1] for j in range(1,len(a)) for k in range(1,len(a[0])))
 if i==832:return [[1-x for x in row[::-1]] for row in a]
 if i==867:return [list(x) for x in zip(*a)]
 if i==883:return sum(x>0 for row in a for x in row)+sum(max(row) for row in a)+sum(max(col) for col in zip(*a))
 if i==892:
  cubes={(x,y,z) for x,row in enumerate(a) for y,h in enumerate(row) for z in range(h)};return sum((x+dx,y+dy,z+dz) not in cubes for x,y,z in cubes for dx,dy,dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)])
 if i==896:return a==sorted(a) or a==sorted(a,reverse=True)
 if i==908:return max(0,max(a)-min(a)-2*args[1])
 if i==922:return None
 if i==942:return None
 if i==944:return sum(list(c)!=sorted(c) for c in zip(*a))
 if i==976:return max([sum(t) for t in itertools.combinations(a,3) if 2*max(t)<sum(t)]+[0])
 if i==977:return sorted(x*x for x in a)
 if i==1005:
  states={tuple(a)}
  for _ in range(args[1]):states={tuple(-x if k==j else x for k,x in enumerate(s)) for s in states for j in range(len(s))}
  return max(map(sum,states))
 if i==1013:return any(sum(a[:j])==sum(a[j:k])==sum(a[k:]) for j in range(1,len(a)-1) for k in range(j+1,len(a)))
 if i==1018:return [int(''.join(map(str,a[:j])),2)%5==0 for j in range(1,len(a)+1)]
 if i==1085:return int(sum(map(int,str(min(a))))%2==0)
 if i==1086:
  ids=sorted({x[0] for x in a});return [[key,sum(sorted([s for key2,s in a if key2==key],reverse=True)[:5])//5] for key in ids]
 if i==1122:
  b=args[1];return sorted(a,key=lambda x:(0,b.index(x)) if x in b else (1,x))
 raise ValueError(i)

def make_cases(i):
 rng=random.Random(SEED+i);out=[]
 text=lambda n,alphabet='abc':''.join(rng.choice(alphabet) for _ in range(n))
 for z in range(72):
  n=1+z%12
  if i==541:args=[text(n),1+z%15]
  elif i==599:
   vals=['w'+str(k) for k in range(12)];a=rng.sample(vals,1+z%10);b=rng.sample(vals,1+(z*3)%10);b=list(dict.fromkeys(b+[a[0]]));args=[a,b]
  elif i==645:
   n=max(2,n);a=list(range(1,n+1));missing,duplicate=rng.sample(a,2);a[missing-1]=duplicate;rng.shuffle(a);args=[a]
  elif i==682:
   ops=[];depth=0
   for _ in range(n):
    pool=['number']+(['C','D'] if depth else [])+(['+'] if depth>=2 else []);x=rng.choice(pool);ops.append(str(rng.randint(-30,30)) if x=='number' else x);depth+=-1 if x=='C' else 1
   args=[ops]
  elif i in [696,796,830,844,859,925]:
   a=text(n,'01' if i==696 else 'ab#' if i==844 else 'abc')
   if i in [696,830]:args=[a]
   elif i==796:args=[a,a[z%n:]+a[:z%n] if z%2 else text(n)]
   elif i==925:args=[a,''.join(c*rng.randint(1,3) for c in a) if z%2 else text(n)]
   else:args=[a,text(n,'ab#' if i==844 else 'abc')]
  elif i==697:args=[[rng.randint(-3,3) for _ in range(n)]]
  elif i==734:
   a=[text(2) for _ in range(n)];b=[x if rng.random()<.4 else text(2) for x in a];pairs=[[x,y] for x,y in zip(a,b) if rng.random()<.6];args=[a,b,pairs]
  elif i==748:
   plate=text(1+z%4,'abAB12 ');required=''.join(c.lower() for c in plate if c.isalpha());words=[text(n),required+'abc',required+'d'];args=[plate,words]
  elif i==806:args=[[rng.randint(1,10) for _ in range(26)],text(n*10,'abcd')]
  elif i==821:
   a=text(n);args=[a,rng.choice(a)]
  elif i==824:args=[' '.join(text(1+z%5,'abcAEiou') for _ in range(n))]
  elif i==893:args=[[text(1+z%6) for _ in range(n)]]
  elif i==914:args=[[rng.randint(0,5) for _ in range(n)]]
  elif i==917:args=[text(n,'abcXYZ-12!')]
  elif i==929:args=[[text(3)+'.'+text(2)+'+'+text(2)+'@'+rng.choice(['x.com','y.org']) for _ in range(n)]]
  elif i in [566,661,766,832,867,883,892]:
   nr=1+z%5;nc=nr if i in [832,883,892] else 1+(z*3)%5;a=[[rng.randint(0,1 if i==832 else 255 if i==661 else 5) for _ in range(nc)] for _ in range(nr)];args=[a]
   if i==566:args += [nc if z%2 else nr+1,nr]
  elif i in [896,908,977,1085]:
   a=[rng.randint(1,10000) if i==1085 else rng.randint(-10000,10000) for _ in range(n)];a=sorted(a,reverse=bool(z%2)) if i==896 and z%3 else sorted(a) if i==977 else a;args=[a]
   if i==908:args.append(rng.randint(0,10000))
  elif i==922:
   a=[2*rng.randint(0,1000) for _ in range(n)]+[2*rng.randint(0,1000)+1 for _ in range(n)];rng.shuffle(a);args=[a]
  elif i==942:args=[text(n,'ID')]
  elif i==944:args=[[text(n) for _ in range(1+z%6)]]
  elif i==976:args=[[rng.randint(1,1000000) for _ in range(n)]]
  elif i==1005:args=[[rng.randint(-100,100) for _ in range(1+z%5)],1+z%4]
  elif i==1013:args=[[rng.randint(-3,3) for _ in range(max(3,n))]]
  elif i==1018:args=[[rng.randint(0,1) for _ in range(n*10)]]
  elif i==1086:
   entries=[[key,rng.randint(0,100)] for key in range(1,1+z%4+1) for _ in range(5+z%5)];rng.shuffle(entries);args=[entries]
  elif i==1122:
   a=[rng.randint(0,20) for _ in range(n)];b=rng.sample(sorted(set(a)),1+z%len(set(a)));args=[a,b]
  else:raise ValueError(i)
  out.append({'args':args,'expected':oracle(i,args)})
 special={541:[['abcdefg',2],['a',100]],599:[[['a','b'],['b','a']]],645:[[[2,2]]],682:[[['5','2','C','D','+']]],696:[['00110011']],697:[[[1,2,2,3,1,4,2]]],734:[[['a','b'],['a'],[]]],748:[['1s3 PSt',['step','steps','stripe','stepple']]],796:[['a','b']],806:[[[10]*26,'a'*200]],821:[['a'*199+'b','b']],824:[['I speak Goat Latin']],830:[['aaa']],844:[['####','a#']],859:[['aa','aa'],['ab','ba']],893:[[['abc','acb','bac','bca','cab','cba']]],914:[[[1]],[[0]*1000]],917:[['a-bC-dEf-ghIj']],925:[['alex','aaleex']],929:[[['test.email+alex@leetcode.com','test.e.mail+bob@leetcode.com']]],566:[[[[1,2],[3,4]],1,4]],661:[[[[255]*20 for _ in range(20)]]],766:[[[[1,2,3],[4,1,2]]]],832:[[[[1]]]],867:[[[[1,2,3]]]],883:[[[[0,0],[0,0]]]],892:[[[[1]]]],896:[[[3,3,3]]],908:[[[0,10000],5000]],922:[[[2,1]]],942:[['I'*100]],944:[[['abc','abc']]],976:[[[1,2,3]],[[1000000]*5]],977:[[[-10000,0,10000]]],1005:[[[0],100]],1013:[[[0,0,0]],[[0,0,0,0]]],1018:[[[1]*1000]],1085:[[[10000,9999]]],1086:[[[[1000,100]]*5]],1122:[[[1000,0,1000,1],[0]]]}
 for args in special[i]:
  # Avoid exponential state enumeration for the degenerate large-k check.
  expected=0 if i==1005 and args==[[0],100] else oracle(i,args)
  out.append({'args':args,'expected':expected})
 return out

def output_ok(i,args,result,expected):
 if i==922:return isinstance(result,list) and collections.Counter(result)==collections.Counter(args[0]) and all(type(x) is int and x%2==j%2 for j,x in enumerate(result))
 if i==942:
  n=len(args[0]);return isinstance(result,list) and sorted(result)==list(range(n+1)) and all((result[j]<result[j+1])==(c=='I') for j,c in enumerate(args[0]))
 if i==599:return isinstance(result,list) and sorted(result)==expected
 return type(result)==type(expected) and result==expected
