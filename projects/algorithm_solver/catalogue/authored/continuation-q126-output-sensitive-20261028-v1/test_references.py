"""Reference/certificate/record controls only; no candidate imports or calls."""
import copy
import importlib.util
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
cases=load(HERE/'cases.py','q126_certificate_controls');bridge=load(HERE/'host_check.py','q126_record_controls')
class ReferenceControls(unittest.TestCase):
    def test_required_chain_is_unique_fifty_edge_path(self):
        args=cases.induced_chain_args();wanted=cases.induced_path_certificate(args)
        self.assertEqual(args[0],'aa');self.assertEqual(args[1],'zz');self.assertEqual(len(args[2]),50)
        self.assertEqual(len(wanted),1);self.assertEqual(len(wanted[0]),51);self.assertEqual(wanted[0][:5],['aa','ba','bb','cb','cc'])
        self.assertEqual(wanted[0][-2:],['zy','zz'])
    def test_bounded_chain_controls_match_existing_exhaustive_graph_oracle(self):
        for last_letter in range(1,8):
            args=cases.induced_chain_args(last_letter)
            self.assertEqual(cases.induced_path_certificate(args),cases.reference.reference(126,args))
    def test_chord_or_disconnection_cannot_claim_unique_path_certificate(self):
        args=cases.induced_chain_args();args[2][args[2].index('mm')]='ab'
        with self.assertRaises(ValueError):cases.induced_path_certificate(args)
    def test_original_cases_and_memberships_unchanged(self):
        original=cases.generator.build_cases(126,include_maximum=True);new=cases.build_cases()
        self.assertEqual(len(new),len(original)+1)
        for index,(old,row) in enumerate(zip(original,new)):
            self.assertEqual({key:value for key,value in row.items() if key!='inherited_q_case_index'},old)
            self.assertEqual(row['inherited_q_case_index'],index)
    def test_record_bridge_both_official_languages_and_strict_failures(self):
        args=cases.induced_chain_args();wanted=cases.induced_path_certificate(args)
        for language in ('python','javascript'):
            record={'native_route':'official-wrapper-q-v1','entry_kind':'python-solution-method' if language=='python' else 'javascript-official-function','problem_id':126,'method':'findLadders','result':wanted,'result_type':'list' if language=='python' else 'object','args_before':args,'args_after':copy.deepcopy(args),'alias_edges':[],'node_identity':None,'node_integrity':None}
            self.assertEqual(bridge.check_observation(126,args,record,language),(True,None))
            for change in ({'result':[]},{'result':wanted+wanted},{'result':[list(reversed(wanted[0]))]},{'args_after':[]},{'alias_edges':[['result.0','args.2']]},{'problem_id':True},{'method':'solve'}):
                self.assertFalse(bridge.check_observation(126,args,{**record,**change},language)[0])
    def test_bridge_keeps_existing_multi_answer_reference(self):
        args=['hit','cog',['hot','dot','dog','lot','log','cog']]
        self.assertEqual(bridge.expected(126,args),cases.reference.reference(126,args))

if __name__=='__main__':unittest.main()
