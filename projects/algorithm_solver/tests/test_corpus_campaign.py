import copy, json, tempfile, unittest
from pathlib import Path
from algsolve import corpus_campaign as c

class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.original=self.write('original','return 1');self.normalized=self.write('normalized','return 1\n');self.standard=self.write('standard','standard')
        self.entry={'id':1,'key':'lc:fixture','family':'fixture','language':'python','source':dict(c.file_ref(self.original),kind='file'),'baseline':{'qualified':True},'independent_sets':[{'uid':'fixture','tests':2,'sha256':'a'*64,'path':'not-opened.json'}],'reservation':None,'status':'pending','normalized':None,'claim':None,'attempts':[],'receipts':[],'blockers':[],'revision':0}
        self.data={'schema':c.SCHEMA,'revision':0,'entries':{'0001:python':self.entry},'events':[]}
    def write(self,name,value):
        p=self.root/name;p.write_text(value if isinstance(value,str) else json.dumps(value));return p
    def start(self):
        self.token=c.claim(self.data,'0001:python','worker')['token']
        contract={'schema':'algsolve.campaign-contract.v1','entry':'0001:python','source_sha256':self.entry['source']['sha256'],'normalized_sha256':c.file_ref(self.normalized)['sha256'],'independent_sets':self.entry['independent_sets'],'comparison':'unchanged','interface':'exact-public-adapter','public_tests':1,'mutation_contract':'unchanged','alias_contract':'no new alias'}
        self.contract=self.write('contract',contract)
        return c.stage(self.data,'0001:python','worker',self.token,self.normalized,self.contract,self.standard,self.root)
    def evidence(self):
        a=self.entry['attempts'][-1];artifact=self.write('observation','independent verifier output fixture')
        common={'schema':'algsolve.campaign-evidence.v1','entry':'0001:python','source_sha256':a['source_sha256'],'normalized_sha256':a['normalized']['sha256'],'contract_sha256':a['contract']['sha256'],'status':'passed','artifacts':[c.file_ref(artifact)]}
        values={'standard':dict(standard_sha256=a['standard']['sha256'],errors=[],idempotent=True),'execution':dict(independent_sets=self.entry['independent_sets'],independent_total=2,independent_passed=2,public_total=1,public_passed=1,mutation_passed=True,alias_passed=True,sandboxed=True,infrastructure_errors=0,expected_outputs_in_sandbox=False),'review':dict(reviewer='independent-reviewer',semantic_role_mapping_reviewed=True,complexity_reviewed=True,unresolved=[])}
        self.receipts={k:dict(common,kind=k,**v) for k,v in values.items()}
        return self.bundle()
    def bundle(self):
        return self.write('bundle',{k:c.file_ref(self.write(k+'.json',v)) for k,v in self.receipts.items()})
    def complete(self,bundle):c.record(self.data,'0001:python','worker',self.token,bundle,self.root)
    def test_success_baseline_distinct_and_artifacts_frozen(self):
        self.assertEqual(c.summary(self.data)['normalized_complete'],{});self.start();self.complete(self.evidence())
        self.assertEqual(self.entry['status'],'complete');self.assertEqual(len(self.entry['receipts']),3)
        self.normalized.write_text('mutated original path');c.verify(self.entry['normalized'])
    def test_pending_and_alias_reservations_cannot_be_claimed(self):
        for state in ('awaiting_delivery','alias_reserved'):
            self.entry['reservation']={'state':state}
            with self.assertRaises(ValueError):c.claim(self.data,'0001:python','worker',True)
    def test_delivered_requires_explicit_reconciliation(self):
        self.entry['reservation']={'state':'delivered_reconciliation'}
        with self.assertRaises(ValueError):c.claim(self.data,'0001:python','worker')
        c.claim(self.data,'0001:python','worker',True)
    def test_source_drift_is_refused(self):
        self.original.write_text('changed')
        with self.assertRaises(ValueError):c.claim(self.data,'0001:python','worker')
    def test_stale_revision_and_owner_are_refused(self):
        path=self.write('ledger',self.data)
        with c.transaction(path,0) as data:c.claim(data,'0001:python','worker')
        with self.assertRaises(ValueError):
            with c.transaction(path,0):pass
        self.start()
        with self.assertRaises(ValueError):c.release(self.data,'0001:python','other',self.token,'no')
    def test_family_claim_blocks_other_owner(self):
        other=copy.deepcopy(self.entry);other['language']='javascript';self.data['entries']['0001:javascript']=other
        c.claim(self.data,'0001:python','worker')
        with self.assertRaises(ValueError):c.claim(self.data,'0001:javascript','other')
    def test_missing_or_stale_evidence_cannot_complete(self):
        self.start();bundle=self.evidence();self.write('observation','tampered')
        with self.assertRaises(ValueError):self.complete(bundle)
        self.assertEqual(self.entry['status'],'staged')
    def test_subset_domain_or_failed_checks_cannot_complete(self):
        self.start();self.evidence()
        for kind,field,value in [('execution','independent_passed',1),('execution','public_passed',0),('execution','mutation_passed',False),('standard','idempotent',False),('review','reviewer','worker')]:
            before=copy.deepcopy(self.receipts);self.receipts[kind][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.complete(self.bundle())
            self.receipts=before
    def test_release_preserves_abandoned_attempt(self):
        self.start();c.release(self.data,'0001:python','worker',self.token,'needs review',True)
        self.assertEqual(self.entry['status'],'blocked');self.assertEqual(self.entry['attempts'][0]['status'],'abandoned')
        self.assertEqual(self.entry['blockers'],['needs review'])
    def test_failed_attempt_retains_evidence(self):
        self.start();failure=self.write('failure',{'status':'timeout'})
        c.fail(self.data,'0001:python','worker',self.token,failure,'sandbox timeout',self.root)
        self.assertEqual(self.entry['status'],'blocked')
        self.assertEqual(self.entry['attempts'][0]['status'],'failed')
        c.verify(self.entry['attempts'][0]['failure_evidence'])
    def test_transaction_exception_does_not_commit(self):
        path=self.write('ledger',self.data)
        with self.assertRaises(ValueError):
            with c.transaction(path,0) as data:
                c.claim(data,'0001:python','worker')
                raise ValueError('abort')
        self.assertEqual(json.loads(path.read_text()),self.data)
    def test_weakened_frozen_set_cannot_stage(self):
        self.start();c.release(self.data,'0001:python','worker',self.token,'retry')
        self.token=c.claim(self.data,'0001:python','worker')['token']
        contract=json.loads(self.contract.read_text());contract['independent_sets']=[]
        self.contract.write_text(json.dumps(contract))
        with self.assertRaises(ValueError):c.stage(self.data,'0001:python','worker',self.token,self.normalized,self.contract,self.standard,self.root)
    def test_full_frozen_census_counts(self):
        p=Path(__file__).parent/'ledger.json'
        if not p.exists():self.skipTest('Private census not supplied')
        d=json.loads(p.read_text());s=c.summary(d)
        self.assertEqual(s['eligible_problems'],2354);self.assertEqual(s['entries'],4708)
        self.assertEqual(s['baseline_qualified'],{'python':2354,'javascript':94})
        self.assertEqual(sum(e['language']=='javascript' and e['source'] is None for e in d['entries'].values()),2099)
        self.assertEqual(sum(e['reservation'] is not None and e['reservation']['state']=='awaiting_delivery' for e in d['entries'].values()),200)
if __name__=='__main__':unittest.main()
