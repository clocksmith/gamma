import unittest
from .recognition_search import recognize, attach_implementation, summarize_development, population_identity


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.ids = ['leetcode:1', 'leetcode:2', 'leetcode:3']
        self.document_hashes = ['a'*64, 'b'*64, 'c'*64]
        self.population_sha256 = population_identity(self.ids, self.document_hashes)
        self.policy = {'population_sha256': self.population_sha256, 'evidence_class': 'development-calibration',
                       'min_cosine': .7, 'min_margin': .1}

    def search(self, scores=(.95, .7, .1), **kwargs):
        return recognize(scores, self.ids, document_hashes=self.document_hashes,
                         population_sha256=self.population_sha256, policy=self.policy, **kwargs)

    def test_unavailable_best_identity_is_still_recognized_never_substituted(self):
        calls = []
        def lookup(pid):
            calls.append(pid)
            return {'problem_id': pid, 'status': 'abstain', 'reason': 'no_qualified_implementation'}
        result = attach_implementation(self.search(), lookup)
        self.assertEqual(result['problem_id'], 'leetcode:1')
        self.assertEqual(result['status'], 'recognized')
        self.assertEqual(calls, ['leetcode:1'])
        self.assertFalse(result['implementation_availability_used'])

    def test_lookup_cannot_replace_winner_with_qualified_neighbor(self):
        with self.assertRaisesRegex(ValueError, 'substituted'):
            attach_implementation(self.search(), lambda _: {'problem_id': 'leetcode:2'})

    def test_reserved_frozen_identity_competes_without_payload_access(self):
        result = self.search((.6, .7, .95))
        self.assertEqual(result['problem_id'], 'leetcode:3')
        self.assertEqual(result['searched_population'], 3)

    def test_tie_abstains_even_with_zero_minimum_margin(self):
        self.policy['min_margin'] = 0
        self.assertEqual(self.search((.9, .9, .2))['reason'], 'ambiguous_tie')

    def test_truncation_is_a_separate_abstention(self):
        self.assertEqual(self.search(query_truncated=True)['reason'], 'truncation')
        self.assertEqual(self.search(index_truncated=True)['reason'], 'truncation')

    def test_changed_competitors_require_population_bound_recalibration(self):
        self.policy['population_sha256'] = 'old-population'
        with self.assertRaisesRegex(ValueError, 'recalibration'):
            self.search()

    def test_missing_calibration_retains_ranking_but_never_accepts(self):
        ids, hashes = self.ids[:2], self.document_hashes[:2]
        result = recognize([.95, .1], ids, document_hashes=hashes,
                           population_sha256=population_identity(ids, hashes))
        self.assertEqual(result['reason'], 'population_not_calibrated')
        self.assertEqual(result['candidates'][0]['problem_id'], 'leetcode:1')

    def test_full_finite_mapping_required(self):
        for scores, ids in [([.8, float('nan')], self.ids[:2]), ([.8, .2], [self.ids[0]]*2), ([.8], self.ids[:2])]:
            with self.assertRaises(ValueError):
                recognize(scores, ids, document_hashes=self.document_hashes[:2], population_sha256='x')

    def test_actual_population_cannot_reuse_unchecked_calibration_hash(self):
        for ids, hashes in [(list(reversed(self.ids)), self.document_hashes),
                            (self.ids, ['d'*64, *self.document_hashes[1:]])]:
            with self.subTest(ids=ids, hashes=hashes):
                with self.assertRaisesRegex(ValueError, 'binding mismatch'):
                    recognize([.95, .7, .1], ids, document_hashes=hashes,
                              population_sha256=self.population_sha256, policy=self.policy)

    def test_population_requires_canonical_ids_and_known_description_hashes(self):
        for ids, hashes in [(['title-not-stable-id', *self.ids[1:]], self.document_hashes),
                            (self.ids, [None, *self.document_hashes[1:]])]:
            with self.assertRaises(ValueError):
                population_identity(ids, hashes)

    def test_matched_implementation_must_bind_exact_identity(self):
        with self.assertRaisesRegex(ValueError, 'omitted exact identity'):
            attach_implementation(self.search(), lambda _: {'status': 'matched', 'code': 'neighbor'})

    def test_recall_variant_ambiguity_and_implementation_are_separate(self):
        result = attach_implementation(self.search(), lambda pid: {'problem_id': pid, 'status': 'abstain'})
        rows = [{'kind': 'variant', 'expected_ids': ['leetcode:1'], 'recognition': result},
                {'kind': 'ambiguity', 'expected_ids': [], 'recognition': self.search((.9, .9, .1))}]
        report = summarize_development(rows)
        self.assertEqual(report['by_kind']['variant']['target_top1'], 1)
        self.assertEqual(report['by_kind']['variant']['implementation_available'], 0)
        self.assertEqual(report['by_kind']['ambiguity']['abstentions'], 1)
        self.assertFalse(report['confirmation_opened'])


if __name__ == '__main__':
    unittest.main()
