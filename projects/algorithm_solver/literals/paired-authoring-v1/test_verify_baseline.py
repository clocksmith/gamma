"""Synthetic evidence-tampering tests; never executes source code."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_baseline as verify
b=verify.replay
class VerificationTests(unittest.TestCase):
    def fixture(self,root):
        observation={'result':1,'result_type':'number','args_before':[],'args_after':[],'alias_edges':[],'error':None}
        loaded={6:{'cases':b.encoded([{'args':[],'expected':1}]),'baseline':b.encoded([observation])}}
        contract={'ids':[6],'input_hashes':{},'input_manifest_sha256':'manifest','runner_sha256':b.sha(Path(b.__file__).read_bytes()),'host_judge_sha256':b.sha(Path(b.host_judge.__file__).read_bytes()),'sandbox_sha256':b.sha(Path(b.sandbox.__file__).read_bytes()),'runtime_adapter_sha256':b.sha(Path(b.pinned_runtime.__file__).read_bytes()),'batch_cases':32,'protected_access':False,'runtime':{},'historical_code_sha256':{name:b.sha((b.LIT/'admission500-v1'/name).read_bytes()) for name in ('harness.cjs','harness-exact-integer.cjs','qualify_rules.py')}}
        b.write(root/'contract.json',contract)
        stdout=b.encoded({'i':0,**observation})+b.encoded({'done':1});(root/'6-0.stdout').write_bytes(stdout);(root/'6-0.stderr').write_bytes(b'')
        report={'contract_sha256':b.sha((root/'contract.json').read_bytes()),'status':'completed','m1_qualified':False,'protected_access':False,'rows':[{'id':6,'cases':1,'checks_passed':1,'passed':True,'failures':[],'calls':[{'stem':'6-0','exit_code':0,'timed_out':False,'stdout_sha256':b.sha(stdout),'stderr_sha256':b.sha(b'')}]}],'qualified':1,'candidate_executions':1,'checks_passed':1,'cases':1};b.write(root/'report.json',report)
        return loaded,report
    def test_replays_and_rejects_forged_output_even_with_updated_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);loaded,report=self.fixture(root)
            with patch.object(b,'load_inputs',return_value=(loaded,{},'manifest')),patch.object(b.pinned_runtime,'validate_manifest'):
                self.assertTrue(verify.verify(root,root/'report.json',[6])['verified'])
                raw=(root/'6-0.stdout').read_bytes().replace(b'"result":1',b'"result":2');(root/'6-0.stdout').write_bytes(raw)
                report['rows'][0]['calls'][0]['stdout_sha256']=b.sha(raw);b.write(root/'report.json',report)
                with self.assertRaisesRegex(ValueError,'oracle/parity'):verify.verify(root,root/'report.json',[6])
    def test_rejects_wrong_population_and_execution_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);loaded,report=self.fixture(root)
            with patch.object(b,'load_inputs',return_value=(loaded,{},'manifest')),patch.object(b.pinned_runtime,'validate_manifest'):
                report['candidate_executions']=0;b.write(root/'report.json',report)
                with self.assertRaisesRegex(ValueError,'aggregate coverage'):verify.verify(root,root/'report.json',[6])
                report['rows'].append(report['rows'][0]);b.write(root/'report.json',report)
                with self.assertRaisesRegex(ValueError,'population'):verify.verify(root,root/'report.json',[6])
if __name__=='__main__':unittest.main()
