"""Deterministic public-only finite foundation corpus; never reads private cases."""
import json
from itertools import product,combinations
from oracle import IDS,expected,exact

def object_tree(root):
 queue=[root];out=[]
 for node in queue:
  if node is None:out.append(None);continue
  if type(node)is not dict or set(node)!={'val','left','right'}:raise ValueError('public authored tree shape')
  out.append(node['val']);queue.extend((node['left'],node['right']))
 while out and out[-1]is None:out.pop()
 return {'__tree_node__':out}
def build(public):
 result={pid:[]for pid in IDS};seen={pid:set()for pid in IDS}
 def add(pid,args,purpose,want=None,assert_want=False):
  key=json.dumps(args,sort_keys=True,separators=(',',':'))
  if key in seen[pid]:return
  value=expected(pid,args)
  if assert_want and not exact(value,want):raise ValueError(f'independent public oracle disagrees: {pid} {purpose}')
  seen[pid].add(key);result[pid].append({'args':args,'expected':value,'purpose':purpose})
 for pid in IDS:
  data=json.loads((public/f'{pid}.cases.json').read_text())
  for row in data['cases']:
   args=row['args']
   if pid==988:args=[object_tree(args[0])]
   # Public real constants may be JSON int while mathematical oracle float.
   if pid==1514:
    if abs(expected(pid,args)-row['expected'])>1e-12:raise ValueError('public probability expectation mismatch')
    add(pid,args,row['purpose'])
   else:add(pid,args,row['purpose'],row['expected'],True)
 for values in product((-1,0,1),repeat=6):
  add(120,[[list(values[:1]),list(values[1:3]),list(values[3:])]],'exhaustive three-row ternary triangle')
 for values in product((-1,0,1),repeat=4):add(931,[[list(values[:2]),list(values[2:])]],'exhaustive binary-width ternary matrix')
 words=[''.join(x)for x in product('ab',repeat=3)]
 for rows in product(words,repeat=2):add(955,[list(rows)],'exhaustive two-row three-column binary')
 for values in product((0,1,25),repeat=3):add(988,[{'__tree_node__':list(values)}],'three-node label boundary combinations')
 for values in product((-2,-1,0,1,2),repeat=2):
  for k in range(1,5):add(1005,[list(values),k],'exhaustive two-number flips')
 for values in product((1,2,3),repeat=4):add(1007,[list(values[:2]),list(values[2:])],'exhaustive two-domino three-face')
 strings=[''.join(v)for n in range(1,4)for v in product('AB',repeat=n)]
 for a,b in product(strings,repeat=2):add(1071,[a,b],'short uppercase divisor pairs')
 expressions=['t','f','!(t)','!(f)']
 for a,b in product(expressions,repeat=2):
  for op in '&|':add(1106,[op+'('+a+','+b+')'],'Boolean composition truth table')
 for a in product((0,1,2),repeat=3):
  for b in sorted(set(a)):add(1122,[list(a),[b]],'short priority multisets')
 for supply in ('a','aa','ab','abc','bb'):
  add(1160,[['a','aa','ab','bb','abc'],supply],'reset supply independently per word')
 for query in ('a','aa','ba','bbb','ababa'):add(1170,[[query],['a','aa','bbb','baba']],'strict smallest-frequency thresholds')
 for probs in product((0.0,0.5,1.0),repeat=3):add(1514,[3,[[0,1],[1,2],[0,2]],list(probs),0,2],'exhaustive triangle edge probabilities')
 for end1,end2 in product((3,4,5),repeat=2):
  for target in range(2):add(1942,[[[1,end1],[2,end2]],target],'two arrivals with release boundaries')
 possible=[(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
 for mask in range(64):add(2192,[4,[list(e)for i,e in enumerate(possible)if mask>>i&1]],'all forward four-node DAGs')
 # Maximum-size fixtures use mathematically controlled topology/values, not
 # candidate output. Oracle work is bounded (Bellman-Ford star settles twice).
 for value in (-10000,10000):add(120,[[[value]*(i+1)for i in range(200)]],'maximum uniform triangle')
 for value in (-100,100):add(931,[[[value]*100 for _ in range(100)]],'maximum uniform square')
 add(955,[['a'*100]*100],'maximum equal rows');add(955,[['z'*100,'a'*100]],'maximum fully descending columns')
 add(988,[{'__tree_node__':[0]+[v for _ in range(8499)for v in (0,None)][:-1]}],'maximum 8500-node left chain')
 add(988,[{'__tree_node__':[25]*8500}],'maximum broad tree')
 add(1005,[[-100]*10000,10000],'maximum full negative flip mass');add(1005,[[100]*10000,9999],'maximum positive odd flips')
 add(1007,[[1,2]*10000,[2,1]*10000],'maximum alternating complementary dominoes')
 add(1071,['A'*1000,'A'*999],'maximum unary strings');add(1071,['A'*999+'B','A'*1000],'late unequal strings')
 for depth in (6665,6666):add(1106,['!('*depth+'t'+')'*depth],'near maximum grammar depth')
 add(1106,['&('+','.join(['t']*9998)+')'],'near maximum wide conjunction')
 add(1122,[[i%1001 for i in range(1000)],list(range(999,-1,-1))],'maximum reversed priority')
 add(1160,[['a'*100]*1000,'a'*100],'maximum repeated good words')
 add(1170,[['a']*2000,['a'*10]*2000],'maximum strict frequency pair count')
 add(1514,[10000,[[0,i]for i in range(1,10000)]+[[i,i+1]for i in range(1,10000)if i+1<10000]+[[1,3],[2,4],[3,5]],[1.0]*20000,0,9999],'maximum edge count one-weight connected graph')
 add(1942,[[[2*i+1,2*i+2]for i in range(10000)],9999],'maximum nonoverlapping arrivals')
 add(2192,[1000,[[i,i+1]for i in range(999)]],'maximum node-count chain')
 return result
