"""Synthetic repair controls; no candidate module is imported or executed."""
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import protocol as p


@dataclass
class Observation:
    stdout:bytes
    stderr:bytes=b''
    exit_code:int=0
    timed_out:bool=False
    output_limit_exceeded:bool=False


class RepairControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'python').mkdir()
        self.source=b'# inert synthetic fixture never executed\n';(self.root/'python/695.py').write_bytes(self.source)
        self.args=SimpleNamespace(output=self.root/'output',freeze_sha256='syntheticfreeze',gate_sha256='syntheticgate')
        self.rows=[{'args':[[[1]]],'expected':1}]
        observer=p.E.TRANSPORT/'harness.py'
        self.value={'execution_gate_sha256':'syntheticgate','runtime':{'synthetic':True},'artifact_hashes':{str(observer):p.sha((p.ROOT/observer).read_bytes())},'plan':[[0,0]]}
        row={'i':0,'result':1,'result_type':'int','args_before':[[[1]]],'args_after':[[[1]]],'alias_edges':[]}
        self.raw=b'\n'.join([p.encoded(row),p.encoded({**row,'i':1}),p.encoded({'done':2})])+b'\n'

    def operation(self,replay=False,error=None):
        with patch.object(p,'verified',return_value=(self.value,{},self.rows)),patch.object(p,'SOURCE_DIR',self.root),patch.object(p,'SOURCE_SHA',p.sha(self.source)),patch.object(p.E,'access'),patch.object(p.E.sandbox,'run',return_value=Observation(self.raw)) as run:
            if error:run.side_effect=error
            result=p.run_or_replay(self.args,replay)
            self.assertEqual(run.call_count,0 if replay else 1)
            return result

    def test_raw_roundtrip_without_reexecution(self):
        self.assertTrue(self.operation()['qualified_finite_suite'])
        self.assertTrue(self.operation(True)['qualified_finite_suite'])

    def test_error_stream_retained_before_judgment(self):
        self.raw=b'{"i":0,"error":"synthetic failure"}\n{"i":1,"error":"synthetic failure"}\n{"done":2}\n'
        self.assertFalse(self.operation()['qualified_finite_suite'])
        self.assertEqual((self.args.output/'695-python-0000.stdout').read_bytes(),self.raw)
        self.assertFalse(self.operation(True)['qualified_finite_suite'])

    def test_tampered_raw_rejected(self):
        self.operation();(self.args.output/'695-python-0000.stdout').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'raw failure evidence'):self.operation(True)

    def test_tampered_start_rejected(self):
        self.operation();(self.args.output/'695-python-0000.start.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'batch binding'):self.operation(True)

    def test_tampered_summary_rejected(self):
        self.operation();(self.args.output/'report.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'report mismatch'):self.operation(True)

    def test_dispatch_exception_retained(self):
        with self.assertRaises(RuntimeError):self.operation(error=RuntimeError('synthetic unavailable'))
        self.assertFalse(p.read_json(self.args.output/'695-python-0000.dispatch-error.json')['process_result_available'])
        self.assertFalse((self.args.output/'695-python-0000.result.json').exists())

    def test_source_drift_blocks_dispatch(self):
        (self.root/'python/695.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'source/observer drift'):self.operation()

    def test_reference_dsu_crosschecks72_cases(self):
        rows=p.generated();self.assertEqual(len(rows),72)
        self.assertIn(2500,[r['expected'] for r in rows]);self.assertIn(1275,[r['expected'] for r in rows])

    def review_fixture(self):
        _,row,problem=p.metadata()
        pins=p.sourcefree_files()
        pins[str((p.BATCH05/'oracles.py').relative_to(p.ROOT))]=p.sha((p.BATCH05/'oracles.py').read_bytes())
        pins[str(p.E.TRANSPORT/'harness.py')]=p.sha((p.ROOT/p.E.TRANSPORT/'harness.py').read_bytes())
        record={'problem_id':695,'language':'python','source_sha256':p.SOURCE_SHA,'manifest_sha256':p.MANIFEST_SHA,
                'semantics_sha256':row['semantics_sha256'],'reference_sha256':pins[str((p.BATCH05/'oracles.py').relative_to(p.ROOT))],
                'case_generator_sha256':pins[str((p.SOURCE_DIR/'cases.py').relative_to(p.ROOT))],
                'definition_content_sha256':problem['statement_constraints_snapshot']['content_sha256'],
                'interface_api_sha256':p.sha(p.encoded(problem['external_interface']['official_metadata'])),
                'observer_sha256':pins[str(p.E.TRANSPORT/'harness.py')],'shared_effect_observer_sha256':pins[str(p.E.TRANSPORT/'harness.py')],
                'reviewer':'synthetic reviewer',**{flag:True for flag in p.E.REVIEW_FLAGS}}
        return record,pins

    def test_manual_acceptance_exact_api_serialization(self):
        record,pins=self.review_fixture()
        self.assertEqual(record['interface_api_sha256'],'03b2b267d2bfe95c54a8a43e26c360fbbd2f281651e44b8d9b363fa1cf0d5181')
        self.assertTrue(p.accept_manual_record(record,pins)['accepted'])

    def test_each_false_mandatory_flag_rejected(self):
        record,pins=self.review_fixture()
        for flag in p.E.REVIEW_FLAGS:
            with self.assertRaisesRegex(ValueError,'all7'):p.accept_manual_record({**record,flag:False},pins)

    def test_wrong_variant_interface_or_observer_rejected(self):
        record,pins=self.review_fixture()
        for field in ('source_sha256','semantics_sha256','interface_api_sha256','observer_sha256','manifest_sha256','reference_sha256'):
            with self.assertRaisesRegex(ValueError,'binding mismatch'):p.accept_manual_record({**record,field:'wrong'},pins)
        with self.assertRaises(ValueError):p.accept_manual_record({**record,'problem_id':True},pins)

    def test_no_nonlinux_freeze(self):
        with patch.object(p.E.sys,'platform','darwin'):
            with self.assertRaises(p.E.sandbox.SandboxUnavailable):p.E.runtime()


if __name__=='__main__':unittest.main()
