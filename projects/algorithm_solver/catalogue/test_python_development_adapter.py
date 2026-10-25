import copy
import hashlib
import json
import unittest
from .python_development_adapter import adapt_development

class PendingPythonImport(unittest.TestCase):
    def fixture(self):
        raw=json.dumps({'rows':[{'id':i}for i in range(400)]}).encode()
        transfer={'filtered_metadata_sha256':hashlib.sha256(raw).hexdigest(),'partition':{'dev_fit':list(range(300)),'dev_val':list(range(300,400))},'final_heldout_payload_files_opened':0,'protected_payload_files_opened':0}
        rows=[]
        for i in range(400):
            eligible=i<372
            rows.append({'id':i,'partition':'dev_fit'if i<300 else'dev_val','current_dot_qualification':eligible,'reference_compatibility_only':372<=i<388,'authored_source_sha256':'a'*64,'canonical_proposal':{'source_sha256':'b'*64,'report_sha256':'c'*64,'entry_point':'solve','evidence_class':'finite-independent-frozen-replay'}if eligible else None})
        rec={'schema':'gamma.python.catalogue-metadata-reconciliation.v1','case_payload_reads':0,'protected_payload_reads':0,'rows':rows}
        return rec,transfer,raw
    def test_pending_not_promoted_and_denominator_fixed(self):
        u,c,s=adapt_development(*self.fixture())
        self.assertEqual(len(u['eligible_problem_ids']),400)
        self.assertEqual(s['authored_pending'],372);self.assertEqual(s['blocked'],28)
        self.assertEqual(s['compatibility_only'],16);self.assertEqual(s['qualified'],0)
        self.assertFalse(s['validation']['complete_dual_language_catalogue'])
        self.assertNotIn('problem_contract_sha256',c['problems'][0]['implementations']['python'])
    def test_missing_identity_fails(self):
        a=list(self.fixture());a[0]['rows'].pop()
        with self.assertRaises(ValueError):adapt_development(*a)
    def test_compatibility_not_promoted(self):
        a=list(self.fixture());a[0]['rows'][0]['reference_compatibility_only']=True
        with self.assertRaises(ValueError):adapt_development(*a)
    def test_forged_metadata_hash_fails(self):
        a=list(self.fixture());a[1]['filtered_metadata_sha256']='d'*64
        with self.assertRaises(ValueError):adapt_development(*a)
    def test_protected_payload_open_fails(self):
        a=list(self.fixture());a[1]['protected_payload_files_opened']=1
        with self.assertRaises(ValueError):adapt_development(*a)
    def test_noncanonical_declared_entry_fails(self):
        a=list(self.fixture());a[0]['rows'][0]['canonical_proposal']['entry_point']='Solution.method'
        with self.assertRaises(ValueError):adapt_development(*a)
    def test_partition_swap_fails(self):
        a=list(self.fixture());a[0]['rows'][0]['partition']='dev_val'
        with self.assertRaises(ValueError):adapt_development(*a)

if __name__=='__main__':unittest.main()
