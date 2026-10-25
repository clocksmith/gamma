import copy,importlib.util,unittest
from pathlib import Path
from projects.algorithm_solver.catalogue.catalogue import digest,validate
SPEC=importlib.util.spec_from_file_location('authorship_metadata',Path(__file__).with_name('patch.py'));p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)

def fixture():
    ids=['leetcode:1','leetcode:1743','leetcode:1788','leetcode:2792','leetcode:99']
    u={'schema':'gamma.catalogue-universe.v1','eligible_problem_ids':ids,'protected_problem_ids':['leetcode:99'],'metadata_sha256':'a'*64,'eligibility_policy':'Synthetic fixed population independent of availability'}
    receipts={};rows=[]
    for pid in ids:
        impls={}
        for lang in ('javascript','python'):
            if pid=='leetcode:1'or(pid=='leetcode:1743'and lang=='python'):
                interface={'schema':'gamma.call-interface.v1','entrypoint':'solve','arguments':'ordered-positional','typed_contract':'b'*64}
                impl=dict.fromkeys(('source_sha256','problem_contract_sha256','runtime_sha256','tests_sha256','effects_sha256'),'b'*64)
                impl.update(interface=interface,interface_sha256=digest(interface),status='qualified',canonical_variant_id=pid+lang,provenance={'synthetic':True})
                receipt={k:impl[k]for k in p.BINDINGS};receipt.update(canonical_variant_id=impl['canonical_variant_id'],provenance_sha256=digest(impl['provenance']),problem_id=pid,language=lang,verdict='qualified',evidence_class='normative-typed-effects',independent_verifier=True)
                rid=digest(receipt);receipts[rid]=receipt;impl['receipt_sha256']=rid
            elif pid=='leetcode:99':impl={'status':'protected','reason':'Synthetic reserved boundary'}
            elif pid=='leetcode:1788':impl={'status':'blocked','reason':'Synthetic unavailable official contract','provenance':{'existing':'preserve'}}
            elif pid=='leetcode:1743':impl={'status':'authored','reason':'Synthetic retained64MiB heap failure','source_sha256':'f'*64,'provenance':{'failure_evidence':['synthetic OOM original and repair']}}
            else:impl={'status':'authored','reason':'Synthetic owner source; contract unresolved','provenance':{}}
            impls[lang]=impl
        rows.append({'problem_id':pid,'implementations':impls})
    c={'schema':'gamma.dual-language-catalogue.v1','universe_sha256':digest(u),'problems':rows};items=[]
    for pid in ids[:-1]:
        for lang in ('javascript','python'):
            items.append({'problem_id':pid,'language':lang,'owner_commit':'c'*40,'git_blob_object_id':'d'*40,'git_object_hash_algorithm':'sha1','repository_path':f'projects/algorithm_solver/catalogue/authored/synthetic/{lang}/{pid.split(":")[1]}.{"js"if lang=="javascript"else"py"}','source_sha256_known_from_this_inventory':False})
    patch={'schema':'gamma.existing-catalogue-authorship-patch.v1','qualification_created':False,'source_publication_authorized':False,'candidate_executions':0,'source_payload_reads':0,'statement_payload_reads':0,'population':len(ids),'language_slots':2*len(ids),'owner_commit':'c'*40,'metadata_inventory':items,'declared_blocked':{'leetcode:1788':'Synthetic explicit contract block'},'current_review_counts':{'qualified_preserved':999}}
    validate(u,c,receipts);return u,c,receipts,patch

class PatchTests(unittest.TestCase):
    def apply(self,*args,**kwargs):return p.apply_inventory(*args,'e'*64,authorize=kwargs.get('authorize',lambda *_:None))
    def test_live_counts_not_stale_patch_counts(self):
        out,audit=self.apply(*fixture());self.assertEqual(audit['qualified_inventory_slots_preserved'],3);self.assertEqual(audit['changed_slot_count'],5)
        self.assertEqual(audit['before']['qualified_by_evidence_class'],audit['after']['qualified_by_evidence_class'])
    def test_inputs_receipts_qualified_and_other_slots_preserved(self):
        args=fixture();original=copy.deepcopy(args);out,audit=self.apply(*args)
        self.assertEqual(args,original)
        for old,new in zip(args[1]['problems'],out['problems']):
            for lang,impl in old['implementations'].items():
                if impl['status']in('qualified','protected'):self.assertEqual(impl,new['implementations'][lang])
    def test_1743_failures_and_existing_hashes_preserved(self):
        u,c,receipts,patch=fixture();old=c['problems'][1]['implementations']['javascript'];out,_=self.apply(u,c,receipts,patch);new=out['problems'][1]['implementations']['javascript']
        self.assertEqual(new['reason'],old['reason']);self.assertEqual(new['source_sha256'],old['source_sha256']);self.assertEqual(new['provenance']['failure_evidence'],old['provenance']['failure_evidence']);self.assertNotIn('receipt_sha256',new)
    def test_idempotent_same_inventory(self):
        u,c,receipts,patch=fixture();one,_=self.apply(u,c,receipts,patch);two,audit=self.apply(u,one,receipts,patch)
        self.assertEqual(one,two);self.assertEqual(audit['changed_slot_count'],0);self.assertEqual(audit['already_applied_unqualified_slots'],5)
    def test_gate_denial_no_partial_mutation(self):
        args=fixture();before=copy.deepcopy(args);calls=[]
        def deny(pid,lang):
            calls.append((pid,lang))
            if len(calls)==4:raise PermissionError
        with self.assertRaises(PermissionError):self.apply(*args,authorize=deny)
        self.assertEqual(args,before)
    def test_duplicate_slot_rejected(self):
        args=list(fixture());args[-1]['metadata_inventory'].append(args[-1]['metadata_inventory'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'):self.apply(*args)
    def test_source_payload_metadata_rejected(self):
        args=list(fixture());args[-1]['metadata_inventory'][0]['source_utf8']='synthetic forbidden payload'
        with self.assertRaisesRegex(ValueError,'whitelisted'):self.apply(*args)
    def test_source_sha256_not_invented_from_git_sha1(self):
        args=list(fixture());args[-1]['metadata_inventory'][0]['source_sha256_known_from_this_inventory']=True
        with self.assertRaisesRegex(ValueError,'Git identity'):self.apply(*args)
    def test_path_identity_and_traversal_rejected(self):
        for path in ('/private/source.js','projects/algorithm_solver/catalogue/authored/../javascript/1.js','projects/algorithm_solver/catalogue/authored/x/javascript/2.js'):
            args=list(fixture());args[-1]['metadata_inventory'][0]['repository_path']=path
            with self.assertRaises(ValueError):self.apply(*args)
    def test_protected_cannot_be_marked_authored(self):
        args=list(fixture());x=copy.deepcopy(args[-1]['metadata_inventory'][0]);x['problem_id']='leetcode:99';x['repository_path']=x['repository_path'].replace('/1.js','/99.js');args[-1]['metadata_inventory'].append(x)
        with self.assertRaises(PermissionError):self.apply(*args)
    def test_conflicting_inventory_requires_new_review(self):
        u,c,receipts,patch=fixture();out,_=self.apply(u,c,receipts,patch);out['problems'][1]['implementations']['javascript']['provenance']['owner_git_metadata']['git_blob_object_id']='a'*40
        with self.assertRaisesRegex(ValueError,'conflicting'):self.apply(u,out,receipts,patch)
    def test_denominator_cannot_change(self):
        args=list(fixture());args[-1]['population']=96
        with self.assertRaisesRegex(ValueError,'denominator'):self.apply(*args)
if __name__=='__main__':unittest.main()
