"""Synthetic bounded exhaustive-small cases and maximum-shape fixtures."""
from itertools import product
from oracle import IDS,expected

def build(_public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS}
 def add(pid,args):
  key=repr(args)
  if key not in seen[pid]:seen[pid].add(key);out[pid].append({'args':args,'expected':expected(pid,args)})
 for n in range(1,501):
  if '0'not in str(n):add(2520,[n])
 for n in(111111111,999999999,123456789):add(2520,[n])
 for n in list(range(1,401))+[999,1000,10001,99999999,10**8,90909,11891]:add(2566,[n])
 arrays=[list(xs)for n in range(1,4)for xs in product((2,3,6),repeat=n)]
 for xs in arrays:
  for ds in arrays:add(2644,[xs,ds])
 add(2644,[[10**9]*1000,list(range(1,1001))]);add(2644,[[999999937]*1000,[10**9]*1000])
 for main,extra in product(range(1,21),repeat=2):add(2739,[main,extra])
 for main,extra in product((1,4,5,99,100),repeat=2):add(2739,[main,extra])
 for n in range(1,6):
  for xs in product((1,2,3),repeat=n):add(2778,[list(xs)])
 add(2778,[list(range(1,51))]);add(2778,[[50]*50])
 for n in range(1,4):
  for ws in product(('a','b','ab','ba'),repeat=n):
   for s in('a','b','ab','ba','aaa'):add(2828,[list(ws),s])
 add(2828,[['a'*10]*100,'a'*100])
 intervals=[[a,b]for a in range(1,4)for b in range(a,4)]
 for n in range(1,4):
  for rows in product(intervals,repeat=n):add(2848,[[list(r)for r in rows]])
 add(2848,[[[i,i]for i in range(1,101)]]);add(2848,[[[1,100]]*100])
 for n in range(1,5):
  for xs in product(range(4),repeat=n):
   for k in range(1,n+1):add(2917,[list(xs),k])
 for xs in([2**31-1]*50,[2**30,0]*25,list(range(50))):
  for k in(1,25,50):add(2917,[xs,k])
 return out
