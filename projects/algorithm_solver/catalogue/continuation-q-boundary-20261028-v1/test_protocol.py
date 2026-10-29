"""Source-free controller regressions, ported from the Q lane to this restricted lane. Sandbox dispatch is always mocked."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
S=importlib.util.spec_from_file_location('q_boundary_test_protocol',HERE/'protocol.py');P=importlib.util.module_from_spec(S);S.loader.exec_module(P)


def program(pid=126,language='python'):
    return {'problem_id':pid,'language':language,'origin':P.wanted_origin(pid),'source_path':f'{language}/{pid}.py' if language=='python' else f'{language}/{pid}.js','source_sha256':'s','semantics_path':f'semantics/{pid}-{language}.json','semantics_sha256':'c'}


def observation(pid,args,result,index=0):
    return {'i':index,'native_route':'official-wrapper-q-v1','entry_kind':'python-solution-method','problem_id':pid,'method':'findLadders','result':result,'result_type':'list','args_before':args,'args_after':args,'alias_edges':[],'node_identity':None,'node_integrity':None}


def stream(records):return b'\n'.join(P.encoded(row) for row in [*records,{'done':len(records)}])+b'\n'


class ControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.pop=P.population();cls.data,cls.owners=P.cases_and_owners(cls.pop)
    def test_exact_eight_source_selection_excludes_old_four(self):
        self.assertEqual(P.program_count(self.pop),8)
        self.assertEqual(sum(row['origin']=='original' for row in self.pop['programs']),4)
        self.assertEqual({row['problem_id'] for row in self.pop['programs'] if row['origin']!='original'},{126,140})
        excluded={row['sha256'] for row in self.pop['excluded_superseded_variants']}
        self.assertEqual(len(excluded),4);self.assertFalse(excluded&{row['source_sha256'] for row in self.pop['programs']})
    def test_old_membership_and_exact_two_new_certificates(self):
        count=0
        for pid,rows in self.data.items():
            identities=[row['case_identity'] for row in rows]
            old=[row for row in identities if row['origin']=='q-original']
            self.assertEqual([row['original_index'] for row in old],list(range(len(old))))
            count+=sum(row['certificate_index'] is not None for row in identities)
        certificate={pid:[row for row in self.data[pid] if row['case_identity']['certificate_index'] is not None] for pid in (126,140)}
        self.assertEqual(count,2);self.assertEqual(len(certificate[126][0]['expected'][0]),51);self.assertEqual(certificate[140][0]['expected'],[])
        for pid,rows in self.data.items():
            origins=[row['case_identity']['origin'] for row in rows];first=origins.index('q-boundary')
            self.assertTrue(all(origin=='q-boundary' for origin in origins[first:]));self.assertNotIn('q-boundary',origins[:first])
    def test_per_language_actual_template_and_raw_metadata_separate(self):
        api={'name':'trueNative','params':[]};raw_api={'name':'wrongRaw','params':[]}
        snippets={'python3':'class Solution: pass','javascript':'var trueNative = function(){};'}
        spec={'id':133,'title':'toy','slug':'toy','content_sha256':P.sha(b'inert content'),'raw_metadata_sha256':P.sha(P.encoded(raw_api)),
              'official_api_sha256':P.sha(P.encoded(api)),'template_sha256':{key:P.sha(value.encode()) for key,value in snippets.items()}}
        q={'questionFrontendId':'133','title':'toy','titleSlug':'toy','isPaidOnly':False,'content':'inert content','metaData':json.dumps(raw_api),'codeSnippets':[{'langSlug':key,'code':value} for key,value in snippets.items()]}
        self.assertEqual(P.validate_definition(P.encoded({'data':{'question':q}}),spec),q)
        wrong=copy.deepcopy(q);wrong['metaData']=json.dumps(api)
        with self.assertRaises(ValueError):P.validate_definition(P.encoded({'data':{'question':wrong}}),spec)
        wrong=copy.deepcopy(q);wrong['codeSnippets'][1]['code']='Solution adapter'
        with self.assertRaises(ValueError):P.validate_definition(P.encoded({'data':{'question':wrong}}),spec)
    def test_live_denial_precedes_public_fetch(self):
        with tempfile.TemporaryDirectory() as temporary:
            args=SimpleNamespace(gate=Path('unused'),gate_sha256='pin',statements=Path(temporary)/'new')
            with patch.object(P,'population',return_value={'programs':[],'problems':[{'id':126}]}),patch.object(P,'gate_file',return_value={}),patch.object(P,'access',side_effect=PermissionError('closed')),patch.object(P.urllib.request,'urlopen') as network:
                with self.assertRaises(PermissionError):P.prepare(args)
                network.assert_not_called()
    def test_macos_cannot_freeze_runtime(self):
        with patch.object(P.sys,'platform','darwin'),patch.object(P.sandbox,'check_available') as check:
            with self.assertRaises(P.sandbox.SandboxUnavailable):P.runtime()
            check.assert_not_called()
    def test_review_float_boolean_string_identities_rejected(self):
        pop={'programs':[program()]}
        for bad in (126.0,True,'126',None):
            with self.subTest(bad=bad),self.assertRaises(ValueError):P.evaluate_reviews(pop,[{'problem_id':bad,'language':'python'}])
    def test_review_flags_are_strict_booleans_and_repair_binding_required(self):
        pop={'programs':[program()]};row={'problem_id':126,'language':'python','reviewer':'synthetic', 'source_sha256':'s',**{flag:True for flag in P.review_flags(126)}}
        with patch.object(P,'review_binding',return_value={'source_sha256':'s'}):
            self.assertTrue(P.evaluate_reviews(pop,[row])['126:python']['approved'])
            for change in ({'mandatory_complexity':1},{'complexity_repair_proof':False},{'source_sha256':'old-superseded'}):
                self.assertFalse(P.evaluate_reviews(pop,[{**row,**change}])['126:python']['approved'])
            with self.assertRaises(ValueError):P.evaluate_reviews(pop,[row,row])
    def test_dynamic_freeze_count_is_not_hardcoded(self):
        pop={'programs':[program()],'excluded_superseded_variants':[]};rows=[{'args':['a','b',['b']],'expected':[['a','b']]}]
        with tempfile.TemporaryDirectory() as temporary:
            temp=Path(temporary);log=temp/'preflight';log.write_bytes(b'37 passed\n')
            args=SimpleNamespace(gate=Path('unused'),gate_sha256='g',preflight=log,preflight_sha256=P.sha(log.read_bytes()),statements=Path('unused'),review=None,freeze=temp/'freeze')
            plan={'batches':[{'indices':[0]}],'blocked_cases':[],'admitted_distinct_cases':1}
            with patch.object(P,'population',return_value=pop),patch.object(P,'gate_file',return_value={'trusted_hashes':{}}),patch.object(P,'runtime',return_value={}),patch.object(P,'definitions',return_value={}),patch.object(P,'artifacts',return_value={}),patch.object(P,'cases_and_owners',return_value=({126:rows},{})),patch.object(P,'batch_plan',return_value=plan),patch.object(P,'manual_reviews',return_value={'126:python':{'approved':False,'record':{}}}),patch.object(P,'coverage_summary',return_value={}):
                result=P.freeze(args)
            self.assertEqual(result['programs'],1);self.assertEqual(P.read_json(args.freeze)['program_count'],1)
    def test_frozen_count_wrong_type_or_value_fails_before_source_open(self):
        pop={'programs':[program()],'excluded_superseded_variants':[]}
        base={'schema':P.SCHEMA,'argv':P.ARGV,'limits':P.asdict(P.LIMITS),'max_input_bytes':P.MAX_INPUT_BYTES,'per_stream_output_bytes':P.PER_STREAM_OUTPUT_BYTES,'dispatch_policy':P.DISPATCH_POLICY,'batch_policy':P.BATCH_POLICY,'projection_policy':P.PROJECTION_POLICY,
              'population_sha256':P.sha((P.HERE/'population.json').read_bytes()),'selected_programs':pop['programs'],'excluded_superseded_variants':[]}
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'freeze'
            for bad in (True,1.0,40):
                path.write_bytes(P.encoded({**base,'program_count':bad}));args=SimpleNamespace(freeze=path,freeze_sha256=P.sha(path.read_bytes()),gate=Path('unused'),gate_sha256='g')
                with patch.object(P,'population',return_value=pop),patch.object(P,'gate_file',return_value={}),patch.object(P,'artifacts') as source:
                    with self.assertRaises(ValueError):P.verified_inputs(args,False)
                    source.assert_not_called()
    def test_bad_preflight_stops_before_source_and_statement_opens(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp=Path(temporary);log=temp/'log';log.write_bytes(b'36 passed\n')
            args=SimpleNamespace(gate=Path('unused'),gate_sha256='g',preflight=log,preflight_sha256=P.sha(log.read_bytes()))
            with patch.object(P,'population',return_value={}),patch.object(P,'gate_file',return_value={}),patch.object(P,'runtime',return_value={}),patch.object(P,'definitions') as definitions,patch.object(P,'artifacts') as source:
                with self.assertRaises(ValueError):P.freeze(args)
                definitions.assert_not_called();source.assert_not_called()
    def test_forged_approved_boolean_requires_actual_bound_review_records(self):
        pop={'programs':[program()],'excluded_superseded_variants':[]};data={126:[{'args':['a','b',['b']],'expected':[['a','b']]}]};plan={'batches':[],'blocked_cases':[],'admitted_distinct_cases':0}
        value={'schema':P.SCHEMA,'argv':P.ARGV,'limits':P.asdict(P.LIMITS),'max_input_bytes':P.MAX_INPUT_BYTES,'per_stream_output_bytes':P.PER_STREAM_OUTPUT_BYTES,'dispatch_policy':P.DISPATCH_POLICY,'batch_policy':P.BATCH_POLICY,'projection_policy':P.PROJECTION_POLICY,'population_sha256':P.sha((P.HERE/'population.json').read_bytes()),'program_count':1,'problem_count':1,'selected_programs':pop['programs'],'excluded_superseded_variants':[],
               'boundary_trusted_hashes':{},'artifact_hashes':{},'statement_pins':{},'case_sha256':P.sha(P.encoded(data)),'case_counts':{'126':1},'prepared_case_coverage':{},'batch_plans':{'126':plan},'review_records':[],'manual_reviews':{'126:python':{'approved':True,'record':{},'reason':None}}}
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'freeze';path.write_bytes(P.encoded(value));args=SimpleNamespace(freeze=path,freeze_sha256=P.sha(path.read_bytes()),gate=Path('unused'),gate_sha256='g',statements=Path('unused'))
            with patch.object(P,'population',return_value=pop),patch.object(P,'gate_file',return_value={'trusted_hashes':{}}),patch.object(P,'artifacts',return_value={}),patch.object(P,'definitions',return_value={}),patch.object(P,'cases_and_owners',return_value=(data,{})),patch.object(P,'batch_plan',return_value=plan),patch.object(P,'review_binding',return_value={}),patch.object(P,'coverage_summary',return_value={}):
                with self.assertRaises(ValueError):P.verified_inputs(args,False)

    def test_argument_packet_never_contains_expected_or_membership(self):
        row={'args':['a','b',['b']],'expected':[['a','b']],'case_identity':{'private':'host'}}
        packet=P.packet(126,[row],[0]);self.assertEqual(set(packet),{'schema','problem_id','calls'});self.assertEqual(set(packet['calls'][0]),{'args'})
        self.assertNotIn(b'expected',P.encoded(packet));self.assertNotIn(b'case_identity',P.encoded(packet))
    def test_all_maximum_tree_graph_list_witnesses_retained(self):
        for pid in P.IDS:
            rows=self.data[pid];plan=P.batch_plan(pid,rows)
            self.assertFalse(plan['blocked_cases']);self.assertEqual(plan['admitted_distinct_cases'],len(rows))
            for index,row in enumerate(rows):
                if row.get('isolate') is True:self.assertEqual([entry['indices'] for entry in plan['batches'] if index in entry['indices']],[[index]])
        self.assertTrue(any(len(row['args'][0]['values'])==100 for row in self.data[144]))
        self.assertTrue(any(len(row['args'][0]['values'])==1000 for row in self.data[129]))
    def test_small_repeat_and_named_transport_blocker(self):
        rows=[{'args':['a','b',['b']],'expected':[['a','b']]},{'args':['a','b',['b']],'expected':[['x'*(P.LIMITS.max_output_bytes+1)]]}]
        plan=P.batch_plan(126,rows)
        self.assertEqual(plan['batches'][0]['indices'],[0,0]);self.assertEqual(plan['blocked_cases'][0]['case'],1)
        self.assertEqual(plan['blocked_cases'][0]['reason'],'single_successful_stdout_exceeds_per_stream_output_cap')
    def test_actual_toy_clone_wire_is_bounded_by_projection(self):
        path=P.ROOT/P.OBSERVER/'test_observers.py';spec=importlib.util.spec_from_file_location('q_projection_toy_fixture',path);toy=importlib.util.module_from_spec(spec);spec.loader.exec_module(toy)
        row={'args':[toy.GRAPH],'expected':toy.GRAPH};record={'i':0,**toy.observe(133,[toy.GRAPH],toy.graph_clone)}
        wire=P.encoded(record)+b'\n'+json.dumps({'done':1}).encode()+b'\n'
        self.assertLessEqual(len(wire),P.projected_stdout(133,'python',[row],[0]))
    def test_partial_duplicate_extra_and_boolean_stream_records_rejected(self):
        record=observation(126,['a','b',['b']],[['a','b']])
        malformed=[P.encoded(record),P.encoded(record)+b'\n{"done":true}\n',stream([{**record,'i':False}]),stream([{**record,'extra':1}]),b'{"i":0,"i":0,"error":"bad"}\n{"done":1}\n']
        for raw in malformed:
            with self.assertRaises((ValueError,UnicodeError)):P.parse(raw,1)
    def test_process_failure_and_false_integer_exit_cannot_pass(self):
        rows=[{'args':['a','b',['b']],'expected':[['a','b']]}];raw=stream([observation(126,rows[0]['args'],rows[0]['expected'])]);owner=SimpleNamespace(check_observation=lambda *args:(True,None))
        for change in ({'exit_code':False},{'exit_code':1},{'signal':9},{'timed_out':True},{'output_limit_exceeded':True},{'stderr_bytes':True}):
            metadata={'exit_code':0,'signal':None,'timed_out':False,'output_limit_exceeded':False,'stderr_bytes':0,**change}
            self.assertEqual(P.verdict(126,'python',rows,[0],metadata,raw,owner)[0]['reason'],'sandbox_process_failure')
    def test_incomplete_calls_or_missing_reviews_cannot_qualify(self):
        rows=[{'args':[],'expected':[]}];plan={'batches':[{'indices':[0,0]}],'admitted_distinct_cases':1,'blocked_cases':[]}
        self.assertFalse(P.program_summary(program(),rows,plan,[],0,{'approved':True})['qualified'])
        self.assertFalse(P.program_summary(program(),rows,plan,[],2,{'approved':False})['qualified'])
    def test_dynamic_report_counts_sources_and_pairs(self):
        contract={'scope':'synthetic'}
        def row(pid,language,good):return {'problem_id':pid,'language':language,'qualified':good}
        report=P.aggregate_report(b'f',contract,[row(126,'python',True),row(126,'javascript',True),row(129,'python',False)])
        self.assertEqual(report['program_count'],3);self.assertEqual(report['qualified_program_count'],2);self.assertEqual(report['qualified_problem_pair_count'],1)

    def test_raw_first_mocked_run_dynamic_count_and_independent_replay(self):
        case={'args':['a','b',['b']],'expected':[['a','b']]};wire=P.encoded(P.packet(126,[case],[0]));raw_stdout=stream([observation(126,case['args'],case['expected'])])
        plan={'batches':[{'indices':[0],'policy':'synthetic','input_bytes':len(wire),'inputs_sha256':P.sha(wire)}],'blocked_cases':[],'admitted_distinct_cases':1}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();directory=root/'source';(directory/'python').mkdir(parents=True);observer=root/'observer';observer.mkdir()
            source=b'# synthetic inert source; never executed\n';(directory/'python/126.py').write_bytes(source)
            helper=b'# synthetic observer; never executed\n'
            for name in ('harness.py','models.py'):(observer/name).write_bytes(helper)
            selected={**program(),'source_sha256':P.sha(source)};pop={'programs':[selected]};pins={'source/python/126.py':P.sha(source),'observer/harness.py':P.sha(helper),'observer/models.py':P.sha(helper)}
            contract={'artifact_hashes':pins,'runtime':{},'selected_programs':[selected],'batch_plans':{'126':plan},'manual_reviews':{'126:python':{'approved':True}},'scope':'synthetic','execution_gate_sha256':'original-gate'}
            args=SimpleNamespace(output=root/'run',gate_sha256='relocated-gate');frozen=b'synthetic-freeze';owner=SimpleNamespace(check_observation=lambda *args:(True,None))
            result=P.sandbox.SandboxResult(exit_code=0,signal=None,stdout=raw_stdout,stderr=b'',wall_seconds=0,timed_out=False,output_limit_exceeded=False)
            actual_verdict=P.verdict
            def judge(*arguments):
                self.assertEqual((args.output/'126-python-0000.stdout').read_bytes(),raw_stdout)
                self.assertTrue((args.output/'126-python-0000.result.json').exists())
                return actual_verdict(*arguments)
            values=(frozen,contract,pop,{}, {126:[case]},{126:owner})
            with patch.object(P,'ROOT',root),patch.object(P,'SOURCES',{'repair126':Path('source')}),patch.object(P,'OBSERVER',Path('observer')),patch.object(P,'verified_inputs',return_value=values),patch.object(P,'access'),patch.object(P.sandbox,'run',return_value=result) as runner,patch.object(P,'verdict',side_effect=judge):
                report=P.execute(args)
                self.assertEqual(report['program_count'],1);self.assertEqual(report['qualified_program_count'],1)
                self.assertEqual(set(runner.call_args.kwargs['files']),{'program.py','harness.py','models.py','inputs.json'})
                self.assertEqual(runner.call_args.kwargs['limits'],P.LIMITS)
                self.assertNotIn(b'expected',runner.call_args.kwargs['files']['inputs.json'])
            spec=importlib.util.spec_from_file_location('q_test_independent_replay',HERE/'verify.py');replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
            with patch.object(replay.P,'verified_inputs',return_value=values):
                receipt=replay.verify(args)
                self.assertEqual(receipt['program_count'],1);self.assertFalse(receipt['candidate_execution_on_replay_host'])
                self.assertEqual(receipt['original_execution_gate_sha256'],'original-gate');self.assertEqual(receipt['replay_gate_sha256'],'relocated-gate')
                saved=P.read_json(args.output/'report.json');saved['program_count']=True;(args.output/'report.json').write_bytes(P.encoded(saved))
                with self.assertRaises(ValueError):replay.verify(args)
                (args.output/'126-python-0000.stdout').write_bytes(raw_stdout+b' ')
                with self.assertRaises(ValueError):replay.verify(args)

    def test_absent_false_and_mismatched_review_dispatch_zero_and_replay_blocked(self):
        selected=program();pop={'programs':[selected]};rows=[{'args':['a','b',['b']],'expected':[['a','b']]}]
        plan={'batches':[{'indices':[0,0]}],'admitted_distinct_cases':1,'blocked_cases':[]}
        wrong={'problem_id':126,'language':'python','reviewer':'synthetic','source_sha256':'superseded',**{flag:True for flag in P.review_flags(126)}}
        with patch.object(P,'review_binding',return_value={'source_sha256':'s'}):mismatched=P.evaluate_reviews(pop,[wrong])
        for label,reviews in [('absent',{}),('false',{'126:python':{'approved':False}}),('mismatched',mismatched)]:
            with self.subTest(label=label),tempfile.TemporaryDirectory() as temporary:
                output=Path(temporary).resolve()/'run';args=SimpleNamespace(output=output,gate_sha256='replay')
                contract={'artifact_hashes':{},'runtime':{},'selected_programs':[selected],'manual_reviews':reviews,'batch_plans':{'126':plan},'scope':'synthetic','execution_gate_sha256':'original'}
                values=(b'freeze',contract,pop,{}, {126:rows},{})
                with patch.object(P,'verified_inputs',return_value=values),patch.object(P,'access') as access,patch.object(P,'staged_files') as stage,patch.object(P.sandbox,'run') as runner:
                    report=P.execute(args)
                    runner.assert_not_called();access.assert_not_called();stage.assert_not_called()
                self.assertEqual(report['executed_call_count'],0);self.assertEqual(report['dispatch_blocked_program_count'],1)
                saved=P.read_json(output/'126-python.summary.json');self.assertEqual(saved['executed_calls'],0)
                for flag in ('execution_complete','admitted_cases_passed','complete_prepared_suite_passed','qualified','actual_official_entry_suite_qualified','dispatch_authorized'):self.assertIs(saved[flag],False,flag)
                self.assertFalse(list(output.glob('*.start.json')))
                spec=importlib.util.spec_from_file_location('q_blocked_replay_'+label,HERE/'verify.py');replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
                with patch.object(replay.P,'verified_inputs',return_value=values),patch.object(replay.P,'bounded_regular_read') as reader:
                    receipt=replay.verify(args);reader.assert_not_called()
                    self.assertEqual(receipt['calls_replayed'],0)
                    (output/'126-python-0000.start.json').write_bytes(b'{}')
                    with self.assertRaises(ValueError):replay.verify(args)
    def test_stdout_and_stderr_caps_are_each_not_aggregate(self):
        rows=[{'args':['a','b',['b']],'expected':[['a','b']]}];plain=stream([observation(126,rows[0]['args'],rows[0]['expected'])]);raw=b' '*(P.PER_STREAM_OUTPUT_BYTES-len(plain))+plain
        metadata={'exit_code':0,'signal':None,'timed_out':False,'output_limit_exceeded':False,'stderr_bytes':P.PER_STREAM_OUTPUT_BYTES}
        owner=SimpleNamespace(check_observation=lambda *args:(True,None))
        self.assertEqual(P.verdict(126,'python',rows,[0],metadata,raw,owner),[])
        for bad in ({**metadata,'stderr_bytes':P.PER_STREAM_OUTPUT_BYTES+1},):self.assertEqual(P.verdict(126,'python',rows,[0],bad,raw,owner)[0]['reason'],'sandbox_process_failure')
        self.assertEqual(P.verdict(126,'python',rows,[0],metadata,raw+b' ',owner)[0]['reason'],'sandbox_process_failure')
    def test_replay_stream_boundary_tamper_and_oversize_before_hash(self):
        spec=importlib.util.spec_from_file_location('q_stream_boundary_replay',HERE/'verify.py');replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
        raw=b'x'*P.PER_STREAM_OUTPUT_BYTES;metadata={'stdout_sha256':P.sha(raw),'stdout_bytes':len(raw)}
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary).resolve()/'stdout';path.write_bytes(raw)
            with patch.object(replay.P,'bounded_regular_read',wraps=replay.P.bounded_regular_read) as reader:
                self.assertEqual(len(replay.read_stream(path,metadata,'stdout')),P.PER_STREAM_OUTPUT_BYTES)
                self.assertEqual(reader.call_args.kwargs['maximum_bytes'],16*1024**2)
            with self.assertRaises(ValueError):replay.read_stream(path,{**metadata,'stdout_sha256':'0'*64},'stdout')
            with self.assertRaises(ValueError):replay.read_stream(path,{**metadata,'stdout_bytes':True},'stdout')
            path.write_bytes(raw+b'x')
            with patch.object(replay.P,'sha') as hasher:
                with self.assertRaises(ValueError):replay.read_stream(path,metadata,'stdout')
                hasher.assert_not_called()
            path.write_bytes(raw);link=path.with_name('linked-stdout');link.symlink_to(path)
            with self.assertRaises((ValueError,OSError)):replay.read_stream(link,metadata,'stdout')

if __name__=='__main__':unittest.main()
