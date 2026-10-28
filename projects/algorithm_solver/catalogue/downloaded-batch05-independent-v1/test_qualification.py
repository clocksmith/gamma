"""Synthetic controller controls only; never imports a candidate program."""
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import qualify as q


@dataclass
class Observation:
    stdout: bytes
    stderr: bytes=b''
    exit_code: int=0
    timed_out: bool=False
    output_limit_exceeded: bool=False


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.output=self.root/'output'
        self.args=SimpleNamespace(output=self.output,freeze_sha256='fixed',gate_sha256='gate',statements=self.root)
        self.rows={560:[{'args':[[1,1],2],'expected':1}]}
        self.source=b'# inert synthetic fixture; never executed\n'
        self.row={'path':'python/560.py','sha256':q.sha(self.source)}
        (self.root/'python').mkdir();(self.root/'python/560.py').write_bytes(self.source)
        observer=q.engine.TRANSPORT/'harness.py'
        self.value={'plans':{'560':[[0,0]]},'reviews':{'560:python':{'approved':True,'dispatch_approved':True,'record':{}}},
                    'runtime':{'synthetic':True},'artifact_hashes':{str(observer):q.sha((q.ROOT/observer).read_bytes())}}
        self.observed={'i':0,'result':1,'result_type':'int','args_before':[[1,1],2],'args_after':[[1,1],2],'alias_edges':[]}
        self.raw=b'\n'.join([q.encoded(self.observed),q.encoded({**self.observed,'i':1}),q.encoded({'done':2})])+b'\n'

    def controls(self):
        return (patch.object(q,'verified',return_value=(self.value,self.root,{(560,'python'):self.row},{},self.rows)),
                patch.object(q,'SELECTED',(560,)),patch.object(q,'LANGUAGES',('python',)),
                patch.object(q.engine,'access'),patch.object(q.engine.sandbox,'run',return_value=Observation(self.raw)))

    def execute(self):
        a,b,c,d,e=self.controls()
        with a,b,c,d,e as runner:
            result=q.run_or_replay(self.args)
            self.assertEqual(runner.call_count,1)
            return result

    def replay(self):
        a,b,c,d,e=self.controls()
        with a,b,c,d,e as runner:
            result=q.run_or_replay(self.args,True)
            runner.assert_not_called()
            return result

    def test_roundtrip_replay_without_execution(self):
        self.assertEqual(self.execute()['executed_calls'],2)
        self.assertEqual(self.replay()['qualified_finite_suite_programs'],1)

    def test_missing_review_is_blocked_not_pass(self):
        self.value['reviews']['560:python']['approved']=False
        self.value['reviews']['560:python']['dispatch_approved']=False
        a,b,c,d,e=self.controls()
        with a,b,c,d,e as runner:
            result=q.run_or_replay(self.args);runner.assert_not_called()
        self.assertEqual(result['executed_calls'],0)
        self.assertEqual(result['qualified_finite_suite_programs'],0)
        self.assertTrue(q.read_json(self.output/'560-python.summary.json')['blocked_review'])
        self.replay()

    def test_failure_preserved_and_replayed(self):
        self.raw=b'{"done":false}\n'
        self.assertEqual(self.execute()['qualified_finite_suite_programs'],0)
        self.assertEqual((self.output/'560-python-0000.stdout').read_bytes(),self.raw)
        self.assertEqual(self.replay()['qualified_finite_suite_programs'],0)

    def test_raw_stream_tamper_rejected(self):
        self.execute();(self.output/'560-python-0000.stdout').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'raw evidence'):self.replay()

    def test_start_tamper_rejected(self):
        self.execute();(self.output/'560-python-0000.start.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'batch identity'):self.replay()

    def test_summary_tamper_rejected(self):
        self.execute();(self.output/'560-python.summary.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'summary'):self.replay()

    def test_source_drift_blocks_before_sandbox(self):
        (self.root/'python/560.py').write_bytes(b'drift')
        a,b,c,d,e=self.controls()
        with a,b,c,d,e as runner:
            with self.assertRaisesRegex(ValueError,'source changed'):q.run_or_replay(self.args)
            runner.assert_not_called()

    def test_gate_denial_blocks_before_source_read(self):
        a,b,c,d,e=self.controls()
        with a,b,c,d as access,e as runner,patch.object(q.engine,'bounded_regular_read') as read:
            access.side_effect=PermissionError('denied')
            with self.assertRaises(PermissionError):q.run_or_replay(self.args)
            read.assert_not_called();runner.assert_not_called()

    def test_definition_reader_live_per_open(self):
        self.args.statements=self.root
        with patch.object(q.engine,'access') as access,patch.object(q.engine,'bounded_regular_read',return_value=b'{}') as read:
            reader=q.definition_reader(self.args,{})
            reader(self.root/'560.json');reader(self.root/'560.json')
            self.assertEqual(access.call_count,4);self.assertEqual(read.call_count,2)
            for pid in q.RESERVED+q.BLOCKED:
                with self.assertRaises(ValueError):reader(self.root/f'{pid}.json')

    def test_process_boolean_exit_is_failure(self):
        status={'exit_code':False,'timed_out':False,'output_limit_exceeded':False}
        self.assertEqual(q.verdict(560,'python',self.rows[560],[0],status,self.raw)[0]['reason'],'sandbox_process_failure')

    def test_no_zero_execution_pass(self):
        result=q.summary(560,'python',self.rows[560],{'approved':True,'dispatch_approved':True},0,[])
        self.assertFalse(result['complete_prepared_suite_passed'])

    def test_mandatory_complexity_failure_cannot_qualify_even_if_values_pass(self):
        self.value['reviews']['560:python']['approved']=False
        result=self.execute()
        self.assertEqual(result['executed_calls'],2)
        self.assertEqual(result['qualified_finite_suite_programs'],0)
        summary=q.read_json(self.output/'560-python.summary.json')
        self.assertTrue(summary['complete_prepared_suite_passed'])
        self.assertFalse(summary['mandatory_review_approved'])
        self.replay()

    def test_dispatch_exception_retained_without_fabricated_process_result(self):
        a,b,c,d,e=self.controls()
        with a,b,c,d,e as runner:
            runner.side_effect=RuntimeError('synthetic sandbox unavailable')
            with self.assertRaises(RuntimeError):q.run_or_replay(self.args)
        saved=q.read_json(self.output/'560-python-0000.dispatch-error.json')
        self.assertEqual(saved['exception_type'],'RuntimeError')
        self.assertFalse(saved['process_result_available'])
        self.assertFalse((self.output/'560-python-0000.result.json').exists())

    def test_no_host_runtime_fallback(self):
        with patch.object(q.engine.sys,'platform','darwin'):
            with self.assertRaises(q.engine.sandbox.SandboxUnavailable):q.engine.runtime()


if __name__=='__main__':unittest.main()
