import copy,unittest
from rank import rerank
class Tests(unittest.TestCase):
 def setUp(self):
  self.bind={'encoder_sha256':'a'*64,'prompt_sha256':'b'*64,'embedding_dimension':1024,'score_units':'raw_cosine_-1_to_1'}
  self.q=[dict(evidence_id='q',request_sha256='c'*64,span=[0,5],text_sha256='d'*64,track='tentative',scope='UNKNOWN',polarity=None)]
  self.c=[dict(clause_id='c',problem_id='p1',role='effects',authority_sha256='e'*64,field='effects',field_sha256='f'*64,span=[0,4],text='test',polarity=1,required=True)]
  self.p=[dict(query_evidence_id='q',clause_id='c',cosine=.8)]
 def run_case(self,**changes):
  d=dict(stable_ids=['p1','p2'],raw_cosines=[.5,.51],existing_hybrid_scores=[.5,.51],query_spans=self.q,clauses=self.c,pairs=self.p,bindings=self.bind,expected_bindings=self.bind,expected_request_sha256='c'*64,expected_population=2);d.update(changes);return rerank(**d)
 def test_signal_raw_and_adjusted_separate(self):
  r=self.run_case();self.assertEqual(r['raw_ranking'],['p2','p1']);self.assertEqual(r['tentative_adjusted_ranking'],['p1','p2']);self.assertAlmostEqual(r['rows'][0]['tentative_signal'],.3);self.assertIsNone(r['acceptance_decisions'])
 def test_duplicate_invariance(self):self.assertEqual(self.run_case(),self.run_case(query_spans=self.q*3,clauses=self.c*3,pairs=self.p*3))
 def test_permutation_and_ties(self):
  q=self.q+[dict(self.q[0],evidence_id='q2')];p=self.p+[dict(self.p[0],query_evidence_id='q2',cosine=.1)];self.assertEqual(self.run_case(query_spans=q,pairs=p),self.run_case(query_spans=q[::-1],pairs=p[::-1]));self.assertEqual(self.run_case(raw_cosines=[.5,.5],existing_hybrid_scores=[.5,.5],pairs=[])['raw_ranking'],['p1','p2'])
 def test_missing_pairs_and_missing_authority_distinct(self):
  rows=self.run_case(pairs=[])['rows'];self.assertEqual(rows[0]['authority_status'],'AUTHORITATIVE');self.assertEqual(rows[0]['unobserved_authoritative_roles'],['effects']);self.assertEqual(rows[1]['authority_status'],'UNKNOWN');self.assertEqual(rows[1]['unobserved_authoritative_roles'],[]);self.assertTrue(all(x['tentative_signal']==0 for x in rows))
 def test_full4081_title_rivals_retained(self):
  ids=['p1']+[str(i)for i in range(4080)];r=self.run_case(stable_ids=ids,raw_cosines=[.5]*4081,existing_hybrid_scores=[.5]*4081,expected_population=4081);self.assertEqual(set(r['tentative_adjusted_ranking']),set(ids));self.assertEqual(len(r['rows']),4081)
 def test_negation_and_conflict_not_cast_to_grounded(self):
  q=[dict(self.q[0],polarity=-1),dict(self.q[0],evidence_id='q2',polarity=1)];p=self.p+[dict(self.p[0],query_evidence_id='q2',cosine=.8)];r=self.run_case(query_spans=q,pairs=p);self.assertEqual(r['rows'][0]['semantic_entailment'],'UNKNOWN');self.assertAlmostEqual(r['rows'][0]['tentative_signal'],.3)
 def test_nonfinite_and_scoreunits(self):
  for value in (float('nan'),float('inf'),1.1,-1.1):
   with self.assertRaises(ValueError):self.run_case(pairs=[dict(self.p[0],cosine=value)])
  with self.assertRaises(ValueError):self.run_case(bindings=dict(self.bind,score_units='normalized0to1'))
 def test_dimensions_and_malformed(self):
  with self.assertRaises(ValueError):self.run_case(bindings=dict(self.bind,embedding_dimension=512))
  with self.assertRaises(ValueError):self.run_case(raw_cosines=[.5])
  with self.assertRaises(ValueError):self.run_case(existing_hybrid_scores=[float('nan'),.5])
 def test_bounds(self):
  r=self.run_case(raw_cosines=[-1,1],existing_hybrid_scores=[-1.05,1.05],pairs=[dict(self.p[0],cosine=1)]);self.assertEqual(r['rows'][0]['tentative_signal'],2);self.assertEqual(r['rows'][0]['tentative_adjustment'],.1)
 def test_provenance_collisions_fail(self):
  for field,rows in [('query_spans',self.q+[dict(self.q[0],scope='explicit')]),('clauses',self.c+[dict(self.c[0],polarity=-1)]),('pairs',self.p+[dict(self.p[0],cosine=.9)])]:
   with self.assertRaises(ValueError):self.run_case(**{field:rows})
 def test_mixed_request_and_malformed_rival_identity(self):
  with self.assertRaises(ValueError):self.run_case(query_spans=self.q+[dict(self.q[0],evidence_id='other',request_sha256='a'*64)])
  for ids in (['p1',{}],['p1',''],['p1',None]):
   with self.assertRaises(ValueError):self.run_case(stable_ids=ids)
 def test_unbound_pair(self):
  with self.assertRaises(ValueError):self.run_case(pairs=[dict(self.p[0],clause_id='unknown')])
if __name__=='__main__':unittest.main()
