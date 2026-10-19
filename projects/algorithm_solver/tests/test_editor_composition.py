import copy,json,unittest
from unittest.mock import patch
from algsolve import editor_composition as api
from algsolve.synth import typed_recipes as r


def problem():
 return dict(title='Add',slug='',statement='Return a+b.',entry={'class':'Solution','method':'solve'},params=[['a','int'],['b','int']],starter_code='class Solution:\n def solve(self, a: int, b: int) -> int:\n  pass\n',public_tests=[{'args':[2,3],'expected':5},{'args':[-8,3],'expected':-5}])

class CompositionTests(unittest.TestCase):
 def test_graph_checks_and_returns_only_example_passed_source(self):
  graph=r.program({'a':'int','b':'int'},[],r.pure('add',r.ref('a'),r.ref('b')),'int')
  result=api.check_graph(problem(),graph)
  self.assertEqual(result['decision'],'answered');self.assertTrue(result['example_passed']);self.assertFalse(result['source_generation']);self.assertIsNone(result['independent_tests_passed'])
  wrong=copy.deepcopy(graph);wrong['return']['op']='sub'
  result=api.check_graph(problem(),wrong);self.assertEqual(result['decision'],'abstain');self.assertIsNone(result['code'])
 def test_invalid_program_and_parameter_order_fail_closed(self):
  for graph in [dict(code='import os'),r.program({'b':'int','a':'int'},[],r.lit(5),'int')]:
   with self.subTest(graph=graph),self.assertRaises(ValueError):api.check_graph(problem(),graph)
 def test_missing_examples_never_answers(self):
  raw=problem();raw['public_tests']=[]
  graph=r.program({'a':'int','b':'int'},[],r.lit(5),'int')
  self.assertFalse(api.check_graph(raw,graph)['example_passed'])
  self.assertEqual(api.compose(raw)['reason'],'query_has_no_public_examples')
 def test_protected_identity_rejected_before_model_load(self):
  from algsolve.records import LANE_ROOT
  reservation=json.loads((LANE_ROOT/'findings/mine-v2-candidates-20261017/split.json').read_text())
  raw=problem();raw['slug']=reservation['confirmation_keys'][0].removeprefix('lc:')
  with patch('torch.load',side_effect=AssertionError('Protected request loaded model')):
   self.assertEqual(api.compose(raw)['reason'],'protected_composition_family')


 def test_inserted_dependency_source_runs_but_modified_source_does_not_gain_backend(self):
  from algsolve.records import LANE_ROOT
  from algsolve.composition_bridge import execute
  stored=json.loads((LANE_ROOT/'findings/editor-composition-128-v1/retrieval-result.json').read_text())
  query=json.loads((LANE_ROOT/'findings/known-sortedcontainers-1a-128-v1/example-query.json').read_text())
  catalog=LANE_ROOT/'findings/known-sortedcontainers-1a-128-v1/approved-library.json'
  result=execute('python',stored['code'],query,catalog)
  self.assertTrue(result['example_passed']);self.assertEqual(result['runtime_dependency'],'algsolve.sortedcontainers-2.4.0.v1')
  result=execute('python',stored['code']+'\n# changed source',query,catalog)
  self.assertFalse(result['example_passed']);self.assertNotIn('runtime_dependency',result)

if __name__=='__main__':unittest.main()
