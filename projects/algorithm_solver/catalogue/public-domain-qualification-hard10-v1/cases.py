"""New deterministic public-domain Hard10 cases, never imported historical tests."""
from itertools import product,combinations
from oracle import IDS,expected
import json

def build(public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS}
 def add(pid,args,purpose):
  key=json.dumps(args,separators=(',',':'))
  if key not in seen[pid]:out[pid].append({'args':args,'expected':expected(pid,args),'purpose':purpose});seen[pid].add(key)
 strings=[''.join(v)for n in range(1,4)for v in product('ab',repeat=n)]
 patterns=[''.join(v)for n in(1,2)for v in product(('a','b','.','a*','b*','.*'),repeat=n)]
 for s,p in product(strings,patterns):add(10,[s,p],'NFA whole-string semantics')
 for n in range(1,6):
  for xs in product((0,1,3),repeat=n):
   for pid in(42,84,123):add(pid,[list(xs)],'exhaustive short ternary arrays')
 for cells in product('01',repeat=6):add(85,[[list(cells[:3]),list(cells[3:])]],'all two-by-three binary rectangles')
 for n in range(1,7):
  for xs in product((1,2),repeat=n):add(546,[list(xs)],'enumerate all same-color contiguous removals')
 for n in range(1,301):add(564,[str(n)],'nearest integer outward search')
 for n in range(1,5):
  for xs in product(range(1,min(n,3)+1),repeat=n):
   for k in range(1,n+1):add(992,[list(xs),k],'all distinct-count subarrays')
 for cells in product((-1,0,1),repeat=4):
  for target in(-2,-1,0,1,2):add(1074,[[list(cells[:2]),list(cells[2:])],target],'all two-by-two ternary submatrices')
 for a in product((0,1,2),repeat=3):
  for size in range(1,4):
   for b in combinations((0,1,2),size):add(1187,[list(a),list(b)],'exhaustive replacement-value products')
 add(10,['a'*20,'a*'*10],'maximum regex lengths repeated starred atom')
 add(10,['a'*19+'b','a*'*9+'b*'],'maximum regex length late different character')
 add(42,[[100000]+[0]*19998+[100000]],'maximum deep basin')
 add(84,[[10000]*100000],'maximum uniform histogram exact safe integer area')
 for value in('0','1'):add(85,[[[value]*200 for _ in range(200)]],'maximum uniform binary matrix')
 add(123,[[0,100000]*50000],'maximum alternating stock profits')
 add(546,[[1]*100],'maximum uniform boxes')
 add(546,[list(range(1,101))],'maximum all-distinct boxes')
 for n in('9'*18,'1'+'0'*17,'1'+'0'*16+'1'):add(564,[n],'maximum digit exact-integer boundary')
 add(992,[[1]*20000,1],'maximum uniform all-subarray count')
 add(992,[list(range(1,20001)),10000],'maximum all-distinct exact-width count')
 add(1074,[[[0]*100 for _ in range(100)],0],'maximum all-zero rectangle count')
 add(1074,[[[0]*100 for _ in range(100)],10**8],'maximum unattainable positive target')
 add(1187,[[0]*2000,list(range(2000))],'maximum increasing replacement chain')
 add(1187,[[10**9]*2000,[0]*2000],'maximum impossible repeated constants')
 return out
