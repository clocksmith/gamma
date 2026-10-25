import copy,itertools,json,unittest
from pathlib import Path
import oracle as o
import qualify as q
from cases import build
class Foundation(unittest.TestCase):
 def test_official_author_cases_and_all_generated_domains(self):
  cases=build(Path(__file__).resolve().parent.parent/'domain-contracts-public-v1')
  self.assertEqual(sum(map(len,cases.values())),1922)
  for pid,rows in cases.items():
   for row in rows:self.assertTrue(o.validate(pid,row['args']));self.assertTrue(o.exact(o.expected(pid,row['args']),row['expected']))
 def test_distinct_rotation_domain(self):
  self.assertTrue(o.validate(153,[[3,5,-2,0]]))
  for a in ([],[1,1],[1,3,2],[True],[5001]):
   with self.assertRaises(ValueError):o.validate(153,[a])
 def test_set_mismatch_structure_not_loose_numeric(self):
  self.assertEqual(o.expected(645,[[2,3,3,4]]),[3,1])
  for a in ([1],[1,2],[2,2,2],[1,1,4]):
   with self.assertRaises(ValueError):o.validate(645,[a])
 def test_contiguous_not_general_subsequence(self):
  self.assertEqual(o.expected(674,[[1,2,0,3,4]]),3)
  self.assertEqual(o.expected(674,[[7,7,7]]),1)
 def test_small_lcis_exhaustive_brute(self):
  for n in range(1,6):
   for a in itertools.product((-1,0,1),repeat=n):
    want=max(j-i for i in range(n)for j in range(i+1,n+1)if all(a[k]<a[k+1]for k in range(i,j-1)))
    self.assertEqual(o.expected(674,[list(a)]),want)
 def test_simultaneous_original_coordinates(self):
  self.assertEqual(o.expected(833,['mnop',[2,0],['op','m'],['x','uvw']]),'uvwnx')
  with self.assertRaises(ValueError):o.validate(833,['abc',[0,1],['ab','bc'],['x','y']])
  self.assertEqual(o.expected(833,['xy',[1],['yz'],['a']]),'xy')
 def test_word_requirements_not_sum(self):
  self.assertEqual(o.expected(916,[['a','aa','ab'],['a','a']]),['a','aa','ab'])
  self.assertEqual(o.expected(916,[['a','aa','ab'],['aa']]),['aa'])
 def test_output_order_allowed_but_duplicates_rejected(self):
  args=[['a','aa','b'],['a']];want=['a','aa'];r={'result':['aa','a'],'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]}
  self.assertEqual(o.compare(916,args,want,r,'python'),(True,None));r['result']=['a','a']
  self.assertEqual(o.compare(916,args,want,r,'python'),(False,'result_value'))
 def test_mutation_and_root_alias_observed(self):
  args=[[[0,1],[1,1]]];want=o.expected(832,args);r={'result':want,'result_type':'list','args_before':args,'args_after':[want],'alias_edges':[['result','args.0']]}
  self.assertEqual(o.compare(832,args,want,r,'python'),(True,None));r['alias_edges']=[]
  self.assertEqual(o.compare(832,args,want,r,'python'),(False,'return_aliases'))
 def test_bool_cannot_masquerade_integer(self):
  args=[[1]];r={'result':True,'result_type':'number','args_before':args,'args_after':args,'alias_edges':[]}
  self.assertEqual(o.compare(153,args,1,r,'javascript'),(False,'result_value'))
 def test_expected_never_enters_packet(self):
  packet=q.make_packet([{'args':[[2,1]],'expected':1,'purpose':'host only'}]);self.assertEqual(packet['calls'],[{'args':[[2,1]]}]);self.assertNotIn('expected',json.dumps(packet))
 def test_review_missing_or_wrong_hash_fails(self):
  with self.assertRaises(ValueError):q.review_check(b'freeze',{})
  r={'schema':'gamma.public-domain.foundation-review.v1','freeze_sha256':q.sha(b'other'),'independent_review':True,'root_execution_authorized':True,'reviewer':'test','reviewed':['official_clauses','independent_oracle','local_effects','twelve_exact_sources','153_logarithmic_static_review']}
  with self.assertRaises(ValueError):q.review_check(b'freeze',r)
 def test_output_protocol_fails_closed(self):
  self.assertEqual(q.parse(b'{"i":0,"result":1}\n{"done":1}\n',1),[{'i':0,'result':1}])
  for data in (b'{"i":0,"i":0}\n{"done":1}\n',b'{"i":0}\n',b'{"i":1}\n{"done":1}\n',b'{"i":0,"result":NaN}\n{"done":1}\n'):
   with self.assertRaises(ValueError):q.parse(data,1)
if __name__=='__main__':unittest.main()
