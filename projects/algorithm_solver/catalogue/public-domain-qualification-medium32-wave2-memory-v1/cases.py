"""Deterministic newly authored public cases; never import hidden/developer tests."""
from itertools import product,permutations,combinations
import random
from oracle import IDS,expected

def build(_public=None):
 out={pid:[]for pid in IDS};seen={pid:set()for pid in IDS}
 def add(pid,args,origin='authored-exhaustive-small'):
  key=repr(args)
  if key not in seen[pid]:seen[pid].add(key);out[pid].append({'args':args,'expected':expected(pid,args),'origin':origin})
 examples={1567:[[[1,-2,-3,4]],[[0,1,-2,-3,-4]],[[-1,-2,-3,0,1]]],1573:[['10101'],['1001'],['0000']],1630:[[[4,6,5,9,3,7],[0,0,2],[2,3,5]],[[-12,-9,-3,-12,-6,15,20,-25,-20,-15,-10],[0,1,6,4,8,7],[4,4,9,7,9,10]]],1653:[['aababbab'],['bbaaaaabb']],1743:[[[[2,1],[3,4],[3,2]]],[[[4,-2],[1,4],[-3,1]]],[[[100000,-100000]]]],1817:[[[[0,5],[1,2],[0,2],[0,5],[1,3]],5],[[[1,1],[2,2],[2,3]],4]],1877:[[[3,5,2,3]],[[3,5,4,2,4,6]]],1887:[[[5,1,3]],[[1,1,1]],[[1,1,2,2,3]]]}
 for pid,rows in examples.items():
  for args in rows:add(pid,args,'official-public-example')
 for n in range(1,8):
  for xs in product((-1,0,1),repeat=n):add(1567,[list(xs)])
 for xs in([-10**9]*100000,[-10**9,0,10**9]*33333+[0],[10**9]*100000):add(1567,[xs],'authored-domain-boundary')
 for n in range(3,11):
  for bits in product('01',repeat=n):add(1573,[''.join(bits)])
 for s in('0'*100000,'1'*100000,'1'+'0'*49998+'1'+'0'*49999+'1'):add(1573,[s],'authored-domain-boundary')
 for n in range(2,6):
  qs=list(combinations(range(n),2));l=[a for a,b in qs];r=[b for a,b in qs]
  for xs in product((-1,0,2),repeat=n):add(1630,[list(xs),l,r])
 for xs in(list(range(500)),[100000]*500,[-100000,100000]*250):add(1630,[xs,[0]*500,[499]*500],'authored-domain-boundary')
 for n in range(1,11):
  for letters in product('ab',repeat=n):add(1653,[''.join(letters)])
 for s in('a'*100000,'b'*50000+'a'*50000,'ab'*50000):add(1653,[s],'authored-domain-boundary')
 for n in range(2,6):
  for xs in permutations(range(-n,0)):
   edges=[list(e)if i%2 else list(reversed(e))for i,e in enumerate(zip(xs,xs[1:]))]
   add(1743,[edges[::-1]])
 xs=list(range(-100000,0));add(1743,[[[a,b]for a,b in zip(xs,xs[1:])]],'authored-domain-boundary')
 options=[(0,1),(0,2),(1,1),(1,2)]
 for n in range(1,5):
  for logs in product(options,repeat=n):
   k=max(len({t for user,t in logs if user==u})for u in{u for u,t in logs})
   for width in(k,k+2):add(1817,[[list(r)for r in logs],width])
 for args in([[[7,i]for i in range(1,10001)],10000],[[[10**9-i,100000]for i in range(10000)],100000],[[[0,1]]*10000,1]):add(1817,args,'authored-domain-boundary')
 for n in(2,4,6):
  for xs in product((1,2,4),repeat=n):add(1877,[list(xs)])
 for xs in([100000]*100000,list(range(1,100001)),[1,100000]*50000):add(1877,[xs],'authored-domain-boundary')
 for n in range(1,7):
  for xs in product((1,2,3),repeat=n):add(1887,[list(xs)])
 for xs in(list(range(1,50001)),[50000]*50000):add(1887,[xs],'authored-domain-boundary')
 rng=random.Random(2026102502)
 for _ in range(50):
  n=rng.randrange(2,35);xs=[rng.randrange(-10**9,10**9+1)for _ in range(n)]
  add(1567,[xs],'authored-seeded');add(1653,[''.join(rng.choice('ab')for _ in range(n))],'authored-seeded')
  vals=rng.sample(range(-100000,100001),n);edges=[]
  for a,b in zip(vals,vals[1:]):edges.append([a,b]if rng.randrange(2)else[b,a])
  rng.shuffle(edges);add(1743,[edges],'authored-seeded')
 return out
