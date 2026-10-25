"""Deterministic independent public cases. No original developer tests imported."""
from itertools import product,combinations
from oracle import IDS,expected

def build(public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS}
 def add(pid,args,purpose):
  import json
  key=json.dumps(args,separators=(',',':'))
  if key not in seen[pid]:out[pid].append({'args':args,'expected':expected(pid,args),'purpose':purpose});seen[pid].add(key)
 for n in (1,2,3):
  for mask in range(1,1<<(n*n)):add(802,[[[j for j in range(n)if mask>>(i*n+j)&1]for i in range(n)]],'all directed graphs through three vertices')
 for fuel in range(1,5):
  for amounts in product((1,2,4),repeat=3):add(871,[8,fuel,[[2,amounts[0]],[4,amounts[1]],[6,amounts[2]]]],'independent stop-count DP')
 add(871,[100,10,[[10,60],[20,30],[30,30],[60,40]]],'multiple reachable choices')
 for values in product((1,2,5),repeat=3):
  for h in range(3,9):add(875,[list(values),h],'enumerated feasible speeds')
 for n in range(1,5):
  for xs in product((1,2,4),repeat=n):
   for limit in (0,1,3):add(1438,[list(xs),limit],'all contiguous subarrays oracle')
 for n in range(2,9):
  for size in range(1,min(4,n-1)+1):
   for cuts in combinations(range(1,n),size):add(1547,[n,list(reversed(cuts))],'exhaustive cut orders independent of interval DP')
 for parents in product(range(3),repeat=2):
  p=[-1,*parents]
  if p[1]==1 or p[2]==2 or (p[1]==2 and p[2]==1):continue
  for s in map(''.join,product('ab',repeat=3)):add(2246,[p,s],'rooted trees with non-topological vertex IDs')
 intervals=[[1,1],[1,2],[2,2],[2,3],[3,3]]
 for rows in product(intervals,repeat=3):add(2406,[[r.copy()for r in rows]],'closed-interval overlap at all left endpoints')
 for ws in product(('a','b','aa','ab','ba'),repeat=3):add(2416,[list(ws)],'pairwise LCP sums including duplicates')
 add(802,[[[i+1]if i<9999 else []for i in range(10000)]],'maximum-depth DAG')
 add(802,[[[i+1]if i<9999 else [0]for i in range(10000)]],'maximum-depth cycle')
 add(802,[[sorted((i+j)%10000 for j in range(4))for i in range(10000)]],'maximum edge count with self-loops')
 add(871,[10**9,1,[[i+1,10**9-1]for i in range(500)]],'maximum station count exact large fuel sums')
 add(875,[[10**9]*10000,10000],'maximum pile count minimum allowed hours')
 add(875,[[10**9]*10000,10**9],'maximum hours and exact non-int32 arithmetic')
 add(1438,[[1]*100000,0],'maximum uniform window')
 add(1438,[list(range(1,100001)),12345],'maximum monotone window')
 add(1438,[[1,10**9]*50000,0],'maximum alternating singleton windows')
 add(1547,[101,list(range(1,101))],'maximum cut count equal unit leaves exact optimal-depth formula')
 add(1547,[10**6,[1,999999]],'maximum stick length')
 add(2246,[[-1]+list(range(99999)),'ab'*50000],'maximum alternating chain')
 add(2246,[[-1]+[0]*99999,'a'+'b'*99999],'maximum unequal star')
 add(2406,[[[1,10**6]for _ in range(100000)]],'maximum all-overlapping intervals')
 add(2406,[[[2*i+1,2*i+1]for i in range(100000)]],'maximum disjoint point intervals')
 add(2416,[['a'*1000]*1000],'maximum total characters duplicated full prefixes')
 return out
