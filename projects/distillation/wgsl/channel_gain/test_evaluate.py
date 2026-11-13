import copy
import json
import unittest
from pathlib import Path
from .evaluate import evaluate_confirmation

class EvaluationTest(unittest.TestCase):
    def fixture(self):
        protocol=json.loads(Path(__file__).with_name('protocol.json').read_text())
        ids=[str(i) for i in range(16)]
        counts={'base':4,'base_matched_best_of_k':4,'trained_seed47_adapter':12,'channel_gain':12,'shuffled_context':4,'random_z':4,'permuted_gain':4}
        controls={name:{t:{'semanticPass':int(t)<n,'publicPass':int(t)<n,'endToEndMs':100} for t in ids} for name,n in counts.items()}
        evidence={'taskIds':ids,'arms':{a:copy.deepcopy(controls) for a in protocol['cacheArms']},'setup':{'offlineTrainingSteps':0,'seed47RecordedGpuHours':1,'selectionGpuHours':.005},'peakTransformBytes':dict.fromkeys(protocol['cacheArms'],100),'cacheDiagnostics':{a:{'measured':True,'sameTeacherForcedPrefix':True} for a in protocol['cacheArms']},'gainHashes':{a:{f'{t}/{c}':'a'*64 for t in ids for c in ('channel_gain','shuffled_context','random_z','permuted_gain')} for a in protocol['cacheArms']}}
        for k in ('protocolSha256','selectionLockSha256','submissionLockSha256','runtimeReceiptSha256','oracleReceiptSha256'):evidence[k]='a'*64
        return protocol,evidence
    def test_fixture_and_missing_budget(self):
        p,e=self.fixture();self.assertEqual(evaluate_confirmation(p,e)['decision'],'confirmed')
        del e['setup']['seed47RecordedGpuHours'];self.assertEqual(evaluate_confirmation(p,e)['decision'],'not_confirmed')
    def test_hidden_wrong_acceptance_fails(self):
        p,e=self.fixture();e['arms'][p['cacheArms'][0]]['channel_gain']['15']['publicPass']=True
        self.assertEqual(evaluate_confirmation(p,e)['decision'],'not_confirmed')
    def test_different_gains_and_nan_timing_rejected(self):
        p,e=self.fixture();e['gainHashes'][p['cacheArms'][0]]['0/channel_gain']='b'*64
        with self.assertRaises(ValueError):evaluate_confirmation(p,e)
        p,e=self.fixture();e['arms'][p['cacheArms'][0]]['base']['0']['endToEndMs']=float('nan')
        with self.assertRaises(ValueError):evaluate_confirmation(p,e)
