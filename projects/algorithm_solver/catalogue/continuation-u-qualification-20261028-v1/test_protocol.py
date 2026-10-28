"""U2 source-free orchestration/identity/replay controls; no candidates."""
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
        self.value={'schema':'gamma.independent-source-observer-static-review.v1','candidate_executions':0,'observer_profile_sha256':p.PROFILE_SHA,'source_manifest_sha256':p.MANIFEST_SHA,'blocked_ids':list(p.BLOCKED),'blocked_ids_opened':False,'selected_programs':len(self.rows),'programs':programs}
    def test_exact_two_selected_slots(self):
        self.assertEqual(len(self.rows),2);self.assertEqual(len(p.accept_reviews(self.value,self.rows,self.contract)),2)
        self.assertTrue(all(r['approved'] for r in p.accept_reviews(self.value,self.rows,self.contract).values()))
    def test_dynamic_counts_not_old_constant(self):
        rows={k:v for k,v in self.rows.items() if k[0]==257};manifest={'active_ids':[257],'excluded':[{'id':i} for i in p.BLOCKED],'source_inventory':list(rows.values())};profile={'source_bindings':{'source_inventory':list(rows.values())}}
        with patch.object(p,'IDS',(257,)):
            self.assertEqual(len(p.inventory(manifest,profile)),2)
    def test_freeze_dynamic_two_and_missing_reviews(self):
        with tempfile.TemporaryDirectory() as directory:
            preflight=Path(directory)/'preflight.txt';preflight.write_bytes(b'37 passed\n')
            args=SimpleNamespace(preflight=preflight,preflight_sha256=p.sha(preflight.read_bytes()),freeze=Path(directory)/'freeze.json',review=None,gate_sha256='mock')
            with patch.object(p.E,'runtime',return_value={'mock':True}),patch.object(p,'gate',return_value={'trusted_hashes':{}}),patch.object(p,'definitions',return_value={}),patch.object(p,'cases_and_plan',return_value=({257:[{'args':[13]}]},{})),patch.object(p,'artifacts',return_value={}),patch.object(p,'observer_review',return_value={'mock':True}):
                result=p.freeze(args)
            self.assertEqual(result['programs'],2);self.assertEqual(result['source_reviews_approved'],0)
            value=p.read_json(args.freeze);self.assertEqual(value['program_count'],2)
    def test_float_review_identity_rejected(self):
        bad=deepcopy(self.value);bad['programs'][0]['problem_id']=257.0
        with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
    def test_boolean_integer_identity_rejected(self):
        bad=deepcopy(self.value);bad['programs'][0]['problem_id']=True
        with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
        bad=deepcopy(self.value);bad['selected_programs']=True
        with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
        manifest=p.read_json(p.SOURCE/'manifest.json');manifest['source_inventory'][0]['id']=257.0
        with self.assertRaises(ValueError):p.inventory(manifest)
    def test_duplicate_or_unassigned_identity_rejected(self):
        bad=deepcopy(self.value);bad['programs'].append(bad['programs'][0])
        with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
        manifest=p.read_json(p.SOURCE/'manifest.json');manifest['source_inventory'][0]['id']=246
        with self.assertRaises(ValueError):p.inventory(manifest)
    def test_missing_review_never_approved(self):
        result=p.accept_reviews(None,self.rows,self.contract);self.assertEqual(sum(r['approved'] for r in result.values()),0)
        bad=deepcopy(self.value);bad['programs'].pop();result=p.accept_reviews(bad,self.rows,self.contract);self.assertEqual(sum(r['approved'] for r in result.values()),1)
    def test_all_flags_strict_true_and_templates_exact(self):
        for flag in p.FLAGS:
            bad=deepcopy(self.value);bad['programs'][0][flag]=1
            self.assertFalse(next(iter(p.accept_reviews(bad,self.rows,self.contract).values()))['approved'])
        for name in ('source_sha256','semantics_sha256','observer_sha256','official_language_template_sha256','native_graph_helper_sha256'):
            bad=deepcopy(self.value);bad['programs'][0][name]='wrong'
            self.assertFalse(next(iter(p.accept_reviews(bad,self.rows,self.contract).values()))['approved'])
    def test_source_review_cannot_be_observer_only(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'wrong.json';path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'source review'):p.reviews(SimpleNamespace(review=path),self.rows,self.contract)
    def test_blocked_statement_is_not_opened(self):
        with patch.object(p.E,'access') as access,patch.object(p.E,'bounded_regular_read') as read:
            for pid in p.BLOCKED+(True,257.0):
                with self.assertRaises(ValueError):p.read_statement({},pid,Path('unused'))
            access.assert_not_called();read.assert_not_called()

