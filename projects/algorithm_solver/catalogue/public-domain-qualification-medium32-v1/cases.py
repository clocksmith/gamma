"""New deterministic host-authored cases; no hidden/developer test imports."""
from itertools import product,combinations
import random
from oracle import IDS,expected

def build(_public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS}
 def add(pid,args,kind='authored-exhaustive-small'):
  key=repr(args)
  if key not in seen[pid]:seen[pid].add(key);out[pid].append({'args':args,'expected':expected(pid,args),'origin':kind})
 examples={1248:[[[1,1,2,1,1],3],[[2,4,6],1],[[2,2,2,1,2,2,1,2,2,2],2]],1319:[[4,[[0,1],[0,2],[1,2]]],[6,[[0,1],[0,2],[0,3],[1,2],[1,3]]],[6,[[0,1],[0,2],[0,3],[1,2]]]],1338:[[[3,3,3,3,5,5,5,2,2,7]],[[7,7,7,7,7,7]]],1400:[['annabelle',2],['leetcode',3],['true',4]],1466:[[6,[[0,1],[1,3],[2,3],[4,0],[4,5]]],[5,[[1,0],[1,2],[3,2],[3,4]]],[3,[[1,0],[2,0]]]],1471:[[[1,2,3,4,5],2],[[1,1,3,5,5],2],[[6,7,11,7,6,8],5]],1482:[[[1,10,3,10,2],3,1],[[1,10,3,10,2],3,2],[[7,7,7,7,12,7,7],2,3]],1540:[['input','ouput',9],['abc','bcd',10],['aab','bbb',27]]}
 for pid,rows in examples.items():
  for args in rows:add(pid,args,'official-public-example')
 for n in range(1,7):
  for xs in product((1,2),repeat=n):
   for k in range(1,n+1):add(1248,[list(xs),k])
 for args in([[1]*50000,1],[[2]*50000,50000],[[1,100000]*25000,12345]):add(1248,args,'authored-domain-boundary')
 for n in range(2,6):
  edges=list(combinations(range(n),2))
  for mask in range(1,1<<len(edges)):add(1319,[n,[list(e)for i,e in enumerate(edges)if mask>>i&1]])
 add(1319,[100000,[[i,i+1]for i in range(99999)]+[[0,99999]]],'authored-domain-boundary')
 add(1319,[100000,[[0,1]]],'authored-domain-boundary')
 for n in(2,4,6):
  for xs in product((1,2,3),repeat=n):add(1338,[list(xs)])
 for xs in([100000]*100000,list(range(1,100001)),[1]*50000+list(range(2,50002))):add(1338,[xs],'authored-domain-boundary')
 for n in range(1,5):
  for letters in product('abc',repeat=n):
   for k in range(1,n+2):add(1400,[''.join(letters),k])
 for args in(['a'*100000,1],['a'*99999+'b',1],['a'*100000,100000],['a',100000]):add(1400,args,'authored-domain-boundary')
 for n in range(2,5):
  for parents in product(*[range(i)for i in range(1,n)]):
   base=[(i+1,p)for i,p in enumerate(parents)]
   for flip in product((0,1),repeat=n-1):add(1466,[n,[[v,u]if b else[u,v]for(u,v),b in zip(base,flip)]])
 add(1466,[50000,[[i,i+1]for i in range(49999)]],'authored-domain-boundary')
 add(1466,[50000,[[i,0]for i in range(1,50000)]],'authored-domain-boundary')
 for n in range(1,6):
  for xs in product((-2,0,2),repeat=n):
   for k in range(1,n+1):add(1471,[list(xs),k])
 add(1471,[list(range(-50000,50000)),100000],'authored-domain-boundary')
 add(1471,[[100000,-100000]*50000,1],'authored-domain-boundary')
 for n in range(1,5):
  for xs in product((1,2,4),repeat=n):
   for k in range(1,n+1):
    for m in range(1,4):add(1482,[list(xs),m,k])
 for args in([[10**9]*100000,1,100000],[list(range(100000,0,-1)),50000,2],[[1],1000000,1],[[1,10**9]*50000,50001,1]):add(1482,args,'authored-domain-boundary')
 for n in range(1,4):
  words=[''.join(x)for x in product('az',repeat=n)]
  for s,t in product(words,repeat=2):
   for k in(0,1,25,26,27,51,52):add(1540,[s,t,k])
 for args in(['a','aa',10**9],['z'*100000,'a'*100000,2599975],['z'*100000,'a'*100000,2599974],['a'*100000,'z'*100000,10**9],['a'*100000,'a'*100000,0]):add(1540,args,'authored-domain-boundary')
 rng=random.Random(20261025)
 for _ in range(60):
  n=rng.randrange(2,40);xs=[rng.randrange(1,100001)for _ in range(n)]
  add(1248,[xs,rng.randrange(1,n+1)],'authored-seeded')
  add(1471,[[x-50000 for x in xs],rng.randrange(1,n+1)],'authored-seeded')
  add(1482,[xs,rng.randrange(1,n+2),rng.randrange(1,n+1)],'authored-seeded')
  edges=[]
  for i in range(1,n):
   e=[i,rng.randrange(i)];edges.append(e if rng.randrange(2)else e[::-1])
  rng.shuffle(edges);add(1466,[n,edges],'authored-seeded')
 return out
