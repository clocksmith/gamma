"""R12 source-free orchestration/identity/replay controls; no candidates."""
from copy import deepcopy
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

class ReviewControls(unittest.TestCase):
    def setUp(self):
        self.rows,self.contract=p.metadata()
        programs=[]
        for (pid,lang),row in self.rows.items():programs.append({'problem_id':pid,'language':lang,'reviewer':'synthetic independent reviewer',**p.binding(pid,lang,row,self.contract),**{flag:True for flag in p.FLAGS}})
        self.value={'schema':'gamma.r-selected-source-static-review.v1','candidate_executions':0,'observer_profile_sha256':p.PROFILE_SHA,'source_manifest_sha256':p.MANIFEST_SHA,'blocked_ids':list(p.BLOCKED),'blocked_ids_opened':[],'selected_programs':len(self.rows),'programs':programs}
    def test_exact_twelve_selected_slots(self):
        self.assertEqual(len(self.rows),12);self.assertEqual(len(p.accept_reviews(self.value,self.rows,self.contract)),12)
        self.assertTrue(all(r['approved'] for r in p.accept_reviews(self.value,self.rows,self.contract).values()))
    def test_dynamic_counts_not_old_constant(self):
        rows={k:v for k,v in self.rows.items() if k[0]==188};manifest={'available_ids':[188],'blocked_ids':list(p.BLOCKED),'source_inventory':list(rows.values())};profile={'source_bindings':{'source_inventory':list(rows.values())}}
        with patch.object(p,'IDS',(188,)):
            self.assertEqual(len(p.inventory(manifest,profile)),2)
    def test_boolean_integer_identity_rejected(self):
        bad=deepcopy(self.value);bad['programs'][0]['problem_id']=True
        with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
        bad=deepcopy(self.value);bad['selected_programs']=True
        with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
        manifest=p.read_json(p.SOURCE/'manifest.json');manifest['source_inventory'][0]['id']=146.0
        with self.assertRaises(ValueError):p.inventory(manifest)
    def test_duplicate_or_unassigned_identity_rejected(self):
        bad=deepcopy(self.value);bad['programs'].append(bad['programs'][0])
        with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
        manifest=p.read_json(p.SOURCE/'manifest.json');manifest['source_inventory'][0]['id']=156
        with self.assertRaises(ValueError):p.inventory(manifest)
    def test_missing_review_never_approved(self):
        result=p.accept_reviews(None,self.rows,self.contract);self.assertEqual(sum(r['approved'] for r in result.values()),0)
        bad=deepcopy(self.value);bad['programs'].pop();result=p.accept_reviews(bad,self.rows,self.contract);self.assertEqual(sum(r['approved'] for r in result.values()),11)
    def test_all_flags_strict_true_and_templates_exact(self):
        for flag in p.FLAGS:
            bad=deepcopy(self.value);bad['programs'][0][flag]=1
            self.assertFalse(next(iter(p.accept_reviews(bad,self.rows,self.contract).values()))['approved'])
        for name in ('source_sha256','semantics_sha256','observer_sha256','official_language_template_sha256','raw_interface_api_sha256','native_graph_helper_sha256'):
            bad=deepcopy(self.value);bad['programs'][0][name]='wrong'
            self.assertFalse(next(iter(p.accept_reviews(bad,self.rows,self.contract).values()))['approved'])
    def test_source_review_cannot_be_observer_only(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'wrong.json';path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'source review'):p.reviews(SimpleNamespace(review=path),self.rows,self.contract)
    def test_blocked_statement_is_not_opened(self):
        with patch.object(p.E,'access') as access,patch.object(p.E,'bounded_regular_read') as read:
            for pid in p.BLOCKED+(True,146.0):
                with self.assertRaises(ValueError):p.read_statement({},pid,Path('unused'))
            access.assert_not_called();read.assert_not_called()

class RunReplayControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve();self.args=SimpleNamespace(output=self.root/'output',freeze_sha256='syntheticfreeze',gate_sha256='syntheticgate')
        body=b'# inert fixture bytes; sandbox is mocked, never executed\n';self.rows={}
        for lang,suffix in (('python','py'),('javascript','js')):
            (self.root/lang).mkdir();(self.root/lang/f'188.{suffix}').write_bytes(body);self.rows[188,lang]={'path':f'{lang}/188.{suffix}','sha256':p.sha(body)}
        self.data={188:[{'args':[1,[0,7]],'expected':7}]};indices=[0,0];wire=p.PLAN.encoded(p.PLAN.packet(188,self.data[188],indices))
        entry={'indices':indices,'host_input_bytes':len(wire),'projected_output_bytes':{'python':8192,'javascript':8192},'mode':'synthetic-repeat'}
        self.value={'runtime':{'synthetic':True},'artifact_hashes':{'synthetic':'pin'},'plans':{'188':{'batches':[entry],'blocked_cases':[],'admitted_distinct_cases':1}},'source_reviews':{f'188:{lang}':{'approved':True} for lang in p.LANGUAGES},'execution_gate_sha256':'syntheticgate'}
        self.malformed=False;self.process_bad=False
    def result(self,argv,**kwargs):
        lang='python' if 'python' in argv[0] else 'javascript'
        raw=b'\n'.join(p.encoded({'i':i,**p.PLAN.successful_record(188,self.data[188][0]['args'],7,lang,p.CHECK.oracle)}) for i in range(2))+b'\n'+p.encoded({'done':2})+b'\n'
        return Observation(b'{"done":false}\n' if self.malformed else raw,exit_code=False if self.process_bad else 0)
    def operation(self,replay=False,side_effect=None):
        with patch.object(p,'verified',return_value=(self.value,self.rows,{},self.data)),patch.object(p,'SOURCE',self.root),patch.object(p.E,'access'),patch.object(p.E.sandbox,'run',side_effect=side_effect or self.result) as run:
            result=p.run_or_replay(self.args,replay)
            self.assertEqual(run.call_count,0 if replay else 2)
            return result
    def test_raw_roundtrip_dynamic_two_programs(self):
        result=self.operation();self.assertEqual(result['programs'],2);self.assertEqual(result['qualified_finite_suite_programs'],2)
        replay=self.operation(True);self.assertEqual(replay['executed_calls'],4);self.assertTrue(p.read_json(self.args.output/'replay.json')['all_observations_match_report'])
    def test_missing_review_dispatches_nothing(self):
        for row in self.value['source_reviews'].values():row['approved']=False
        with patch.object(p,'verified',return_value=(self.value,self.rows,{},self.data)),patch.object(p.E.sandbox,'run') as run:
            result=p.run_or_replay(self.args);run.assert_not_called()
        self.assertEqual(result['qualified_finite_suite_programs'],0);self.assertEqual(result['blocked_review_programs'],2);self.assertEqual(result['executed_calls'],0)
    def test_no_zero_execution_pass(self):
        plan=self.value['plans']['188'];row=p.summary(188,'python',self.data[188],plan,0,[],{'approved':True});self.assertFalse(row['qualified_finite_suite'])
        row=p.summary(188,'python',self.data[188],plan,2,[],{'approved':False});self.assertFalse(row['qualified_finite_suite'])
    def test_raw_evidence_written_before_verdict(self):
        original=p.verdict
        def check(pid,lang,rows,indices,status,stdout):
            stem=self.args.output/f'188-{lang}-0000'
            for suffix in ('.stdout','.stderr','.result.json'):self.assertTrue(Path(str(stem)+suffix).exists())
            return original(pid,lang,rows,indices,status,stdout)
        with patch.object(p,'verdict',side_effect=check):self.operation()
    def test_protocol_failure_retained_and_replayed(self):
        self.malformed=True;self.assertEqual(self.operation()['qualified_finite_suite_programs'],0)
        self.assertEqual((self.args.output/'188-python-0000.stdout').read_bytes(),b'{"done":false}\n')
        self.assertEqual(self.operation(True)['qualified_finite_suite_programs'],0)
    def test_boolean_exit_code_not_success(self):
        self.process_bad=True;self.assertEqual(self.operation()['qualified_finite_suite_programs'],0)
    def test_stream_tamper_rejected(self):
        self.operation();(self.args.output/'188-python-0000.stdout').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'raw evidence'):self.operation(True)
    def test_start_tamper_rejected(self):
        self.operation();(self.args.output/'188-python-0000.start.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'start drift'):self.operation(True)
    def test_summary_tamper_rejected(self):
        self.operation();(self.args.output/'188-python.summary.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'summary'):self.operation(True)
    def test_source_drift_rejected_before_dispatch(self):
        (self.root/'python/188.py').write_bytes(b'drift')
        with patch.object(p,'verified',return_value=(self.value,self.rows,{},self.data)),patch.object(p,'SOURCE',self.root),patch.object(p.E,'access'),patch.object(p.E.sandbox,'run') as run:
            with self.assertRaisesRegex(ValueError,'source changed'):p.run_or_replay(self.args)
            run.assert_not_called()
    def test_live_denial_blocks_read_and_dispatch(self):
        with patch.object(p,'verified',return_value=(self.value,self.rows,{},self.data)),patch.object(p.E,'access',side_effect=PermissionError('denied')),patch.object(p.E,'bounded_regular_read') as read,patch.object(p.E.sandbox,'run') as run:
            with self.assertRaises(PermissionError):p.run_or_replay(self.args)
            read.assert_not_called();run.assert_not_called()
    def test_uncertain_dispatch_exception_retained_without_fake_status(self):
        with self.assertRaises(RuntimeError):self.operation(side_effect=RuntimeError('synthetic uncertain transport'))
        path=self.args.output/'188-python-0000.dispatch-error.json';value=p.read_json(path);self.assertFalse(value['process_result_available']);self.assertIn('uncertain',value['execution_outcome']);self.assertFalse((self.args.output/'188-python-0000.result.json').exists())
    def test_strict_native_json_framing(self):
        for raw in (b'{"i":false,"error":"x"}\n{"done":1}\n',b'{"i":0,"i":0,"error":"x"}\n{"done":1}\n',b'{"i":0,"error":"x"}\n{"done":true}\n'):
            with self.assertRaises(ValueError):p.parse_rows(raw,1)
    def test_no_nonlinux_runtime_fallback(self):
        with patch.object(p.E.sys,'platform','darwin'):
            with self.assertRaises(p.E.sandbox.SandboxUnavailable):p.E.runtime()

if __name__=='__main__':unittest.main()
