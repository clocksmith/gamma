import copy,importlib.util,sys,unittest
from pathlib import Path
HERE=Path(__file__).parent;sys.path.insert(0,str(HERE))
from test_patch import fixture,p
SPEC=importlib.util.spec_from_file_location('contract_blocker',HERE/'blockers.py');b=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(b)

def inputs():
    u,c,r,inventory=fixture();c,_=p.apply_inventory(u,c,r,inventory,'e'*64,authorize=lambda *_:None)
    patch={'schema':'gamma.catalogue-contract-blocker-patch.v1','problem_ids':['leetcode:2792'],'languages':['javascript','python'],'predecessor_inventory_patch_sha256':'e'*64,'reason':'Synthetic official contract unavailable; owner Git availability retained.','authority_review':{'sha256':'a'*64},'worklist':{'sha256':'b'*64},'authority_freeze':{'sha256':'c'*64},'qualification_created':False,'source_publication_authorized':False,'source_payload_reads':0,'statement_payload_reads':0,'candidate_executions':0}
    return u,c,r,patch

class BlockerTests(unittest.TestCase):
    def apply(self,args,authorize=lambda *_:None):return b.correct(*args,'d'*64,authorize=authorize)
    def test_exact_two_slots_with_all_provenance_preserved(self):
        args=inputs();before=copy.deepcopy(args);out,audit=self.apply(args)
        self.assertEqual(args,before);self.assertEqual(audit['changed_slot_count'],2)
        for old,new in zip(args[1]['problems'],out['problems']):
            for lang,slot in old['implementations'].items():
                updated=new['implementations'][lang]
                if old['problem_id']=='leetcode:2792':
                    self.assertEqual(updated['status'],'blocked');self.assertEqual(updated['provenance']['owner_git_metadata'],slot['provenance']['owner_git_metadata'])
                    self.assertEqual(updated['provenance']['contract_availability_blocker']['previous_reason'],slot['reason'])
                else:self.assertEqual(updated,slot)
        self.assertEqual(audit['before']['qualified_by_evidence_class'],audit['after']['qualified_by_evidence_class'])
    def test_1743_failure_and_1788_block_remain_exact(self):
        args=inputs();out,_=self.apply(args)
        for pid in ('leetcode:1743','leetcode:1788'):
            self.assertEqual(next(x for x in out['problems']if x['problem_id']==pid),next(x for x in args[1]['problems']if x['problem_id']==pid))
    def test_qualified_slot_cannot_be_demoted(self):
        args=list(inputs());args[-1]['problem_ids']=['leetcode:1']
        with self.assertRaisesRegex(ValueError,'qualified'):self.apply(args)
    def test_live_denial_preserves_input(self):
        args=inputs();before=copy.deepcopy(args)
        def deny(*_):raise PermissionError
        with self.assertRaises(PermissionError):self.apply(args,authorize=deny)
        self.assertEqual(args,before)
    def test_requires_old_inventory_linkage(self):
        args=list(inputs());args[-1]['predecessor_inventory_patch_sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'Git provenance'):self.apply(args)
    def test_idempotent_exact_blocker(self):
        u,c,r,patch=inputs();one,_=self.apply((u,c,r,patch));two,audit=self.apply((u,one,r,patch));self.assertEqual(one,two);self.assertEqual(audit['changed_slot_count'],0)
    def test_review_and_worklist_consistency(self):
        patch=inputs()[-1];review={'independent_review':True,'blocked_ids':[2792],'ids':[2709],'freeze_sha256':'c'*64};worklist={'blocked_ids':{'2792':'locked'},'wave_ids':[2709],'previous_blocked_ids':{'1788':'locked'}}
        b.validate_authority(patch,review,worklist)
        for bad in (dict(review,independent_review=False),dict(review,ids=[2792]),dict(review,freeze_sha256='a'*64)):
            with self.assertRaises(ValueError):b.validate_authority(patch,bad,worklist)
    def test_no_payload_claims(self):
        patch=inputs()[-1];patch['source_payload_reads']=1
        review={'independent_review':True,'blocked_ids':[2792],'ids':[],'freeze_sha256':'c'*64};worklist={'blocked_ids':{'2792':'locked'},'wave_ids':[],'previous_blocked_ids':{'1788':'locked'}}
        with self.assertRaisesRegex(ValueError,'metadata-only'):b.validate_authority(patch,review,worklist)
if __name__=='__main__':unittest.main()
