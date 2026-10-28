import json
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from algsolve.authoring_variants import (build, query, sha, main, from_canonical_contracts,
                                        reconcile_official_identities, query_official_identity)


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


class OfficialIdentityTests(unittest.TestCase):
    setUp = CatalogTests.setUp
    make = CatalogTests.make

    def fixture(self, *, sources=(b'inert one',), question=None):
        manifests, provenance = [], {}
        for i, source in enumerate(sources):
            path = self.make(str(i), source)
            assignment = path.parent / 'assignment.public-safe.json'
            packet = json.loads(assignment.read_bytes()); packet['problems'][0]['slug'] = 'original-slug'
            raw = json.dumps(packet).encode(); assignment.write_bytes(raw)
            manifest = json.loads(path.read_bytes()); manifest['assignment_sha256'] = sha(raw)
            path.write_text(json.dumps(manifest)); manifests.append(path)
            provenance[sha(raw)] = raw; provenance[sha(path.read_bytes())] = path.read_bytes()
        catalog = build(manifests); catalog_raw = json.dumps(catalog).encode()
        if question is None:
            question = {'questionId': '11', 'questionFrontendId': '7', 'title': 'Current title',
                        'titleSlug': 'current-slug', 'isPaidOnly': True,
                        'metaData': '{"name":"f","params":[]}'}
        metadata = json.dumps({'data': {'question': question}}).encode()
        official = {'question_id': question['questionId'], 'frontend_id': question['questionFrontendId'],
                    'title': question['title'], 'title_slug': question['titleSlug'],
                    'is_paid_only': question['isPaidOnly'],
                    'signature_metadata_sha256': sha(question['metaData'].encode()) if question['metaData'] is not None else None}
        rows = []
        for variant in catalog['variants']:
            rows.append({'variant_id': variant['variant_id'], 'original_problem_id': variant['problem_id'],
                         **{k: variant[k] for k in ('language', 'source_sha256', 'semantics_sha256',
                                                   'problem_contract_sha256')},
                         'provenance': variant['provenance'][0], 'delivered_slug': 'original-slug',
                         'queried_slug': 'current-slug', 'official_metadata_sha256': sha(metadata),
                         'official_identity': official})
        evidence = {'schema': 'gamma.authoring-official-identity-evidence.v1',
                    'authoring_catalog_sha256': sha(catalog_raw), 'records': rows}
        return catalog, catalog_raw, evidence, {sha(metadata): metadata}, provenance

    def run_reconcile(self, fixture, evidence=None, metadata=None, provenance=None):
        _, raw, original, snapshots, sources = fixture
        encoded = json.dumps(original if evidence is None else evidence).encode()
        return reconcile_official_identities(raw, sha(raw), encoded, sha(encoded),
                                             snapshots if metadata is None else metadata,
                                             sources if provenance is None else provenance)

    def test_multiple_variants_share_official_identity_without_relabel_or_preference(self):
        f = self.fixture(sources=(b'inert first', b'inert second')); before = copy.deepcopy(f[0])
        with patch('builtins.open', side_effect=AssertionError('payload open')):
            result = self.run_reconcile(f)
            evidence = json.dumps(f[2]).encode()
            found = query_official_identity(f[1], sha(f[1]), evidence, sha(evidence), f[3], f[4], 7, 'python')
        self.assertEqual(len(result['bindings']), 2)
        self.assertEqual(found, query(f[0], 1, 'python'))
        self.assertEqual(query(f[0], 7, 'python'), ())
        self.assertEqual(f[0], before)
        self.assertIsNone(f[0]['preferred_variant'])
        self.assertTrue(all(v['qualification']['status'] == 'unknown' for v in found))
        self.assertTrue(all(r['numeric_identity_changed'] and r['slug_changed'] for r in result['bindings']))
        self.assertFalse(result['qualification_created']); self.assertFalse(result['semantic_contract_established'])
        self.assertFalse(result['canonical_adoption_created']); self.assertFalse(result['original_catalog_changed'])
        self.assertEqual(result['source_payloads_opened'], 0)

    def test_exact_source_contract_assignment_and_manifest_bindings(self):
        f = self.fixture()
        for key in ('source_sha256', 'semantics_sha256', 'problem_contract_sha256', 'variant_id'):
            evidence = copy.deepcopy(f[2]); evidence['records'][0][key] = '0' * 64
            with self.subTest(key=key), self.assertRaises(ValueError): self.run_reconcile(f, evidence)
        for key in ('assignment_sha256', 'manifest_sha256', 'source_path', 'semantics_path'):
            evidence = copy.deepcopy(f[2]); evidence['records'][0]['provenance'][key] = 'unbound'
            with self.subTest(key=key), self.assertRaises(ValueError): self.run_reconcile(f, evidence)
        with self.assertRaises(ValueError): self.run_reconcile(f, provenance={})
        for pin, raw in f[4].items():
            snapshots = dict(f[4]); snapshots[pin] = raw + b' '
            with self.subTest(pin=pin), self.assertRaises(ValueError): self.run_reconcile(f, provenance=snapshots)

    def test_delivered_slug_is_checked_against_original_assignment(self):
        f = self.fixture(); evidence = copy.deepcopy(f[2]); evidence['records'][0]['delivered_slug'] = 'invented-original'
        with self.assertRaisesRegex(ValueError, 'exact original assignment'): self.run_reconcile(f, evidence)

    def test_numeric_types_and_metadata_identity_claims_fail_closed(self):
        f = self.fixture()
        for pid in (True, 1.0, '1', None):
            evidence = copy.deepcopy(f[2]); evidence['records'][0]['original_problem_id'] = pid
            with self.subTest(pid=pid), self.assertRaises(ValueError): self.run_reconcile(f, evidence)
        snapshot = json.loads(next(iter(f[3].values())))
        for key, value in [('questionFrontendId', True), ('questionFrontendId', 7),
                           ('questionFrontendId', '07'), ('questionId', 11.0), ('isPaidOnly', 1),
                           ('titleSlug', ''), ('metaData', '[]')]:
            modified = copy.deepcopy(snapshot); modified['data']['question'][key] = value
            raw = json.dumps(modified).encode(); evidence = copy.deepcopy(f[2])
            evidence['records'][0]['official_metadata_sha256'] = sha(raw)
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.run_reconcile(f, evidence, {sha(raw): raw})
        for field in ('frontend_id', 'title', 'title_slug', 'signature_metadata_sha256'):
            evidence = copy.deepcopy(f[2]); evidence['records'][0]['official_identity'][field] = 'invented'
            with self.subTest(field=field), self.assertRaises(ValueError): self.run_reconcile(f, evidence)

    def test_duplicate_or_conflicting_variant_evidence_is_not_merged(self):
        f = self.fixture(); evidence = copy.deepcopy(f[2]); evidence['records'] *= 2
        with self.assertRaisesRegex(ValueError, 'ambiguous duplicate'): self.run_reconcile(f, evidence)

    def test_null_official_response_stays_unresolved_without_guessing(self):
        f = self.fixture(); raw = b'{"data":{"question":null}}'; evidence = copy.deepcopy(f[2])
        evidence['records'][0].update(official_metadata_sha256=sha(raw), official_identity=None)
        result = self.run_reconcile(f, evidence, {sha(raw): raw})
        self.assertEqual(result['bindings'], [])
        self.assertEqual(result['unresolved'][0]['reason'], 'official_question_not_found')
        evidence['records'][0]['official_identity'] = f[2]['records'][0]['official_identity']
        with self.assertRaises(ValueError): self.run_reconcile(f, evidence, {sha(raw): raw})

    def test_metadata_hash_drift_and_non_metadata_response_are_rejected(self):
        f = self.fixture(); pin, raw = next(iter(f[3].items()))
        with self.assertRaises(ValueError): self.run_reconcile(f, metadata={pin: raw + b' '})
        with self.assertRaises(ValueError): self.run_reconcile(f, metadata={})
        snapshot = json.loads(raw); snapshot['data']['question']['content'] = 'not identity metadata'
        modified = json.dumps(snapshot).encode(); evidence = copy.deepcopy(f[2])
        evidence['records'][0]['official_metadata_sha256'] = sha(modified)
        with self.assertRaisesRegex(ValueError, 'identity-only'): self.run_reconcile(f, evidence, {sha(modified): modified})
        raw_evidence = json.dumps(f[2]).encode()
        for catalog_pin, evidence_pin in [('0'*64, sha(raw_evidence)), (sha(f[1]), '0'*64)]:
            with self.assertRaises(ValueError):
                reconcile_official_identities(f[1], catalog_pin, raw_evidence, evidence_pin, f[3], f[4])

    def test_official_query_revalidates_every_call_and_rejects_coercions(self):
        f = self.fixture(); raw = json.dumps(f[2]).encode()
        for pid in (True, '7', 7.0, 0):
            with self.subTest(pid=pid), self.assertRaises(ValueError):
                query_official_identity(f[1], sha(f[1]), raw, sha(raw), f[3], f[4], pid, 'python')
        for language in ('ruby', None, []):
            with self.subTest(language=language), self.assertRaises(ValueError):
                query_official_identity(f[1], sha(f[1]), raw, sha(raw), f[3], f[4], 7, language)
        with self.assertRaises(ValueError):
            query_official_identity(f[1], sha(f[1]), raw, sha(raw), {}, f[4], 7, 'python')


if __name__ == '__main__':
    unittest.main()
