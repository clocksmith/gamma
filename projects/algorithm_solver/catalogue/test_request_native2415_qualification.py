"""Source-free fixed native request boundary and representation controls."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_native2415_qualification as owner


class NativeRequestTests(unittest.TestCase):
    def test_fixed_oracle_and_native_domain(self):
        self.assertEqual(owner.IDS, (2415,))
        self.assertEqual(q.file_hash(owner.oracle.__file__), owner.ORACLE_SHA256)
        owner.validate(2415, [{'__tree_node__': [0, 100000, 2]}])
        for pid, args in ((True, [{'__tree_node__': [1]}]), (2416, [{'__tree_node__': [1]}]),
                          (2415, [[1]]), (2415, [{'__tree_node__': [True]}]),
                          (2415, [{'__tree_node__': [1, 2]}]),
                          (2415, [{'__tree_node__': [1], 'extra': 0}])):
            with self.subTest(pid=pid, args=args), self.assertRaises(ValueError):
                owner.validate(pid, args)

    def test_projection_preserves_values_order_and_original_objects(self):
        semantic = [{'args': [[8, 2, 3]], 'compare': 'return', 'expected': [8, 3, 2]},
                    {'args': [[7]], 'compare': 'return', 'expected': [7]}]
        original = deepcopy(semantic)
        native = owner.project(semantic)
        self.assertEqual(native, [
            {'args': [{'__tree_node__': [8, 2, 3]}], 'compare': 'return', 'expected': {'__tree_node__': [8, 3, 2]}},
            {'args': [{'__tree_node__': [7]}], 'compare': 'return', 'expected': {'__tree_node__': [7]}}])
        native[0]['args'][0]['__tree_node__'][0] = 99
        native[0]['expected']['__tree_node__'][0] = 88
        self.assertEqual(semantic, original)

    def test_projection_rejects_shape_and_result_domain_drift(self):
        cases = [
            {'args': [[1]], 'compare': 'return', 'expected': [1], 'hidden': 1},
            {'args': [[1]], 'compare': 'custom', 'expected': [1]},
            {'args': [[1]], 'compare': 'return', 'expected': [1, 2, 3]},
            {'args': [[1]], 'compare': 'return', 'expected': [True]},
            {'args': [[1.0]], 'compare': 'return', 'expected': [1]},
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                owner.project([case])

    def test_batches_are_singletons_and_expected_values_stay_on_host(self):
        cases = owner.project([{'args': [[1]], 'compare': 'return', 'expected': [99999]}] * 3)
        rows = owner.native_batches(cases)
        self.assertEqual([(r['offset'], r['count']) for r in rows], [(0, 1), (1, 1), (2, 1)])
        for offset, batch in q.batches(cases, 1, True):
            raw = q.encoded(q.packet(batch, True))
            self.assertNotIn(b'99999', raw)
            self.assertTrue(q.decode(raw)['node_identity'])
            self.assertEqual(rows[offset]['packet_sha256'], q.sha(raw))

    def test_maximum_projection_obeys_unchanged_packet_bound(self):
        case = owner.project([{'args': [[100000] * 16383], 'compare': 'return', 'expected': [100000] * 16383}])
        row = owner.native_batches(case)[0]
        self.assertLessEqual(row['packet_bytes'], 114937)
        self.assertLess(row['packet_bytes'], q.MAX_PACKET)

    def test_identity_and_denial_fail_before_source_read(self):
        for pid, language in ((True, 'python'), (2416, 'python'), (2415, 'ruby')):
            with patch.object(q, 'read') as read, patch.object(owner, 'authorize_before_open') as gate:
                with self.assertRaises(ValueError): owner.source_bytes('/unused', pid, language, {})
                read.assert_not_called(); gate.assert_not_called()
        with patch.object(owner, 'authorize_before_open', side_effect=PermissionError('closed')) as gate, patch.object(q, 'read') as read:
            with self.assertRaises(PermissionError):
                owner.source_bytes('/unused', 2415, 'python', {'artifact_paths': {}, 'trusted_hashes': {}})
            gate.assert_called_once(); read.assert_not_called()

    def test_changed_source_is_not_rewritten(self):
        with patch.object(owner, 'authorize_before_open') as gate, patch.object(q, 'read', return_value=b'changed inert bytes'):
            with self.assertRaisesRegex(ValueError, 'Git source binding'):
                owner.source_bytes('/unused', 2415, 'python', {'artifact_paths': {}, 'trusted_hashes': {}})
            gate.assert_called_once()

    def test_job_binding_requires_native_identity_and_singleton_route(self):
        cases = owner.project([{'args': [[1]], 'compare': 'return', 'expected': [1]}])
        for language in owner.LANGUAGES:
            job = owner.make_job(Path('/unused'), 2415, language, cases, '/original/source')
            self.assertEqual(job['source_interface'], owner.INTERFACES[language])
            self.assertIs(job['node_identity'], True)
            self.assertEqual(job['max_cases_per_batch'], 1)
            self.assertEqual(job['comparison_policy'], 'problem:2415')
            self.assertEqual(job['source_sha256'], owner.SOURCE_SHA256[2415][language])
        for pid, language in ((True, 'python'), (2416, 'python'), (2415, 'ruby')):
            with self.assertRaises(ValueError): owner.make_job(Path('/unused'), pid, language, cases, '/unused')

    def test_population_drift_fails_before_evidence(self):
        with patch.object(owner, 'evidence') as evidence:
            for jobs in ([], [{'id': 2415, 'language': 'python'}], [{'id': 2416, 'language': 'javascript'}]):
                with self.assertRaises(ValueError): owner.verify_freeze(Path('/unused'), {'jobs': jobs}, {})
            evidence.assert_not_called()

    def test_runtime_failure_precedes_payloads_and_output(self):
        with tempfile.TemporaryDirectory() as root:
            args = SimpleNamespace(output=Path(root) / 'freeze')
            with patch.object(q, 'runtime', side_effect=ValueError('unavailable')), patch.object(owner, 'evidence') as evidence:
                with self.assertRaisesRegex(ValueError, 'unavailable'): owner.prepare(args)
                evidence.assert_not_called()
            self.assertFalse(args.output.exists())

    def test_interface_contract_uses_relocatable_code_identity(self):
        value = owner.interface_contract()
        self.assertTrue(value['projection_only'])
        self.assertFalse(value['automatic_promotion'])
        self.assertFalse(value['constructor_injection'])
        self.assertFalse(value['source_rewriting'])
        self.assertTrue(all(not Path(name).is_absolute() for name in value['native_code_sha256']))
        self.assertEqual(value['semantic_cases_sha256'], owner.SEMANTIC_CASES_SHA256)

    def test_interface_approval_binds_each_required_claim_and_code_hash(self):
        contract = q.encoded(owner.interface_contract())
        valid = {'schema': 'gamma.native2415-interface-review.v1', 'reviewer': 'independent synthetic reviewer',
                 'contract_sha256': q.sha(contract), 'native_code_sha256': owner.native_code(),
                 **{k: True for k in ('independent_review', 'approved', 'original_candidate_bytes_unchanged',
                     'semantic_expectations_unchanged', 'runtime_bounds_unchanged',
                     'original_pre_source_gap_preserved', 'original_observer_bytes_unchanged')}}
        for key, bad in [(k, False) for k, v in valid.items() if v is True] + [
                ('reviewer', ''), ('contract_sha256', '0' * 64), ('native_code_sha256', {})]:
            with self.subTest(key=key), patch.object(owner, 'pinned', side_effect=[contract, q.encoded({**valid, key: bad})]):
                with self.assertRaises(ValueError): owner.approved_interface(Path('/unused'), 'synthetic pin')
        with patch.object(owner, 'pinned', side_effect=[contract, q.encoded(valid)]):
            self.assertEqual(owner.approved_interface(Path('/unused'), 'synthetic pin'), (contract, q.encoded(valid)))


if __name__ == '__main__':
    unittest.main()
