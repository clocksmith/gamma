"""Software boundary tests, separate from the real reconstruction measurement."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from algsolve.rebuild_download import verify
from algsolve.rebuild_recognition import boundary, exclusion, prepare, bound_receipt


class ReconstructionBoundaries(unittest.TestCase):
    def test_transitive_recorded_alias_families_and_uids_are_excluded(self):
        limits=boundary({'excluded':{'lc:alias-ii':'protected_composition_alias'}},
            {'reservation':{'pool':[{'key':'lc:reserved','family':'reserved','members':['lcd:9'],'judge_uid':'lcd:10'}]}})
        for row in ({'task_id':'alias','question_id':1},{'task_id':'reserved-iii','question_id':2},
                    {'task_id':'other','question_id':9},{'task_id':'other','question_id':10}):
            self.assertIsNotNone(exclusion(row,limits))
        self.assertIsNone(exclusion({'task_id':'permitted','question_id':11},limits))

    def test_protected_and_unselected_payloads_never_reach_signature_or_test_parser(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); asset=root/'asset'; out=root/'out'; asset.mkdir(); out.mkdir()
            # No statement, starter, completion or tests: touching any such
            # field before metadata exclusion would raise KeyError.
            rows=[{'task_id':'blocked','question_id':1},{'task_id':'unselected','question_id':2}]
            (asset/'LeetCodeDataset-train.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            result=prepare(asset,out,{'lc:blocked'},{'lc:blocked'},
                {'keys':['lc:blocked'],'families':[],'uids':[]},{'lc:blocked','lc:unselected'})
            self.assertEqual(result['indexed_entries'],0)
            self.assertEqual(result['missing_targets'],['lc:blocked'])
            self.assertEqual(json.loads((out/'entries.json').read_text()),[])

    def test_receipt_resumes_without_repeating_work_and_rejects_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'receipt.json'; binding={'candidate':'fixture'}; calls=[]
            def make(): calls.append(1); return {'answer':'fixture'}
            self.assertEqual(bound_receipt(path,binding,make),{'answer':'fixture'})
            self.assertEqual(bound_receipt(path,binding,make),{'answer':'fixture'})
            self.assertEqual(calls,[1])
            with self.assertRaises(ValueError): bound_receipt(path,{'candidate':'changed'},make)
            row=json.loads(path.read_text()); row['value']['answer']='tampered'; path.write_text(json.dumps(row))
            with self.assertRaises(ValueError): bound_receipt(path,binding,make)

    def test_payload_size_and_both_hash_kinds_are_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'fixture'; path.write_bytes(b'fixture')
            sha=hashlib.sha256(b'fixture').hexdigest()
            self.assertEqual(verify(path,(7,'sha256',sha))['sha256'],sha)
            blob=hashlib.sha1(b'blob 7\0fixture').hexdigest()
            self.assertEqual(verify(path,(7,'git-blob-sha1',blob))['sha256'],sha)
            for spec in ((8,'sha256',sha),(7,'sha256','wrong')):
                with self.assertRaises(ValueError): verify(path,spec)


if __name__=='__main__': unittest.main()
