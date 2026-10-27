import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from .guide_admission import build, project, save_snapshot, verify_source_bindings
from . import test_catalogue


class GuideAdmission(unittest.TestCase):
    def inputs(self):
        universe, catalogue, receipts = test_catalogue.Catalogue().fixture()
        policy = SimpleNamespace(authorized={'a', 'b'}, protected=set(), unknown=set(),
                                 policy_sha256='c'*64, proof_sha256='d'*64)
        census = {'problems': [{'global_id': pid, 'implementations': {
            language: {'availability': 'development_tested_import',
                       'evidence': [{'path': '/must/not/be/opened/source.py'}]}
            for language in ('javascript', 'python')}} for pid in ('a', 'b')]}
        return universe, catalogue, receipts, policy, {'alias-a': 'a'}, census, {'a': [{'kind': 'fitted'}]}

    def test_bound_qualification_is_not_browser_or_corpus_admission(self):
        result = project(*self.inputs())
        self.assertEqual(result['summary']['language_slots'], 4)
        row = result['problems'][0]
        self.assertIsNone(row['split'])
        for slot in row['implementations'].values():
            self.assertTrue(slot['qualification']['receipt_binding_checked'])
            self.assertFalse(slot['browser_guide_admitted'])
            self.assertFalse(slot['development_corpus_admitted'])
            self.assertIn('license_record_not_joined', slot['blockers'])

    def test_import_cannot_promote_or_grant_permission(self):
        args = list(self.inputs())
        args[3].authorized.remove('b'); args[3].unknown.add('b')
        args[1]['problems'][1]['implementations']['python'] = {'status': 'blocked', 'reason': 'unverified import'}
        row = project(*args)['problems'][1]
        self.assertEqual(row['permission'], 'unresolved')
        self.assertIn('qualification_not_established', row['implementations']['python']['blockers'])
        self.assertIn('permission_unresolved', row['implementations']['python']['blockers'])

    def test_protected_member_cannot_be_relabelled(self):
        args = list(self.inputs())
        args[3].authorized.remove('b'); args[3].protected.add('b')
        with self.assertRaisesRegex(ValueError, 'universe disagree'):
            project(*args)

    def test_missing_exposure_never_becomes_fresh(self):
        result = project(*self.inputs())
        self.assertEqual(result['problems'][1]['exposure']['status'], 'unknown')
        self.assertFalse(result['problems'][1]['exposure']['freshness_established'])
        self.assertEqual(result['problems'][0]['aliases'], ['alias-a'])

    def test_stale_qualified_source_and_missing_census_fail(self):
        args = list(self.inputs())
        args[1]['problems'][0]['implementations']['python']['source_sha256'] = 'e'*64
        with self.assertRaises(ValueError): project(*args)
        args = list(self.inputs()); args[5]['problems'].pop()
        with self.assertRaisesRegex(ValueError, 'denominator'): project(*args)

    def test_snapshot_is_detached_and_cannot_be_overwritten(self):
        result = project(*self.inputs())
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)/'snapshot'
            hashes = save_snapshot(dest, result)
            self.assertEqual(hashes['queue.json'], hashlib.sha256((dest/'queue.json').read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError): save_snapshot(dest, copy.deepcopy(result))

    def test_source_verification_skips_denied_and_unqualified_slots(self):
        result = project(*self.inputs())
        result['problems'][1]['permission'] = 'protected'
        result['problems'][0]['implementations']['python']['qualification']['receipt_binding_checked'] = False
        service = Mock()
        service.request.return_value = {'status': 'abstain', 'reason': 'source_materialization_failed'}
        verify_source_bindings(result, service)
        service.request.assert_called_once_with('a', language='javascript', include_source=True)
        self.assertIn('source_bytes_not_rechecked', result['problems'][0]['implementations']['javascript']['blockers'])
        self.assertEqual(result['summary']['source_payload_read_upper_bound'], 1)
        self.assertIsNone(result['summary']['source_payload_reads'])

    def test_current_bytes_do_not_create_adapter_qualification(self):
        result = project(*self.inputs())
        source_hash = hashlib.sha256(b'source').hexdigest()
        for row in result['problems']:
            for slot in row['implementations'].values():
                slot['bindings']['source_sha256'] = source_hash
        service = Mock()
        service.request.return_value = {'artifact': {'status': 'materialized',
            'source_sha256': source_hash, 'source_utf8': 'source'}}
        verify_source_bindings(result, service)
        self.assertEqual(result['summary']['source_payload_reads'], 4)
        slot = result['problems'][0]['implementations']['javascript']
        self.assertNotIn('source_bytes_not_rechecked', slot['blockers'])
        self.assertFalse(slot['browser_guide_admitted'])

    def test_pinned_metadata_entrypoint_and_drift(self):
        universe, catalogue, receipts, policy, aliases, census, _ = self.inputs()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def pin(name, value):
                raw = json.dumps(value).encode(); path = root/name; path.write_bytes(raw)
                return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}
            alias = pin('identity.json', {'by_key': aliases})
            gate = pin('gate.json', {'artifact_paths': {'identity_aliases': alias['path']},
                                      'trusted_hashes': {'identity_aliases': alias['sha256']}})
            service = pin('service.json', {'schema': 'gamma.known-spec-service.v2',
                'universe': pin('universe.json', universe), 'catalogue': pin('catalogue.json', catalogue),
                'verified_receipts': pin('receipts.json', receipts), 'source_access': {
                    'boundary_gate': gate, 'aliases': pin('history.json', {'aliases': {'development:1': 'a'}})}})
            config = {'service': service, 'source_census': pin('census.json', census)}
            with patch(build.__module__+'.validate_policy', return_value=policy):
                result = build(config)
                self.assertEqual(result['summary']['problems'], 2)
                self.assertEqual(result['summary']['source_payload_reads'], 0)
                Path(config['source_census']['path']).write_text('{}')
                with self.assertRaises(ValueError): build(config)


if __name__ == '__main__':
    unittest.main()
