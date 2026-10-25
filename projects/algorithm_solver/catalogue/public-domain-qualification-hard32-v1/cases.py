"""New synthetic fixtures; no historical, imported, or protected test reads."""
from itertools import product,combinations
import json,random
from oracle import IDS,expected,validate

def build(public=None):
 out={i:[]for i in IDS};seen={i:set()for i in IDS}
 def add(pid,args,purpose):
  key=json.dumps(args,separators=(',',':'))
  if key not in seen[pid]:out[pid].append({'args':args,'expected':expected(pid,args),'purpose':purpose});seen[pid].add(key)
 for n in range(1,5):
  for a in product(range(n),repeat=n):add(798,[list(a)],'exhaustive short rotation scores and ties')
 for value in(0,99999):add(798,[[value]*100000],'maximum constant rotation tie')
 add(798,[[2,3,1,4,0]],'official example')
 r=random.Random(798801913)
 for n in range(2,9):
  for _ in range(12):
   a=sorted(r.sample(range(30),n));b=sorted(r.sample(range(30),n))
   for i in range(n):
    if r.randrange(2):a[i],b[i]=b[i],a[i]
   add(801,[a,b],'guaranteed-feasible independently enumerated swap masks')
 add(801,[[1,3,5,4],[1,2,3,7]],'official example')
 add(801,[list(range(100000)),list(range(100000,200000))],'maximum already-increasing arrays')
 for n in range(1,6):
  for s in map(''.join,product('ab',repeat=n)):
   for k in set((1,n)):add(899,[s,k],'reachable-state exhaustive binary strings')
 add(899,[('zyxwvutsrqponmlkjihgfedcba'*39)[:1000],1],'long minimum rotation')
 add(899,['z'*999+'a',2],'maximum first-two permutation generator')
 # Enumerate all small undirected graphs, reject officially impossible cat moves.
 for n in(3,4):
  edges=list(combinations(range(n),2))
  for mask in range(1<<len(edges)):
   g=[[]for _ in range(n)]
   for j,(a,b)in enumerate(edges):
    if mask>>j&1:g[a].append(b);g[b].append(a)
   try:validate(913,[g])
   except ValueError:continue
   add(913,[g],'all valid small undirected game graphs')
 add(913,[[[2,5],[3],[0,4,5],[1,4,5],[2,3],[0,2,3]]],'official draw with repeated-state rule')
 add(913,[[[1,3],[0],[3],[0,2]]],'official mouse victory')
 add(913,[[[j for j in range(50)if j!=i]for i in range(50)]],'maximum dense graph')
 for n in range(5,9):
  for _ in range(6):
   edges={(i,(i+1)%n)for i in range(n)}|{(a,b)for a,b in combinations(range(n),2)if r.randrange(3)==0};g=[set()for _ in range(n)]
   for a,b in edges:g[a].add(b);g[b].add(a)
   add(913,[[sorted(x)for x in g]],'seeded cycle-plus-chords game')
 for n in(2,3,4):
  edges=list(combinations(range(n),2))
  for mask in range(1<<len(edges)):
   g=[[int(i==j)for j in range(n)]for i in range(n)]
   for j,(a,b)in enumerate(edges):
    if mask>>j&1:g[a][b]=g[b][a]=1
   for initial in([0],list(range(n-1)),[n-1,0]if n>2 else[1]):add(928,[g,initial],'independent node-deletion infection propagation')
 add(928,[[[1]*300 for _ in range(300)],[299,1,0]],'maximum dense malware tie')
 add(928,[[[int(i==j)for j in range(300)]for i in range(300)],[299,1,0]],'maximum isolated malware tie')
 texts=['0','1','9999','0.','1.','0.0','0.0000','0.(0)','0.(9)','0.9(9)','0.(3)','0.(33)','0.3(3)','0.1(6)','0.16(6)','0.166(66)','0.1666(6)','0.(52)','0.5(25)','9999.9999(9999)','9999.9999(9998)','0.0000(0001)','0.0000(0010)']
 for i,s in enumerate(texts):
  for t in texts[i:]:add(972,[s,t],'exact finite and periodic decimal pair matrix')
 for n in(1,2):
  for e in('a','b','z','aa','aba','zz'):
   add(1397,[n,'a'*n,'z'*n,e],'complete small lexical interval')
 for _ in range(24):
  a=r.randrange(26**3-500);b=a+r.randrange(500)
  def word(x):
   cs=[]
   for _ in range(3):x,d=divmod(x,26);cs.append(chr(97+d))
   return ''.join(reversed(cs))
  add(1397,[3,word(a),word(b),r.choice(('a','ab','aaa','zz'))],'seeded short lexical intervals')
 add(1397,[2,'aa','da','b'],'official example')
 add(1397,[500,'a'*500,'z'*500,'a'],'maximum length single-forbidden-letter formula')
 add(1397,[500,'a'*500,'a'*500,'a'*50],'maximum pattern present singleton interval')
 add(1397,[500,'z'*500,'z'*500,'a'*50],'maximum pattern absent singleton interval')
 choices=[list(c)for k in(1,2,3)for c in combinations((1,2,3),k)]
 for n in(1,2,3):
  for h in product(choices,repeat=n):
   if n<3 or r.randrange(6)==0:add(1434,[list(h)],'small distinct assignment inclusion-exclusion')
 add(1434,[[list(range(1,41))for _ in range(10)]],'maximum rectangular permanent')
 add(1434,[[[1]for _ in range(10)]],'maximum impossible identical singleton hats')
 add(1434,[[[i+1]for i in range(10)]],'maximum unique forced hats')
 return out
