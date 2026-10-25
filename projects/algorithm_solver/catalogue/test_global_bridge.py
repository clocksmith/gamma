import hashlib
import json
import unittest
from . import test_evidence_policy
from .catalogue import digest
from .global_bridge import import_global


class GlobalBridge(unittest.TestCase):
    def fixture(self):
        u,c,r=test_evidence_policy.EvidencePolicy().fixture()
        u['eligible_problem_ids']=['development400:1','development400:2']
        new_receipts={}
        for pid,row in zip(u['eligible_problem_ids'],c['problems']):
            row['problem_id']=pid
            for impl in row['implementations'].values():
                receipt=dict(r[impl['receipt_sha256']]);receipt['problem_id']=pid;rid=digest(receipt);impl['receipt_sha256']=rid;new_receipts[rid]=receipt
        c['universe_sha256']=digest(u)
        global_u={'schema':'gamma.catalogue-universe.v1','eligible_problem_ids':['leetcode:1','leetcode:2','leetcode:3','leetcode:4'],'protected_problem_ids':['leetcode:4'],'metadata_sha256':'a'*64,'eligibility_policy':'independent synthetic complete universe'}
        encode=lambda o:json.dumps(o,sort_keys=True).encode();raw_u=encode(u);raw_g=encode(global_u);sha=lambda b:hashlib.sha256(b).hexdigest()
        aliases={'schema':'gamma.numeric-id-alias-map.v1','source_payload_reads':0,'case_payload_reads':0,'from_universe_sha256':sha(raw_u),'to_universe_sha256':sha(raw_g),'aliases':dict(zip(u['eligible_problem_ids'],global_u['eligible_problem_ids'][:2]))}
        policy={'schema':'gamma.all4081-source-access-policy.v1','authorized_existing_source_problem_ids':['leetcode:1','leetcode:2'],'new_source_access_authorized':False,'source_publication_authorized':False,'population_size':4,'language_slots':8,'outside_authorized_count':2}
        raw_a,raw_p=encode(aliases),encode(policy)
        anchors={k:sha(v)for k,v in [('development_universe',raw_u),('global_universe',raw_g),('aliases',raw_a),('access_policy',raw_p)]}
        return [raw_u,c,new_receipts,raw_g,raw_a,raw_p,anchors]

    def test_full_denominator_and_exact_receipt_rebinding(self):
        c,r,s=import_global(*self.fixture());self.assertEqual(s['eligible_problems'],4);self.assertFalse(s['complete_dual_language_catalogue']);self.assertEqual(s['language_counts']['python']['qualified'],2)
        rows={row['problem_id']:row for row in c['problems']};self.assertEqual(rows['leetcode:3']['implementations']['python']['status'],'blocked');self.assertEqual(rows['leetcode:4']['implementations']['python']['status'],'protected')
        receipt=r[rows['leetcode:1']['implementations']['python']['receipt_sha256']];self.assertTrue(receipt['identity_rebinding_only']);self.assertEqual(receipt['problem_id'],'leetcode:1')

    def test_tampered_alias_bytes_rejected(self):
        args=self.fixture();args[4]+=b' '
        with self.assertRaises(ValueError):import_global(*args)

    def test_numeric_identity_cannot_redirect(self):
        args=self.fixture();a=json.loads(args[4]);a['aliases']={'development400:1':'leetcode:2','development400:2':'leetcode:1'};args[4]=json.dumps(a).encode();args[6]['aliases']=hashlib.sha256(args[4]).hexdigest()
        with self.assertRaises(ValueError):import_global(*args)

    def test_source_authority_cannot_expand(self):
        args=self.fixture();p=json.loads(args[5]);p['new_source_access_authorized']=True;args[5]=json.dumps(p).encode();args[6]['access_policy']=hashlib.sha256(args[5]).hexdigest()
        with self.assertRaises(ValueError):import_global(*args)

if __name__=='__main__':unittest.main()
