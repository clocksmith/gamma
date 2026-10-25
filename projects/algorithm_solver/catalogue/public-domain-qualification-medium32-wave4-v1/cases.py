"""Deterministic authored fixtures; no candidate or private test access."""
from itertools import product
import json,random
from oracle import IDS,expected

def build(public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS};rng=random.Random(21702602)
 def add(pid,args,purpose):
  key=json.dumps(args,separators=(',',':'))
  if key not in seen[pid]:out[pid].append({'args':args,'expected':expected(pid,args),'purpose':purpose});seen[pid].add(key)
 for n in range(1,6):
  for x in product((1,2,3),repeat=n):add(2170,[list(x)],'enumerate two distinct target values including unused values')
 add(2170,[[100000]*100000],'maximum constant parity conflict')
 for n in range(1,5):
  for x in product('ab',repeat=n):
   for y in('a','b','ab','bbaa'):add(2186,[''.join(x),y],'sorted matching multiplicity')
 add(2186,['a'*200000,'z'*200000],'both maximum length disjoint strings')
 add(2186,['ab'*100000,'ba'*100000],'both maximum length equal multisets')
 for n in range(1,6):
  for x in product((0,1,3),repeat=n):add(2256,[list(x)],'independent slice averages, floor and first-tie')
 for value in(0,100000):add(2256,[[value]*100000],'maximum homogeneous averages')
 for n in range(1,5):
  for x in product((0,1,3),repeat=n):add(2433,[list(x)],'independent per-bit triangular system')
 add(2433,[[1000000,0]*50000],'maximum list and bit values')
 for n in range(1,6):
  for _ in range(20):add(2587,[[rng.randrange(-3,4)for _ in range(n)]],'complete permutation objective')
 for x in([1000000]*100000,[-1000000]*100000,[0]*100000):add(2587,[x],'maximum positive/negative/zero families')
 for n in range(1,7):
  for _ in range(20):add(2597,[[rng.randrange(1,8)for _ in range(n)],rng.randrange(1,5)],'index-subset conflict masks, duplicate multiplicity')
 for a,k in [([1000]*18,1000),(list(range(1,19)),1),([1,2]*9,1)]:add(2597,[a,k],'maximum18 index subsets')
 for n in range(1,6):
  for _ in range(25):add(2602,[[rng.randrange(1,10)for _ in range(n)],[rng.randrange(1,12)for _ in range(4)]],'direct absolute differences, queries independently reset')
 add(2602,[[1]*100000,[1]*100000],'both maximum lengths, representable complete packet')
 add(2602,[[10**9]*100000,[1,10**9]],'maximum values/n and1e14safe result')
 add(2602,[[1],[10**9]*100000],'maximum query count and values')
 for n in range(1,7):
  for _ in range(35):add(2860,[[rng.randrange(n)for _ in range(n)]],'selected-index subsets and strict happiness inequalities')
 for x in([0]*100000,[99999]*100000):add(2860,[x],'maximum forced-all and zero-or-all family')
 return out
