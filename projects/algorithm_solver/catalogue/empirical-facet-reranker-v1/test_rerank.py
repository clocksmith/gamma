import unittest
from enum import Enum
from rerank import signed_facets,agreement,rerank,decide_hybrid
class F(Enum):UNKNOWN='unknown';SATISFIED='satisfied';VIOLATED='violated'
class G:
 Facet=F
 @staticmethod
 def compare(q,c):return {'facets':{k:(F.UNKNOWN.value if k not in c['facts']else F.SATISFIED.value if c['facts'][k]==v else F.VIOLATED.value)for k,v in q['facts'].items()}}
def e(k,v,p='positive'):return dict(facet=k,value=v,polarity=p)
def c(**facts):return dict(facts=facts,conflicts=[])
class Service:
 def request(self,pid,**kw):return dict(status='matched',consumer_selection=dict(status='selected'))
class Tests(unittest.TestCase):
 def test_unknown_zero(self):self.assertEqual(agreement(dict(facts={'x':'a'},excluded_values={}),c(),G),0)
 def test_negative(self):
  q=dict(facts={},excluded_values={'x':['a']});self.assertEqual(agreement(q,c(x='a'),G),-1);self.assertEqual(agreement(q,c(x='b'),G),0)
 def test_conflict(self):
  q,cs=signed_facets(dict(tentative_evidence=[e('x','a'),e('x','a','negative'),e('y','b')]));self.assertEqual(cs,['x']);self.assertEqual(q['facts'],{'y':'b'})
 def test_multiplepositive_conflict(self):self.assertEqual(signed_facets(dict(tentative_evidence=[e('x','a'),e('x','b')]))[1],['x'])
 def test_rivals(self):
  r=rerank([.7,.72],['a','b'],{'a':c(x='a'),'b':c()},dict(tentative_evidence=[e('x','a')]),G,expected_population=2);self.assertEqual(len(r['hybrid']),2);self.assertEqual(r['raw_cosines']['b'],r['hybrid'][1][1]);self.assertEqual(r['hybrid'][0][0],'a')
 def test_raw_threshold(self):
  r=rerank([.64,.63],['a','b'],{'a':c(x='a'),'b':c()},dict(tentative_evidence=[e('x','a')]),G,expected_population=2);d=decide_hybrid(r,dict(min_cosine=.65,min_margin=0),Service());self.assertEqual(d['status'],'abstain')
 def test_tie_abstains(self):
  r=rerank([.7,.7],['a','b'],{'a':c(),'b':c()},dict(tentative_evidence=[]),G,expected_population=2);self.assertEqual(decide_hybrid(r,dict(min_cosine=.6,min_margin=0),Service())['status'],'abstain')
 def test_universe_reject(self):
  with self.assertRaises(ValueError):rerank([.7],['a'],{'a':c()},dict(tentative_evidence=[]),G)
class ThresholdTests(unittest.TestCase):
 def test_exact_raw_boundary(self):
  for score in [.45,.55,.65,.75,.85]:
   r=rerank([score,score-.2],['a','b'],{'a':c(x='a'),'b':c()},dict(tentative_evidence=[e('x','a')]),G,expected_population=2)
   self.assertEqual(decide_hybrid(r,dict(min_cosine=score,min_margin=.12),Service())['status'],'accepted')
 def test_zero_adjustment_policy_parity(self):
  from projects.algorithm_solver.catalogue.empirical_recognition import decide
  for c0 in [.45,.55,.65,.75,.85]:
   for m in [0,.04,.08,.12]:
    r=rerank([.75,.65],['a','b'],{'a':c(),'b':c()},dict(tentative_evidence=[]),G,expected_population=2);p=dict(min_cosine=c0,min_margin=m)
    self.assertEqual(decide(r['baseline'],p,Service())['status'],decide_hybrid(r,p,Service())['status'])
if __name__=='__main__':unittest.main()
