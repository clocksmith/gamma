import unittest,sys,json,hashlib,os,subprocess
from itertools import product
from pathlib import Path
import oracles as o
import cases
class References(unittest.TestCase):
 def test_dice(self):
  for n in range(1,5):
   for k in range(1,5):
    totals=[sum(v)for v in product(range(1,k+1),repeat=n)]
    for t in range(1,n*k+2):self.assertEqual(o.expected(1155,[n,k,t]),totals.count(t))
 def test_merge(self):
  self.assertEqual(o.expected(1167,[[1,1,1]]),5);self.assertEqual(o.expected(1167,[[1,2,3,4]]),19)
 def test_probability(self):
  self.assertEqual([o.expected(1227,[n])for n in range(1,9)],[1.0]+[0.5]*7)
 def test_matrix_feasibility(self):
  for n in range(1,5):
   for cols in product(range(3),repeat=n):
    options={(sum(top),sum(bottom))for top in product((0,1),repeat=n)for bottom in product((0,1),repeat=n)if all(t+b==c for t,b,c in zip(top,bottom,cols))}
    for u in range(n+1):
     for l in range(n+1):self.assertEqual(o.expected(1253,[u,l,list(cols)]),(u,l)in options)
 def test_predicate_negative_controls(self):
  self.assertTrue(o.matches(1238,[2,3],[3,2,0,1],None));self.assertFalse(o.matches(1238,[2,3],[3,2,1,0],None));self.assertFalse(o.matches(1238,[2,3],[3,2,0,True],None))
  self.assertTrue(o.matches(1249,['(a))'],'(a)',1));self.assertFalse(o.matches(1249,['(a))'],'a',1));self.assertFalse(o.matches(1249,['(a))'],'(b)',1))
  self.assertFalse(o.matches(1253,[1,1,[1,1]],[[True,0],[0,1]],True));self.assertFalse(o.matches(1169,[[]],['x','x'],['x']))
  row={'result':1,'result_type':'int','args_before':[[1]],'args_after':[[2]],'alias_edges':[]};self.assertEqual(o.compare(1281,[[1]],1,row,'python'),(False,'input_effects'))
  row['args_after']=[[1]];row['alias_edges']=[[0,0]];self.assertEqual(o.compare(1281,[[1]],1,row,'python'),(False,'mutable_alias'))
 def test_gold_definition(self):
  self.assertEqual(o.expected(1219,[[[1,2],[3,4]]]),10);self.assertEqual(o.expected(1219,[[[1,0,2]]]),2)
 def test_determinism(self):
  code='import cases,json,hashlib;print(hashlib.sha256(json.dumps(cases.build(),sort_keys=True).encode()).hexdigest())'
  outputs=[subprocess.check_output([sys.executable,'-c',code],cwd=Path(__file__).parent,env=dict(os.environ,PYTHONHASHSEED=str(seed)))for seed in (1,2)]
  self.assertEqual(*outputs)
if __name__=='__main__':unittest.main()
