import copy
from types import SimpleNamespace
import unittest

from . import recognition_inventory as r


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.boundary = SimpleNamespace(authorized={'leetcode:1', 'leetcode:2'}, protected={'leetcode:3'},
            unknown={'leetcode:4'}, policy_sha256='a'*64, universe_sha256='b'*64, proof_sha256='c'*64)
        self.metadata = {'rows': [{'global_problem_id': f'leetcode:{i}', 'title': f'Title {i}',
            'source_availability': 'unverified'} for i in range(1, 5)]}
        self.aliases = {f'lc:title-{i}': [f'leetcode:{i}'] for i in range(1, 5)}
        self.execution = {key: 'same' for key in r.EXECUTION_FIELDS}
        self.execution.update({key: 'a'*64 for key in r.EXECUTION_FIELDS if key.endswith('_sha256')})
        self.execution.update(threads=2, interop_threads=1, batch_size=4, max_tokens=1024, dimension=1024,
                              document_instruction='')
        self.descriptions = [{'problem_id': f'leetcode:{i}', 'document_sha256': r.text_hash(f'Title {i}'),
                              'knowledge_class': 'title-only', 'provenance': {'title': 'a'*64}}
                             for i in range(1, 5)]
        self.vectors = [{'problem_id': d['problem_id'], 'document_sha256': d['document_sha256'],
                         'execution_sha256': r.execution_identity(self.execution), 'validated': True,
                         'binding_verified': True, 'vector_file_sha256': 'b'*64, 'row': i}
                        for i, d in enumerate(self.descriptions)]

    def build(self):
        return r.inventory(self.metadata, self.boundary, self.aliases, metadata_sha256='a'*64,
                           description_records=self.descriptions, vector_records=self.vectors)

    def plan(self, current=None, prior=None, baseline_execution='same'):
        return r.incremental_plan(current or self.build(), prior or self.build(), execution=self.execution,
            baseline_execution=self.execution if baseline_execution == 'same' else baseline_execution,
            baseline_id='separately-identified-development-baseline')

    def test_recount_not_historical_constant(self):
        counts = self.build()['counts']
        self.assertEqual(counts['authorized'], 2)
        self.assertEqual(counts['reserved'], 1)
        self.assertEqual(counts['unresolved'], 1)
        self.assertEqual(counts['authorized_missing_descriptions'], 2)

    def test_exact_document_execution_reuses_all_frozen_competitors(self):
        p = self.plan()
        self.assertEqual(p['counts']['reuse_vectors'], 4)
        self.assertEqual(p['counts']['embed_vectors'], 0)
        self.assertFalse(p['requires_full_population_recalibration'])

    def test_changed_description_embeds_only_changed_eligible_row(self):
        old = self.build()
        self.descriptions[0]['document_sha256'] = 'f'*64
        self.descriptions[0]['knowledge_class'] = 'permitted-development-statement'
        p = self.plan(prior=old)
        self.assertEqual(p['counts']['changed'], 1)
        self.assertEqual(p['counts']['embed_vectors'], 1)
        self.assertEqual(p['counts']['reuse_vectors'], 3)
        self.assertTrue(p['requires_full_population_recalibration'])

    def test_dimension_is_not_execution_provenance(self):
        old = self.build()
        self.execution['pooling'] = 'different'
        p = self.plan(prior=old, baseline_execution={**self.execution, 'pooling': 'same'})
        self.assertEqual(p['counts']['reuse_vectors'], 0)
        self.assertEqual(p['counts']['blocked_vectors'], 2)
        self.assertEqual(p['counts']['embed_vectors'], 2)
        self.assertTrue(p['requires_full_population_recalibration'])

    def test_missing_historical_provenance_is_not_filled(self):
        p = self.plan(baseline_execution=None)
        self.assertIsNone(p['baseline_execution_sha256'])
        self.assertEqual(p['counts']['reuse_vectors'], 0)
        self.assertFalse(p['historical_provenance_invented'])
        self.assertTrue(p['requires_full_population_recalibration'])

    def test_false_vector_provenance_cannot_reuse(self):
        for field, value in [('document_sha256', 'f'*64), ('row', -1),
                             ('binding_verified', False), ('validated', False)]:
            with self.subTest(field=field):
                prior = self.build()
                prior['rows'][0]['existing_vector'][field] = value
                self.assertEqual(self.plan(prior=prior)['counts']['reuse_vectors'], 3)

    def test_statement_permission_not_source_availability(self):
        self.metadata['rows'][2]['source_availability'] = 'available'
        self.descriptions[2]['knowledge_class'] = 'permitted-development-statement'
        with self.assertRaises(PermissionError):
            self.build()

    def test_ambiguous_alias_is_reported_never_resolved_by_availability(self):
        self.aliases['lc:ambiguous'] = ['leetcode:1', 'leetcode:3']
        inv = self.build()
        self.assertEqual(inv['counts']['ambiguous_identities'], 2)
        with self.assertRaisesRegex(ValueError, 'duplicate/ambiguous'):
            self.plan(current=inv)

    def test_duplicates_reported_without_denominator_inflation(self):
        self.metadata['rows'].append(copy.deepcopy(self.metadata['rows'][0]))
        inv = self.build()
        self.assertEqual(inv['population'], 4)
        self.assertEqual(inv['metadata_rows'], 5)
        self.assertEqual(inv['counts']['duplicate_identities'], 1)
        with self.assertRaises(ValueError):
            self.plan(current=inv)

    def test_duplicate_enriched_rows_do_not_inflate_description_coverage(self):
        self.descriptions[0]['knowledge_class'] = 'permitted-development-statement'
        self.metadata['rows'].extend(copy.deepcopy([self.metadata['rows'][0]]) * 3)
        counts = self.build()['counts']
        self.assertEqual(counts['authorized_descriptions'], 1)
        self.assertEqual(counts['authorized_missing_descriptions'], 1)

    def test_unknown_description_hash_never_counts_as_verified_coverage(self):
        self.descriptions[0]['knowledge_class'] = 'permitted-development-statement'
        self.descriptions[0]['document_sha256'] = None
        self.assertEqual(self.build()['counts']['authorized_descriptions'], 0)

    def test_original_baseline_must_have_separate_identity(self):
        for baseline_id in (None, '', '  '):
            with self.assertRaisesRegex(ValueError, 'separately identified'):
                r.incremental_plan(self.build(), self.build(), execution=self.execution,
                    baseline_execution=None, baseline_id=baseline_id)

    def test_reranker_or_alias_change_does_not_request_document_rebuild(self):
        prior = self.build()
        self.aliases['lc:extra-reviewed-alias'] = ['leetcode:1']
        p = self.plan(prior=prior)
        self.assertNotEqual(p['inventory_sha256'], p['baseline_inventory_sha256'])
        self.assertEqual(p['counts']['reuse_vectors'], 4)
        self.assertEqual(p['counts']['embed_vectors'], 0)
        with self.assertRaisesRegex(ValueError, 'complete exact'):
            r.execution_identity({**self.execution, 'reranker': 'new'})

    def test_removed_identity_is_explicit(self):
        prior = self.build()
        self.metadata['rows'].pop()
        self.boundary.unknown = set()
        del self.aliases['lc:title-4']
        self.descriptions.pop(); self.vectors.pop()
        p = self.plan(prior=prior)
        self.assertEqual(p['removed_problem_ids'], ['leetcode:4'])
        self.assertEqual(p['counts']['removed'], 1)
        self.assertTrue(p['requires_full_population_recalibration'])


if __name__ == '__main__':
    unittest.main()
