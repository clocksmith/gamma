"""Deterministic synthetic finite cases, separate from incoming sources."""
from itertools import product,combinations
from oracle import IDS,expected

def build(_public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS}
 def add(pid,args):
  key=repr(args)
  if key not in seen[pid]:seen[pid].add(key);out[pid].append({'args':args,'expected':expected(pid,args)})
 for n in range(1,5):
  for chars in product('ab',repeat=n):
   for k in range(1,6):
    for fill in 'az':add(2138,[''.join(chars),k,fill])
 add(2138,['a'*100,99,'z']);add(2138,['a',100,'z'])
 subsets=[list(s)for n in range(1,4)for s in combinations((1,2,3),n)]
 for n in range(1,4):
  for rows in product(subsets,repeat=n):add(2248,[[list(r)for r in rows]])
 add(2248,[[[1]for _ in range(1000)]]);add(2248,[[list(range(1,1001))]])
 for n in range(2,6):
  for chars in product('abc',repeat=n):
   s=''.join(chars)
   if len(set(s))<len(s):add(2351,[s])
 add(2351,['abcdefghijklmnopqrstuvwxyz'+'z'*74])
 for n in range(1,4):
  for es in product((1,3),repeat=n):
   for xs in product((1,3),repeat=n):
    for e,x in product((1,4),repeat=2):add(2383,[e,x,list(es),list(xs)])
 add(2383,[1,1,[100]*100,[100]*100]);add(2383,[100,100,[1]*100,[1]*100])
 for n in range(1,4):
  for ids in product(range(3),repeat=n):
   if any(a==b for a,b in zip(ids,ids[1:])):continue
   for durations in product((1,2),repeat=n):
    ends=[];total=0
    for d in durations:total+=d;ends.append(total)
    add(2432,[3,[[i,t]for i,t in zip(ids,ends)]])
 add(2432,[500,[[i%2,i+1]for i in range(500)]]);add(2432,[500,[[499,500]]])
 for n in range(3,6):
  for xs in product((1,2,3),repeat=n):add(2475,[list(xs)])
 add(2475,[list(range(1,101))]);add(2475,[[1000]*100])
 for m,n in product((1,2),repeat=2):
  for flat in product((1,2,3),repeat=m*n):add(2500,[[list(flat[i*n:(i+1)*n])for i in range(m)]])
 add(2500,[[list(range(1,51))for _ in range(50)]]);add(2500,[[[100]*50 for _ in range(50)]])
 for n in range(1,5):
  for ws in product(('a','b','ab','ba','aaa'),repeat=n):add(2506,[list(ws)])
 add(2506,[['abcdefghijklmnopqrstuvwxyz'*3+'a'*22]*100])
 return out
