import hashlib,unittest
from adapter import query,contract,normalized_cosine,compatibility_observations
class Tests(unittest.TestCase):
 def clause(self):return dict(clause_id='c',authority_sha256='a'*64,field='effect',field_sha256='b'*64,span=[0,4],text='test',problem_id='synthetic',role='effects',polarity=1,required=True)
 def test_unicode_spans(self):
  text='  Return an integer.\n Élargissez cette idée!';r=query(text)
  for q in r['evidence']:
   self.assertEqual(q['text'],text[slice(*q['span'])]);self.assertEqual(q['text_sha256'],hashlib.sha256(q['text'].encode()).hexdigest())
  self.assertFalse(r['document_closed_grammar'])
 def test_grounded_composition_and_negation(self):
  r=query('Return an integer. Do not modify the input.');self.assertTrue(r['document_closed_grammar']);self.assertEqual([x['polarity']for x in r['evidence']],[1,-1])
 def test_scope_unknown_preserves_tentative(self):
  for text in ('If needed; return an integer.','They said: return an integer.','Return an integer. This is optional.','"Return an integer."','Is it correct to return an integer?','Return an integer..'):
   r=query(text);self.assertFalse(r['document_closed_grammar'],text);self.assertTrue(r['evidence']);self.assertTrue(all(x['track']=='tentative'and x['polarity']is None for x in r['evidence']))
 def test_conflicting_effect_unknown(self):
  r=query('Modify the input. Do not modify the input.');self.assertTrue(r['conflicting_predicates']);self.assertFalse(r['document_closed_grammar'])
 def test_unrestricted_prose_not_rejected(self):
  r=query('Find an optimal arrangement under these constraints.');self.assertEqual(r['evidence'][0]['track'],'tentative');self.assertIsNone(r['recognition_decision']);self.assertEqual(len(r['evidence'][0]['role_hypotheses']),6)
 def test_normalization_explicit(self):
  self.assertEqual([normalized_cosine(v)for v in (-1,0,1)],[0,.5,1])
  for v in (float('nan'),float('inf'),-1.01,1.01,True):
   with self.assertRaises(ValueError):normalized_cosine(v)
 def test_contract_purpose_not_inferred(self):
  c=self.clause();r=contract([c])[0];self.assertEqual(r['obligation_purpose'],'UNKNOWN');self.assertFalse(r['request_repetition_required']);self.assertEqual(r['span'],c['span']);self.assertEqual(contract([c],{'c':'carried_domain_or_api'})[0]['obligation_purpose'],'carried_domain_or_api')
 def test_tentative_score_never_entailment(self):
  r=query('Could you transform this input somehow?');q=r['evidence'][0];obs=compatibility_observations(r,[self.clause()],{(q['evidence_id'],'c'):1})[0];self.assertEqual(obs['normalized_compatibility'],1);self.assertEqual(obs['semantic_entailment'],'UNKNOWN');self.assertEqual(obs['track'],'tentative');self.assertIsNone(obs['query_polarity'])
 def test_missing_observation_empty_not_negative(self):self.assertEqual(compatibility_observations(query('Return an integer.'),[self.clause()],{}),[])
 def test_identity_collisions(self):
  c=self.clause()
  with self.assertRaises(ValueError):contract([c,dict(c,polarity=-1)])
  r=query('Return an integer.');r['evidence'].append(dict(r['evidence'][0],scope='UNKNOWN'))
  with self.assertRaises(ValueError):compatibility_observations(r,[c],{})
  self.assertEqual(contract([c,c]),contract([c]))
 def test_deterministic_observations(self):
  r=query('Return an integer. Modify the input.');pairs={(q['evidence_id'],'c'):.2 for q in r['evidence']};self.assertEqual(compatibility_observations(r,[self.clause()],pairs),compatibility_observations(r,[self.clause()],dict(reversed(list(pairs.items())))))
if __name__=='__main__':unittest.main()
