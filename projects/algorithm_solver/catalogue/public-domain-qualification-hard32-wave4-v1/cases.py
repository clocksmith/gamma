"""Deterministic finite fixtures authored before candidate inspection."""
import json,random
from itertools import product
from oracle import IDS,expected

def build(public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS};rng=random.Random(27093130)
 def add(pid,args,purpose):
  key=json.dumps(args,separators=(',',':'))
  if key not in seen[pid]:
   case={'args':args,'expected':expected(pid,args),'purpose':purpose}
   if pid==3130:case['singleton']=True
   out[pid].append(case);seen[pid].add(key)
 for n in range(1,5):
  for a in product((1,2,3,6),repeat=n):add(2709,[list(a)],'all small pair-GCD connectivity graphs')
 for v in(1,2,99991,100000):add(2709,[[v]*100000],'maximum homogeneous connectivity')
 words=[''.join(x)for n in range(1,7)for x in product('ab',repeat=n)]
 for _ in range(200):add(2781,[rng.choice(words),[rng.choice(words[:30])for _ in range(rng.randrange(1,8))]],'all-substring forbidden containment')
 for f in(['a'],['a'*10],['b'*10],['b']*100000):add(2781,['a'*100000,f],'maximum word and repeated maximum forbidden count')
 for n in range(1,7):
  for _ in range(30):
   s=''.join(rng.choice('abcxyz')for _ in range(n));add(2953,[s,rng.randrange(1,n+1)],'independent interval histogram and adjacency constraints')
 for k in(1,2,99999,100000):add(2953,['z'*100000,k],'maximum homogeneous complete intervals')
 for n in range(1,6):
  for _ in range(20):
   s=''.join(rng.choice('abc')for _ in range(n))
   for k in(1,2,3,26):add(3003,[s,k],'all26 replacements at every index, explicit longest-prefix partitioning')
 for s,k in(('a'*10000,1),('a'*10000,2),('ab'*5000,1),('abcdefghijklmnopqrstuvwxyz'*384+'abcd',26)):add(3003,[s,k],'maximum fixed-family partition proofs')
 for n in range(1,8):
  for _ in range(25):add(3041,[[rng.randrange(1,8)for _ in range(n)]],'all increment masks and maximal distinct runs')
 for a in([1000000]*100000,list(range(1,100001)),list(range(1,300001,3))):add(3041,[a],'maximum duplicate/consecutive/separated families')
 for _ in range(160):add(3093,[[rng.choice(words)for _ in range(rng.randrange(1,9))],[rng.choice(words)for _ in range(rng.randrange(1,9))]],'pairwise suffix lengths, shortest word and first-index tie')
 add(3093,[['abcd','bcd','xbcd'],['cd','bcd','xyz']],'official suffix tie hierarchy')
 add(3093,[['a'*50]*10000,['a'*50]*10000],'both total-length and word-count maximums with duplicate tie')
 add(3093,[['a'*5000,'b'],['c'*4999+'a','z'*5000]],'maximum individual word length')
 for z in range(1,9):
  for o in range(1,9):
   for limit in range(1,6):add(3130,[z,o,limit],'independent bounded-composition inclusion-exclusion over alternating runs')
 for args in([1000,1000,1],[1000,999,1],[999,1000,1],[1000,1000,2],[1000,1000,500],[1000,1000,1000],[1,1000,1000],[1000,1,1000]):add(3130,list(args),'maximum count/limit and modular combinatorial controls')
 return out
