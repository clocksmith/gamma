"""Synthetic metadata/observations only: no candidate or private case execution."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import admitted_gap_adapter as a
from .catalogue import BINDINGS, digest, validate


class AdmittedGapAdapterTests(unittest.TestCase):
    def fixture(self):
        sources = {i: f'# synthetic source {i}\n'.encode() for i in a.GAP_IDS}
        semantics = {i: a.encoded({'problem_id': i, 'entry_point': 'solve', 'language': 'python'}) for i in a.GAP_IDS}
        pins = {p: a.sha(p.encode()) for p in a.CODE_PATHS}
        source_rows = {str(i): {'path': f'{i}.py', 'method': 'solve', 'bytes': len(sources[i]),
                              'sha256': a.sha(sources[i]), 'semantics_sha256': a.sha(semantics[i]),
                              'reference_source_sha256': a.sha(f'js {i}'.encode())} for i in a.GAP_IDS}
        freezes = {}
        for name, population in [('pending', [i for i in a.GAP_IDS if i not in (1152, 1165)]), ('done', [1152, 1165])]:
            freezes[name] = {'schema': 'gamma.python.compatibility-source-freeze.v1', 'ids': population,
                            'sources': {str(i): source_rows[str(i)] for i in population}, 'partition': 'dev_fit',
                            'code_sha256': pins, 'source_frozen_before_replay': True, 'dictionary_fitting_allowed': False,
                            'evidence_class': a.COMPAT, 'normative_domain_resolved': False,
                            'protected_access': False, 'm1_qualified': False}
        js = {'implementations': {}, 'binding_descriptors': {}, 'verified_receipts': {}}
        inputs = {str(i): {'cases': a.sha(f'cases {i}'.encode()), 'baseline': a.sha(f'base {i}'.encode()),
                          'source': source_rows[str(i)]['reference_source_sha256']} for i in a.GAP_IDS}
        for i in a.GAP_IDS:
            key = f'development400:{i}'
            contract = {'schema': 'gamma.existing-javascript-admission-binding.v1',
                        'numeric_development_id': i, 'qualification_contract_sha256': '1'*64,
                        'tests_sha256': inputs[str(i)]['cases'],
                        'behavior_effects_sha256': inputs[str(i)]['baseline'],
                        'admitted_reference_sha256': inputs[str(i)]['source'], 'frozen_input_manifest_sha256': 'a'*64}
            effects = {'host_judge_sha256': pins['algsolve/judge/judge.py'],
                       'historical_observation_sha256': inputs[str(i)]['baseline']}; runtime = {'recorded': 'b'*64}
            interface = {'schema': 'gamma.call-interface.v1', 'entrypoint': 'solve', 'arguments': 'ordered-positional',
                         'typed_contract': digest(contract)}
            impl = {'status': 'qualified', 'source_sha256': inputs[str(i)]['source'], 'problem_contract_sha256': digest(contract),
                    'tests_sha256': inputs[str(i)]['cases'], 'effects_sha256': digest(effects), 'runtime_sha256': digest(runtime),
                    'interface': interface, 'interface_sha256': digest(interface), 'canonical_variant_id': 'js:' + str(i),
                    'evidence_class': a.EVIDENCE, 'contract_scope': 'synthetic admitted scope', 'caveats': ['Finite only'],
                    'provenance': {'case_count': 1, 'qualification_contract_sha256': '1'*64}}
            receipt = {k: impl[k] for k in (*BINDINGS, 'canonical_variant_id', 'evidence_class', 'contract_scope', 'caveats')}
            receipt.update(problem_id=key, language='javascript', verdict='qualified', independent_verifier=True,
                           provenance_sha256=digest(impl['provenance']))
            impl['receipt_sha256'] = digest(receipt); js['implementations'][key] = impl
            js['verified_receipts'][digest(receipt)] = receipt
            js['binding_descriptors'][key] = {'problem_contract': contract, 'effects': effects, 'runtime': runtime}
        run = {'schema': 'gamma.python.compatibility-runtime-replay.v1', 'ids': [1152, 1165],
               'source_freeze_sha256': '', 'code_sha256': pins, 'limits': dict(a.LIMITS), 'batch_cases': 32,
               'max_wall_seconds': 600, 'python_runtime_sha256': 'c'*64, 'input_manifest_sha256': 'a'*64,
               'input_hashes': {str(i): inputs[str(i)] for i in (1152, 1165)}, 'protected_access': False, 'm1_qualified': False}
        rows = [{'id': i, 'cases': 1, 'checks_passed': 1, 'passed': True, 'failures': [],
                 'calls': [{'stem': f'{i}-0', 'exit_code': 0, 'timed_out': False, 'output_limit_exceeded': False,
                            'stdout_sha256': 'd'*64, 'stderr_sha256': 'e'*64}]} for i in (1152, 1165)]
        report = {'schema': run['schema'], 'contract_sha256': '', 'status': 'completed', 'qualified': 0, 'compatible': 2,
                  'rows': rows, 'checks_passed': 2, 'candidate_executions': 2, 'evidence_class': a.COMPAT,
                  'normative_domain_resolved': False, 'protected_access': False, 'm1_qualified': False}
        verified = {'schema': 'gamma.python.compatibility-independent-verification.v1', 'report_sha256': '', 'verified': True,
                    'compatible_ids': [1152, 1165], 'failed_ids': [], 'blocked_ids': [], 'programs': 2, 'qualified': 0,
                    'compatible': 2, 'checks': 2, 'executions': 2, 'evidence_class': a.COMPAT,
                    'normative_domain_resolved': False, 'protected_access': False, 'm1_qualified': False}
        return {'js': js, 'freezes': freezes, 'run': run, 'report': report, 'verified': verified,
                'sources': sources, 'semantics': semantics}

    def arguments(self, fixture):
        f = copy.deepcopy(fixture)
        freezes = {k: a.encoded(v) for k, v in f['freezes'].items()}
        f['run']['source_freeze_sha256'] = a.sha(freezes['done'])
        run = a.encoded(f['run']); f['report']['contract_sha256'] = a.sha(run)
        report = a.encoded(f['report']); f['verified']['report_sha256'] = a.sha(report)
        replays = {'done': {'run': run, 'report': report, 'verified': a.encoded(f['verified'])}}
        js = a.encoded(f['js'])
        hashes = {'javascript': a.sha(js), **{'freeze:' + k: a.sha(v) for k, v in freezes.items()},
                  **{'done:' + k: a.sha(v) for k, v in replays['done'].items()}}
        return (js, freezes, replays, f['sources'], f['semantics']), {'trusted_hashes': hashes, 'allowed_ids': list(a.GAP_IDS)}

    def review(self, fixture=None):
        args, kw = self.arguments(fixture or self.fixture())
        return a.review_gap(*args, **kw)

    def approval(self, review, selected=(1152, 1165)):
        raw = a.encoded(review)
        approval = {'schema': 'gamma.python-admitted-gap-approval.v1', 'decision': 'approve',
                    'scope': 'exact-reviewed-frozen-admitted-typed-effects', 'review_sha256': a.sha(raw),
                    'approved_ids': list(selected), 'approver': 'root-delegate', 'normative_domain_resolved': False,
                    'protected_access': False, 'publication_authorized': False}
        ar = a.encoded(approval)
        return raw, ar, {'trusted_review_sha256': a.sha(raw), 'trusted_approval_sha256': a.sha(ar)}

    def test_review_never_qualifies_and_six_unrun_remain_blocked(self):
        r = self.review()
        self.assertEqual(r['qualified'], 0); self.assertFalse(r['adoption_authorized'])
        self.assertEqual(r['ready_ids'], [1152, 1165]); self.assertEqual(len(r['blocked_ids']), 6)
        for p in r['proposals'].values():
            self.assertNotEqual(p.get('implementation', {}).get('status'), 'qualified')

    def test_explicit_adoption_binds_same_js_contract_and_valid_catalogue(self):
        f = self.fixture(); review = self.review(f); raw, ar, kw = self.approval(review)
        out = a.adopt_review(raw, ar, **kw)
        for key, impl in out['implementations'].items():
            self.assertEqual(impl['problem_contract_sha256'], f['js']['implementations'][key]['problem_contract_sha256'])
            self.assertEqual(impl['interface']['typed_contract'], impl['problem_contract_sha256'])
            self.assertFalse(impl['provenance']['normative_domain_resolved'])
        universe = {'schema': 'gamma.catalogue-universe.v1', 'eligible_problem_ids': list(out['implementations']),
                    'protected_problem_ids': [], 'metadata_sha256': 'f'*64, 'eligibility_policy': 'synthetic only'}
        catalogue = {'schema': 'gamma.dual-language-catalogue.v2', 'universe_sha256': digest(universe),
                     'evidence_policy': {'schema': 'gamma.catalogue-evidence-policy.v1', 'allowed_classes': [a.EVIDENCE],
                                         'scope_rule': 'exact-bound-contract-only'},
                     'problems': [{'problem_id': k, 'implementations': {'python': v, 'javascript': f['js']['implementations'][k]}}
                                  for k, v in out['implementations'].items()]}
        receipts = dict(f['js']['verified_receipts']); receipts.update(out['verified_receipts'])
        self.assertTrue(validate(universe, catalogue, receipts)['complete_dual_language_catalogue'])
        self.assertFalse(out['current_serving_runtime_verified']); self.assertFalse(out['publication_authorized'])

    def test_caveats_are_receipt_bound(self):
        r = self.review(); raw, ar, kw = self.approval(r); out = a.adopt_review(raw, ar, **kw)
        impl = out['implementations']['development400:1152']
        self.assertTrue(any('ASCII' in c and 'UTF16' in c for c in impl['caveats']))
        self.assertEqual(out['verified_receipts'][impl['receipt_sha256']]['caveats'], impl['caveats'])

    def test_no_approval_or_wrong_external_approval_hash(self):
        raw, ar, kw = self.approval(self.review())
        for replacement in (None, 'f'*64):
            kw['trusted_approval_sha256'] = replacement
            with self.assertRaises(ValueError): a.adopt_review(raw, ar, **kw)

    def test_cannot_approve_unrun_or_non_gap_probe(self):
        for selected in ([252], [955]):
            raw, ar, kw = self.approval(self.review(), selected)
            with self.assertRaises(ValueError): a.adopt_review(raw, ar, **kw)

    def test_unknown_approval_field_and_claim_escalation(self):
        raw, ar, kw = self.approval(self.review())
        for key, value in [('new_authority', True), ('publication_authorized', True), ('normative_domain_resolved', True)]:
            approval = a.parse(ar); approval[key] = value; changed = a.encoded(approval)
            kw['trusted_approval_sha256'] = a.sha(changed)
            with self.assertRaises(ValueError): a.adopt_review(raw, changed, **kw)

    def test_original_compatibility_flags_cannot_be_relabeled(self):
        for target in ('report', 'verified'):
            f = self.fixture(); f[target]['qualified'] = 2
            with self.assertRaises(ValueError): self.review(f)

    def test_input_and_manifest_and_reference_mismatch_rejected(self):
        for kind in ('cases', 'baseline', 'source', 'manifest'):
            f = self.fixture()
            if kind == 'manifest': f['run']['input_manifest_sha256'] = 'f'*64
            else: f['run']['input_hashes']['1152'][kind] = 'f'*64
            with self.assertRaises(ValueError): self.review(f)

    def test_source_semantics_and_freeze_drift(self):
        for name in ('sources', 'semantics'):
            f = self.fixture(); f[name][1152] += b' '
            with self.assertRaises(ValueError): self.review(f)
        args, kw = self.arguments(self.fixture()); args[1]['done'] += b' '
        with self.assertRaises(ValueError): a.review_gap(*args, **kw)

    def test_missing_batches_effect_bindings_and_failed_process(self):
        for change in ('calls', 'hash', 'process', 'checks'):
            f = self.fixture(); row = f['report']['rows'][0]
            if change == 'calls': row['calls'] = []
            elif change == 'hash': row['calls'][0]['stdout_sha256'] = None
            elif change == 'process': row['calls'][0]['timed_out'] = True
            else: row['checks_passed'] = 0
            with self.assertRaises(ValueError): self.review(f)

    def test_failed_native_row_retained_not_promoted(self):
        f = self.fixture(); row = f['report']['rows'][0]
        row.update(checks_passed=0, passed=False, failures=[{'case_index': 0, 'effect_type_parity': False}])
        f['report'].update(compatible=1, checks_passed=1)
        f['verified'].update(compatible_ids=[1165], failed_ids=[1152], compatible=1, checks=1)
        r = self.review(f); self.assertEqual(r['ready_ids'], [1165]); self.assertIn(1152, r['blocked_ids'])
        raw, ar, kw = self.approval(r, [1152])
        with self.assertRaises(ValueError): a.adopt_review(raw, ar, **kw)

    def test_population_duplicate_omission_and_unauthorized(self):
        f = self.fixture(); f['verified']['failed_ids'] = [1152]
        with self.assertRaises(ValueError): self.review(f)
        args, kw = self.arguments(self.fixture()); kw['allowed_ids'] = [i for i in a.GAP_IDS if i != 1152]
        with self.assertRaises(ValueError): a.review_gap(*args, **kw)

    def test_runtime_harness_and_js_receipt_drift(self):
        for kind in ('runtime', 'harness', 'js'):
            f = self.fixture()
            if kind == 'runtime': f['run']['limits']['cpu_seconds'] = 5
            elif kind == 'harness': del f['run']['code_sha256']['literals/python-compat-replay-v1/harness.py']
            else: f['js']['implementations']['development400:1152']['source_sha256'] = 'f'*64
            with self.assertRaises(ValueError): self.review(f)

    def test_strict_json_and_bool_ids(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.assertRaises(ValueError): a.parse(raw)
        with self.assertRaises(ValueError): a.ids([True])
        f = self.fixture(); f['report']['rows'][0]['cases'] = True
        with self.assertRaises(ValueError): self.review(f)

    def test_full_verifier_rejects_unauthorized_ids_before_freeze_or_subprocess(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root); run = a.encoded({'ids': [99999], 'source_freeze': '/must-not-open'})
            report = a.encoded({'status': 'completed'})
            (p/'contract.json').write_bytes(run); (p/'report.json').write_bytes(report)
            with patch.object(a.subprocess, 'run') as execute:
                with self.assertRaisesRegex(ValueError, 'BEFORE payload'):
                    a.reverify_original_report(p, p, p/'report.json', allowed_ids=list(a.GAP_IDS),
                                               trusted_hashes={'run': a.sha(run), 'report': a.sha(report)})
                execute.assert_not_called()

    def test_existing_adapter_still_rejects_compatibility(self):
        from .python_receipt_adapter import SCHEMAS
        self.assertNotIn('gamma.python.compatibility-runtime-replay.v1', SCHEMAS)

    def test_original_comparator_checks_return_type_and_every_effect(self):
        # Import trusted judge/checker code, never candidate code or private cases.
        import importlib.util
        path = Path(__file__).resolve().parents[1] / 'literals/python-compat-replay-v1/qualify.py'
        spec = importlib.util.spec_from_file_location('admitted_gap_synthetic_checker', path)
        checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
        case = {'args': [[1]], 'expected': True}
        baseline = {'result': True, 'result_type': 'boolean', 'args_before': [[1]], 'args_after': [[1]], 'alias_edges': []}
        record = dict(baseline, result_type='bool')
        self.assertEqual(checker.compare(case, record, baseline), (True, True))
        for field in ('result', 'result_type', 'args_before', 'args_after', 'alias_edges'):
            changed = copy.deepcopy(record); changed.pop(field)
            self.assertNotEqual(checker.compare(case, changed, baseline), (True, True))
        for field, value in [('result', 1), ('result_type', 'int'), ('args_before', [[2]]),
                             ('args_after', [[2]]), ('alias_edges', [[0, 1]]), ('error', 'synthetic failure')]:
            changed = copy.deepcopy(record); changed[field] = value
            self.assertNotEqual(checker.compare(case, changed, baseline), (True, True))


if __name__ == '__main__':
    unittest.main()
