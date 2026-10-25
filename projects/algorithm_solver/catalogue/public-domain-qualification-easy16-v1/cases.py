"""Authored deterministic public cases, not imported developer/benchmark tests."""
from itertools import product,combinations
from oracle import IDS,expected

def build(_public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS}
 def add(pid,args):
  key=repr(args)
  if key not in seen[pid]:seen[pid].add(key);out[pid].append({'args':args,'expected':expected(pid,args)})
 for t in range(1001):add(3894,[t])
 for n in range(1,5):
  edges=list(combinations(range(n),2))
  for values in product((0,1),repeat=len(edges)):
   m=[[0]*n for _ in range(n)]
   for (i,j),v in zip(edges,values):m[i][j]=m[j][i]=v
   add(3898,[m])
 add(3898,[[[int(i!=j)for j in range(100)]for i in range(100)]])
 for n in range(1,5):
  for xs in product((0,1,3),repeat=n):
   for k in(0,1,3):add(3903,[list(xs),k])
 add(3903,[[10**9-i for i in range(100)],0]);add(3903,[[0,10**9]*50,10**9])
 for n in list(range(101))+[1000,10001,10101,99999,100000]:
  for x in range(10):add(3908,[n,x])
 for n in range(1,5):
  for xs in product((1,2,3),repeat=n):
   for pid in(3912,3917,3925):add(pid,[list(xs)])
 for pid in(3912,3917,3925):
  for xs in([1]*100,list(range(1,101)),list(range(100,0,-1)),[1,100]*50):add(pid,[xs])
 for n in range(1,4):
  for events in product(('0','6','W','WD','NB'),repeat=n):add(3921,[list(events)])
 for events in([ '6']*1000,['W']*1000,['W']*9+['6','WD','NB','W','6'],['NB','WD']*500):add(3921,[events])
 for n in(2,3):
  for digits in product('01239',repeat=n):add(3931,[''.join(digits)])
 for s in('0123456789'*10,'9'*100,'0909'*25):add(3931,[s])
 for n in range(1,7):
  for bits in product((0,1),repeat=n):add(3936,[list(bits)])
 for xs in([0]*100,[100]*100,[0,100]*50,[0]*50+[100]*50):add(3936,[xs])
 for n in range(1,6):
  for s in range(101):add(4000,[n,s])
 for n in range(1,7):
  for bits in product('01',repeat=n):add(4006,[''.join(bits)])
 for s in('0'*100,'1'*100,'01'*50,'0'*50+'1'*50):add(4006,[s])
 for n in range(2,5):
  for xs in product((1,2,3,6),repeat=n):add(4010,[list(xs)])
 for xs in([100000]*2000,[99991,100000]*1000,[1,100000]+[2]*1998):add(4010,[xs])
 for floors in range(1,5):
  for n in range(1,4):
   for req in product(range(floors),repeat=n):add(4020,[floors,list(req)])
 add(4020,[100,[0,99]*50])
 drones=[[0,0,1],[1,0,1],[-1,0,1],[25,25,1],[-25,-25,100]]
 for n in range(1,4):
  for ds in product(drones,repeat=n):
   for target in([0,0],[25,-25]):add(4024,[[list(d)for d in ds],target])
 add(4024,[[[25,25,100]for _ in range(100)],[-25,-25]])
 for n in range(1,4):
  for letters in product('abfz',repeat=n):add(4030,[''.join(letters)])
 for s in('a'*100,'abcdefghijklmnopqrstuvwxyz'*3+'a'*22):add(4030,[s])
 return out
