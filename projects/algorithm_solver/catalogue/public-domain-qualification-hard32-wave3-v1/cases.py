"""Deterministic authored fixtures independent of owner source bytes."""
from itertools import product
import json,random
from oracle import IDS,expected,lcp_matrix,beautiful

def build(public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS};rng=random.Random(21322569)
 def add(pid,args,purpose):
  key=json.dumps(args,separators=(',',':'))
  if key not in seen[pid]:out[pid].append({'args':args,'expected':expected(pid,args),'purpose':purpose});seen[pid].add(key)
 for m,n in((1,1),(1,3),(2,2),(2,3)):
  for cells in product((0,1),repeat=m*n):
   grid=[list(cells[i*n:(i+1)*n])for i in range(m)]
   for h,w in((1,1),(1,2),(2,1),(2,2),(3,3)):add(2132,[grid,h,w],'all small placement unions and oversized stamps')
 for grid,h,w in([[[0]*100000],1,100000],[[[1]*100000],100000,100000],[[[0]*200 for _ in range(1000)],1,1]):
  add(2132,[grid,h,w],'maximum-area homogeneous placement proof')
 for m,n in((1,1),(1,4),(2,2),(2,3),(3,3)):
  for cells in product('()',repeat=m*n):add(2267,[[list(cells[i*n:(i+1)*n])for i in range(m)]],'all small monotone path balance states')
 add(2267,[[['(']*100 for _ in range(100)]],'maximum grid impossible final balance')
 for m,n in((1,2),(1,5),(2,2),(2,3),(3,3)):
  for inner in product((0,1),repeat=m*n-2):
   cells=(0,)+inner+(0,);add(2290,[[list(cells[i*n:(i+1)*n])for i in range(m)]],'all small weighted paths independent heap search')
 add(2290,[[[0]*100000]],'maximum single corridor')
 for n in range(2,8):
  for _ in range(25):add(2426,[[rng.randrange(-5,6)for _ in range(n)],[rng.randrange(-5,6)for _ in range(n)],rng.randrange(-5,6)],'direct pair inequality with negative and ties')
 for d in(-10000,0,10000):add(2426,[[10000]*100000,[-10000]*100000,d],'maximum length counts beyond32bits')
 words=[''.join(x)for n in range(1,5)for x in product('ab',repeat=n)]
 for _ in range(180):add(2565,[rng.choice(words),rng.choice(words)],'all contiguous deletion spans and subsequence scan')
 for a,b in(('a'*100000,'a'*100000),('a'*100000,'z'*100000)):add(2565,[a,b],'maximum equality/disjoint exact proof')
 for n in range(1,9):
  for _ in range(15):
   qs=[]
   for j in range(15):
    op=rng.randrange(1,4)
    if op==1:l=rng.randrange(n);q=[op,l,rng.randrange(l,n)]
    elif op==2:q=[op,rng.choice([0,1,1000000]),0]
    else:q=[op,0,0]
    qs.append(q)
   qs.append([3,0,0]);add(2569,[[rng.randrange(2)for _ in range(n)],[rng.choice([0,1,10**9])for _ in range(n)],qs],'explicit per-element state transitions')
 add(2569,[[1]*100000,[0]*100000,[[2,1000000,0]]*91997+[[3,0,0],[2,1,0],[3,0,0]]],'large representable exact integer totals above2**53 and low-bit update')
 for n in range(1,7):
  for _ in range(8):
   s=''.join(rng.choice('abc')for _ in range(n));a=lcp_matrix(s);add(2573,[a],'independent restricted-growth partition enumeration')
   b=[r[:]for r in a];i=rng.randrange(n);j=rng.randrange(n);b[i][j]=rng.randrange(n+1);add(2573,[b],'perturbed consistency matrices')
 for n in(26,27,100):add(2573,[[[n-i if i==j else 0 for j in range(n)]for i in range(n)]],'alphabet exhaustion and unique-symbol diagonal proof')
 add(2573,[lcp_matrix('a'*100)],'representable repeated-symbol suffix matrix')
 for n in range(1,6):
  for s in map(''.join,product('abcd',repeat=n)):
   if beautiful(s):add(2663,[s,4],'all small beautiful strings and lexicographic successor')
 for s in('z','yz','xyz','zyx','abcdabcd'):add(2663,[s,26],'maximum alphabet and successor carry')
 return out
