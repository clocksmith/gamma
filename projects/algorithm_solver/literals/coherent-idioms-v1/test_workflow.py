"""Service-bound development workflow tests with synthetic source fixtures."""
from pathlib import Path
import tempfile
import unittest
import run


class FakeService:
    def __init__(self, mismatch=False):
        self.calls=[]; self.mismatch=mismatch
    def request(self, pid, *, language, include_source):
        self.calls.append((pid,language,include_source))
        if pid.endswith(':2'):
            return {'status':'abstain','reason':'source_not_authorized'}
        source='def solve(x):\n    return x\n'
        digest=run.sha(source.encode())
        return {'artifact':{'status':'materialized','source_utf8':source},
            'consumer_selection':{'implementation':{'status':'qualified',
                'source_sha256':'0'*64 if self.mismatch else digest,
                'receipt_sha256':'1'*64,'problem_contract_sha256':'2'*64,
                'runtime_sha256':'3'*64,'tests_sha256':'4'*64,
                'contract_scope':'synthetic unit fixture only','caveats':[]}}}


class WorkflowTest(unittest.TestCase):
    def test_materialization_keeps_service_abstentions_and_exact_evidence(self):
        service=FakeService()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'sources'
            records,membership=run.materialize(service,[1,2],'python',root)
            self.assertEqual(set(records),{'1'})
            self.assertEqual(len(membership),2)
            self.assertEqual(membership[1]['status'],'unavailable')
            self.assertFalse((root/'2.source').exists())
            self.assertEqual(run.sha((root/'1.source').read_bytes()),records['1']['sha256'])
            self.assertEqual(records['1']['problem_id'],'leetcode:1')
            self.assertEqual(service.calls,[('leetcode:1','python',True),('leetcode:2','python',True)])

    def test_stale_source_binding_fails_without_writing_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'sources'
            with self.assertRaisesRegex(ValueError,'qualification binding'):
                run.materialize(FakeService(mismatch=True),[1],'python',root)
            self.assertEqual(list(root.iterdir()),[])

    def test_complete_packets_charge_framing_padding_and_dictionary(self):
        for width in (6,7,8):
            table={'width':width,'entries':[{'literal':'return '},{'literal':'value;'}]}
            spans=[{'code':0},{'code':1}]
            dictionary,packet=run.packet_for_complete('return value;',table,spans)
            self.assertEqual(run.PACKET.decode(dictionary,packet),'return value;')
            self.assertEqual(len(packet),41+(2*width+7)//8)
            self.assertEqual(len(dictionary),8+2*4+len('return value;'.encode()))
            with self.assertRaisesRegex(ValueError,'uncovered'):
                run.packet_for_complete('return value;',table,[{'code':0},{'code':None}])
            with self.assertRaises(ValueError):
                run.packet_for_complete('different',table,spans)

    def test_summary_retains_unavailable_and_uncovered_denominator(self):
        report={'total_programs':2,'uncovered_bytes':5,'programs':{
            '1':{'complete':True,'selections':7,'selection_bits':42},
            '2':{'complete':False,'selections':2,'selection_bits':12}}}
        summary=run.summarize(report,3)
        self.assertEqual(summary['population'],3)
        self.assertEqual(summary['complete_programs'],1)
        self.assertEqual(summary['unavailable_sources'],1)
        self.assertEqual(summary['median_selections'],7)
        self.assertEqual(summary['selection_bits_on_complete_programs'],42)
        self.assertIsNone(summary['packet_bits_on_complete_programs'])
        self.assertIsNone(summary['singleton_selection_bits_on_complete_programs'])
        report['programs']['1'].update(packet_bits=376,singleton_selection_bits=0)
        self.assertEqual(run.summarize(report,3)['packet_bits_on_complete_programs'],376)
        report['programs']['1']['complete']=False
        self.assertIsNone(run.summarize(report,3)['median_selections'])


if __name__=='__main__':unittest.main()
