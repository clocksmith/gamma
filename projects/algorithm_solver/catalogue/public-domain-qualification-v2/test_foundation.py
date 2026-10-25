import importlib.util,json,sys,unittest
from pathlib import Path
from itertools import product
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import oracle as o
import harness
from cases import build
class DomainTests(unittest.TestCase):
 def test_rejections(self):
  bad={120:[[[1],[2]]],931:[[[1,2]]],955:[['ab','a']],988:[{'__tree_node__':[0,None,None,1]}],1005:[[True],1],1007:[[1,2],[1]],1071:['abc','ABC'],1106:['!(t,f)'],1122:[[1],[1,1]],1160:[['ä'],'a'],1170:[[''],['a']],1514:[2,[[0,1],[1,0]],[.5,.5],0,1],1942:[[[1,2],[1,3]],0],2192:[2,[[0,1],[1,0]]]}
  for pid,args in bad.items():
   with self.subTest(pid=pid),self.assertRaises(ValueError):o.validate(pid,args)
 def test_boolean_grammar(self):
  for x in ('','&()','t,f','tt','(t)','!(t,)','&(,t)','&(t,,f)','!(t)f','&(!t)','!((t))'):
   with self.subTest(x=x),self.assertRaises(ValueError):o.boolean_expression(x)
  self.assertTrue(o.boolean_expression('!('*6666+'t'+')'*6666))
 def test_tree_bound(self):
  for a in ([],[None],[0,None],[0,26],[0,True],[0,None,None,1],[0]*8501):
   with self.subTest(a=a[:5]),self.assertRaises(ValueError):o.tree_arrays({'__tree_node__':a})
  self.assertEqual(len(o.tree_arrays({'__tree_node__':[0]*8500})[0]),8500)
 def test_probability_gate(self):
  for p in (True,float('nan'),float('inf'),-0.1,1.1):
   with self.assertRaises(ValueError):o.validate(1514,[2,[[0,1]],[p],0,1])
 def test_all_public_cases_regenerate(self):
  cases=build(HERE.parent/'domain-contracts-public-v2')
  self.assertEqual(set(cases),set(o.IDS));self.assertGreater(sum(map(len,cases.values())),1500)
 def test_flip_histogram_against_full_state_enumeration(self):
  for a in product((-2,-1,0,1,2),repeat=3):
   states={a}
   for k in range(1,5):
    states={s[:i]+(-s[i],)+s[i+1:]for s in states for i in range(3)}
    self.assertEqual(o.expected(1005,[list(a),k]),max(map(sum,states)))
 def test_boolean_result_not_integer(self):
  r={'result':1,'result_type':'int','args_before':['t'],'args_after':['t'],'alias_edges':[]}
  self.assertFalse(o.compare(1106,['t'],True,r,'python')[0])
 def test_probability_tolerance_boundary(self):
  args=[2,[[0,1]],[0.5],0,1]
  for value,good in ((0.5000099,True),(0.5000101,False),(True,False),(float('nan'),False)):
   r={'result':value,'result_type':'float','args_before':args,'args_after':args,'alias_edges':[]}
   self.assertEqual(o.compare(1514,args,.5,r,'python')[0],good)
 def test_effect_rejection(self):
  args=[[1,2],[1]];r={'result':[1,2],'result_type':'list','args_before':args,'args_after':args,'alias_edges':[['result','args.0']]}
  self.assertFalse(o.compare(1122,args,[1,2],r,'python')[0])
class TransportTests(unittest.TestCase):
 @staticmethod
 def recursive(args,result):
  seen={};edges=[]
  def walk(v,p):
   if v is None or type(v)in(str,bool,int,float):return
   if id(v)in seen:edges.append([p,seen[id(v)]]);return
   seen[id(v)]=p
   for key,item in harness.fields(v):walk(item,p+'.'+str(key))
  walk(args,'args');walk(result,'result');return edges
 def test_alias_order_matches_old_reference(self):
  shared=[];cycle=[];cycle.append(cycle);node=harness.TreeNode(1);node.left=node
  fixtures=[([],[]),([shared,shared],shared),([cycle],cycle),([node],node),([{'x':shared,'y':[shared]}],{'a':shared})]
  for args,result in fixtures:self.assertEqual(harness.aliases(args,result),self.recursive(args,result))
 def test_depth_8500_roundtrip_and_noalias(self):
  tag={'__tree_node__':[0]+[v for _ in range(8499)for v in(0,None)][:-1]}
  tree=harness.decode(tag);self.assertEqual(harness.encode(tree),tag);self.assertEqual(harness.aliases([tree],'a'*8500),[])
 def test_deep_alias_path_exact(self):
  root=harness.TreeNode(0);p=root
  for _ in range(50):p.left=harness.TreeNode(0);p=p.left
  self.assertEqual(harness.aliases([root],p),[['result','args.0'+'.left'*50]])
if __name__=='__main__':unittest.main()
