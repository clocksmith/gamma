"""Frozen-rule synthetic domains, authored independently of candidate source/tests."""
from itertools import product
import random,json
from oracle import IDS,expected

def build(public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS};rng=random.Random(18941976)
 def add(pid,args,purpose):
  key=json.dumps(args,separators=(',',':'))
  if key not in seen[pid]:out[pid].append({'args':args,'expected':expected(pid,args),'purpose':purpose});seen[pid].add(key)
 for n in range(1,5):
  for xs in product((1,2,3),repeat=n):
   for k in (1,sum(xs),sum(xs)+1,2*sum(xs)-1):add(1894,[list(xs),k],'strict exhaustion and wrap boundary')
 for a,k in [([1]*100000,10**9),([100000]*100000,10**9)]:add(1894,[a,k],'maximum independent uniform family')
 for n in range(1,7):
  for xs in product((1,2),repeat=n):add(1911,[list(xs)],'exhaustive subsequence selection')
 for a in [list(range(1,100001)),list(range(100000,0,-1)),[100000,1]*50000]:add(1911,[a],'maximum analytic subsequence family')
 for n in range(1,7):
  for _ in range(24):add(1921,[[rng.randrange(1,12)for _ in range(n)],[rng.randrange(1,5)for _ in range(n)]],'all shot orders independent oracle')
 for d,s in [([1,3,4],[1,1,1]),([1,1,2,3],[1]*4),([100000]*100000,[1]*100000),([1]*100000,[100000]*100000)]:add(1921,[d,s],'deadline equality and maximum families')
 for n in range(1,5):
  for xs in product((1,2,3),repeat=n):add(1953,[list(xs)],'complete nonrepeating schedule search')
 for a in [[10**9],[10**9]*100000,[10**9,1,1]]:add(1953,[a],'64bit-safe totals and separator bound')
 add(1976,[1,[]],'single intersection empty walk')
 for n in range(2,8):
  for _ in range(12):
   roads=[[i-1,i,rng.randrange(1,6)]for i in range(1,n)]
   for u in range(n):
    for v in range(u+2,n):
     if rng.randrange(2):roads.append([u,v,rng.randrange(1,10)])
   add(1976,[n,roads],'independent Floyd distance and positive-edge DAG counting')
 add(1976,[200,[[i-1,i,10**9]for i in range(1,200)]],'maximum path weights beyond signed32')
 add(1976,[200,[[i,j,1]for i in range(200)for j in range(i+1,200)]],'maximum complete graph')
 # Layered binary choices give 2**30 shortest routes, exercising modulo.
 layers=[[0]]+[[2*i-1,2*i]for i in range(1,31)]+[[61]]
 add(1976,[62,[[u,v,1]for left,right in zip(layers,layers[1:])for u in left for v in right]],'modulo many equal shortest paths')
 for n in range(1,5):
  for xs in product((1,2,3),repeat=n):
   for cap in(max(xs),sum(xs),max(xs)+1):add(2079,[list(xs),cap],'explicit river route, exact remaining-water boundary')
 for a,cap in [([10**6]*1000,10**6),([10**6]*1000,10**9)]:add(2079,[a,cap],'maximum steps and capacity')
 for n in range(1,6):
  for _ in range(25):add(2131,[[rng.choice(['aa','ab','ba','bb'])for _ in range(n)]],'enumerated concatenations, duplicate multiplicity')
 for a in [['aa']*100000,['ab']*100000,['ab']*50000+['ba']*50000,['ab']*99999+['ba']]:add(2131,[a],'maximum repeated and paired families')
 words=['a','b','c','ab','ac','bc','abc']
 for _ in range(160):add(2135,[[rng.choice(words)for _ in range(rng.randrange(1,8))],[rng.choice(words)for _ in range(rng.randrange(1,8))]],'independent strict subset relation and duplicate targets')
 for a,b in [(['abcdefghijklmnopqrstuvwxy']*50000,['abcdefghijklmnopqrstuvwxyz']),(['abcdefghijklmnopqrstuvwxy'],['abcdefghijklmnopqrstuvwxyz']*50000),(['abcdefghijklmnopqrstuvwxyz']*50000,['abcdefghijklmnopqrstuvwxyz']),(['a'],['a','ab','ab'])]:add(2135,[a,b],'maximum lengths, duplicates, mandatory new letter')
 return out
