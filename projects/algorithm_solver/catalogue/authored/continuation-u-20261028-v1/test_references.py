"""Source-free U domain, reference, effect and multiplicity controls."""
import importlib.util
from pathlib import Path
import json
import unittest
ROOT=Path(__file__).parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
o=load('gamma_u_test_reference','oracles.py');cases=load('gamma_u_test_cases','cases.py')
class References(unittest.TestCase):
    def test_public_example(self):
        p={'values':[1,2,3,5],'left':[1,None,None,None],'right':[2,3,None,None],'root':0};self.assertEqual(o.expected(257,[p]),['1->2->5','1->3'])
    def test_single_negative(self):self.assertEqual(o.expected(257,[cases.complete([-100])]),['-100'])
    def test_anyorder_multiset(self):
        p=cases.complete([1,2,3]);self.assertTrue(o.accepts_result(257,[p],['1->3','1->2']))
    def test_duplicate_strings_are_required(self):
        p=cases.complete([1,2,2]);self.assertEqual(o.expected(257,[p]),['1->2','1->2']);self.assertFalse(o.accepts_result(257,[p],['1->2']));self.assertTrue(o.accepts_result(257,[p],['1->2','1->2']))
    def test_malformed_alias_or_cycle_rejected(self):
        p={'values':[1,2],'left':[1,None],'right':[1,None],'root':0}
        with self.assertRaises(ValueError):o.validate(257,[p])
        p={'values':[1,2],'left':[1,0],'right':[None,None],'root':0}
        with self.assertRaises(ValueError):o.validate(257,[p])
    def test_empty_and_disconnected_rejected(self):
        with self.assertRaises(ValueError):o.validate(257,[{'values':[],'left':[],'right':[],'root':None}])
        with self.assertRaises(ValueError):o.validate(257,[{'values':[1,2],'left':[None,None],'right':[None,None],'root':0}])
    def test_bool_value_or_pointer_rejected(self):
        with self.assertRaises(ValueError):o.validate(257,[{'values':[True],'left':[None],'right':[None],'root':0}])
        with self.assertRaises(ValueError):o.validate(257,[{'values':[1],'left':[None],'right':[None],'root':False}])
    def test_permuted_pool_does_not_change_paths(self):
        p=cases.complete([1,2,3,4,5]);q=cases.permute(p,[3,1,4,2,0]);self.assertEqual(o.expected(257,[p]),o.expected(257,[q]))
    def test_readonly_effect_record(self):
        args=[cases.complete([1,2,2])];plan=o.effect_plan(257,args);identity={key:plan[key] for key in ('before','after','argument_roots','fixture_roots','result_root','result_order')};record={'args_before':args,'args_after':args,'node_identity':identity,'result':['1->2','1->2']};self.assertEqual(o.check_observation(257,args,record,'python'),(True,None));bad=json.loads(json.dumps(record));bad['node_identity']['after'][0]['value']=9;self.assertFalse(o.check_effects(257,args,bad)[0])
    def test_all_premium_members_stay_unavailable(self):
        for pid in o.BLOCKED_IDS:
            with self.assertRaises(ValueError):o.validate(pid,[cases.complete([1])])
    def test_maximum_depth_without_reference_recursion(self):
        p=cases.chain([-100]*100,True);self.assertEqual(o.expected(257,[p]),['->'.join(['-100']*100)])
    def test_generated_suite_valid_and_inputs_unchanged(self):
        data=cases.build_cases();self.assertEqual(set(data),{257});self.assertGreater(len(data[257]),1500)
        for row in data[257]:
            before=cases.encoded(row['args']);o.validate(257,row['args']);self.assertTrue(o.accepts_result(257,row['args'],row['expected']));self.assertEqual(before,cases.encoded(row['args']))
if __name__=='__main__':unittest.main()
