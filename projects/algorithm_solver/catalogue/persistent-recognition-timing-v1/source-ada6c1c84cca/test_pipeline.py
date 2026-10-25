import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).parent
sys.path.insert(0,str(HERE))
import pipeline as p
import artifacts as a

IDS=[f'leetcode:{i}' for i in range(1,4082)]
class Clock:
    def __init__(self):self.t=0
    def __call__(self):self.t+=1;return self.t
class Encoder:
    def __init__(self,truncated=False):self.calls=[];self.truncated=truncated
    def encode(self,texts,query):
        self.calls.append((texts,query));self.last_request_info={'rows':1,'truncated':[self.truncated],'token_counts_before_truncation':[25]};return 'synthetic-vector'
class Index:
    def __init__(self,accept=True):self.calls=0;self.accept=accept
    def scores(self,vector):
        self.calls+=1;return [.9 if self.accept else .3]+[.1]*4080
class Service:
    def __init__(self,tamper=False,unavailable=False):self.calls=[];self.tamper=tamper;self.unavailable=unavailable
    def request(self,pid,language=None,include_source=False):
        self.calls.append((pid,language,include_source))
        if include_source and self.unavailable:return {'status':'abstain'}
        raw=b'SYNTHETIC_SOURCE_NEVER_PUBLISH';digest=p.sha(raw)
        sel={'status':'selected','problem_id':pid,'language':language,'implementation':{'source_sha256':digest,'receipt_sha256':'f'*64}}
        result={'status':'matched','consumer_selection':sel}
        if include_source:result['artifact']={'status':'materialized','language':language,'source_utf8':raw.decode()+('bad' if self.tamper else ''),'source_sha256':digest,'bytes':len(raw)}
        return result

