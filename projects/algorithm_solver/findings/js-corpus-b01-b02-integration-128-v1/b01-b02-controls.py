from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import importlib.util,json,sys,unittest,itertools,math
T=Path('/home/x/Documents/Codex/2026-10-19/task');R=Path('/home/x/deco/gamma/projects/algorithm_solver');sys.path.insert(0,str(R))
from algsolve.judge import judge,sandbox

def load(name):
 s=importlib.util.spec_from_file_location(name,T/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=load('b01-b02-contracts');d=load('b01-b02-domains')
def p(n):return SimpleNamespace(uid=f'lcd:{n}',slug={23:'merge-k-sorted-lists',30:'substring-with-concatenation-of-all-words'}[n],entry={'method':{23:'mergeKLists',30:'findSubstring'}[n]},params=[['lists','List[Optional[ListNode]]']])
def score(expected,actual):
 raw=(json.dumps({'i':0,'result':actual})+'\n'+json.dumps({'done':1})+'\n').encode();return judge._score_functional(sandbox.SandboxResult(0,None,raw,b'',0),c.prepare(p(30),[dict(args=['abab',['ab']],expected=expected)])).passed
class Contracts(unittest.TestCase):
 def test_index_order_and_duplicate_rejection(self):
  self.assertTrue(score([0,2,4],[4,0,2]))
  for a in [[0,2],[0,2,4,6],[0,2,2],[0,2,True],[0,2,4.0],['0',2,4],None]:self.assertFalse(score([0,2,4],a))
 def test_identity_scope(self):
  for field in ['uid','slug','entry']:
   q=p(30);setattr(q,field,{'method':'wrong'} if field=='entry' else 'wrong')
   with self.assertRaises(ValueError):c.prepare(q,[dict(args=[],expected=[])])
 def test_typed_nodes_and_immutability(self):
  raw=[dict(args=[[[],None,[1,3],{'__list_node__':[2]}]],expected={'__list_node__':[1,2,3]})];before=deepcopy(raw);t=c.prepare(p(23),raw)[0]
  self.assertEqual(raw,before);self.assertEqual(t.expected,raw[0]['expected']);self.assertEqual(t.args,[[{'__list_node__':[]},None,{'__list_node__':[1,3]},{'__list_node__':[2]}]])
 def test_bad_typed_nodes_fail(self):
  for args in [[{}],[[{'unrecognized':[]}]],[[1]],[]]:
   with self.assertRaises(ValueError):c.prepare(p(23),[dict(args=args,expected=None)])
 def test_pair_domain_independent_enumeration(self):
  for a in itertools.product(range(-1,2),repeat=3):
   for t in range(-2,3):
    pairs=sum(a[i]+a[j]==t for i in range(3) for j in range(i+1,3));self.assertEqual(not d.reasons(1,[list(a),t]),pairs==1)
 def test_rotation_domain_enumeration(self):
  valid={(0,1,2,3)[k:]+(0,1,2,3)[:k] for k in range(4)}
  for a in itertools.permutations(range(4)):self.assertEqual(not d.reasons(33,[list(a),0]),a in valid)
 def test_reachability_domain_independent_bfs(self):
  for a in itertools.product(range(3),repeat=5):
   visited={0}
   for i in range(5):
    if i in visited:visited.update(range(i+1,min(5,i+a[i]+1)))
   self.assertEqual(not d.reasons(45,[list(a)]),4 in visited)
 def test_positive_distinct_and_phone_domains(self):
  for a in [[0,2],[-1,2],[2,2],[1,2]]:self.assertTrue(d.reasons(39,[a,4]))
  self.assertFalse(d.reasons(39,[[2,3],6]))
  for s in ['1','0','23456']:self.assertTrue(d.reasons(17,[s]))
  self.assertFalse(d.reasons(17,['239']))
 def test_float_domain_bounds(self):
  for a in [[100.,1],[0.,0],[2.,2**31],[10.,10]]:self.assertTrue(d.reasons(50,a))
  for a in [[0.,1],[-2.,-3],[2.,-2**31],[10.,4]]:self.assertFalse(d.reasons(50,a))
if __name__=='__main__':unittest.main()
