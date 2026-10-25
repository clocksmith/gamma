import unittest
import axis944 as a
class Tests(unittest.TestCase):
 def test_distinct_axes(self):self.assertTrue(a.extract('I have not specified whether sorting means each column, each row, or whole rows.'))
 def test_equivalent_axes(self):self.assertFalse(a.extract('I have not specified whether sorting means each column or columns independently.'))
 def test_omission_unknown(self):
  for t in ['Delete columns to make strings sorted.','Return a count of columns.','Sort each column independently.']:self.assertFalse(a.extract(t))
 def test_resolved_both_orders(self):
  u='The sorting axis is unspecified.';r='Sort each column independently.'
  for t in (u+' '+r,r+' '+u):self.assertFalse(a.extract(t))
 def test_scopes(self):
  for t in ['If needed; the sorting axis is unspecified.','"The sorting axis is unspecified."','It is false that the sorting axis is unspecified.','The sorting axis for optional debugging is unspecified.']:self.assertFalse(a.extract(t))
 def test_selected_only_delivery(self):
  o=dict(value='independent-columns');b=dict(status='accepted',problem_id='leetcode:944',implementations={'source':'private'});v,e=a.apply('The sorting axis is unspecified.',b,o);self.assertEqual(v['status'],'abstain');self.assertNotIn('implementations',v)
  b['problem_id']='leetcode:955';self.assertEqual(a.apply('The sorting axis is unspecified.',b,o)[0],b)
class IncompatibleResolutionTests(unittest.TestCase):
 def test_incompatible_axis_resolves_uncertainty(self):
  unknown='I have not specified whether sorting means each column or each row.'
  for resolved in ['Sort each row independently.','Sorting means each row.','The sorting axis is within rows.']:
   for t in (unknown+' '+resolved,resolved+' '+unknown):self.assertFalse(a.extract(t),t)
if __name__=='__main__':unittest.main()
