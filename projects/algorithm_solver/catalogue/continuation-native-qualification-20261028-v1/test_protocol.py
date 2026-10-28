"""Source-free native protocol controls; no numbered candidate is loaded."""
import importlib.util
import json
from pathlib import Path
import unittest

SPEC=importlib.util.spec_from_file_location('native_qualification_protocol',Path(__file__).with_name('protocol.py'))
p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)

class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pop=p.population();cls.data,cls.owners=p.cases_and_owners(cls.pop)

    def record(self,pid=3709,language='python'):
        case=self.data[pid][0];expected=case['expected']
        types=['constructed']
        for name in case['args'][0][1:]:
            types.append(('int' if language=='python' else 'number') if name in ('totalScore','getHighestBidder') else ('list' if language=='python' else 'object') if name=='matchDriverWithRider' else ('NoneType' if language=='python' else 'undefined'))
        return {'i':0,'result':expected,'result_type':p.return_type(pid,case,language),'args_before':case['args'],'args_after':case['args'],'alias_edges':[],
            'native_route':'direct-class-v1','native_class':self.owners[pid].oracle.CLASSES[pid],'native_receiver_count':1,
            'native_method_snapshots':expected,'native_method_return_types':types}

    def test_fixed_population(self):
        self.assertEqual(p.IDS,{'native':(3709,3815,3829)})

    def test_all_maxima_retained(self):
        for pid,rows in self.data.items():
            self.assertEqual(rows[-1]['category'],'analytic-maximum-method-count')
            plan=p.batch_plan(pid,rows)
            self.assertFalse(plan['blocked_cases']);self.assertEqual(plan['admitted_distinct_cases'],len(rows))
            for batch in plan['batches']:
                self.assertLessEqual(batch['input_bytes'],p.MAX_INPUT_BYTES)
                self.assertLessEqual(max(batch['projected_output_bytes'].values()),p.LIMITS.max_output_bytes)

    def test_packet_contains_no_expected(self):
        packet=p.packet(self.data[3709],[0]);self.assertEqual(set(packet),{'schema','native_problem_id','calls'})
        self.assertEqual(set(packet['calls'][0]),{'args'})

    def test_both_languages_native(self):
        for pid in p.IDS['native']:
            for language in p.LANGUAGES:
                self.assertIsNone(p.compare(pid,language,self.data[pid][0],self.record(pid,language),self.owners[pid]))

    def test_bad_route_receiver_type_and_state(self):
        for field,value in [('native_route','solve'),('native_receiver_count',True),('native_method_return_types',[]),('native_method_snapshots',[])]:
            record=self.record();record[field]=value
            self.assertIsNotNone(p.compare(3709,'python',self.data[3709][0],record,self.owners[3709]))

    def test_effects_and_aliases(self):
        for field,value in [('args_after',[]),('alias_edges',[[0,1]]),('result',[True])]:
            record=self.record();record[field]=value
            self.assertIsNotNone(p.compare(3709,'python',self.data[3709][0],record,self.owners[3709]))

    def test_partial_duplicate_and_extra_streams(self):
        record=self.record()
        for raw in [p.encoded(record),p.encoded(record)+b'\n{"done":true}\n',p.encoded(record)+b'\n{"done":1,"done":1}\n']:
            with self.assertRaises(ValueError):p.parse(raw,1)
        record['unexpected']=1
        with self.assertRaises(ValueError):p.parse(p.encoded(record)+b'\n{"done":1}\n',1)

    def test_process_failure_retained(self):
        failures=p.verdict(3709,'python',self.data[3709],[0],{'exit_code':1,'timed_out':False,'output_limit_exceeded':False},b'',self.owners[3709])
        self.assertEqual(failures,[{'case':0,'reason':'sandbox_process_failure'}])

    def test_missing_review_cannot_qualify(self):
        rows=self.data[3709];plan=p.batch_plan(3709,rows)
        result=p.program_summary(3709,'python',rows,plan,[],100,{'approved':False})
        self.assertFalse(result['qualified']);self.assertFalse(result['official_wrapper_execution_qualified'])

    def test_unknown_packet_class(self):
        with self.assertRaises(KeyError):p.packet([{'args':[['Unknown'],[[]]]}],[0])

if __name__=='__main__':unittest.main()
