"""Synthetic protocol controls only: no candidate imports, execution or network."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('continuation_protocol',HERE/'protocol.py')
P=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(P)


def observation(case,result=None,index=0,language='python'):
    return {'i':index,'result':case['expected'] if result is None else result,
        'result_type':P.return_type(3627,case,language),'args_before':case['args'],
        'args_after':case['args'],'alias_edges':[]}


def raw_stream(records):
    return b'\n'.join(P.encoded(row) for row in [*records,{'done':len(records)}])+b'\n'


class FixedProtocolTests(unittest.TestCase):
    def test_fixed_population_and_original_source_routes(self):
        value=P.population()
        self.assertEqual(tuple(value['cohorts']['d']['problems'][0][key] for key in ('id','slug')),
                         (3702,'longest-subsequence-with-non-zero-bitwise-xor'))
        self.assertEqual(sum(len(row['problems']) for row in value['cohorts'].values()),20)
        self.assertEqual(P.ARGV['javascript'],['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs'])

    def test_de_owner_apis_cases_and_analytic_isolation(self):
        data,owners=P.cases_and_owners(P.population())
        self.assertEqual(set(data),set(P.IDS['d']+P.IDS['e']))
        for pid,rows in data.items():
            if pid in P.IDS['d']:self.assertTrue(any(row.get('category')=='analytic-domain-maximum' for row in rows))
            else:self.assertTrue(any(row.get('category')!='seeded-bounded-independent-reference' for row in rows))
            plan=P.batch_plan(pid,rows)
            self.assertEqual(plan['admitted_distinct_cases'],len(rows));self.assertFalse(plan['blocked_cases'])
            for index,row in enumerate(rows):
                if row.get('isolate'):
                    batches=[entry for entry in plan['batches'] if index in entry['indices']]
                    self.assertEqual([entry['indices'] for entry in batches],[[index]])
            for language in P.LANGUAGES:
                record=observation(rows[0],language=language)
                self.assertIsNone(P.compare(pid,language,rows[0],record,owners[pid]))

    def test_public_definition_identity_content_api_and_paid_fail_closed(self):
        api={'name':'solve','params':[],'return':{'type':'integer'}}
        question={'questionFrontendId':'1','title':'synthetic','titleSlug':'synthetic','isPaidOnly':False,
                  'content':'inert synthetic definition','metaData':json.dumps(api)}
        spec={'id':1,'title':'synthetic','slug':'synthetic','content_sha256':P.sha(question['content'].encode()),
              'api_sha256':P.sha(P.encoded(api))}
        self.assertEqual(P.validate_definition(P.encoded({'data':{'question':question}}),spec),question)
        for key,bad in (('questionFrontendId','2'),('titleSlug','other'),('title','other'),('isPaidOnly',True),
                        ('content','changed'),('metaData','{}')):
            with self.subTest(key=key),self.assertRaises(ValueError):
                P.validate_definition(P.encoded({'data':{'question':{**question,key:bad}}}),spec)

    def test_wrong_live_permission_identity_never_authorizes_open(self):
        good={'authorized':True,'problem_id':'leetcode:3623','language':'python','payload_kind':'source'}
        for change in ({'authorized':1},{'authorized':False},{'problem_id':'leetcode:3625'},
                       {'language':'javascript'},{'payload_kind':'statement'}):
            with self.subTest(change=change),patch.object(P,'authorize_before_open',return_value={**good,**change}),self.assertRaises(PermissionError):
                P.access({'artifact_paths':{},'trusted_hashes':{}},3623,'python')

    def test_denial_precedes_public_network_fetch(self):
        pop={'cohorts':{'a':{'problems':[{'id':3623,'slug':'synthetic'}]}}}
        with tempfile.TemporaryDirectory() as temporary:
            args=SimpleNamespace(gate=Path('/unused'),gate_sha256='pin',statements=Path(temporary)/'new')
            with patch.object(P,'population',return_value=pop),patch.object(P,'gate_file',return_value={}), \
                    patch.object(P,'access',side_effect=PermissionError('closed')),patch.object(P.urllib.request,'urlopen') as network:
                with self.assertRaises(PermissionError):P.prepare(args)
                network.assert_not_called()

    def test_runtime_refuses_macos_before_process_or_freeze(self):
        with patch.object(P.sys,'platform','darwin'),patch.object(P.sandbox,'check_available') as check:
            with self.assertRaises(P.sandbox.SandboxUnavailable):P.runtime()
            check.assert_not_called()

    def test_preflight_failure_precedes_definition_and_source_open(self):
        with tempfile.TemporaryDirectory() as temporary:
            log=Path(temporary)/'log';log.write_bytes(b'36 passed\n')
            args=SimpleNamespace(gate=Path('/unused'),gate_sha256='pin',preflight=log,
                preflight_sha256=P.sha(log.read_bytes()),freeze=Path(temporary)/'freeze')
            with patch.object(P,'population',return_value={}),patch.object(P,'gate_file',return_value={}), \
                    patch.object(P,'runtime',return_value={}),patch.object(P,'definitions') as definitions,patch.object(P,'artifacts') as sources:
                with self.assertRaises(ValueError):P.freeze(args)
                definitions.assert_not_called();sources.assert_not_called();self.assertFalse(args.freeze.exists())

    def test_small_batch_keeps_same_interpreter_repeat(self):
        rows=[{'args':[[i]],'expected':i} for i in range(3)]
        result=P.batch_plan(3627,rows)
        self.assertEqual(result['batches'][0]['indices'],[0,1,2,0])
        self.assertEqual(result['blocked_cases'],[])
        self.assertEqual(result['admitted_distinct_cases'],3)

    def test_large_output_brackets_one_large_call_with_small_repeat(self):
        rows=[{'args':['x'],'expected':0},{'args':['x'*5000000],'expected':0}]
        result=P.batch_plan(3627,rows)
        large=next(entry for entry in result['batches'] if 1 in entry['indices'])
        self.assertEqual(large['indices'],[0,1,0]);self.assertEqual(large['policy'],'small-large-small')
        self.assertLessEqual(max(large['projected_output_bytes'].values()),P.LIMITS.max_output_bytes)
        self.assertLessEqual(large['input_bytes'],P.MAX_INPUT_BYTES)
        self.assertEqual(result['blocked_cases'],[])

    def test_single_observation_above_output_cap_remains_explicitly_blocked(self):
        rows=[{'args':['x'],'expected':0},{'args':['x'*9000000],'expected':0}]
        result=P.batch_plan(3627,rows)
        self.assertEqual(result['blocked_cases'][0]['case'],1)
        self.assertEqual(result['logical_case_count'],2);self.assertEqual(result['admitted_distinct_cases'],1)
        self.assertEqual({i for entry in result['batches'] for i in entry['indices']},{0})

    def test_output_byte_projection_matches_small_success_wire(self):
        rows=[{'args':[[1,2,3]],'expected':2}];record=observation(rows[0])
        # Python harness uses compact records but default done-key spacing.
        wire=json.dumps(record,separators=(',',':')).encode()+b'\n'+json.dumps({'done':1}).encode()+b'\n'
        self.assertEqual(P.projected_output(3627,'python',rows,[0]),len(wire))

    def test_no_host_expected_or_policy_leaks_into_argument_packet(self):
        rows=[{'args':[[1]],'expected':987654321,'category':'private-host','comparison_policy':'exact'}]
        packet=P.packet(rows,[0,0]);self.assertEqual(packet,{'entry':'solve','calls':[{'args':[[1]]},{'args':[[1]]}]})
        self.assertNotIn(b'987654321',P.encoded(packet));self.assertNotIn(b'expected',P.encoded(packet))

    def test_partial_extra_reordered_duplicate_nan_and_boolean_done_rejected(self):
        case={'args':[1],'expected':2};record=observation(case)
        malformed=[P.encoded(record)+b'\n',raw_stream([dict(record,i=1)]),
                   raw_stream([dict(record,extra=1)]),P.encoded(record)+b'\n{"done":true}\n',
                   b'{"i":0,"i":0,"error":"bad"}\n{"done":1}\n',
                   b'{"i":0,"result":NaN}\n{"done":1}\n',raw_stream([record])+b'{}\n']
        for raw in malformed:
            with self.subTest(raw=raw[:50]),self.assertRaises((ValueError,UnicodeError)):P.parse(raw,1)

    def test_process_failures_cannot_become_value_passes(self):
        rows=[{'args':[1],'expected':2}];wire=raw_stream([observation(rows[0])])
        for change in ({'exit_code':1},{'exit_code':False},{'timed_out':True},{'output_limit_exceeded':True}):
            meta={'exit_code':0,'timed_out':False,'output_limit_exceeded':False,**change}
            self.assertEqual(P.verdict(3627,'python',rows,[0],meta,wire,None)[0]['reason'],'sandbox_process_failure')

    def test_values_types_mutation_alias_and_candidate_errors_rejected(self):
        case={'args':[[1,2,3]],'expected':2};record=observation(case)
        self.assertIsNone(P.compare(3627,'python',case,record,SimpleNamespace(matches=lambda *args:True)))
        for change,wanted in [({'result':True},'result_value'),({'result':2.0},'result_value'),
                              ({'result_type':'float'},'result_type'),({'args_after':[[1,2,True]]},'input_effects'),
                              ({'args_before':[[3,2,1]]},'input_effects'),({'alias_edges':[['result','args.0']]},'return_aliases'),
                              ({'error':'failed'},'candidate_error')]:
            self.assertEqual(P.compare(3627,'python',case,{**record,**change},SimpleNamespace(matches=lambda *args:True)),wanted)

    def test_missing_reviews_and_blocked_cases_prevent_qualification(self):
        rows=[{'args':[1],'expected':2}];plan={'blocked_cases':[],'admitted_distinct_cases':1}
        summary=P.program_summary(3627,'python',rows,plan,[],1,{'approved':False})
        self.assertTrue(summary['admitted_cases_passed']);self.assertFalse(summary['qualified'])
        summary=P.program_summary(3627,'python',rows,{**plan,'blocked_cases':[{'case':0}]},[],1,{'approved':True})
        self.assertFalse(summary['qualified']);self.assertFalse(summary['complete_prepared_suite_passed'])
        summary=P.program_summary(3627,'python',rows,{'blocked_cases':[{'case':0}],'admitted_distinct_cases':0},[],0,{'approved':True})
        self.assertFalse(summary['admitted_cases_passed']);self.assertFalse(summary['qualified'])

    def test_freeze_hash_and_settings_drift_precede_source_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            frozen=Path(temporary)/'freeze';frozen.write_bytes(P.encoded({'schema':'wrong'}))
            args=SimpleNamespace(freeze=frozen,freeze_sha256=P.sha(frozen.read_bytes()))
            with patch.object(P,'population') as population:
                with self.assertRaises(ValueError):P.verified_inputs(args,False)
                population.assert_not_called()
            args.freeze_sha256='0'*64
            with self.assertRaises(ValueError):P.verified_inputs(args,False)

    def test_raw_streams_and_process_metadata_saved_before_verdict(self):
        case={'args':[1],'expected':2};stream=raw_stream([observation(case)])
        plan={'batches':[{'indices':[0],'policy':'synthetic','input_bytes':len(P.encoded(P.packet([case],[0])))}],
              'blocked_cases':[],'admitted_distinct_cases':1}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();directory=root/'source';(directory/'python').mkdir(parents=True)
            source=b'# inert source bytes; not executed\n';(directory/'python/3627.py').write_bytes(source)
            transport=root/'observer';transport.mkdir();harness=b'# inert observer bytes; not executed\n';(transport/'harness.py').write_bytes(harness)
            output=root/'run';raw=b'synthetic-freeze';pins={'source/python/3627.py':P.sha(source),'observer/harness.py':P.sha(harness)}
            contract={'artifact_hashes':pins,'runtime':{},'batch_plans':{'3627':plan},
                      'manual_reviews':{'3627:python':{'approved':False}},'scope':'synthetic'}
            args=SimpleNamespace(output=output)
            result=P.sandbox.SandboxResult(exit_code=0,signal=None,stdout=stream,stderr=b'',wall_seconds=0,
                                            timed_out=False,output_limit_exceeded=False)
            real_verdict=P.verdict
            def judge(*arguments):
                self.assertEqual((output/'3627-python-000.stdout').read_bytes(),stream)
                self.assertTrue((output/'3627-python-000.result.json').exists())
                return real_verdict(*arguments)
            with patch.object(P,'ROOT',root),patch.object(P,'IDS',{'a':(3627,)}),patch.object(P,'LANGUAGES',('python',)), \
                    patch.object(P,'DIRECTORIES',{'a':Path('source')}),patch.object(P,'TRANSPORT',Path('observer')), \
                    patch.object(P,'verified_inputs',return_value=(raw,contract,{}, {},{3627:[case]},{3627:SimpleNamespace(matches=lambda *args:True)})), \
                    patch.object(P,'access'),patch.object(P.sandbox,'run',return_value=result) as runner,patch.object(P,'verdict',side_effect=judge):
                summary=P.execute(args)
                self.assertEqual(summary['qualified_finite_suite_programs'],0)
                inputs=runner.call_args.kwargs['files']['inputs.json']
                self.assertNotIn(b'expected',inputs)
                self.assertEqual(runner.call_args.kwargs['limits'],P.LIMITS)
            sys.path.insert(0,str(HERE))
            try:
                spec=importlib.util.spec_from_file_location('continuation_replay_test',HERE/'verify.py')
                replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
            finally:
                sys.path.pop(0)
            contract['execution_gate_sha256']='synthetic-gate';args.gate_sha256='relocated-synthetic-gate'
            with patch.object(replay,'ROOT',root),patch.object(replay,'IDS',{'a':(3627,)}), \
                    patch.object(replay,'DIRECTORIES',{'a':Path('source')}),patch.object(replay,'LANGUAGES',('python',)), \
                    patch.object(replay,'verified_inputs',return_value=(raw,contract,{}, {},{3627:[case]},{3627:SimpleNamespace(matches=lambda *args:True)})):
                result=replay.verify(args)
                self.assertEqual(result['programs_replayed'],1);self.assertFalse(result['candidate_execution_on_replay_host'])
                (output/'3627-python-000.stdout').write_bytes(stream+b' ')
                with self.assertRaises(ValueError):replay.verify(args)


if __name__=='__main__':unittest.main()
