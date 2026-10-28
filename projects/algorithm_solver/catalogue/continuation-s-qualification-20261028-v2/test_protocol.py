"""S20 source-free controller/required-witness controls; no candidate modules."""
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import tempfile
import json
import tracemalloc
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

class MetadataControls(unittest.TestCase):
    def setUp(self):
        self.rows,self.contract=p.metadata();programs=[]
        for (pid,lang),row in self.rows.items():programs.append({'problem_id':pid,'language':lang,'reviewer':'synthetic independent reviewer',**p.binding(pid,lang,row,self.contract),**{f:True for f in p.FLAGS},'source_safety':p.SAFETY_REVIEW_TEXT})
        self.value={'schema':'gamma.s-independent-mandatory-static-review.v1','candidate_executions':0,'static_failures':[],'static_reviewed_programs':len(self.rows),'programs':programs}
    def test_exact_twenty_and_dynamic_four_slots(self):
        self.assertEqual(len(self.rows),20);self.assertEqual(sum(r['approved'] for r in p.accept_reviews(self.value,self.rows,self.contract).values()),20)
        selected={k:v for k,v in self.rows.items() if k[0] in (208,214)}
        with patch.object(p,'IDS',(208,214)):self.assertEqual(len(p.inventory({'source_inventory':list(selected.values())})),4)
    def test_boolean_float_unknown_duplicate_ids_rejected(self):
        for bad_id in (True,199.0,999):
            bad=deepcopy(self.value);bad['programs'][0]['problem_id']=bad_id
            with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
        bad=deepcopy(self.value);bad['programs'].append(bad['programs'][0])
        with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
        bad=deepcopy(self.value);bad['static_reviewed_programs']=20.0
        with self.assertRaises(ValueError):p.accept_reviews(bad,self.rows,self.contract)
    def test_missing_false_unbound_reviews_not_approved(self):
        self.assertEqual(sum(r['approved'] for r in p.accept_reviews(None,self.rows,self.contract).values()),0)
        for field in p.FLAGS:
            bad=deepcopy(self.value);bad['programs'][0][field]=1
            self.assertFalse(next(iter(p.accept_reviews(bad,self.rows,self.contract).values()))['approved'])
        for field in ('observer_sha256','source_sha256','official_language_template_sha256','source_safety'):
            bad=deepcopy(self.value);bad['programs'][0][field]=True
            self.assertFalse(next(iter(p.accept_reviews(bad,self.rows,self.contract).values()))['approved'])
    def test_source_review_not_observer_only_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad.json';path.write_text('{}')
            with self.assertRaises(ValueError):p.reviews(SimpleNamespace(review=path),self.rows,self.contract)
    def test_required_witness_exact_arithmetic_and_evidence(self):
        b=p.required_blockers(self.contract)['208'][0];proof=b['proof'];spec=next(r for r in self.contract['problems'] if r['id']==208)
        self.assertEqual(proof['raw_word_utf8_lower_bound_bytes'],20000000);self.assertEqual(proof['exact_compact_args_bytes'],20140015);self.assertEqual(proof['argument_echo_stdout_lower_bound_bytes'],40280030)
        self.assertGreater(proof['input_packet_lower_bound_bytes'],16777216);self.assertGreater(proof['argument_echo_stdout_lower_bound_bytes'],16777216)
        self.assertEqual(b['official_evidence']['definition_content_sha256'],spec['official_content_sha256']);self.assertFalse(b['witness']['materialized'])
    def test_formula_small_instances_without_giant_allocation(self):
        for n in range(4):
            for length in (1,2,7,31):
                args=[['Trie']+['insert']*n,[[]]+[['a'*length] for _ in range(n)]]
                self.assertEqual(len(p.encoded(args)),15+n*(length+14))
        tracemalloc.start()
        try:
            b=p.required_blockers(self.contract);_,peak=tracemalloc.get_traced_memory()
            self.assertLess(peak,256*1024);self.assertLess(len(p.encoded(b)),4096)
        finally:tracemalloc.stop()
    def test_original_frozen_case_hash_and_count_preserved(self):
        owner,freeze=p.PLAN.references();data=owner.build_cases()
        self.assertEqual(sum(map(len,data.values())),2111);self.assertEqual(p.sha(owner.encoded(data)),freeze['case_sha256'])
        self.assertEqual(len(data[208]),34)
    def test_208_cannot_be_complete_even_with_finite_pass(self):
        cases=[{'args':[],'expected':[]}];plan={'batches':[{'indices':[0,0]}],'blocked_cases':[],'admitted_distinct_cases':1}
        b=p.required_blockers(self.contract)['208'];r=p.summary(208,'python',cases,plan,2,[],{'approved':True},b)
        self.assertTrue(r['original_finite_suite_passed']);self.assertFalse(r['complete_required_scope_passed']);self.assertFalse(r['qualified'])
        with self.assertRaises(ValueError):p.summary(208,'python',cases,plan,2,[],{'approved':True},[])
    def test_scope_note_missing_or_wrong_never_removes_blocker(self):
        self.assertIn('208',p.required_blockers(self.contract))
        with self.assertRaises(ValueError):p.scope_note(SimpleNamespace(scope_note=None),self.contract)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad.json';path.write_text('{}')
            with self.assertRaises(ValueError):p.scope_note(SimpleNamespace(scope_note=path),self.contract)
    def test_no_cap_change_or_unassigned_statement_open(self):
        with patch.object(p.PLAN,'MAX_HOST_PACKET_BYTES',32*1024**2):
            with self.assertRaises(ValueError):p.required_blockers(self.contract)
        with patch.object(p.E,'access') as access,patch.object(p.E,'bounded_regular_read') as read:
            for pid in (True,208.0,1):
                with self.assertRaises(ValueError):p.read_statement({},pid,Path('unused'))
            access.assert_not_called();read.assert_not_called()

