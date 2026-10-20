import copy,json,tempfile,unittest
from pathlib import Path
from algsolve import corpus_campaign as c
from algsolve import campaign_public_contracts as p
from campaign_public_fixture import fixture,stage,evidence,record,write

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.f=fixture(Path(temp.name))
    def change_contract(self,fn):
        fn(self.f['contract']);write(self.f['contract_path'],self.f['contract'])
    def ready(self):stage(self.f);self.receipts=evidence(self.f)
    def mutate_artifact(self,name,fn):
        e=self.receipts['execution'];ref=e[name];path=Path(ref['path']);value=json.loads(path.read_text());fn(value);write(path,value);new=c.file_ref(path)
        for receipt in self.receipts.values():
            receipt['artifacts']=[new if x['path']==ref['path'] else x for x in receipt['artifacts']]
        e[name]=new
        # Retarget the qualification links too, so tests reach semantic validation.
        if name in ['host_tests','qualification_freeze']:
            qpath=Path(e['semantic_qualification']['path']);q=json.loads(qpath.read_text());q['host_tests_sha256' if name=='host_tests' else 'freeze_sha256']=new['sha256'];write(qpath,q);qref=c.file_ref(qpath)
            for receipt in self.receipts.values():receipt['artifacts']=[qref if x['path']==str(qpath) else x for x in receipt['artifacts']]
            e['semantic_qualification']=qref
    def test_valid_profile_admits_and_preserves_strict_failure(self):
        self.ready();record(self.f,self.receipts);self.assertEqual(self.f['entry']['status'],'complete');self.assertEqual(self.receipts['execution']['strict_public_passed'],2)
        self.assertTrue(self.f['entry']['attempts'][-1]['public_profile'])
    def test_missing_coordinator_policy_rejected(self):
        del self.f['data']['inputs']['public_comparison_policy']
        with self.assertRaises((ValueError,TypeError)):stage(self.f)
    def test_self_approval_rejected(self):
        registry=json.loads(self.f['policy'].read_text());registry['approved_by']='/root/review_standard';write(self.f['policy'],registry);ref=c.file_ref(self.f['policy']);self.f['data']['inputs']['public_comparison_policy']=ref;self.change_contract(lambda x:x['public_comparison'].update(policy_sha256=ref['sha256']))
        with self.assertRaises(ValueError):stage(self.f)
    def test_legacy_downgrade_rejected(self):
        self.change_contract(lambda x:x.update(schema='algsolve.campaign-contract.v1',comparison='unchanged'))
        with self.assertRaises(ValueError):stage(self.f)
    def test_fully_stripped_legacy_downgrade_rejected(self):
        def strip(contract):
            for name in ['public_comparison','independent_comparison','source_author']:contract.pop(name,None)
            contract.update(schema='algsolve.campaign-contract.v1',comparison='unchanged')
        self.change_contract(strip)
        with self.assertRaises(ValueError):stage(self.f)

    def test_missing_or_unknown_mode_rejected(self):
        for value in [None,'unchanged','return:unordered_distinct_int']:
            self.change_contract(lambda x:x.update(comparison=value))
            with self.subTest(value=value),self.assertRaises(ValueError):stage(self.f)
    def test_caller_statement_cannot_replace_pinned_packet(self):
        new=write(self.f['root']/'forged-packet.json',{'statement':'Return the answer in any order.'})
        self.change_contract(lambda x:x['public_comparison'].update(packet_sha256=c.file_ref(new)['sha256']))
        with self.assertRaises(ValueError):stage(self.f)
    def test_runtime_substitution_rejected(self):
        registry=json.loads(self.f['policy'].read_text());registry['entries'][self.f['entry']['key']]['runtime']['judge/declared_comparison.py']='0'*64;write(self.f['policy'],registry);ref=c.file_ref(self.f['policy']);self.f['data']['inputs']['public_comparison_policy']=ref;self.change_contract(lambda x:x['public_comparison'].update(policy_sha256=ref['sha256']))
        with self.assertRaises(ValueError):stage(self.f)
    def test_policy_mutation_after_stage_rejected(self):
        self.ready();self.f['policy'].write_text('{}')
        with self.assertRaises(ValueError):record(self.f,self.receipts)
    def test_count_only_evidence_rejected(self):
        self.ready();del self.receipts['execution']['semantic_qualification']
        with self.assertRaises((ValueError,TypeError)):record(self.f,self.receipts)
    def test_public_expected_rewrite_rejected(self):
        self.ready();self.mutate_artifact('host_tests',lambda groups:groups[0]['effective_tests'][2].update(expected=['wrong']))
        with self.assertRaises(ValueError):record(self.f,self.receipts)
    def test_independent_comparison_change_rejected(self):
        self.ready();self.mutate_artifact('host_tests',lambda groups:groups[1]['effective_tests'][0].update(compare='return:unordered_outer'))
        with self.assertRaises(ValueError):record(self.f,self.receipts)
    def test_independent_subset_rejected(self):
        self.ready();self.mutate_artifact('host_tests',lambda groups:groups[1]['raw_tests'].pop())
        with self.assertRaises(ValueError):record(self.f,self.receipts)
    def test_independent_metadata_change_rejected(self):
        self.change_contract(lambda x:x.update(independent_sets=[]))
        with self.assertRaises(ValueError):stage(self.f)
    def test_public_statement_without_declaration_rejected(self):
        packet=self.f['work']/'0599-packet.json';value=json.loads(packet.read_text());value['statement']='Return the answer in sorted order.';write(packet,value)
        registry=json.loads(self.f['policy'].read_text());registry['entries'][self.f['entry']['key']]['packet']=c.file_ref(packet);write(self.f['policy'],registry);self.f['data']['inputs']['public_comparison_policy']=c.file_ref(self.f['policy'])
        with self.assertRaises(ValueError):stage(self.f)
    def test_review_missing_comparison_or_self_review_rejected(self):
        self.ready()
        for changes in [{'public_comparison_reviewed':False},{'public_comparison_sha256':'0'*64},{'reviewer':'/root/review_standard'}]:
            old=copy.deepcopy(self.receipts['review']);self.receipts['review'].update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):record(self.f,self.receipts)
            self.receipts['review']=old
    def test_strict_failure_cannot_be_relabelled_success(self):
        self.ready();self.receipts['execution']['strict_public_passed']=3
        with self.assertRaises(ValueError):record(self.f,self.receipts)
    def test_bad_transcripts_rejected_before_judge(self):
        self.ready();q=json.loads(Path(self.receipts['execution']['semantic_qualification']['path']).read_text());chunk=q['results'][1]['chunks'][0];cases=json.loads(Path(self.receipts['execution']['host_tests']['path']).read_text())[0]['raw_tests'];payload=chunk['result']
        bad=[]
        for field,value in [('exit_code',None),('exit_code',True),('signal',9),('timed_out',True),('wall_seconds',float('nan')),('wall_seconds',9),('output_limit_exceeded',True)]:
            v=copy.deepcopy(payload);v[field]=value;bad.append(v)
        for change in ['duplicate','missing','bool-index','bool-done','mutation','alias','wrong-call']:
            v=copy.deepcopy(payload);rows=[json.loads(x) for x in v['stdout'].splitlines()]
            if change=='duplicate':rows[1]=copy.deepcopy(rows[0])
            elif change=='missing':rows.pop(0)
            elif change=='bool-index':rows[0]['i']=False
            elif change=='bool-done':rows[-1]['done']=True
            elif change=='mutation':rows[0]['args_after']=[]
            elif change=='alias':rows[0]['returned_input_ids']=[0]
            elif change=='wrong-call':rows[0]['args_before']=[]
            v['stdout']='\n'.join(json.dumps(x) for x in rows)+'\n';bad.append(v)
        for i,v in enumerate(bad):
            with self.subTest(case=i),self.assertRaises(ValueError):p.sandbox_result(v,cases)
    def test_forged_success_observation_rejected(self):
        self.ready()
        def wrong(q):
            chunk=q['results'][1]['chunks'][0];rows=[json.loads(x) for x in chunk['result']['stdout'].splitlines()];rows[2]['result']=['happy','happy'];chunk['result']['stdout']='\n'.join(json.dumps(x) for x in rows)+'\n'
        self.mutate_artifact('semantic_qualification',wrong)
        with self.assertRaises(ValueError):record(self.f,self.receipts)
    def test_missing_chunk_rejected(self):
        self.ready();self.mutate_artifact('semantic_qualification',lambda q:q['results'][1]['chunks'].pop())
        with self.assertRaises(ValueError):record(self.f,self.receipts)

if __name__=='__main__':unittest.main(verbosity=2)