class PipelineTests(unittest.TestCase):
    def invoke(self,**kw):
        return p.request(kw.pop('service',Service()),mode=kw.pop('mode','description'),ids=IDS,encoder=kw.pop('encoder',Encoder()),index=kw.pop('index',Index()),text='synthetic description',clock=Clock(),**kw)
    def test_full_success_stage_scope_and_redaction(self):
        r=self.invoke()
        self.assertEqual(r['status'],'artifact_returned')
        for stage in ('query_encoding','full_population_ranking','empirical_decision_and_metadata','materialize_javascript','materialize_python','response_serialization'):
            self.assertEqual(r['timing_seconds'][stage],1)
        self.assertGreater(r['timing_seconds']['end_to_end'],sum(v for k,v in r['timing_seconds'].items() if k!='end_to_end'))
        self.assertNotIn('SYNTHETIC_SOURCE_NEVER_PUBLISH',json.dumps(r));self.assertNotIn('source_utf8',json.dumps(r))
        self.assertEqual(r['candidate_executions'],0);self.assertFalse(r['recognition_qualified'])
    def test_warm_repeats_do_not_cache_query_vectors(self):
        e=Encoder();i=Index();s=Service()
        for _ in range(8):self.invoke(encoder=e,index=i,service=s)
        self.assertEqual(len(e.calls),8);self.assertEqual(i.calls,8)
        self.assertTrue(all(x==(['synthetic description'],True) for x in e.calls))
    def test_threshold_abstain_has_costs_no_source(self):
        s=Service();r=self.invoke(service=s,index=Index(False))
        self.assertEqual(r['status'],'abstain');self.assertEqual(r['reason'],'empirical_confidence_threshold')
        self.assertFalse(any(c[2] for c in s.calls));self.assertIn('response_serialization',r['timing_seconds'])
    def test_truncation_abstains_even_high_score(self):
        s=Service();r=self.invoke(service=s,encoder=Encoder(True))
        self.assertEqual(r['reason'],'truncated_query_or_index');self.assertEqual(s.calls,[])
    def test_materialization_tamper_error_retains_stage_cost(self):
        r=self.invoke(service=Service(tamper=True))
        self.assertEqual(r['status'],'error');self.assertEqual(r['failed_stage'],'materialize_javascript')
        self.assertIn('materialize_javascript',r['timing_seconds']);self.assertNotIn('source_utf8',json.dumps(r))
    def test_artifact_unavailable_abstains_no_fallback(self):
        s=Service(unavailable=True);r=self.invoke(service=s)
        self.assertEqual(r['status'],'abstain');self.assertEqual(r['reason'],'artifact_unavailable')
        self.assertTrue(all(c[0]=='leetcode:1' for c in s.calls))
    def test_exact_id_has_no_model_stages(self):
        e=Encoder();r=self.invoke(mode='exact-id-artifact',problem_id='leetcode:802',encoder=e)
        self.assertEqual(r['status'],'artifact_returned');self.assertEqual(e.calls,[])
        self.assertNotIn('query_encoding',r['timing_seconds']);self.assertIn('exact_id_metadata',r['timing_seconds'])
    def test_exact_id_scope_excludes_execution_and_other_ids(self):
        self.assertEqual(self.invoke(mode='execution')['status'],'error')
        self.assertEqual(self.invoke(mode='exact-id-artifact',problem_id='leetcode:1')['status'],'error')
    def test_fatal_resource_signal_not_swallowed(self):
        e=Encoder()
        with patch.object(e,'encode',side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):self.invoke(encoder=e)
    def test_incomplete_population_before_encode(self):
        e=Encoder();r=p.request(Service(),mode='description',ids=IDS[:-1],encoder=e,text='fixture')
        self.assertEqual(r['status'],'error');self.assertEqual(e.calls,[])
    def test_pin_tamper_and_duplicate_json_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'fixture.json';f.write_text('{"a":1}')
            pin={'path':str(f),'sha256':a.sha(f)};self.assertEqual(a.pinned(pin),{'a':1})
            f.write_text('{"a":2}')
            with self.assertRaises(ValueError):a.pinned(pin)
            f.write_text('{"a":1,"a":2}');pin['sha256']=a.sha(f)
            with self.assertRaises(ValueError):a.pinned(pin)
    def test_projection_takes_order_only(self):
        rows=[{'query_id':str(i),'text':f'synthetic{i}','kind':'not-for-selection','expected_id':'do-not-consume'} for i in range(52)]
        with patch.object(a,'pinned',return_value={'queries':rows}):got=a.first_queries({})
        self.assertEqual([r['position'] for r in got],[0,1,2,3])
        self.assertTrue(all(set(r)=={'position','query_id','text'} for r in got))
    def test_supervisor_failure_manifest_without_child_report(self):
        import launch
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'run'
            fixture={'code_sha256':{},'python':'/synthetic/python','encoder_cache_identity':{'native_python_sha256':'x'},'resources':{'wall_seconds':240}}
            child=unittest.mock.Mock();child.wait.return_value=7;child.returncode=7
            with patch.object(launch,'pinned',return_value=fixture),patch.object(launch,'sha',return_value='x'),patch.object(launch.subprocess,'Popen',return_value=child),patch.object(launch,'cleanup_group',return_value={'synthetic':True}):
                code=launch.launch(SimpleNamespace(freeze='synthetic',freeze_sha256='h',output=str(target)))
            self.assertEqual(code,1);self.assertTrue((target/'failure.json').exists())
            self.assertEqual(json.loads((target/'supervisor.json').read_text())['exit_code'],7)

    def test_supervisor_cancellation_terminates_child(self):
        import launch
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as d:
            fixture={'code_sha256':{},'python':'/synthetic/python','encoder_cache_identity':{'native_python_sha256':'x'},'resources':{'wall_seconds':240}}
            child=unittest.mock.Mock();child.wait.side_effect=[KeyboardInterrupt(),-15];child.returncode=-15
            with patch.object(launch,'pinned',return_value=fixture),patch.object(launch,'sha',return_value='x'),patch.object(launch.subprocess,'Popen',return_value=child),patch.object(launch,'cleanup_group',return_value={'synthetic':True}) as cleanup:
                self.assertEqual(launch.launch(SimpleNamespace(freeze='synthetic',freeze_sha256='h',output=str(Path(d)/'run'))),1)
            cleanup.assert_called_once_with(child)

    def test_owned_group_cleanup_after_leader_exit(self):
        import launch,subprocess,time,os
        script="import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); print(p.pid,flush=True)"
        leader=subprocess.Popen([sys.executable,'-c',script],start_new_session=True,stdout=subprocess.PIPE,text=True)
        sleeper=int(leader.stdout.readline());leader.stdout.close();leader.wait(timeout=5)
        try:
            evidence=launch.cleanup_group(leader)
            self.assertEqual(evidence['process_group_id'],leader.pid)
            self.assertTrue(evidence['term_sent'])
            deadline=time.monotonic()+2
            while time.monotonic()<deadline:
                stat=Path(f'/proc/{sleeper}/stat')
                if not stat.exists() or stat.read_text().split()[2]=='Z':break
                time.sleep(.01)
            else:self.fail('owned sleeper descendant remains executing after leader exit')
        finally:
            try:os.killpg(leader.pid,9)
            except ProcessLookupError:pass

    def test_cache_structure_tamper_before_numpy(self):
        with self.assertRaises(ValueError):a.restore_index({'stable_ids':IDS,'baseline_chunks':[]},None)

if __name__=='__main__':unittest.main()
