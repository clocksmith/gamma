import unittest
import guard as g
class Tests(unittest.TestCase):
 def test_modifier_unknown(self):
  for text in ['Return the value of the count.','Return the values provided that the array is sorted.','The array of distinct integers is prohibited.','Return an index only in the optional diagnostic mode.','Return the length squared.','Return the index-independent value.','Is it correct to return an index?','The instruction to return an index is false.','Reject the instruction: return an index.','Return the values only when the input is sorted.','Return values.','Not the values.']:
   q=g.parse_query(text);self.assertFalse(q['facts'],text);self.assertFalse(q['excluded_values'],text)
 def test_separate_complete_clause(self):
  q=g.parse_query('An unsupported operation happens. Return an index.');self.assertFalse(q['facts']);self.assertFalse(q['grammar_complete']);self.assertTrue(q['tentative_evidence'])
 def test_tentative_not_active(self):
  q=g.parse_query('Return the length squared.');self.assertTrue(q['tentative_evidence']);self.assertFalse(q['facts']);self.assertFalse(q['evidence'])
 def test_count(self):q=g.parse_query('Return the length.');self.assertEqual(q['facts']['output_measure'],'count');self.assertNotIn('returned_entity',q['facts'])
 def test_input_values_negation(self):
  t='Return input values, not their indices.';q=g.parse_query(t);self.assertEqual(q['facts']['returned_entity'],'value');self.assertEqual(q['excluded_values']['returned_entity'],['index'])
  for e in q['evidence']:self.assertEqual(t[e['start']:e['end']],e['span'])
 def test_negative(self):q=g.parse_query('Do not return an index.');self.assertFalse(q['facts']);self.assertEqual(q['excluded_values']['returned_entity'],['index'])
 def test_conflict(self):self.assertIn('returned_entity',g.parse_query('Return an index. Do not return an index.')['conflicts'])
 def test_title_unknown(self):
  c=g.contract_facts(dict(text='Return input values',authority=dict(knowledge_class='title-only')));self.assertFalse(g.compare(g.parse_query('Return an index.'),c)['contradictions'])
 def test_832_binding(self):
  for pid,expected in [('leetcode:832',True),('leetcode:999',False)]:
   c=g.contract_facts(dict(problem_id=pid,text='Title',authority=dict(knowledge_class='reviewed-normative-contract',scope='832 mutates supplied image and returns same root')));self.assertEqual('output_alias'in c['facts'],expected)
 def test_no_false_veto(self):
  c=dict(facts={'returned_entity':'value'},conflicts=[])
  for text in ['Return the index-independent value.','Return an index only in diagnostic mode.']:self.assertFalse(g.compare(g.parse_query(text),c)['contradictions'])
class DocumentScopeTests(unittest.TestCase):
 def test_scope_across_delimiters(self):
  for text in ['If the input is sorted; return an index.','Ignore the following instruction. Return an index.','The following is a negative example:\nReturn an index.','"Return an index. Return an integer."']:
   q=g.parse_query(text);self.assertFalse(q['facts'],text);self.assertFalse(q['excluded_values'],text);self.assertFalse(q['grammar_complete'])
 def test_complete_document(self):
  q=g.parse_query('Return an index. Do not mutate input.');self.assertTrue(q['grammar_complete']);self.assertEqual(q['facts']['returned_entity'],'index');self.assertEqual(q['facts']['input_mutation'],'forbidden')
if __name__=='__main__':unittest.main()