class DefinitionPinControls(unittest.TestCase):
    def setUp(self):
        self.spec={'id':199,'slug':'synthetic-slug','official_definition_sha256':'0'*64,'official_content_sha256':p.sha(b'<p>c</p>'),
                   'official_api':{'name':'f'},'actual_language_templates_sha256':{'python3':p.sha(b'py'),'javascript':p.sha(b'js')}}
    def raw(self,content='<p>c</p>',other='kotlin template'):
        q={'questionFrontendId':'199','title':'t','titleSlug':'synthetic-slug','isPaidOnly':False,'content':content,'metaData':json.dumps({'name':'f'}),
           'codeSnippets':[{'langSlug':'python3','code':'py'},{'langSlug':'javascript','code':'js'},{'langSlug':'kotlin','code':other}]}
        return json.dumps({'data':{'question':q}}).encode()
    def pins(self,raw):
        with patch.object(p,'IDS',(199,)),patch.object(p,'read_statement',return_value=raw):
            return p.definitions(SimpleNamespace(statements=Path('unused')),{},{'problems':[self.spec]})
    def test_unselected_language_change_is_recorded_not_rejected(self):
        raw=self.raw(other='changed kotlin template');pin=self.pins(raw)['199']
        self.assertEqual(pin['definition_sha256'],p.sha(raw));self.assertEqual(pin['original_definition_sha256'],'0'*64)
    def test_content_api_or_selected_template_change_still_rejected(self):
        with self.assertRaises(ValueError):self.pins(self.raw(content='<p>changed</p>'))
        changed=json.loads(self.raw());changed['data']['question']['codeSnippets'][0]['code']='py2'
        with self.assertRaises(ValueError):self.pins(json.dumps(changed).encode())
        changed=json.loads(self.raw());changed['data']['question']['metaData']=json.dumps({'name':'g'})
        with self.assertRaises(ValueError):self.pins(json.dumps(changed).encode())

class RunReplayControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve();self.args=SimpleNamespace(output=self.root/'output',freeze_sha256='syntheticfreeze',gate_sha256='syntheticgate')
        body=b'# inert fixture never executed; sandbox mocked\n';self.rows={}
        for lang,suffix in (('python','py'),('javascript','js')):
            (self.root/lang).mkdir()
            for pid in (208,214):
                (self.root/lang/f'{pid}.{suffix}').write_bytes(body);self.rows[pid,lang]={'path':f'{lang}/{pid}.{suffix}','sha256':p.sha(body)}
        self.data={208:[{'args':[['Trie','insert','search'],[[],['a'],['a']]],'expected':[None,None,True]}],214:[{'args':['a'],'expected':'a'}]};plans={}
        for pid,rows in self.data.items():
            ix=[0,0];wire=p.PLAN.encoded(p.PLAN.packet(pid,rows,ix));plans[str(pid)]={'batches':[{'indices':ix,'host_input_bytes':len(wire),'projected_output_bytes':{'python':8192,'javascript':8192},'mode':'synthetic-repeat'}],'blocked_cases':[],'admitted_distinct_cases':1}
        _,contract=p.metadata();self.value={'runtime':{'synthetic':True},'artifact_hashes':{'synthetic':'pin'},'plans':plans,'source_reviews':{f'{pid}:{lang}':{'approved':True} for pid,lang in self.rows},'execution_gate_sha256':'syntheticgate','required_scope_blockers':p.required_blockers(contract)};self.malformed=False
    def result(self,argv,files,**kwargs):
        lang='python' if 'python' in argv[0] else 'javascript';packet=json.loads(files['inputs.json']);pid=packet['problem_id'];row=self.data[pid][0]
        raw=b'\n'.join(p.encoded({'i':i,**p.PLAN.successful_record(pid,row['args'],row['expected'],lang,p.CHECK.reference)}) for i in range(2))+b'\n'+p.encoded({'done':2})+b'\n'
        return Observation(b'{"done":false}\n' if self.malformed else raw)
    def operation(self,replay=False,side_effect=None):
        with patch.object(p,'verified',return_value=(self.value,self.rows,{},self.data)),patch.object(p,'SOURCE',self.root),patch.object(p.E,'access'),patch.object(p.E.sandbox,'run',side_effect=side_effect or self.result) as run:
            result=p.run_or_replay(self.args,replay);self.assertEqual(run.call_count,0 if replay else 4);return result
    def test_raw_roundtrip_finite_pass_separate_208_required_block(self):
        r=self.operation();self.assertEqual(r['programs'],4);self.assertEqual(r['original_finite_suite_pass_programs'],4);self.assertEqual(r['qualified_programs'],2);self.assertEqual(r['required_scope_transport_blocked_programs'],2)
        r=self.operation(True);self.assertEqual(r['qualified_programs'],2);self.assertEqual(r['dispatched_call_slots'],8)
    def test_missing_reviews_execute_nothing(self):
        for r in self.value['source_reviews'].values():r['approved']=False
        with patch.object(p,'verified',return_value=(self.value,self.rows,{},self.data)),patch.object(p.E.sandbox,'run') as run:
            r=p.run_or_replay(self.args);run.assert_not_called()
        self.assertEqual(r['qualified_programs'],0);self.assertEqual(r['dispatched_call_slots'],0)
    def test_raw_first_process_failure_preserved(self):
        self.malformed=True;original=p.verdict
        def check(pid,lang,rows,indices,status,stdout):
            for suffix in ('.stdout','.stderr','.result.json'):self.assertTrue((self.args.output/f'{pid}-{lang}-0000{suffix}').exists())
            return original(pid,lang,rows,indices,status,stdout)
        with patch.object(p,'verdict',side_effect=check):self.assertEqual(self.operation()['qualified_programs'],0)
        self.assertEqual(self.operation(True)['qualified_programs'],0)
    def test_tampered_raw_summary_and_start_rejected(self):
        self.operation();path=self.args.output/'208-python-0000.stdout';path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'raw evidence'):self.operation(True)
    def test_required_blocker_tamper_in_report_rejected(self):
        self.operation();path=self.args.output/'208-python.summary.json';r=p.read_json(path);r['required_scope_transport_blockers']=[];path.write_bytes(p.encoded(r))
        with self.assertRaisesRegex(ValueError,'summary'):self.operation(True)
    def test_denial_prevents_open_or_dispatch(self):
        with patch.object(p,'verified',return_value=(self.value,self.rows,{},self.data)),patch.object(p.E,'access',side_effect=PermissionError('denied')),patch.object(p.E,'bounded_regular_read') as read,patch.object(p.E.sandbox,'run') as run:
            with self.assertRaises(PermissionError):p.run_or_replay(self.args)
            read.assert_not_called();run.assert_not_called()
    def test_dispatch_exception_is_uncertain_not_a_success(self):
        with self.assertRaises(RuntimeError):self.operation(side_effect=RuntimeError('synthetic uncertain'))
        value=p.read_json(self.args.output/'208-python-0000.dispatch-error.json');self.assertFalse(value['process_result_available']);self.assertIn('uncertain',value['execution_outcome'])
    def test_strict_native_frame_integer_counts(self):
        for raw in (b'{"i":false,"error":"x"}\n{"done":1}\n',b'{"i":0,"error":"x"}\n{"done":true}\n',b'{"i":0,"i":0,"error":"x"}\n{"done":1}\n'):
            with self.assertRaises(ValueError):p.parse_rows(raw,1)
    def test_no_nonlinux_fallback(self):
        with patch.object(p.E.sys,'platform','darwin'):
            with self.assertRaises(p.E.sandbox.SandboxUnavailable):p.E.runtime()

if __name__=='__main__':unittest.main()