class RefetchControls(unittest.TestCase):
    def test_distinct_response_hashes_keep_content_api_and_templates(self):
        pid=257;q={'questionFrontendId':'257','titleSlug':'binary-tree-paths','isPaidOnly':False,'content':'public definition','metaData':'{"name":"binaryTreePaths"}','codeSnippets':[{'langSlug':'python3','code':'python template'},{'langSlug':'javascript','code':'js template'}]}
        raw=p.encoded({'data':{'question':q}});templates={r['langSlug']:p.sha(r['code'].encode()) for r in q['codeSnippets']}
        pin={'response_sha256':'original raw snapshot hash','content_sha256':p.sha(q['content'].encode()),'actual_template_sha256':templates}
        contract={'problems':[{'id':pid,'slug':q['titleSlug'],'definition':pin,'raw_fixture_metadata':{'name':'binaryTreePaths'}}]}
        receipt={'selected_ids':[pid],'blocked_ids':list(p.BLOCKED),'candidate_executions':0,'pins':{str(pid):{'refetched_response_sha256':p.sha(raw),'original_response_sha256':pin['response_sha256'],'content_sha256':pin['content_sha256'],'api_sha256':p.sha(p.encoded({'name':'binaryTreePaths'})),'templates':deepcopy(templates)}}}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);p.write(root/'refetch-receipt.json',receipt)
            with patch.object(p,'IDS',(pid,)),patch.object(p,'read_statement',return_value=raw):
                result=p.definitions(SimpleNamespace(statements=root),{},contract)
                self.assertNotEqual(result[str(pid)]['definition_sha256'],result[str(pid)]['original_definition_sha256'])
                receipt['pins'][str(pid)]['templates']['javascript']='wrong';(root/'refetch-receipt.json').write_bytes(p.encoded(receipt))
                with self.assertRaisesRegex(ValueError,'refetch receipt'):p.definitions(SimpleNamespace(statements=root),{},contract)

class IndependentObserverApprovalControls(unittest.TestCase):
    def test_author_source_receipt_does_not_approve_own_controller(self):
        with self.assertRaisesRegex(ValueError,'separate independent'):p.observer_review(SimpleNamespace())
    def test_exact_separate_observer_and_controller_binding(self):
        value={'schema':'gamma.u-independent-observer-controller-review.v1','profile_sha256':p.PROFILE_SHA,'source_manifest_sha256':p.MANIFEST_SHA,'controller_sha256':p.sha(Path(p.__file__).read_bytes()),'independent_observer_review':True,'independent_controller_review':True,'reviewer':'synthetic external reviewer'}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'review.json';path.write_bytes(p.encoded(value));args=SimpleNamespace(observer_review=path,observer_review_sha256=p.sha(path.read_bytes()))
            self.assertEqual(p.observer_review(args)['sha256'],args.observer_review_sha256)
            value['independent_controller_review']=1;path.write_bytes(p.encoded(value));args.observer_review_sha256=p.sha(path.read_bytes())
            with self.assertRaisesRegex(ValueError,'approval binding'):p.observer_review(args)
            value['independent_controller_review']=True;value['controller_sha256']='different controller';path.write_bytes(p.encoded(value));args.observer_review_sha256=p.sha(path.read_bytes())
            with self.assertRaisesRegex(ValueError,'approval binding'):p.observer_review(args)

class RunReplayControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve();self.args=SimpleNamespace(output=self.root/'output',freeze_sha256='syntheticfreeze',gate_sha256='syntheticgate')
        body=b'# inert fixture bytes; sandbox is mocked, never executed\n';self.rows={}
        for lang,suffix in (('python','py'),('javascript','js')):
            (self.root/lang).mkdir();(self.root/lang/f'257.{suffix}').write_bytes(body);self.rows[257,lang]={'path':f'{lang}/257.{suffix}','sha256':p.sha(body)}
        self.data={257:[{'args':[{'values':[1],'left':[None],'right':[None],'root':0}],'expected':['1']}]};indices=[0,0];wire=p.PLAN.encoded(p.PLAN.packet(257,self.data[257],indices))
        entry={'indices':indices,'host_input_bytes':len(wire),'projected_output_bytes':{'python':8192,'javascript':8192},'mode':'synthetic-repeat'}
        self.value={'runtime':{'synthetic':True},'artifact_hashes':{'synthetic':'pin'},'plans':{'257':{'batches':[entry],'blocked_cases':[],'admitted_distinct_cases':1}},'source_reviews':{f'257:{lang}':{'approved':True} for lang in p.LANGUAGES},'execution_gate_sha256':'syntheticgate'}
        self.malformed=False;self.process_bad=False
    def result(self,argv,**kwargs):
        lang='python' if 'python' in argv[0] else 'javascript'
        raw=b'\n'.join(p.encoded({'i':i,**p.PLAN.successful_record(257,self.data[257][0]['args'],['1'],lang,p.CHECK.reference)}) for i in range(2))+b'\n'+p.encoded({'done':2})+b'\n'
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
        plan=self.value['plans']['257'];row=p.summary(257,'python',self.data[257],plan,0,[],{'approved':True});self.assertFalse(row['qualified_finite_suite'])
        row=p.summary(257,'python',self.data[257],plan,2,[],{'approved':False});self.assertFalse(row['qualified_finite_suite'])
    def test_raw_evidence_written_before_verdict(self):
        original=p.verdict
        def check(pid,lang,rows,indices,status,stdout):
            stem=self.args.output/f'257-{lang}-0000'
            for suffix in ('.stdout','.stderr','.result.json'):self.assertTrue(Path(str(stem)+suffix).exists())
            return original(pid,lang,rows,indices,status,stdout)
        with patch.object(p,'verdict',side_effect=check):self.operation()
    def test_protocol_failure_retained_and_replayed(self):
        self.malformed=True;self.assertEqual(self.operation()['qualified_finite_suite_programs'],0)
        self.assertEqual((self.args.output/'257-python-0000.stdout').read_bytes(),b'{"done":false}\n')
        self.assertEqual(self.operation(True)['qualified_finite_suite_programs'],0)
    def test_boolean_exit_code_not_success(self):
        self.process_bad=True;self.assertEqual(self.operation()['qualified_finite_suite_programs'],0)
    def test_stream_tamper_rejected(self):
        self.operation();(self.args.output/'257-python-0000.stdout').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'raw evidence'):self.operation(True)
    def test_start_tamper_rejected(self):
        self.operation();(self.args.output/'257-python-0000.start.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'start drift'):self.operation(True)
    def test_summary_tamper_rejected(self):
        self.operation();(self.args.output/'257-python.summary.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'summary'):self.operation(True)
    def test_source_drift_rejected_before_dispatch(self):
        (self.root/'python/257.py').write_bytes(b'drift')
        with patch.object(p,'verified',return_value=(self.value,self.rows,{},self.data)),patch.object(p,'SOURCE',self.root),patch.object(p.E,'access'),patch.object(p.E.sandbox,'run') as run:
            with self.assertRaisesRegex(ValueError,'source changed'):p.run_or_replay(self.args)
            run.assert_not_called()
    def test_live_denial_blocks_read_and_dispatch(self):
        with patch.object(p,'verified',return_value=(self.value,self.rows,{},self.data)),patch.object(p.E,'access',side_effect=PermissionError('denied')),patch.object(p.E,'bounded_regular_read') as read,patch.object(p.E.sandbox,'run') as run:
            with self.assertRaises(PermissionError):p.run_or_replay(self.args)
            read.assert_not_called();run.assert_not_called()
    def test_uncertain_dispatch_exception_retained_without_fake_status(self):
        with self.assertRaises(RuntimeError):self.operation(side_effect=RuntimeError('synthetic uncertain transport'))
        path=self.args.output/'257-python-0000.dispatch-error.json';value=p.read_json(path);self.assertFalse(value['process_result_available']);self.assertIn('uncertain',value['execution_outcome']);self.assertFalse((self.args.output/'257-python-0000.result.json').exists())
    def test_strict_native_json_framing(self):
        for raw in (b'{"i":false,"error":"x"}\n{"done":1}\n',b'{"i":0,"i":0,"error":"x"}\n{"done":1}\n',b'{"i":0,"error":"x"}\n{"done":true}\n'):
            with self.assertRaises(ValueError):p.parse_rows(raw,1)
    def test_no_nonlinux_runtime_fallback(self):
        with patch.object(p.E.sys,'platform','darwin'):
            with self.assertRaises(p.E.sandbox.SandboxUnavailable):p.E.runtime()

if __name__=='__main__':unittest.main()
