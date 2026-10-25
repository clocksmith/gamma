"""Synthetic adapted evidence tests; solution text remains inert data."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_adapted as v
b=v.b
class AdaptedVerificationTests(unittest.TestCase):
    def fixture(self,root):
        source=b'class Solution { sample() { return 1; } }\n';complete,adapter=v.adapted.emit(source,'sample');(root/'6.js').write_bytes(complete)
        item={'id':6,'path':'6.js','candidate_bytes':len(source),'adapter_bytes':len(adapter),'complete_bytes':len(complete),'candidate_sha256':b.sha(source),'adapter_sha256':b.sha(adapter),'adapted_sha256':b.sha(complete)}
        observation={'result':1,'result_type':'number','args_before':[],'args_after':[],'alias_edges':[],'error':None}
        loaded={6:{'cases':b.encoded([{'args':[],'expected':1}]),'baseline':b.encoded([observation])}}
        contract={'schema':'gamma.adapted-paired-qualification.v1','ids':[6],'input_hashes':{},'input_manifest_sha256':'manifest','code_sha256':b.sha(Path(v.adapted.__file__).read_bytes()),'baseline_loader_sha256':b.sha(Path(b.__file__).read_bytes()),'paired_verifier_sha256':b.sha(Path(v.adapted.paired.__file__).read_bytes()),'batch_cases':32,'protected_access':False,'runtime':{},'harness_sha256':b.sha((b.LIT/'admission500-v1/harness.cjs').read_bytes()),'oracle_sha256':b.sha((b.LIT/'admission500-v1/qualify_rules.py').read_bytes()),'sources':[item]};b.write(root/'contract.json',contract)
        stdout=b.encoded({'i':0,**observation})+b.encoded({'done':1});(root/'6-0.stdout').write_bytes(stdout);(root/'6-0.stderr').write_bytes(b'')
        report={'contract_sha256':b.sha((root/'contract.json').read_bytes()),'status':'completed','rows':[{'id':6,'adapted_sha256':item['adapted_sha256'],'cases':1,'checks_passed':1,'passed':True,'failures':[],'calls':[{'stem':'6-0','exit_code':0,'timed_out':False,'stdout_sha256':b.sha(stdout),'stderr_sha256':b.sha(b'')}]}],'candidate_executions':1};b.write(root/'report.json',report)
        pool={'qualification_report_sha256':b.sha((root/'report.json').read_bytes()),'qualification_contract_sha256':report['contract_sha256'],'alternatives':[item]};b.write(root/'fit-pool.json',pool)
        return loaded,report,pool
    def test_independent_observation_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);loaded,report,pool=self.fixture(root)
            with patch.object(b,'load_inputs',return_value=(loaded,{},'manifest')),patch.object(v.adapted.paired,'inputs'),patch.object(b.pinned_runtime,'validate_manifest'):
                self.assertEqual(len(v.verify(root,root/'report.json')['alternatives']),1)
                raw=(root/'6-0.stdout').read_bytes().replace(b'"result":1',b'"result":2');(root/'6-0.stdout').write_bytes(raw);report['rows'][0]['calls'][0]['stdout_sha256']=b.sha(raw);b.write(root/'report.json',report)
                pool['qualification_report_sha256']=b.sha((root/'report.json').read_bytes());b.write(root/'fit-pool.json',pool)
                with self.assertRaisesRegex(ValueError,'independent replay'):v.verify(root,root/'report.json')
    def test_source_and_adapter_bytes_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);loaded,report,pool=self.fixture(root)
            with patch.object(b,'load_inputs',return_value=(loaded,{},'manifest')),patch.object(v.adapted.paired,'inputs'),patch.object(b.pinned_runtime,'validate_manifest'):
                with (root/'6.js').open('ab') as stream:stream.write(b'/*hidden*/')
                with self.assertRaisesRegex(ValueError,'source or charged adapter'):v.verify(root,root/'report.json')
if __name__=='__main__':unittest.main()
