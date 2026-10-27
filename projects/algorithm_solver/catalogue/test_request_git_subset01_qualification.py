"""Source-free fixed request boundary controls; no imported candidate execution."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_git_subset01_qualification as owner


class FixedRequestTests(unittest.TestCase):
    def test_fixed_ids_and_immutable_oracle_owner(self):
        self.assertEqual(owner.IDS, (2110, 2221))
        self.assertEqual(q.file_hash(owner.oracle.__file__), owner.ORACLE_SHA256)
        owner.validate(2110, [[3, 2, 1]])
        owner.validate(2221, [[0, 9]])
        for pid, args in ((2110, [[True]]), (2221, [[1.0]]), (2111, [[1]]), (True, [[1]])):
            with self.subTest(pid=pid, args=args), self.assertRaises(ValueError):
                owner.validate(pid, args)

    def test_source_identity_rejected_before_gate_and_read(self):
        for pid, lang in ((True, 'python'), (2111, 'python'), (2110, 'ruby')):
            with self.subTest(pid=pid, lang=lang), patch.object(owner, 'authorize_before_open') as gate, patch.object(q, 'read') as read:
                with self.assertRaises(ValueError):
                    owner.source_bytes('/unused', pid, lang, {})
                gate.assert_not_called();read.assert_not_called()

    def test_new_request_rejects_unselected_id_before_payloads(self):
        job = {'id': 2111, 'language': 'python', 'domain_validator': owner.DOMAIN}
        with patch.object(q, 'read') as read, patch.object(q, 'authorize_before_open') as gate:
            with self.assertRaises(ValueError):
                q.job_inputs(Path('/unused'), job, {})
            read.assert_not_called();gate.assert_not_called()

    def test_job_inputs_dispatch_every_case_to_fixed_oracle(self):
        cases = [{'args': [[1]], 'expected': 1}, {'args': [[2, 1]], 'expected': 3}]
        source = b'synthetic bytes; never executed';raw = q.encoded(cases)
        job = owner.make_job(Path('/unused'), 2110, 'python', cases, '/original/2110.py')
        job.update(source_sha256=q.sha(source), tests_raw_sha256=q.sha(raw), case_count=2)
        with patch.object(q, 'authorize_before_open'), patch.object(q, 'read', side_effect=[source, raw]), patch.object(owner, 'validate') as validate:
            self.assertEqual(q.job_inputs(Path('/unused'), job, {'artifact_paths': {}, 'trusted_hashes': {}}), (source, cases))
        self.assertEqual([c.args for c in validate.call_args_list], [(2110, [[1]]), (2110, [[2, 1]])])

    def test_population_drift_fails_before_evidence_reads(self):
        with patch.object(owner, 'evidence') as evidence:
            for jobs in ([], [{'id': 2110, 'language': 'python'}], [{'id': 2111, 'language': 'javascript'}]):
                with self.assertRaises(ValueError):
                    owner.verify_freeze(Path('/unused'), {'jobs': jobs}, {})
            evidence.assert_not_called()

    def test_runtime_failure_precedes_payloads_and_output(self):
        with tempfile.TemporaryDirectory() as root:
            args = SimpleNamespace(output=Path(root) / 'freeze')
            with patch.object(q, 'runtime', side_effect=ValueError('runtime unavailable')), patch.object(owner, 'evidence') as evidence:
                with self.assertRaisesRegex(ValueError, 'runtime unavailable'):
                    owner.prepare(args)
                evidence.assert_not_called()
            self.assertFalse(args.output.exists())

    def test_successor_is_explicit_not_retroactive(self):
        value = owner.interface_contract()
        self.assertIn('post-source', value['declaration_timing'])
        self.assertEqual(value['javascript'], 'commonjs-function-solve-v1')
        self.assertTrue(value['effects_and_domain_unchanged'])
        self.assertFalse(value['automatic_promotion'])

    def test_review_must_approve_exact_successor(self):
        contract = q.encoded(owner.interface_contract())
        valid = {'schema': 'gamma.git-subset01-interface-review.v1', 'independent_review': True,
                 'reviewer': 'independent synthetic reviewer', 'approved': True, 'contract_sha256': q.sha(contract),
                 'original_candidate_bytes_unchanged': True, 'effects_and_domain_unchanged': True,
                 'original_pre_source_gap_preserved': True, 'old_object_loader_sha256': owner.OLD_LOADER_SHA256,
                 'new_function_loader_sha256': owner.FUNCTION_LOADER_SHA256}
        for key, bad in [('approved', False), ('independent_review', False), ('contract_sha256', '0' * 64),
                         ('original_pre_source_gap_preserved', False), ('effects_and_domain_unchanged', False),
                         ('new_function_loader_sha256', '0' * 64), ('reviewer', '')]:
            with self.subTest(key=key), patch.object(owner, 'pinned', side_effect=[contract, q.encoded({**valid, key: bad})]):
                with self.assertRaises(ValueError):
                    owner.approved_interface(Path('/unused'), 'synthetic trusted pin')
        with patch.object(owner, 'pinned', side_effect=[contract, q.encoded(valid)]):
            self.assertEqual(owner.approved_interface(Path('/unused'), 'synthetic trusted pin'), (contract, q.encoded(valid)))

    def test_source_digest_mismatch_is_not_rewritten(self):
        with patch.object(owner, 'authorize_before_open') as gate, patch.object(q, 'read', return_value=b'inert changed bytes'):
            with self.assertRaisesRegex(ValueError, 'source binding'):
                owner.source_bytes('/unused', 2110, 'python', {'artifact_paths': {}, 'trusted_hashes': {}})
        gate.assert_called_once()
