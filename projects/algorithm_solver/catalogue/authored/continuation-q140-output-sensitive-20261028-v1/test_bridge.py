"""Post-source record-validator controls; frozen reference controls unchanged."""
import importlib.util
from pathlib import Path
import unittest

class CertificateBridgeControls(unittest.TestCase):
    def test_large_zero_certificate_strict_record_and_language_routes(self):
        spec=importlib.util.spec_from_file_location('q140_new_record_bridge',Path(__file__).with_name('host_check.py'));bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
        args=['b'+'a'*19,['a'*size for size in range(1,11)]]
        self.assertEqual(bridge.expected(140,args),[])
        for language in ('python','javascript'):
            record={'native_route':'official-wrapper-q-v1','entry_kind':'python-solution-method' if language=='python' else 'javascript-official-function','problem_id':140,'method':'wordBreak','result':[],'result_type':'list' if language=='python' else 'object','args_before':args,'args_after':args,'alias_edges':[],'node_identity':None,'node_integrity':None}
            self.assertEqual(bridge.check_observation(140,args,record,language),(True,None))
            for change in ({'result':['a']},{'result':False},{'args_after':[]},{'alias_edges':[['result','args.1']]},{'problem_id':True},{'method':'solve'}):
                self.assertFalse(bridge.check_observation(140,args,{**record,**change},language)[0])
    def test_feasible_prefix_delegates_existing_reference(self):
        spec=importlib.util.spec_from_file_location('q140_new_bridge_delegation',Path(__file__).with_name('host_check.py'));bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
        self.assertEqual(bridge.expected(140,['aa',['a','aa']]),['a a','aa'])

if __name__=='__main__':unittest.main()
