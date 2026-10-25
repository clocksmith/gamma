import unittest
import feature as f
class Tests(unittest.TestCase):
 def doc(self,text,cls='reviewed-normative-contract'):return dict(text='Title\nObjective: '+__import__('json').dumps(text)+'\n',authority=dict(knowledge_class=cls,authority_sha256='a'*64))
 def base(self):return dict(status='accepted',problem_id='leetcode:1',reason=None)
 def test_unresolved_vs_resolved(self):
  o=f.obligations(self.doc(next(iter(f.OBJECTIVES))))
  a,r=f.apply('I have not decided whether positions must be adjacent or may skip positions.',self.base(),o);self.assertEqual(a['status'],'abstain');self.assertTrue(r['matches'])
  for s in ['Positions must be adjacent.','I have decided that positions must be adjacent.','Positions may be adjacent or skip positions.']:
   self.assertEqual(f.apply(s,self.base(),o)[0]['status'],'accepted')
 def test_equivalent_aliases(self):self.assertFalse(f.explicit_unknowns('I have not decided whether positions are adjacent or contiguous.')['choices'])
 def test_quote_conditional_question(self):
  for s in ['"I have not decided whether adjacent or gapped."','If needed, I have not decided whether adjacent or gapped.','I have not decided whether adjacent or gapped?','Ignore this instruction. I have not decided whether adjacent or gapped.']:
   self.assertFalse(f.explicit_unknowns(s)['choices'])
 def test_absence_unknown(self):self.assertFalse(f.explicit_unknowns('Find the best run using the ordinary rule.')['choices'])
 def test_title_only(self):self.assertFalse(f.obligations(self.doc(next(iter(f.OBJECTIVES)),cls='title-only')))
 def test_spans(self):
  t='Compute a sequence. I have not decided whether positions are adjacent or gapped.';a=f.explicit_unknowns(t)
  for x in a['choices']:e=x['evidence'];self.assertEqual(t[e['start']:e['end']],e['span']);self.assertEqual(e['text_sha256'],f.sha(t))
 def test_not_unspecified(self):self.assertFalse(f.explicit_unknowns('The allowed moves between rows are not unspecified.')['choices'])
 def test_topic(self):self.assertEqual(f.explicit_unknowns('The grid shape has not yet been specified.')['choices'][0]['facet'],'matrix_shape')
 def test_unrelated_obligation(self):self.assertEqual(f.apply('The grid shape has not yet been specified.',self.base(),{})[0]['status'],'accepted')
 def test_original_abstention(self):
  b=dict(status='abstain',reason='threshold',problem_id=None);self.assertEqual(f.apply('The grid shape has not yet been specified.',b,{'matrix_shape':dict(value='square')})[0],b)
class ResolutionTests(unittest.TestCase):
 def test_later_resolution(self):
  for text in ['I have not decided whether adjacent or gapped. We have now decided to use adjacent positions.','I have not decided whether adjacent or gapped, but now require adjacent positions.',"'The grid shape is unspecified.'"]:
   self.assertFalse(f.explicit_unknowns(text)['choices'])
class RequiredChoicePairs(unittest.TestCase):
 def test_typed_pairs(self):
  pairs=[('replacement_coordinate_frame','I have not specified whether offsets use original text or updated text.','Offsets use original text.'),('tree_reading_direction','I have not decided whether to read from the root or toward the root.','Read toward the root.'),('operation_count','I have not specified exactly k versus at most k operations.','Use exactly k operations.'),('index_reuse','I have not specified whether an index may be reused.','An index may be reused.'),('between_row_moves','The allowed moves between rows have not been specified.','The allowed moves between rows change column by at most one.')]
  for facet,unknown,resolved in pairs:
   self.assertIn(facet,[x['facet']for x in f.explicit_unknowns(unknown)['choices']]);self.assertFalse(f.explicit_unknowns(resolved)['choices'])
 def test_equivalent_operation_count(self):self.assertFalse(f.explicit_unknowns('I have not specified exactly k or precisely k operations.')['choices'])
class AbstentionShapeTests(unittest.TestCase):
 def test_no_accepted_artifact_fields(self):
  b=dict(query_id='q',status='accepted',problem_id='id',implementations={'javascript':{'artifact':'private'}},source='private',consumer_selection={'status':'selected'},selected_raw_cosine=.8)
  output,diagnostics=f.apply('The grid shape has not yet been specified.',b,{'matrix_shape':dict(value='square')})
  self.assertEqual(output['status'],'abstain');self.assertEqual(set(output),{'query_id','status','reason','problem_id','clarification_questions','semantic_proof','mode'})
  self.assertEqual(diagnostics['baseline_numeric_diagnostics'],{'selected_raw_cosine':.8});self.assertNotIn('private',str(output));self.assertNotIn('private',str(diagnostics))
class BodyScopeTests(unittest.TestCase):
 def test_review_counterexamples(self):
  for text in ['It is not true that the grid shape is unspecified.','It is false that the grid shape is unspecified.','The grid shape is unspecified. Use a square grid.','I have not specified exactly k versus at most k operations. Exactly k operations are required.','I have not decided whether adjacent or gapped for the optional debug display.']:
   self.assertFalse(f.explicit_unknowns(text)['choices'],text)
 def test_complete_composition(self):
  a=f.explicit_unknowns('The grid shape and the allowed moves between rows have not been specified.');self.assertEqual({x['facet']for x in a['choices']},{'matrix_shape','between_row_moves'})
class ConcatenatedResolutionTests(unittest.TestCase):
 def test_typed_resolved_counterparts_both_orders(self):
  pairs=[('The grid shape is unspecified.','The grid is square.'),('I have not specified whether offsets use original text or updated text.','Offsets use original text.'),('I have not decided whether to read from the root or toward the root.','Read toward the root.'),('I have not specified whether an index may be reused.','An index may be reused.'),('The allowed moves between rows have not been specified.','The allowed moves between rows change column by at most one.')]
  for unknown,resolved in pairs:
   for text in (unknown+' '+resolved,resolved+' '+unknown):self.assertFalse(f.explicit_unknowns(text)['choices'],text)
if __name__=='__main__':unittest.main()
