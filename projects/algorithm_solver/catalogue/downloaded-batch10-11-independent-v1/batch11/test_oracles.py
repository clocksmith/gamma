import unittest,itertools,math,sys,subprocess,os,json
from collections import deque
from pathlib import Path
import oracles as o
import cases
class ReferenceTests(unittest.TestCase):
 def test_ball_labeled_enumeration(self):
  for balls in ([1,1],[2,2],[1,2,1],[3,1,2],[2,2,2],[4,2]):
   labels=[i for i,n in enumerate(balls)for _ in range(n)];good=total=0
   for chosen in itertools.combinations(range(len(labels)),len(labels)//2):
    selected=set(chosen);good+=len({c for i,c in enumerate(labels)if i in selected})==len({c for i,c in enumerate(labels)if i not in selected});total+=1
   self.assertAlmostEqual(o.balls_probability(balls),good/total)
 def test_probability_numeric_domain(self):
  for pid in (1467,1514):
   self.assertTrue(o.matches(pid,[],1,1.0));self.assertTrue(o.matches(pid,[],0.5,0.5));self.assertFalse(o.matches(pid,[],True,1.0));self.assertFalse(o.matches(pid,[],float('nan'),0))
  args=[2,[[0,1]],[1.0],0,1];other=[2,[[0,1]],[1],0,1];self.assertTrue(o.input_matches(1514,other,args));other[2]=[True];self.assertFalse(o.input_matches(1514,other,args))
 def test_drying_freedom(self):
  args=[[1,2,0,0,2,1]];self.assertTrue(o.expected(1488,args));self.assertTrue(o.matches(1488,args,[-1,-1,2,1,-1,-1],True));self.assertFalse(o.matches(1488,args,[-1,-1,1,1,-1,-1],True));self.assertFalse(o.matches(1488,args,[],True));self.assertFalse(o.expected(1488,[[1,2,0,1,2]]))
 def test_function_operation_bfs(self):
  for target in itertools.product(range(4),repeat=3):
   q=deque([((0,0,0),0)]);seen={(0,0,0)}
   while q:
    state,d=q.popleft()
    if state==target:self.assertEqual(o.expected(1558,[list(target)]),d);break
    options=[tuple(v*2 for v in state)]+[tuple(v+int(i==j)for i,v in enumerate(state))for j in range(3)]
    for new in options:
     if new not in seen and all(v<=w for v,w in zip(new,target)):seen.add(new);q.append((new,d+1))
 def test_wheel_capacity_bound(self):
  for customers in itertools.product(range(4),repeat=3):
   waiting=profit=0;best=0;answer=-1;r=0
   while r<len(customers)or waiting:
    waiting+=customers[r]if r<len(customers)else 0;boarded=min(waiting,4);waiting-=boarded;profit+=boarded*3-4;r+=1
    if profit>best:best=profit;answer=r
   self.assertEqual(o.expected(1599,[list(customers),3,4]),answer)
 def test_bit_reflection_and_codes(self):
  s='0'
  for n in range(1,7):
   if n>1:s=s+'1'+''.join('1'if c=='0'else'0'for c in s[::-1])
   for k,c in enumerate(s,1):self.assertEqual(o.expected(1545,[n,k]),c)
  for k in range(1,7):self.assertTrue(o.expected(1461,[cases.debruijn(k),k]))
 def test_effect_type_freedom_negative_controls(self):
  self.assertTrue(o.matches(1576,['?a?'],'bab',None));self.assertFalse(o.matches(1576,['?a?'],'aaa',None));self.assertFalse(o.matches(1576,['?a?'],'bzb',None))
  row={'result':1,'result_type':'int','args_before':['aaa',[9,2,1]],'args_after':['aaa',[9,9,9]],'alias_edges':[]};self.assertEqual(o.compare(1578,['aaa',[9,2,1]],1,row,'python'),(False,'input_effects'))
 def test_seed_determinism(self):
  code='import cases,json,hashlib;print(hashlib.sha256(json.dumps(cases.build(),sort_keys=True).encode()).hexdigest())';v=[subprocess.check_output([sys.executable,'-c',code],cwd=Path(__file__).parent,env=dict(os.environ,PYTHONHASHSEED=str(seed)))for seed in (1,2)];self.assertEqual(*v)
if __name__=='__main__':unittest.main()
