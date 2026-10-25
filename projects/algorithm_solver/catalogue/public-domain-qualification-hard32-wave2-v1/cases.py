"""Deterministic public synthetic cases, no imported tests or candidate execution."""
from itertools import product,permutations
import json,random
from oracle import IDS,expected

def build(public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS};r=random.Random(15151521)
 def add(pid,args,purpose):
  key=json.dumps(args,separators=(',',':'))
  if key not in seen[pid]:
   case={'args':args,'expected':expected(pid,args),'purpose':purpose}
   if pid==1515:case['singleton']=True
   out[pid].append(case);seen[pid].add(key)
 for points in ([[0,0]],[[100,100]],[[0,0],[100,100]],[[0,0],[0,100],[100,0]],[[0,0],[1,0],[100,1]],[[0,1],[1,0],[1,2],[2,1]],[[3,4]]*50,[[50,50]]*49+[[0,0]],[[i*2,50]for i in range(50)]):add(1515,[points],'analytic point/segment/triangle/symmetry geometric median')
 for _ in range(10):add(1515,[[[r.randrange(101),r.randrange(101)]for _ in range(3)]],'seeded analytic Fermat triangle, including obtuse')
 points=[]
 for _ in range(25):
  x,y=r.randrange(101),r.randrange(101);points.extend([[x,y],[100-x,100-y]])
 add(1515,[points],'maximum centrally symmetric50point optimum')
 for n in range(1,5):
  for xs in product((1,2,3),repeat=n):
   for t in(0,2,4):add(1521,[list(xs),t],'exhaustive small interval AND')
 add(1521,[[1000000]*100000,10000000],'maximum integer target and constant AND')
 add(1521,[[1,2]*50000,0],'maximum disjoint adjacent bits')
 for n in range(1,7):
  for s in product('012',repeat=n):add(1542,[''.join(s)],'exhaustive count-parity substrings')
 for s in('9'*100000,'0123456789'*10000):add(1542,[s],'maximum palindromizable full string')
 for n in range(1,5):
  for s in map(''.join,product('012',repeat=n)):
   candidates=sorted(set(map(''.join,permutations(s))))
   for t in candidates:add(1585,[s,t],'all multiset permutations and adjacent inversion reachability')
 add(1585,['0123','0124'],'different multiset')
 add(1585,['84532','34852'],'official multi-sort example')
 for s,t in(('9'*50000+'0'*50000,'0'*50000+'9'*50000),('0'*50000+'9'*50000,'9'*50000+'0'*50000),('0123456789'*10000,'0123456789'*10000)):add(1585,[s,t],'maximum sorted/identity invariant families')
 for n in range(1,5):
  for a in permutations(range(1,5),n):
   for _ in range(5):add(1713,[list(a),[r.randrange(1,6)for _ in range(r.randrange(1,8))]],'small full LCS dynamic table')
 add(1713,[list(range(1,100001)),list(range(100000,0,-1))],'maximum reversed unique target')
 add(1713,[list(range(1,100001)),list(range(1,100001))],'maximum exact subsequence')
 add(1713,[list(range(1,100001)),[10**9]*100000],'maximum disjoint values')
 for n in range(1,7):
  for _ in range(25):
   a=[r.randrange(1,n+1)for _ in range(n)]
   for k in range(1,n+1):add(2111,[a,k],'quadratic nondecreasing subsequence control')
 for k in(1,13,100000):add(2111,[list(range(100000,0,-1)),k],'maximum descending residue chains')
 add(2111,[[1]*100000,1],'maximum equal values must be nonstrict')
 for n in range(2,5):
  choices=[[j for j in range(n)if j!=i]for i in range(n)]
  for f in product(*choices):add(2127,[list(f)],'all small circular seating relations')
 for n in(5,6,7):
  for _ in range(12):
   f=[r.choice([j for j in range(n)if j!=i])for i in range(n)];add(2127,[f],'seeded exhaustive circular permutations')
 n=100000
 for f in(list(range(1,n))+[0],[i^1 for i in range(n)],[1,0]+[0]*(n-2),[1,0]+list(range(1,n-1))):add(2127,[f],'maximum known cycle/pairs/star/chain graph families')
 return out
