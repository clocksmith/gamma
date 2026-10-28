"""P controller toy/mock controls; never import or execute candidate sources."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('p_fixed_controller_tests',HERE/'protocol.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)


def record(i=0,lang='python'):
    r={'i':i,'native_route':'official-wrapper-p-v1','problem_id':17,'method':'letterCombinations',
       'result':['a','b','c'],'result_type':'list'if lang=='python'else'object','args_before':['2'],
       'args_after':['2'],'alias_edges':[],'node_identity':None,'node_integrity':None,'board_identity':None}
    if lang=='javascript':r['entry_kind']='javascript-official-function'
    return r

def stream(records):return b'\n'.join(P.encoded(r)for r in records+[{'done':len(records)}])+b'\n'


class ProtocolTests(unittest.TestCase):
    def test_exact_selected_twenty_and_profile(self):
        pop=P.population();inv=P.inventory(pop)
        self.assertEqual(len(inv),20)
        self.assertTrue(all(str(P.OFFICIAL_JS)in str(P.DIRECTORIES[lang])for pid,lang in inv if lang=='javascript'))
        self.assertEqual(P.ARGV['javascript'],['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs'])

    def test_exact_language_template_hashes_are_not_definition_raw_hashes(self):
        pop=P.population()
        self.assertTrue(all(r['response_sha256']!=r['templates']['javascript']['response_sha256']for r in pop['problems']))
        q={'questionFrontendId':'17','title':'toy','titleSlug':'toy','isPaidOnly':False,'codeSnippets':[{'langSlug':'python3','code':'toy py'},{'langSlug':'javascript','code':'toy js'}]}
        raw=P.encoded({'data':{'question':q}});spec={'id':17,'title':'toy','slug':'toy','templates':{lang:{'response_sha256':P.sha(raw),'template_sha256':P.sha(code.encode())}for lang,code in [('python','toy py'),('javascript','toy js')]}}
        self.assertEqual(set(P.validate_templates(raw,spec)),set(P.LANGUAGES))
        for bad in ('wrong raw','wrong code'):
            pins=json.loads(json.dumps(spec));pins['templates']['javascript']['response_sha256'if bad=='wrong raw'else'template_sha256']='0'*64
            with self.assertRaises(ValueError):P.validate_templates(raw,pins)

    def test_denial_precedes_any_public_request(self):
        with tempfile.TemporaryDirectory()as temp:
            args=SimpleNamespace(gate=Path('/unused'),gate_sha256='pin',statements=Path(temp)/'new')
            with patch.object(P,'population',return_value={'problems':[{'id':17,'slug':'toy'}]}),patch.object(P.engine,'gate_file',return_value={}),patch.object(P,'live',side_effect=PermissionError('closed')),patch.object(P.urllib.request,'urlopen')as network:
                with self.assertRaises(PermissionError):P.prepare(args)
                network.assert_not_called()

    def test_wrong_source_route_rejected(self):
        pop=P.population();bad=json.loads(json.dumps(pop));bad['source_directories']['javascript']=str(P.REFERENCE)
        original=P.read_json
        with patch.object(P,'read_json',side_effect=lambda p:bad if Path(p)==HERE/'population.json'else original(p)):
            with self.assertRaises(ValueError):P.population()

    def test_review_rejects_wrong_template_and_false_native_flags(self):
        pop=P.population();inv=P.inventory(pop);key=(17,'python');source=inv[key]
        binding=P.review_binding(pop,*key,source)
        toy={'problem_id':17,'language':'python','reviewer':'synthetic test only',**binding,**{f:True for f in P.FLAGS}}
        with tempfile.TemporaryDirectory()as temp:
            path=Path(temp)/'toy-review.json'
            def judge(row):
                path.write_bytes(P.encoded({'programs':[row]}))
                return P.reviews(path,{**pop,'review_sha256':P.sha(path.read_bytes())},{key:source})['17:python']['approved']
            self.assertTrue(judge(toy))
            self.assertFalse(judge({**toy,'official_language_template_sha256':'wrong'}))
            self.assertFalse(judge({**toy,'native_mutation_and_topology':False}))
            self.assertFalse(judge({**toy,'source_path':str(P.OFFICIAL_JS/'javascript/17.js')}))
            with self.assertRaises(ValueError):judge({**toy,'problem_id':17.0})

    def test_packet_contains_no_answers_or_graph_effect_plans(self):
        rows=[{'args':[{'__tree_node__':[1,2]}],'expected':{'secret_effect':123}}]
        wire=P.encoded(P.packet(114,rows,[0,0]))
        self.assertNotIn(b'expected',wire);self.assertNotIn(b'secret_effect',wire)
        self.assertEqual(json.loads(wire)['schema'],'gamma.p-official-wrapper-packet.v1')

    def test_native_entry_kind_only_javascript(self):
        self.assertEqual(P.parse(stream([record(lang='javascript')]),1,'javascript')[0]['entry_kind'],'javascript-official-function')
        for raw,lang in[(stream([record(lang='javascript')]),'python'),(stream([record()]),'javascript'),(stream([{**record(lang='javascript'),'entry_kind':'custom-Solution'}]),'javascript')]:
            with self.assertRaises(ValueError):P.parse(raw,1,lang)

    def test_truncated_reordered_extra_duplicate_boolean_done_rejected(self):
        for raw in (P.encoded(record())+b'\n',stream([record(1)]),stream([{**record(),'unknown':1}]),P.encoded(record())+b'\n{"done":true}\n',b'{"i":0,"i":0,"error":"bad"}\n{"done":1}\n',stream([record()])+b'{}\n'):
            with self.assertRaises(ValueError):P.parse(raw,1,'python')

    def test_process_failure_never_becomes_native_pass(self):
        rows=[{'args':['2'],'expected':['a','b','c']}]
        for meta in ({'exit_code':1,'timed_out':False,'output_limit_exceeded':False},{'exit_code':0,'timed_out':True,'output_limit_exceeded':False}):
            self.assertEqual(P.verdict(17,'python',rows,[0],meta,stream([record()]))[0]['reason'],'sandbox_process_failure')

    def test_owner_checker_rejects_faked_physical_identity(self):
        meta={'exit_code':0,'timed_out':False,'output_limit_exceeded':False}
        rows=[{'args':['2'],'expected':['a','b','c']}]
        self.assertEqual(P.verdict(17,'python',rows,[0],meta,stream([record()])),[])
        self.assertTrue(P.verdict(17,'python',rows,[0],meta,stream([{**record(),'node_identity':{}}])))

    def test_missing_review_is_no_qualification(self):
        rows=[{'args':['2'],'expected':['a','b','c']}];plan=P.batch_plan(17,rows)
        r=P.summary(17,'python',rows,plan,[],2,{'approved':False})
        self.assertFalse(r['qualified_finite_official_interface']);self.assertTrue(r['blocked_review'])
        self.assertFalse(P.summary(17,'python',rows,plan,[],0,{'approved':True})['qualified_finite_official_interface'])

    def test_preserved_maximum_forest_and_tree_cases_fit_without_caps_change(self):
        examples={95:{'args':[8],'expected':None},108:{'args':[list(range(10000))],'expected':None},116:{'args':[{'__next_node__':[1]*4095}],'expected':None},117:{'args':[{'__next_node__':[1]*6000}],'expected':None},99:{'args':[{'__tree_node__':[1]*1000}],'expected':None},114:{'args':[{'__tree_node__':[1]*2000}],'expected':None}}
        for pid,large in examples.items():
            small={'args':[1],'expected':None}if pid==95 else{'args':[[1]],'expected':None}if pid==108 else{'args':[{'__next_node__'if pid in(116,117)else'__tree_node__':[1]}],'expected':None}
            plan=P.batch_plan(pid,[small,large]);self.assertEqual(plan['blocked_cases'],[])
            self.assertIn(1,{i for b in plan['batches']for i in b['indices']})
            self.assertLessEqual(max(b['conservative_output_bound_bytes']for b in plan['batches']),P.LIMITS.max_output_bytes)
        self.assertEqual(P.LIMITS.memory_bytes,1024**3);self.assertEqual(P.LIMITS.cpu_seconds,3)

    def test_impossible_transport_case_is_named_and_not_qualified(self):
        rows=[{'args':['2'],'expected':['a','b','c']}]
        with patch.object(P,'output_bound',return_value=P.LIMITS.max_output_bytes+1):plan=P.batch_plan(17,rows)
        self.assertEqual(plan['blocked_cases'][0]['case'],0)
        self.assertFalse(P.summary(17,'python',rows,plan,[],0,{'approved':True})['qualified_finite_official_interface'])

    def test_dynamic_freeze_summary_ten_ids_twenty_programs_no_execution(self):
        rows={pid:[{'args':['toy'],'expected':False}]for pid in P.IDS}
        with tempfile.TemporaryDirectory()as temp:
            temp=Path(temp);log=temp/'log';log.write_bytes(b'37 passed\n');args=SimpleNamespace(gate=temp/'unused',gate_sha256='pin',preflight=log,preflight_sha256=P.sha(log.read_bytes()),review=None,freeze=temp/'freeze')
            with patch.object(P,'population',return_value={}),patch.object(P.engine,'gate_file',return_value={'trusted_hashes':{}}),patch.object(P.engine,'runtime',return_value={}),patch.object(P,'inputs',return_value={}),patch.object(P,'inventory',return_value={}),patch.object(P,'artifacts',return_value={}),patch.object(P,'cases',return_value=rows),patch.object(P,'batch_plan',return_value={'blocked_cases':[]}),patch.object(P,'reviews',return_value={}),patch.object(P.engine.sandbox,'run')as candidate:
                value=P.freeze(args)
            self.assertEqual((value['problems'],value['programs'],value['candidate_executions']),(10,20,0));candidate.assert_not_called()

    def test_mocked_raw_retention_and_separate_replay_never_executes_candidates(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary).resolve();source=root/'source/python';source.mkdir(parents=True);(source/'17.py').write_bytes(b'# inert toy source; never executed\n');observers=root/'observer';observers.mkdir();(observers/'harness.py').write_bytes(b'# inert toy observer\n')
            rows=[{'args':['2'],'expected':['a','b','c']}];plan=P.batch_plan(17,rows);raw=b'synthetic-freeze';value={'artifact_hashes':{'observer/harness.py':P.sha((observers/'harness.py').read_bytes())},'runtime':{},'plans':{'17':plan},'reviews':{'17:python':{'approved':True}},'execution_gate_sha256':'original'};inv={(17,'python'):{'path':'python/17.py','sha256':P.sha((source/'17.py').read_bytes())}};args=SimpleNamespace(output=root/'out',gate_sha256='replay')
            sandbox=P.engine.sandbox.SandboxResult(exit_code=0,signal=None,stdout=stream([record(),record(1)]),stderr=b'',wall_seconds=0,timed_out=False,output_limit_exceeded=False)
            def judge(*args):
                self.assertTrue((root/'out/17-python-0000.stdout').exists());self.assertTrue((root/'out/17-python-0000.result.json').exists());return[]
            with patch.object(P,'ROOT',root),patch.object(P,'DIRECTORIES',{'python':Path('source')}),patch.object(P,'OBSERVERS',Path('observer')),patch.object(P,'IDS',(17,)),patch.object(P,'LANGUAGES',('python',)),patch.object(P,'verified',return_value=(raw,value,{}, {},inv,{17:rows})),patch.object(P,'live'),patch.object(P,'verdict',side_effect=judge),patch.object(P.engine.sandbox,'run',return_value=sandbox)as candidate:
                self.assertEqual(P.run_or_replay(args)['programs'],1)
                self.assertEqual(P.run_or_replay(args,True)['executed_calls'],2);candidate.assert_called_once()
                value['reviews']['17:python']['approved']=False
                args.output=root/'unreviewed'
                skipped=P.run_or_replay(args);self.assertEqual(skipped['executed_calls'],0);candidate.assert_called_once()
                value['reviews']['17:python']['approved']=True;args.output=root/'out'
                (root/'out/17-python-0000.stdout').write_bytes(b'changed')
                with self.assertRaises(ValueError):P.run_or_replay(args,True)

if __name__=='__main__':unittest.main()
