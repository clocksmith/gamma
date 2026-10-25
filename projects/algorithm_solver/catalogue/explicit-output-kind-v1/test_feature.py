import unittest,json
import feature as f
class Tests(unittest.TestCase):
 def scalar(self):return f.contract_kind(dict(text='Title\nResult: '+json.dumps({'type':'integer'})+'\n',authority=dict(knowledge_class='reviewed-normative-contract',authority_sha256='a'*64)))
 def baseline(self):return dict(status='accepted',problem_id='id',query_id='q',implementations={'javascript':{'artifact':'private'}})
 def test_explicit_collections(self):
  for text in ['Return a complete event log with timestamps.','Return all paths.','Return the best route and its flag.']:
   out,e=f.apply(text,self.baseline(),self.scalar());self.assertEqual(out['status'],'abstain');self.assertTrue(e['conflict']);self.assertNotIn('implementations',out)
 def test_positive_scalar_counterparts(self):
  for text in ['Return the count of events.','Return the number of paths.','Return the probability.']:
   self.assertEqual(f.apply(text,self.baseline(),self.scalar())[0]['status'],'accepted')
 def test_unknown_not_rejected(self):self.assertEqual(f.apply('Compute whatever the ordinary rule requests.',self.baseline(),self.scalar())[0]['status'],'accepted')
 def test_title_unknown(self):
  c=f.contract_kind(dict(text='Return integer',authority=dict(knowledge_class='title-only')));self.assertEqual(f.apply('Return all paths.',self.baseline(),c)[0]['status'],'accepted')
 def test_scope_negation(self):
  for text in ['Do not return all paths.','Return the number of paths, not all paths.','If asked; return all paths.','This is an example. Return all paths.','"Return all paths. Return a complete log."','Return all paths only in optional diagnostic mode.','Do not compute the graph and return all paths.']:
   self.assertFalse(f.apply(text,self.baseline(),self.scalar())[1]['conflict'],text)
 def test_conjunctive_request(self):self.assertEqual(f.query_kinds('Maximize a score and return all tied paths.')['kinds'],['path-collection'])
 def test_operational_condition_not_output_scope(self):self.assertEqual(f.query_kinds('Reject events if full. Return a complete event log.')['kinds'],['record-collection'])
 def test_conflicting_outputs_unknown(self):self.assertFalse(f.query_kinds('Return all paths. Return the number of paths.')['kinds'])
 def test_span(self):
  text='Compute a value and return all paths.'
  for x in f.query_kinds(text)['evidence']:e=x['evidence'];self.assertEqual(text[e['start']:e['end']],e['span']);self.assertEqual(e['text_sha256'],f.digest(text))
 def test_prior_abstention(self):
  b=dict(status='abstain',reason='threshold',problem_id=None);self.assertEqual(f.apply('Return all paths.',b,self.scalar())[0],b)
class QuoteTests(unittest.TestCase):
 def test_quote_vs_apostrophe(self):
  self.assertFalse(f.query_kinds("'Return a value. Return all paths. Return a count.'")['kinds'])
  self.assertEqual(f.query_kinds('Compute each route’s score. Return the best route and its flag.')['kinds'],['route-and-flag'])
class CorrectionTests(unittest.TestCase):
 def test_later_correction_unknown(self):
  for t in ['Return all paths. Instead, return the count.','Return all paths. Actually, return an integer.','Return all paths. Correction: return a count.','They said: return all paths.']:
   self.assertFalse(f.query_kinds(t)['kinds'],t)
class DiagnosticScopeTests(unittest.TestCase):
 def test_optional_rejected_context(self):
  for t in ['For debugging; return all paths.','Optionally; return all paths.','Return all paths. This is only an optional diagnostic output.','The following request is rejected. Return all paths.']:
   self.assertFalse(f.query_kinds(t)['kinds'],t)
if __name__=='__main__':unittest.main()
