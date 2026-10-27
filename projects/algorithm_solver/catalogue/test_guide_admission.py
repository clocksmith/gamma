import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from .guide_admission import (build, project, reconcile_source_evidence, save_snapshot,
                             verify_source_bindings, reconcile_development_replay)
from .catalogue import BINDINGS, digest
from ..algsolve import authoring_variants
from . import test_catalogue


class HistoricalDevelopmentReplay(unittest.TestCase):
    def fixture(self):
        partition = {'dev_fit': [1, 2], 'dev_val': [3]}
        self.source = {'schema': 'gamma.cost-decomposition.contract.v1', 'partition': partition,
            'sources': [{'id': i, 'relative_path': f'style150/submitted/{i}.js', 'sha256': str(i) * 64}
                        for i in range(1, 4)]}
        self.qual = {'schema': 'gamma.name-search.v1', 'parent_contract_sha256': 'a' * 64,
            'partition': copy.deepcopy(partition), 'qualification': [{'id': i, 'files': {
                f'population500/{i}-tests.json': 'b' * 64,
                f'population500-baseline/qualification/baselines/{i}.json': 'c' * 64}} for i in range(1, 4)]}
        self.aliases = {'aliases': {f'development400:{i}': f'leetcode:{i}' for i in range(1, 4)}}
        self.keys = {'by_key': {'lc:alpha': 'leetcode:1', 'lc:beta': 'leetcode:2', 'lc:gamma': 'leetcode:3'}}
        self.catalogue = {'problems': [{'problem_id': f'leetcode:{i}', 'implementations': {
            lang: dict({k: 'd' * 64 for k in BINDINGS}, status='qualified',
                source_sha256=str(i) * 64 if lang == 'javascript' else 'e' * 64,
                receipt_sha256='f' * 64, canonical_variant_id=f'{lang}:{i}')
            for lang in ('javascript', 'python')}} for i in range(1, 5)]}
        self.boundary = SimpleNamespace(authorized={f'leetcode:{i}' for i in range(1, 4)})

    def join(self):
        return reconcile_development_replay(self.catalogue, self.aliases, self.keys,
            self.source, self.qual, 'a' * 64, self.boundary)

    def test_historical_fit_needs_no_new_sidecar_or_authoring_registry(self):
        self.fixture(); original = copy.deepcopy(self.catalogue)
        with patch('builtins.open', side_effect=AssertionError('payload opened')):
            result = self.join()
        self.assertEqual(result['summary']['eligible'], {'javascript': 2, 'python': 0})
        self.assertEqual(self.catalogue, original)
        slot = result['problems'][0]['implementations']['javascript']
        self.assertEqual(slot['canonical_variant_id'], 'javascript:1')
        self.assertIsNone(slot['sidecar_semantics_sha256'])
        self.assertFalse(slot['authoring_variant_created'])
        self.assertFalse(result['summary']['fresh_confirmation_created'])
        self.assertFalse(result['summary']['complete_near_duplicate_closure_established'])

    def test_canonical_languages_group_together_and_validation_stays_excluded(self):
        self.fixture(); result = self.join(); row = result['problems'][2]
        self.assertEqual(row['historical_membership'], 'dev_val')
        self.assertEqual(row['canonical_group_members'], ['leetcode:3'])
        self.assertEqual(row['known_cross_membership_conflicts'], [])
        for slot in row['implementations'].values():
            self.assertIn('preserved_consumed_development_validation', slot['exclusions'])
            self.assertFalse(slot['eligible'])

    def test_known_sibling_cross_split_conflict_excludes_without_reallocation(self):
        self.fixture(); self.keys['by_key'].update({'lc:related-i': 'leetcode:1', 'lc:related-ii': 'leetcode:3'})
        result = self.join()
        self.assertEqual(result['summary']['eligible']['javascript'], 1)
        self.assertEqual(result['problems'][0]['known_cross_membership_conflicts'], ['leetcode:3'])
        self.assertEqual(result['problems'][0]['historical_membership'], 'dev_fit')
        self.assertEqual(self.source['partition']['dev_val'], [3])

    def test_known_group_to_unknown_member_is_excluded(self):
        self.fixture(); self.keys['by_key'].update({'lc:related-i': 'leetcode:2', 'lc:related-ii': 'leetcode:4'})
        result = self.join()
        self.assertFalse(result['problems'][1]['implementations']['javascript']['eligible'])

    def test_changed_source_and_denied_identity_cannot_inherit_fit(self):
        self.fixture(); self.catalogue['problems'][0]['implementations']['javascript']['source_sha256'] = '0' * 64
        self.boundary.authorized.remove('leetcode:2')
        result = self.join()
        self.assertEqual(result['summary']['eligible']['javascript'], 0)
        self.assertIn('historical_exact_language_source_not_joined', result['problems'][0]['implementations']['javascript']['exclusions'])

    def test_partition_alias_language_and_chain_drift_fail_closed(self):
        changes = [lambda: self.qual.update(parent_contract_sha256='0' * 64),
            lambda: self.aliases['aliases'].update({'development400:1': 'leetcode:4'}),
            lambda: self.source['sources'][0].update(relative_path='style150/submitted/1.py'),
            lambda: self.qual['qualification'][0]['files'].clear(),
            lambda: self.source['partition']['dev_fit'].append(3)]
        for change in changes:
            self.fixture(); change()
            with self.assertRaises(ValueError): self.join()


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
                config.update(authoring_catalog=pin('authoring.json', {
                    'schema': 'gamma.authoring-variant-catalog-pilot.v1', 'variants': []}),
                    source_evidence=pin('evidence.json', []), historical_guides=pin('guides.json', []))
                joined = build(config)
                self.assertEqual(joined['summary']['source_evidence_reconciliation']['authoring_records'], 0)
                self.assertEqual(joined['inputs']['source_evidence_sha256'], config['source_evidence']['sha256'])
                self.assertIn('authoring_variants.py', joined['inputs']['code_sha256'])
                self.assertEqual(joined['summary']['source_payload_reads'], 0)
                original = Path(config['source_evidence']['path']).read_text()
                Path(config['source_evidence']['path']).write_text('{}')
                with self.assertRaises(ValueError): build(config)
                Path(config['source_evidence']['path']).write_text(original)
                Path(config['source_census']['path']).write_text('{}')
                with self.assertRaises(ValueError): build(config)


