"""Deterministic synthetic fixtures; no imported owner/developer/private cases."""
from itertools import product
from oracle import IDS,expected,validate

def build(_public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS}
 def add(pid,args):
  key=repr(args)
  if key not in seen[pid]:seen[pid].add(key);out[pid].append({'args':args,'expected':expected(pid,args)})
 for n in list(range(2,302))+[999,1000,1001,9999,10000]:add(1317,[n])
 for m in range(1,4):
  for n in range(1,4):
   for flat in product((-1,0,1),repeat=m*n):
    grid=[list(flat[i*n:(i+1)*n])for i in range(m)]
    try:validate(1351,[grid])
    except ValueError:continue
    add(1351,[grid])
 for g in([[-100]*100 for _ in range(100)],[[100]*100 for _ in range(100)],[[100-i-j for j in range(100)]for i in range(100)]):add(1351,[g])
 for n in range(1,4):
  for xs in product((1,2),repeat=2*n):add(1470,[list(xs),n])
 add(1470,[list(range(1,1001)),500])
 for n in list(range(201))+[999,1000,1001,999999,1000000,1000001,2**31-1]:add(1556,[n])
 for n in range(1,6):
  for ops in product(('../','./','a/'),repeat=n):add(1598,[list(ops)])
 for ops in(['abcdefghi/']*1000,['../']*1000,['a1/','../']*500,['0/','./']*500):add(1598,[ops])
 for n in range(1,1001):add(1716,[n])
 for n in range(1,6):
  for xs in product((1,2,3),repeat=n):add(1800,[list(xs)])
 for xs in(list(range(1,101)),list(range(100,0,-1)),[100]*100,[1,100]*50):add(1800,[xs])
 intervals=[[a,b]for a in range(1950,1954)for b in range(a+1,1954)]
 for n in range(1,4):
  for logs in product(intervals,repeat=n):add(1854,[[[a,b]for a,b in logs]])
 for logs in([ [1950,2050]]*100,[[y,y+1]for y in range(1950,2050)],[[1950,1951],[2049,2050]]):add(1854,[logs])
 return out
