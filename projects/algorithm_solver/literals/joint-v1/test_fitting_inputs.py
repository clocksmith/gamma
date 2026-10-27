"""Synthetic metadata gates; no real corpus or candidate execution."""
import copy
from contextlib import redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import fitting_inputs as fitting
import idiom_pilot


class FittingInputTests(unittest.TestCase):
    def fixture(self, count=2):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.texts = {i: f'def solve(x):\n    return x + {i}\n' for i in range(1, count + 1)}
        self.catalog = {'schema': 'gamma.authoring-variant-catalog-pilot.v1', 'variants': []}
        self.canonical = {'problems': []}
        self.admission = {'schema': 'gamma.source-to-guide-inventory.v1', 'inputs': {}, 'problems': []}
        self.policy = {'schema': 'gamma.idiom-fitting-policy.v1', 'authority': 'synthetic operator fixture',
                       'reference': 'synthetic reviewed membership', 'purpose': 'development-fitting',
                       'inputs': {}, 'variants': []}
        for i, text in self.texts.items():
            identity = {'problem_id': i, 'language': 'python', 'source_sha256': fitting.owner.sha(text.encode()),
                        'semantics_sha256': 'a' * 64, 'problem_contract_sha256': 'b' * 64}
            vid = fitting.owner.sha(fitting.owner.canonical(identity).encode())
            self.catalog['variants'].append(dict(identity, variant_id=vid, qualification={'status': 'unknown'},
                                                 provenance=[{'source_path': '/must/not/follow/authoring.py'}]))
            impl = {k: 'c' * 64 for k in fitting.BINDINGS}
            impl.update(status='qualified', source_sha256=identity['source_sha256'],
                        problem_contract_sha256=identity['problem_contract_sha256'], receipt_sha256='d' * 64)
            self.canonical['problems'].append({'problem_id': f'leetcode:{i}', 'implementations': {'python': impl}})
            self.admission['problems'].append({'problem_id': f'leetcode:{i}', 'permission': 'source_access_authorized',
                'permission_binding': {'policy_sha256': 'e' * 64, 'proof_sha256': 'f' * 64},
                'split': 'development_fit', 'exposure': {'status': 'previously_exposed'},
                'grouping': {'group_id': f'group-{i}', 'near_duplicate_closure': 'reviewed',
                             'problem_and_languages_together': True},
                'implementations': {'python': {'bindings': {k: impl[k] for k in fitting.BINDINGS},
                    'development_corpus_admitted': True, 'blockers': [],
                    'license': {'synthetic_admitted_evidence': True},
                    'adapter': {'synthetic_admitted_evidence': True},
                    'qualification': {'receipt_binding_checked': True, 'receipt_sha256': impl['receipt_sha256']}}}})
            self.policy['variants'].append({'problem_id': i, 'language': 'python', 'variant_id': vid,
                                            'membership': 'development_fit', 'group_id': f'group-{i}'})
        self.boundary = SimpleNamespace(policy_sha256='e' * 64, proof_sha256='f' * 64,
                                        authorize=Mock())
        self.service = Mock()
        def materialize(pid, *, language, include_source):
            self.assertEqual(language, 'python'); self.assertIs(include_source, True)
            text = self.texts[int(pid.split(':')[1])]
            return {'artifact': {'status': 'materialized', 'source_utf8': text,
                                 'source_sha256': fitting.owner.sha(text.encode())}}
        self.service.request.side_effect = materialize
        self.patchers = [patch.object(fitting.KnownSpecService, 'from_config', return_value=self.service),
                         patch.object(fitting, '_boundary_snapshot', return_value=self.boundary)]
        for patcher in self.patchers:
            patcher.start(); self.addCleanup(patcher.stop)

    def pin(self, name, value):
        raw = json.dumps(value).encode(); path = self.root / name; path.write_bytes(raw)
        return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}

    def config(self):
        canonical = self.pin('canonical.json', self.canonical)
        gate = self.pin('gate.json', {})
        service = self.pin('service.json', {'catalogue': canonical, 'source_access': {
            'boundary_gate': gate, 'authorized_problem_ids': [f'leetcode:{i}' for i in self.texts]}})
        self.admission['inputs']['service_sha256'] = service['sha256']
        admission = self.pin('admission.json', self.admission)
        catalog = self.pin('authoring.json', self.catalog)
        self.policy['inputs'] = {k + '_sha256': v['sha256'] for k, v in
                                [('service', service), ('admission', admission), ('authoring_catalog', catalog)]}
        policy = self.pin('policy.json', self.policy)
        return self.pin('config.json', {'schema': 'gamma.idiom-fitting-config.v1', 'language': 'python',
            'service': service, 'admission': admission, 'authoring_catalog': catalog, 'fitting_policy': policy})

    def load(self):
        spec = self.config()
        return fitting.load_fitting_inputs(spec['path'], spec['sha256'])

    def test_240_problem_selection_preserves_owner_ids_and_memberships(self):
        self.fixture(240)
        before = copy.deepcopy(self.catalog)
        sources, metadata = self.load()
        self.assertEqual(len(sources), 240)
        self.assertEqual(self.service.request.call_count, 240)
        self.assertEqual(metadata['problem_count'], 240)
        self.assertEqual(metadata['memberships'], [dict(row,
            **{k: record[k] for k in ('source_sha256', 'semantics_sha256', 'problem_contract_sha256')})
            for row, record in zip(self.policy['variants'], self.catalog['variants'])])
        self.assertEqual(self.catalog, before)
        self.assertFalse(metadata['qualification_created'])
        self.assertFalse(metadata['publication_authorized'])

    def test_all_selected_metadata_is_checked_before_first_source_request(self):
        for field, value in [('split', None), ('permission', 'protected'), ('permission', 'unresolved')]:
            with self.subTest(field=field, value=value):
                self.fixture(); self.admission['problems'][-1][field] = value
                with self.assertRaises(ValueError): self.load()
                self.service.request.assert_not_called()

    def test_qualification_does_not_replace_completed_development_admission(self):
        for field, value in [('development_corpus_admitted', False),
                             ('blockers', ['license_acceptance_not_established']),
                             ('license', None), ('adapter', None)]:
            with self.subTest(field=field):
                self.fixture()
                self.admission['problems'][-1]['implementations']['python'][field] = value
                with self.assertRaisesRegex(ValueError, 'completed source-to-guide'):
                    self.load()
                self.service.request.assert_not_called()

    def test_unknown_exposure_grouping_and_heldout_memberships_fail_closed(self):
        for mutate in [lambda row: row.update(exposure={'status': 'unknown'}),
                       lambda row: row.update(split='development_validation'),
                       lambda row: row['grouping'].update(problem_and_languages_together=False),
                       lambda row: row['grouping'].update(near_duplicate_closure='not_reviewed'),
                       lambda row: row['grouping'].update(group_id='other')]:
            with self.subTest(mutate=mutate):
                self.fixture(); mutate(self.admission['problems'][-1])
                with self.assertRaises(ValueError): self.load()
                self.service.request.assert_not_called()

    def test_group_cannot_cross_fit_and_validation_even_if_validation_unselected(self):
        self.fixture()
        self.admission['problems'][1]['grouping']['group_id'] = 'group-1'
        self.admission['problems'][1]['split'] = 'development_validation'
        self.policy['variants'] = self.policy['variants'][:1]
        with self.assertRaisesRegex(ValueError, 'group crosses'): self.load()
        self.service.request.assert_not_called()

    def test_source_presence_or_authoring_status_never_substitutes_for_qualification(self):
        self.fixture(); self.admission['problems'][1]['implementations']['python']['qualification']['receipt_binding_checked'] = False
        with self.assertRaisesRegex(ValueError, 'qualification join'): self.load()
        self.service.request.assert_not_called()

    def test_tampered_authoring_identity_rejected(self):
        self.fixture(); self.catalog['variants'][1]['semantics_sha256'] = '9' * 64
        with self.assertRaisesRegex(ValueError, 'authoring identity'): self.load()
        self.service.request.assert_not_called()

    def test_rehashed_variant_with_different_contract_is_not_canonical_qualification(self):
        self.fixture()
        record = self.catalog['variants'][1]
        record['problem_contract_sha256'] = '9' * 64
        identity = {k: record[k] for k in ('problem_id', 'language', 'source_sha256',
                                          'semantics_sha256', 'problem_contract_sha256')}
        record['variant_id'] = fitting.owner.sha(fitting.owner.canonical(identity).encode())
        self.policy['variants'][1]['variant_id'] = record['variant_id']
        with self.assertRaisesRegex(ValueError, 'qualification join'): self.load()
        self.service.request.assert_not_called()

    def test_duplicate_byte_variants_and_extra_language_are_not_read(self):
        self.fixture(); self.policy['variants'].append(dict(self.policy['variants'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.load()
        self.service.request.assert_not_called()
        self.policy['variants'].pop(); self.policy['variants'][1]['language'] = 'javascript'
        with self.assertRaises(ValueError): self.load()
        self.service.request.assert_not_called()

    def test_boundary_denial_is_before_any_payload_and_source_drift_is_retained(self):
        self.fixture(); self.boundary.authorize.side_effect = PermissionError('synthetic denied')
        with self.assertRaises(PermissionError): self.load()
        self.service.request.assert_not_called()
        self.boundary.authorize.side_effect = None
        self.service.request.side_effect = None
        self.service.request.return_value = {'artifact': {'status': 'materialized', 'source_utf8': 'drift', 'source_sha256': '0' * 64}}
        with self.assertRaisesRegex(ValueError, 'exact source bytes'): self.load()

    def test_config_and_policy_pins_cannot_be_rewritten_in_place(self):
        self.fixture(); spec = self.config()
        (self.root / 'policy.json').write_text('{}')
        with self.assertRaises(ValueError): fitting.load_fitting_inputs(spec['path'], spec['sha256'])
        self.service.request.assert_not_called()

    def test_cli_reports_pinned_population_and_full_costs_for_all_widths(self):
        self.fixture(); spec = self.config(); output = self.root / 'report'
        argv = ['idiom_pilot.py', '--config', spec['path'], '--config-sha256', spec['sha256'],
                '--output', str(output)]
        with patch('sys.argv', argv), redirect_stdout(StringIO()):
            idiom_pilot.main()
        contract = json.loads((output / 'contract.json').read_text())
        self.assertEqual(contract['fitting_inputs']['config_sha256'], spec['sha256'])
        self.assertEqual(contract['source_count'], 2)
        self.assertEqual(contract['objective'], 'compact')
        report = json.loads((output / 'summary.json').read_text())
        self.assertEqual(len(report['rows']), 40)
        self.assertEqual({row['arm'] for row in report['rows']}, {'strict', 'punctuation_fallback'})
        self.assertEqual({row['width'] for row in report['rows']}, set(range(4, 9)))
        for row in report['rows']:
            result = row['final']
            self.assertEqual(result['target'], 2)
            self.assertEqual(result['literal_bits'], result['selections'] * row['width'])
            self.assertEqual(result['singleton_bits'], result['singleton_selections'] * row['width'])
            self.assertEqual(result['package_bytes'], result['dictionary_bytes'] + result['packet_bytes'])
            self.assertFalse(result['milestone_qualified'])


if __name__ == '__main__':
    unittest.main()
