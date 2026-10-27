import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from algsolve.authoring_variants import build, query, sha, main, from_canonical_contracts


class CatalogTests(unittest.TestCase):
    def canonical_fixture(self):
        contract = {'domain': 'ASCII λ', 'result': 'integer', 'effects': 'read-only'}
        contract_hash = sha(json.dumps(contract, sort_keys=True, separators=(',', ':')).encode())
        return {'problems': [{'problem_id': 'leetcode:1', 'implementations': {
            language: {'status': 'qualified', 'canonical_variant_id': language + ':' + 'a' * 64,
                       'source_sha256': 'a' * 64, 'problem_contract_sha256': contract_hash,
                       'receipt_sha256': 'b' * 64,
                       'provenance': {'public_batch': {'problem_contract': contract}}}
            for language in ('javascript', 'python')}}]}

    def test_canonical_contract_view_preserves_identity_without_qualification(self):
        value = self.canonical_fixture(); raw = json.dumps(value).encode()
        with patch('builtins.open', side_effect=AssertionError('payload opened')):
            result = from_canonical_contracts(raw, sha(raw))
        self.assertEqual(result['variant_count'], 2)
        record = query(result, 1, 'python')[0]
        self.assertEqual(record['qualification']['status'], 'unknown')
        self.assertEqual(record['provenance'][0]['canonical_variant_id'], 'python:' + 'a' * 64)
        self.assertFalse(record['provenance'][0]['authoring_sidecar_created'])
        self.assertEqual(record['semantics_sha256'], record['problem_contract_sha256'])
        self.assertFalse(result['qualification_created'])

    def test_missing_contract_stays_unresolved_and_hash_drift_fails(self):
        value = self.canonical_fixture()
        value['problems'][0]['implementations']['python']['provenance'] = {}
        raw = json.dumps(value).encode(); result = from_canonical_contracts(raw, sha(raw))
        self.assertEqual(result['variant_count'], 1)
        self.assertEqual(len(result['unresolved_canonical_slots']), 1)
        value['problems'][0]['implementations']['javascript']['problem_contract_sha256'] = 'c' * 64
        raw = json.dumps(value).encode()
        with self.assertRaisesRegex(ValueError, 'Exact canonical'):
            from_canonical_contracts(raw, sha(raw))
        with self.assertRaisesRegex(ValueError, 'Pinned bounded'):
            from_canonical_contracts(raw, '0' * 64)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def make(self, label, source=b'return 1', contract='integer'):
        root = self.root / label
        root.mkdir()
        packet = {'problems': [{'id': 1, 'external_interface': {'return': contract},
                               'return_domain': contract,
                               'statement_constraints_snapshot': ['n >= 0']}]}
        pb = json.dumps(packet).encode()
        sem = b'{"algorithm":"synthetic"}'
        for name, data in [('assignment.public-safe.json', pb), ('1.py', source), ('1.semantics.json', sem)]:
            (root / name).write_bytes(data)
        m = {'assignment_sha256': sha(pb), 'source_inventory': [
            {'id': 1, 'language': 'python', 'path': '1.py', 'sha256': sha(source)}],
             'files': [{'path': '1.py', 'sha256': sha(source)},
                       {'path': '1.semantics.json', 'sha256': sha(sem)}]}
        p = root / 'DELIVERY_MANIFEST.json'
        p.write_text(json.dumps(m))
        return p

    def test_multiple_variants_and_no_preference(self):
        a, b = self.make('a'), self.make('b', b'return 2')
        d = build([a, b])
        self.assertEqual(d['unique_problem_count'], 1)
        self.assertEqual(d['variant_count'], 2)
        self.assertEqual(len(query(d, 1, 'python')), 2)
        self.assertEqual(query(d, 1, 'javascript'), ())
        self.assertIsNone(d['preferred_variant'])
        self.assertTrue(all(x['qualification']['status'] == 'unknown' for x in d['variants']))

    def test_duplicates_do_not_inflate(self):
        a, b = self.make('a'), self.make('b')
        d = build([a, b, a])
        self.assertEqual((d['unique_problem_count'], d['variant_count']), (1, 1))
        self.assertEqual(len(d['variants'][0]['provenance']), 1)

    def test_deterministic_order(self):
        a, b = self.make('a'), self.make('b', b'return 2')
        self.assertEqual(build([a, b]), build([b, a]))

    def test_source_hash_mismatch(self):
        a = self.make('a')
        (a.parent / '1.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
            build([a])

    def test_contract_bytes_mismatch(self):
        a = self.make('a')
        (a.parent / '1.semantics.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
            build([a])

    def test_contract_reference_mismatch(self):
        a = self.make('a')
        d = json.loads(a.read_text())
        d['source_inventory'][0]['semantics_sha256'] = 'bad'
        a.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, 'Contract reference mismatch'):
            build([a])

    def test_problem_contract_mismatch(self):
        a, b = self.make('a'), self.make('b', contract='string')
        with self.assertRaisesRegex(ValueError, 'Problem contract mismatch'):
            build([a, b])

    def test_packet_hash_mismatch(self):
        a = self.make('a')
        (a.parent / 'assignment.public-safe.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
            build([a])

    def test_authoring_claim_cannot_qualify_variant(self):
        a = self.make('a')
        d = json.loads(a.read_text())
        d['status'] = 'accepted'
        d['source_inventory'][0]['qualification'] = 'verified'
        a.write_text(json.dumps(d))
        result = build([a])
        self.assertEqual(result['variants'][0]['qualification']['status'], 'unknown')
        self.assertIsNone(result['preferred_variant'])

    def test_separate_return_domain_conflict(self):
        a, b = self.make('a'), self.make('b')
        pp = b.parent / 'assignment.public-safe.json'
        packet = json.loads(pp.read_text())
        packet['problems'][0]['return_domain'] = 'strict boolean'
        raw = json.dumps(packet).encode()
        pp.write_bytes(raw)
        manifest = json.loads(b.read_text())
        manifest['assignment_sha256'] = sha(raw)
        b.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Problem contract mismatch'):
            build([a, b])

    def test_cli_matches_utf8_lf_render(self):
        manifest = self.make('a')
        output = self.root / 'catalog.json'
        with patch('sys.argv', ['authoring_variants', str(manifest), '--output', str(output)]):
            main()
        expected = (json.dumps(build([manifest]), sort_keys=True, indent=2) + '\n').encode('utf-8')
        self.assertEqual(output.read_bytes(), expected)
        self.assertNotIn(b'\r\n', output.read_bytes())


if __name__ == '__main__':
    unittest.main()
