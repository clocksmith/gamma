"""Invented 36-ID artifact fixture; never opens the private population."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import common,engine,qualification,report,run
from common import write,sha,seal_files
ALPHABET=[chr(i) for i in range(32,127)]+['\n']
CFG={'rounds':2,'search':{'trials':1,'seconds':10},'neighborhood':{'additions':96,'swaps':500,'pairs':150,'pair_additions':16,'pair_removals':8,'designed_fraction':.25}}
def spec(p):return {'file':str(p),'sha256':sha(p.read_bytes())}
def fixture(root):
    out=root/'run';out.mkdir();meta=root/'metadata';meta.mkdir();here=root/'implementation';here.mkdir()
    ids=list(range(1,37));fitids=ids[:27];val=ids[27:]
    texts={str(p):f'class Solution:\n    def solve(self,n):\n        total = n + {1+p%2}\n        return total\n' for p in ids}
    c={**CFG,'partition':{'dev_fit':fitids,'dev_val':val},'entries':{str(p):'solve' for p in ids},'sources':[],'inputs':{},
       'predictions':{f'P{i}':'synthetic' for i in range(1,6)},'decoder_source_bytes':13010,'offline_encoder_bytes':1000,
       'overall_seconds':2400,'supervisor_cleanup_seconds':30,'timing_receipt_tolerance_seconds':1,'qualification_cores':[0,1,2,3],
       'limits':{'qualification_batch_cases':32,'qualification_seconds':1800,'fit_seconds':300}}
    for pid in ids:
        expected=2+pid%2;tp=meta/f'{pid}-tests.json';write(tp,[{'args':[1],'expected':expected}])
        obs={'i':0,'result':expected,'result_type':'int','args_before':[1],'args_after':[1],'aliases':[],'error':None}
        bp=meta/f'{pid}-baseline.stdout';bp.write_text(json.dumps(obs)+'\n'+json.dumps({'done':1})+'\n')
        c['sources'].append({'id':pid,'entry':'solve','tests_file':str(tp),'tests_sha256':sha(tp.read_bytes()),'cases':1,'baseline_calls':[{**spec(bp),'cases':1}]})
    fits={str(p):texts[str(p)] for p in fitids};vals={str(p):texts[str(p)] for p in val}
    parent={'arms':[],'baseline':{}};results=[];allfit={};allchoice={};refs={};qjobs={}
    for width in (7,8):
        p=meta/f'w{width}';p.mkdir();write(p/'sources.json',texts);write(p/'fit.json',fits);write(p/'dictionary.json',ALPHABET)
        c['inputs'][str(width)]={'sources':spec(p/'sources.json'),'original_sources':spec(p/'sources.json'),'fit':spec(p/'fit.json'),'seed_dictionary':spec(p/'dictionary.json'),'baseline_dictionary':spec(p/'dictionary.json')}
        rec=engine.fit_supplied(fits,ALPHABET,width,{p:'solve' for p in fits},CFG)
        vr,vm=engine.validation_supplied(vals,{a:ALPHABET for a in engine.ARMS},width)
        for name in (*engine.ARMS,'R'):
            arm=out/f'w{width}'/name;arm.mkdir(parents=True)
            if name!='R':
                r=rec['arms'][name];v=vr[name];selected={**r['fit_sources'],**v['sources']};menus={**r['menus'],**vm}
                for file,value in [('dictionary',ALPHABET),('fit-sources',r['fit_sources']),('fit-variants',r['variants']),('fit-menus',r['menus'])]:write(arm/f'{file}.json',value)
                write(arm/'fit-record.json',{k:v for k,v in r.items() if k not in ('dictionary','fit_sources','variants','menus','all_menu_bans')})
                write(arm/'fit-seal.json',{'width':width,'arm':name,'validation_loaded':False,'case_data_loaded':False,'files':seal_files(arm,run.FIT_FILES)})
                key=common.identity(width,name);allfit[key]={'width':width,'arm':name,'elapsed':0,'fit_seal_sha256':sha((arm/'fit-seal.json').read_bytes())}
                for file,value in [('sources',selected),('validation-variants',v['variants']),('validation-menus',vm),('validation-choices',v['source_choices'])]:write(arm/f'{file}.json',value)
            else:
                selected=texts;menus={p:{'candidates':{'original':t}} for p,t in texts.items()}
                write(arm/'dictionary.json',ALPHABET);write(arm/'sources.json',selected)
            a=common.evaluate(selected,ALPHABET,width,c,menus);a.update(arm=name,source_choice_count=sum(selected[p]!=texts[p] for p in texts))
            write(arm/'unqualified-results.json',a);common.save_packets(arm,selected,ALPHABET,width)
            if name!='R':
                write(arm/'choices-seal.json',{'case_data_loaded':False,'files':seal_files(arm,run.CHOICE_FILES)})
                allchoice[common.identity(width,name)]={'width':width,'arm':name,'choices_seal_sha256':sha((arm/'choices-seal.json').read_bytes())}
            else:refs[str(width)]=seal_files(arm,('dictionary.json','sources.json','unqualified-results.json'))
            if name in ('U','R'):
                old=copy.deepcopy(a);old['arm']='scope_joint' if name=='U' else 'control';old['qualification']={p:{'passed':True} for p in texts};parent['arms'].append(old)
                if name=='R':parent['baseline'][str(width)]=copy.deepcopy(old)
            a['qualification']={}
            for pid,text in selected.items():
                if text!=texts[pid]:qjobs[f'{pid}-{sha(text.encode())}']=(next(s for s in c['sources'] if str(s['id'])==pid),text)
            results.append(a)
    pp=meta/'parent-receipt.json';write(pp,parent);c['qualification']=spec(pp)
    write(here/'contract.json',c);digest=sha((here/'contract.json').read_bytes())
    write(out/'all-fit-seal.json',{'validation_loaded':False,'case_data_loaded':False,'arms':allfit})
    write(out/'all-choices-seal.json',{'case_data_loaded':False,'all_fit_seal_sha256':sha((out/'all-fit-seal.json').read_bytes()),'arms':allchoice,'references':refs})
    write(out/'qualification-plan.json',{'all_choices_seal_sha256':sha((out/'all-choices-seal.json').read_bytes()),'keys':sorted(qjobs),'new_sources':len(qjobs),'cases':len(qjobs)})
    receipts={}
    for key,(s,text) in qjobs.items():
        folder=out/'qualification'/key;folder.mkdir(parents=True);raw=Path(s['baseline_calls'][0]['file']).read_bytes()
        (folder/'0.stdout').write_bytes(raw);(folder/'0.stderr').write_bytes(b'')
        batches=[{'offset':0,'cases':1,'ok':True,'exit_code':0,'timed_out':False,'output_limit_exceeded':False,'wall_seconds':0,'stdout_sha256':sha(raw),'stderr_sha256':sha(b'')}]
        receipts[key]=qualification.finish(s,text,batches,1,[]);write(folder/'receipt.json',receipts[key])
    write(out/'qualification-private.json',receipts)
    for a in results:
        selected=json.loads((out/f'w{a["width"]}'/a['arm']/'sources.json').read_text())
        for pid,text in selected.items():
            if text==texts[pid]:q={'passed':True,'reused':True,'receipt_sha256':c['qualification']['sha256']}
            else:
                key=f'{pid}-{sha(text.encode())}';q={'passed':True,'reused':False,'checks_passed':1,'cases':1,'receipt_sha256':sha((out/'qualification'/key/'receipt.json').read_bytes())}
            a['qualification'][pid]=q
        a['qualified']=36
    write(out/'results.json',{'contract_sha256':digest,'arms':results,'elapsed':1,'fresh_sources':len(qjobs),'fresh_cases':len(qjobs)})
    write(out/'run-binding.json',{'contract_sha256':digest});write(out/'status.json',{'complete':True,'phase':'complete','elapsed':1})
    write(out/'supervisor-receipt.json',{'complete':True,'exit_code':0,'outer_timeout':False,'contract_sha256':digest,'elapsed':1})
    return out,c,here
class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.out,cls.c,cls.here=fixture(cls.root)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def replay(self):
        with patch.object(report,'verify'),patch.object(report,'HERE',self.here):return report.replay(self.out,self.c)
    def test_independent_complete_artifact_replay(self):
        r=self.replay();self.assertTrue(r['complete']);self.assertEqual(len(r['arms']),10);self.assertEqual(r['fresh_sources'],36)
        self.assertTrue(r['predictions']['P1']);self.assertEqual(sum(a['qualified'] for a in r['arms']),360)
        self.assertTrue(all(w['S']['ready'] for w in r['verdicts_by_width'].values()))
        self.assertFalse(any(w['J']['ready'] for w in r['verdicts_by_width'].values()));self.assertNotIn('class Solution',json.dumps(r))
    def test_packet_tamper_rejected(self):
        p=self.out/'w7/S/packets/1.bin';raw=p.read_bytes();p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
        try:
            with self.assertRaises((AssertionError,ValueError)):self.replay()
        finally:p.write_bytes(raw)
    def test_missing_arm_rejected(self):
        p=self.out/'results.json';raw=p.read_bytes();r=json.loads(raw);r['arms'].pop();write(p,r)
        try:
            with self.assertRaises(AssertionError):self.replay()
        finally:p.write_bytes(raw)
    def test_failed_incomplete_execution_no_verdict(self):
        p=self.out/'failure.json';write(p,{'phase':'synthetic_timeout'})
        try:
            with patch.object(report,'verify'),patch.object(report,'HERE',self.here):
                with self.assertRaises(AssertionError):report.publish(self.out,self.c,self.root/'failed-report')
            r=json.loads((self.root/'failed-report/results.json').read_text());self.assertIsNone(r['verdicts_by_width']);self.assertFalse(r['promotion_allowed']);self.assertTrue(p.exists())
        finally:p.unlink()
    def test_seed_body_collision_retained_and_fixed(self):
        texts={'a':'class Solution:\n    def solve(self,n):\n        return n + 1\n','b':'class Solution:\n    def solve(self,n):\n        return n + 2\n'}
        seed=ALPHABET+['return n+1'];r=engine.fit_arm_supplied(texts,seed,7,{p:'solve' for p in texts},CFG,'S');self.assertEqual(r['dictionary'],seed)
        c={'entries':{p:'solve' for p in texts},'partition':{'dev_fit':['a'],'dev_val':['b']}}
        a=common.evaluate(r['fit_sources'],seed,7,c,r['menus']);self.assertEqual(a['illegal_entry_sha256'],[sha(b'return n+1')])
    def test_strict_observations_and_failure_retained(self):
        s=self.c['sources'][0];tests,base=qualification.inputs(s);raw=Path(s['baseline_calls'][0]['file']).read_bytes()
        self.assertEqual(qualification.observations(tests,base,raw,True,0),(1,[]))
        bad=raw.replace(b'"result_type": "int"',b'"result_type": "float"');passed,failures=qualification.observations(tests,base,bad,True,0)
        self.assertEqual(passed,0);self.assertEqual(failures,[{'case':0,'oracle':True,'parity':False}])
        with self.assertRaises(ValueError):qualification.parse(b'{"i":0,"i":0}\n{"done":1}\n',1)
        with self.assertRaises(AssertionError):qualification.parse(raw.splitlines()[0],1)
    def test_both_unencodable_tie_and_qualification_gate(self):
        a={'per_problem':{'1':{'encodable':False}}};self.assertEqual(report.paired(a,a,[1]),{'better':0,'same':1,'worse':0})
        r=self.replay();arms={(a['width'],a['arm']):a for a in r['arms']};a=copy.deepcopy(arms[7,'S']);a['qualified']=35
        self.assertFalse(report.gates(a,arms[7,'U'],self.c,True)['passed'])
    def test_output_limit_with_zero_exit_is_retained_qualification_failure(self):
        folder=self.root/'output-limit';folder.mkdir();s=self.c['sources'][0];source='class Solution:\n def solve(self,n):return n+2\n'
        raw=Path(s['baseline_calls'][0]['file']).read_bytes();(folder/'0.stdout').write_bytes(raw);(folder/'0.stderr').write_bytes(b'')
        batch={'offset':0,'cases':1,'ok':False,'exit_code':0,'timed_out':False,'output_limit_exceeded':True,'wall_seconds':0,'stdout_sha256':sha(raw),'stderr_sha256':sha(b'')}
        expected=qualification.finish(s,source,[batch],0,[{'offset':0,'reason_type':'AssertionError'}]);write(folder/'receipt.json',expected)
        self.assertEqual(qualification.replay(folder,s,source,self.c),expected);self.assertFalse(expected['passed'])
    def test_partial_costs_are_explicit_and_full_cohort_totals_null(self):
        rows={'1':{'encodable':True,'selections':1,'actions':2,'single_characters':1,'packet_bytes':42},'2':{'encodable':False}}
        c={'partition':{'dev_fit':[1],'dev_val':[2]},'decoder_source_bytes':13010}
        a={'width':7,'dictionary_bytes':100,'per_problem':rows,
           'fit':common.tail.aggregate(rows,[1],100),'validation':common.tail.aggregate(rows,[2],100)}
        report.augment_costs(a,{'1':'x','2':'y'},c)
        self.assertTrue(a['fit']['full_cohort_cost_available']);self.assertFalse(a['validation']['full_cohort_cost_available'])
        self.assertIsNone(a['validation']['full_cohort_actions']);self.assertIsNone(a['validation']['full_cohort_package_bytes'])
        self.assertIn('incomplete',a['validation']['aggregate_scope']);self.assertEqual(a['validation']['package_bytes'],100)
    def test_unknown_result_field_cannot_be_published(self):
        p=self.out/'results.json';raw=p.read_bytes();r=json.loads(raw);r['private_debug']='PRIVATE SOURCE FRAGMENT';write(p,r)
        try:
            with self.assertRaisesRegex(AssertionError,'unexpected result metadata'):self.replay()
        finally:p.write_bytes(raw)
    def test_nonfinite_overbudget_and_incoherent_run_timing_rejected(self):
        cases=[('results.json',999999),('results.json',float('inf')),('supervisor-receipt.json',float('nan')),
               ('supervisor-receipt.json',2432),('supervisor-receipt.json',0.5),('status.json',float('nan'))]
        for filename,seconds in cases:
            with self.subTest(filename=filename,seconds=seconds):
                p=self.out/filename;raw=p.read_bytes();r=json.loads(raw);r['elapsed']=seconds;write(p,r)
                try:
                    with self.assertRaises(AssertionError):self.replay()
                finally:p.write_bytes(raw)
        p=self.out/'all-fit-seal.json';raw=p.read_bytes();r=json.loads(raw);r['arms']['w7/U']['elapsed']=301.1;write(p,r)
        try:
            with self.assertRaisesRegex(AssertionError,'timing receipt exceeds'):self.replay()
        finally:p.write_bytes(raw)
    def test_search_stop_and_cost_metadata_are_constrained(self):
        good={'trials':1,'seconds':0.1,'selections':100,'stop':'trial_limit'}
        self.assertEqual(len(report.checked_search_rounds({'search':[good,good]},'J',self.c,1)),2)
        for field,value in [('stop','PRIVATE SOURCE'),('seconds',float('nan')),('seconds',2.1),('selections','PRIVATE SOURCE')]:
            bad={**good,field:value}
            with self.subTest(field=field):
                with self.assertRaises(AssertionError):report.checked_search_rounds({'search':[bad,good]},'J',self.c,1)
        with self.assertRaises(AssertionError):report.checked_search_rounds({'search':[good]},'S',self.c,1)
    def test_nonfinite_qualification_batch_time_rejected(self):
        folder=next((self.out/'qualification').iterdir());p=folder/'receipt.json';raw=p.read_bytes();receipt=json.loads(raw)
        spec=next(s for s in self.c['sources'] if str(s['id'])==receipt['id'])
        source=json.loads((self.out/'w7/S/sources.json').read_text())[receipt['id']]
        receipt['batches'][0]['wall_seconds']=float('nan');write(p,receipt)
        try:
            with self.assertRaisesRegex(AssertionError,'invalid timing receipt'):qualification.replay(folder,spec,source,self.c)
        finally:p.write_bytes(raw)
    def test_failure_replaces_previous_successful_markdown(self):
        output=self.root/'replace-success'
        with patch.object(report,'verify'),patch.object(report,'HERE',self.here):report.publish(self.out,self.c,output)
        self.assertIn('ready:',(output/'REPORT.md').read_text())
        p=self.out/'failure.json';write(p,{'phase':'synthetic_timeout'})
        try:
            with patch.object(report,'verify'),patch.object(report,'HERE',self.here):
                with self.assertRaises(AssertionError):report.publish(self.out,self.c,output)
            self.assertIn('**No verdict.**',(output/'REPORT.md').read_text());self.assertNotIn('ready:',(output/'REPORT.md').read_text())
            self.assertFalse(json.loads((output/'results.json').read_text())['complete'])
        finally:p.unlink()
if __name__=='__main__':unittest.main()