class SourceEvidenceReconciliation(unittest.TestCase):
    def setUp(self):
        args = list(GuideAdmission().inputs())
        names = {'a': 'leetcode:1', 'b': 'leetcode:2'}
        args[0]['eligible_problem_ids'] = list(names.values())
        args[1]['universe_sha256'] = digest(args[0])
        receipts = {}
        for problem in args[1]['problems']:
            problem['problem_id'] = names[problem['problem_id']]
            for impl in problem['implementations'].values():
                receipt = copy.deepcopy(args[2][impl['receipt_sha256']])
                receipt['problem_id'] = problem['problem_id']
                impl['receipt_sha256'] = digest(receipt)
                receipts[impl['receipt_sha256']] = receipt
        args[2] = receipts
        args[3].authorized = set(names.values())
        args[4] = {'alias-a': names['a']}
        for observed in args[5]['problems']:
            observed['global_id'] = names[observed['global_id']]
        args[6] = {names['a']: [{'kind': 'previously_fitted'}]}
        self.result = project(*args)
        self.slot = self.result['problems'][0]['implementations']['javascript']
        identity = {'problem_id': 1, 'language': 'javascript', 'source_sha256': 'b'*64,
                    'semantics_sha256': 'c'*64, 'problem_contract_sha256': 'b'*64}
        self.authored = dict(identity, variant_id=authoring_variants.sha(authoring_variants.canonical(identity).encode()),
                             qualification={'status': 'unknown', 'reason': 'Authoring is not qualification'},
                             provenance=[{'source_path': '/must/not/open/source.js'}])
        self.catalog = {'schema': 'gamma.authoring-variant-catalog-pilot.v1', 'variants': [self.authored]}

    def evidence(self, kind='license'):
        return {'problem_id': 'leetcode:1', 'language': 'javascript', 'kind': kind,
                'bindings': copy.deepcopy(self.slot['bindings']),
                'evidence': {'path': '/must/not/open/evidence.json', 'status': 'unknown'}}

    @staticmethod
    def first_slot(result):
        return result['problems'][0]['implementations']['javascript']

    def test_authoring_owner_query_and_identity_reused_without_promotion(self):
        original = copy.deepcopy(self.catalog)
        with patch.object(authoring_variants, 'query', wraps=authoring_variants.query) as queried:
            value = reconcile_source_evidence(self.result, authoring_catalog=self.catalog)
        self.assertEqual(queried.call_count, 4)
        row = self.first_slot(value)['authoring_variants']['records'][0]
        self.assertEqual(row['record']['variant_id'], self.authored['variant_id'])
        self.assertEqual(row['record']['qualification']['status'], 'unknown')
        self.assertEqual(row['qualification_join'], 'exact_existing_canonical_receipt')
        self.assertEqual(row['canonical_qualification_receipt_sha256'], self.slot['qualification']['receipt_sha256'])
        self.assertEqual(self.catalog, original)
        self.assertNotIn('authoring_variants', self.slot)
        self.assertFalse(self.first_slot(value)['development_corpus_admitted'])

    def test_different_source_and_contract_never_inherit_canonical_receipt(self):
        for changed_field in ('source_sha256', 'problem_contract_sha256'):
            with self.subTest(changed_field=changed_field):
                row = copy.deepcopy(self.authored)
                row[changed_field] = 'e'*64
                identity = {k: row[k] for k in ('problem_id', 'language', 'source_sha256', 'semantics_sha256', 'problem_contract_sha256')}
                row['variant_id'] = authoring_variants.sha(authoring_variants.canonical(identity).encode())
                catalog = dict(self.catalog, variants=[row])
                value = reconcile_source_evidence(self.result, authoring_catalog=catalog)
                joined = self.first_slot(value)['authoring_variants']['records'][0]
                self.assertEqual(joined['qualification_join'], 'not_joined')
                self.assertIsNone(joined['canonical_qualification_receipt_sha256'])

    def test_tampered_or_reclassified_authoring_record_rejected(self):
        for mutate in (lambda r: r.update(variant_id='a'*64),
                       lambda r: r.update(qualification={'status': 'qualified'}),
                       lambda r: r.update(qualification=None)):
            with self.subTest(mutate=mutate):
                catalog = copy.deepcopy(self.catalog); mutate(catalog['variants'][0])
                with self.assertRaisesRegex(ValueError, 'authoring record'):
                    reconcile_source_evidence(self.result, authoring_catalog=catalog)
        with self.assertRaisesRegex(ValueError, 'duplicate authoring'):
            reconcile_source_evidence(self.result, authoring_catalog=dict(self.catalog, variants=[self.authored, self.authored]))
        self.assertNotIn('authoring_variants', self.slot)

    def test_exact_evidence_joins_do_not_invent_acceptance_or_read_paths(self):
        records = [self.evidence(kind) for kind in ('license', 'browser_adapter', 'host_api')]
        with patch('pathlib.Path.open', side_effect=AssertionError('no path reads')):
            value = reconcile_source_evidence(self.result, source_evidence=records)
        slot = self.first_slot(value)
        self.assertTrue(all(r['status'] == 'exact_binding_joined' for r in slot['source_evidence_joins']))
        self.assertTrue(all(r['record']['evidence']['status'] == 'unknown' for r in slot['source_evidence_joins']))
        self.assertFalse(slot['license']['acceptance_evaluated'])
        self.assertIn('license_acceptance_not_established', slot['blockers'])
        self.assertIn('browser_adapter_acceptance_not_established', slot['blockers'])
        self.assertIn('determinism_and_host_api_acceptance_not_established', slot['blockers'])
        self.assertFalse(slot['browser_guide_admitted'])
        self.assertFalse(slot['development_corpus_admitted'])
        self.assertEqual(value['summary']['source_payload_reads'], 0)
        self.assertEqual(value['summary']['source_evidence_reconciliation']['exact_binding_joined'], 3)

    def test_every_qualification_binding_is_required_and_exact(self):
        for field in BINDINGS:
            with self.subTest(field=field):
                record = self.evidence(); record['bindings'][field] = 'f'*64
                slot = self.first_slot(reconcile_source_evidence(self.result, source_evidence=[record]))
                joined = slot['source_evidence_joins'][0]
                self.assertEqual(joined['reason'], 'canonical_binding_mismatch')
                self.assertEqual(joined['mismatching_bindings'], [field])
                self.assertIsNone(slot['license'])
                self.assertIn('license_record_not_joined', slot['blockers'])
                del record['bindings'][field]
                with self.assertRaisesRegex(ValueError, 'complete exact bindings'):
                    reconcile_source_evidence(self.result, source_evidence=[record])

    def test_permission_and_qualification_cannot_be_bypassed_by_evidence(self):
        for permission, qualified, expected in [('protected', True, 'permission_not_authorized'),
                ('unresolved', True, 'permission_not_authorized'),
                ('source_access_authorized', False, 'qualification_not_established')]:
            with self.subTest(permission=permission, qualified=qualified):
                result = copy.deepcopy(self.result)
                result['problems'][0]['permission'] = permission
                self.first_slot(result)['qualification']['receipt_binding_checked'] = qualified
                value = reconcile_source_evidence(result, source_evidence=[self.evidence()])
                self.assertEqual(self.first_slot(value)['source_evidence_joins'][0]['reason'], expected)
                self.assertIsNone(self.first_slot(value)['license'])

    def test_historical_guides_stay_distinct_even_if_source_matches(self):
        for source_hash in ('b'*64, 'f'*64):
            with self.subTest(source_hash=source_hash):
                guide = {'problem_id': 'leetcode:1', 'language': 'javascript', 'source_sha256': source_hash,
                         'profile_id': 'historical-profile', 'evidence': {'passed': True, 'scope': 'separate historical record'}}
                value = reconcile_source_evidence(self.result, historical_guides=[guide])
                row = self.first_slot(value)['historical_guides'][0]
                self.assertEqual(row['canonical_source_match'], source_hash == 'b'*64)
                self.assertEqual(row['qualification_join'], 'not_joined')
                self.assertFalse(row['canonical_evidence_transplanted'])
                self.assertEqual(row['record']['evidence'], guide['evidence'])

    def test_absent_inputs_are_not_global_absence_or_freshness(self):
        value = reconcile_source_evidence(self.result)
        self.assertEqual(self.first_slot(value)['authoring_variants']['status'], 'not_supplied')
        self.assertFalse(self.first_slot(value)['authoring_variants']['exhaustive_inventory'])
        empty = reconcile_source_evidence(self.result, authoring_catalog=dict(self.catalog, variants=[]))
        self.assertEqual(self.first_slot(empty)['authoring_variants']['status'], 'queried')
        self.assertEqual(self.first_slot(empty)['authoring_variants']['records'], [])
        self.assertEqual(empty['problems'][1]['exposure']['status'], 'unknown')
        self.assertFalse(empty['summary']['fresh_confirmation_created'])
        self.assertIsNone(empty['problems'][1]['split'])

    def test_duplicate_unknown_and_bad_evidence_fail_without_changing_inventory(self):
        record = self.evidence()
        bad = copy.deepcopy(record); bad['problem_id'] = 'leetcode:999'
        for records in ([record, record], [bad], [dict(record, broad_approval=True)]):
            with self.subTest(records=records):
                with self.assertRaises(ValueError):
                    reconcile_source_evidence(self.result, source_evidence=records)
        self.assertNotIn('source_evidence_joins', self.slot)

    def test_reconciliation_is_one_shot_not_an_in_place_accumulator(self):
        value = reconcile_source_evidence(self.result, source_evidence=[self.evidence()])
        with self.assertRaisesRegex(ValueError, 'new inventory snapshot'):
            reconcile_source_evidence(value, source_evidence=[self.evidence()])


if __name__ == '__main__':
    unittest.main()
