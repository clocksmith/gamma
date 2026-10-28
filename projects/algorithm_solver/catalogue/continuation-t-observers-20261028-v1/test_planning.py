"""Prospective source-free plan and model-record controls, no actual candidates."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
plan=load('t_test_planning','plan.py');host=load('t_test_model_host','host_check.py')
class Planning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases,cls.freeze=plan.references();cls.data=cls.cases.build_cases()
    def test_full_suite_no_silent_drop(self):
        self.assertEqual(sum(map(len,self.data.values())),2174)
        for pid,rows in self.data.items():
            result=plan.batch_plan(pid,rows,self.cases.o);covered={i for batch in result['batches'] for i in batch['indices']};blocked={row['case'] for row in result['blocked_cases']}
            self.assertEqual(covered|blocked,set(range(len(rows))));self.assertFalse(covered&blocked)
            for batch in result['batches']:
                self.assertLessEqual(len(batch['indices']),33);packet=plan.packet(pid,rows,batch['indices'])
                self.assertTrue(all(set(call)=={'args'} for call in packet['calls']))
                self.assertLessEqual(len(plan.encoded(packet)),plan.MAX_HOST_PACKET_BYTES)
                self.assertLessEqual(max(batch['projected_output_bytes'].values()),plan.MAX_OUTPUT_BYTES)
    def test_prospective_records_match_host_contracts(self):
        for pid,rows in self.data.items():
            # Include every case with large/native boundary envelopes, plus
            # first/last; ordinary semantic suite is independently owner-tested.
            indices={0,len(rows)-1}|{i for i,row in enumerate(rows) if len(plan.encoded(row['args']))>5000}
            for index in indices:
                row=rows[index]
                for language in ('python','javascript'):
                    record=plan.successful_record(pid,row['args'],row['expected'],language,self.cases.o)
                    self.assertEqual(host.check_observation(pid,row['args'],record,language),(True,None))
if __name__=='__main__':unittest.main()
