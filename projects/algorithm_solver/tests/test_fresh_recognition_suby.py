"""Synthetic fresh-harness boundary checks, not fresh recognition results."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from algsolve.fresh_recognition_suby import public_request,verify_review_seal,retrieval_evidence


class FreshRecognitionBoundaries(unittest.TestCase):
    def case(self):return {'id':'independent_fixture','kind':'complete_description','query':'Count items.',
                          'public_examples':[{'args':[[1,2]],'expected':2}]}

    def test_only_initial_public_fields_become_problem(self):
        case=self.case();p=public_request(case)
        self.assertEqual(p.statement,case['query'])
        self.assertEqual(p.public_tests,[dict(e,compare='return:exact') for e in case['public_examples']])
        self.assertNotIn('compare',case['public_examples'][0])
        self.assertFalse(p.entry);self.assertFalse(p.params);self.assertFalse(p.slug)
        for forbidden in ('expected_key','private_checks','oracle_signature','requirements'):
            with self.subTest(field=forbidden):
                with self.assertRaises(ValueError):public_request(dict(case,**{forbidden:'forbidden'}))

    def test_missing_examples_bad_ids_and_kinds_reject_before_route(self):
        for changes in ({'public_examples':[]},{'id':'../escape'},{'kind':'invented'}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):public_request(dict(self.case(),**changes))

    def test_filter_abstention_does_not_hide_executed_retrieval(self):
        result={'decision':'abstain','requirement_filter':{'raw_retrieval':[{'key':'target'}]},'match':{'candidates':[]}}
        evidence=retrieval_evidence(result,'target')
        self.assertTrue(evidence['retrieval_executed']);self.assertTrue(evidence['top_five'])
        self.assertFalse(evidence['post_filter_top_five'])
        self.assertFalse(retrieval_evidence({},None)['retrieval_executed'])

    def test_review_identities_and_all_hashes_bound_without_parsing_cases(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);files=('public.json','private.json','dispositions.json','authored.json');catalogs=('author_catalog.json','reviewer_sources.json')
            for name in files+catalogs:(root/name).write_text('not parsed by metadata verifier')
            digest=lambda name:hashlib.sha256((root/name).read_bytes()).hexdigest()
            seal={'author_agent':'isolated-A','reviewer_agent':'isolated-B',
                  'files_sha256':{n:digest(n) for n in files},'catalog_sha256':{n:digest(n) for n in catalogs}}
            (root/'seal.json').write_text(json.dumps(seal));self.assertEqual(verify_review_seal(root),seal)
            seal['reviewer_agent']='isolated-A';(root/'seal.json').write_text(json.dumps(seal))
            with self.assertRaises(ValueError):verify_review_seal(root)
            seal['reviewer_agent']='isolated-B';(root/'seal.json').write_text(json.dumps(seal));(root/'private.json').write_text('changed')
            with self.assertRaises(ValueError):verify_review_seal(root)

if __name__=='__main__':unittest.main()
