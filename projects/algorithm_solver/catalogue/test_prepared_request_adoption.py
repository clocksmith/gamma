"""Source-free synthetic controls; actual retained-run review is separate."""
import ast
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import public_batch_adapter as a
from .catalogue import digest


class PreparedRequestTests(unittest.TestCase):
    def test_fixed_thirty_ids_and_no_cross_lane_import(self):
        seen = []
        for lane in a.PREPARED_REQUESTS:
            owner = a.prepared_request_owner(lane)
            for pid in owner.IDS:
                oracle = a.prepared_request_oracle(lane, pid)
                self.assertIn(pid, oracle.IDS)
                self.assertEqual(len(oracle.CASES_SHA256[pid]), 64)
                seen.append(pid)
        self.assertEqual(len(seen), 30)
        self.assertEqual(len(set(seen)), 30)
        for lane in ('../../evil', '/tmp/owner.py', 'request-parallel-fgh15-v1', None, [], True):
            with self.subTest(lane=lane), self.assertRaises(ValueError):
                a.prepared_request_owner(lane)
        for lane, pid in [('request-next5-v1', 3223), ('request-parallel15-v1', 3514),
                          ('request-next5-v1', True), ('request-next5-v1', 3514.0),
                          ('request-parallel10-v1', 3514), ('request-next5-v1', 3513)]:
            with self.subTest(lane=lane, pid=pid), self.assertRaises(ValueError):
                a.prepared_request_oracle(lane, pid)

    def test_both_runs_required_before_artifact_reads(self):
        plan = {key: {} for key in ('universe', 'catalogue', 'receipts', 'execution_catalogue',
                'execution_receipts', 'predecessor_review', 'predecessor_authority_review',
                'boundary_gate', 'qualification_service', 'qualification_boundary_gate')}
        plan['schema'] = 'gamma.prepared-next20-adoption-plan.v1'
        bad = [[], [{'lane': 'request-next5-v1'}],
               [{'lane': 'request-parallel15-v1'}, {'lane': 'request-next5-v1'}],
               [{'lane': 'request-next5-v1'}, {'lane': 'request-next5-v1'}]]
        with patch.object(a, 'pinned', side_effect=AssertionError('must not read')):
            for runs in bad:
                with self.subTest(runs=runs), self.assertRaises(ValueError):
                    a.adopt_prepared_next20_plan({**plan, 'runs': runs}, 'a' * 64)

    def test_counts_do_not_substitute_for_predecessor_receipts(self):
        raw = {key: b'{"qualified":948}' for key in ('execution_catalogue', 'execution_receipts',
               'catalogue', 'receipts', 'predecessor_review', 'predecessor_authority_review')}
        with patch.object(a, 'validate', side_effect=AssertionError('must not validate')):
            with self.assertRaisesRegex(ValueError, 'identity'):
                a.check_next20_execution_delta({}, raw)

    def test_second_replay_failure_cannot_emit_partial_successor(self):
        plan = {key: {} for key in ('universe', 'catalogue', 'receipts', 'execution_catalogue',
                'execution_receipts', 'predecessor_review', 'predecessor_authority_review',
                'boundary_gate', 'qualification_service', 'qualification_boundary_gate')}
        plan.update(schema='gamma.prepared-next20-adoption-plan.v1',
                    runs=[{'lane': 'request-next5-v1'}, {'lane': 'request-parallel15-v1'}])
        with patch.object(a, 'pinned', return_value=({}, b'{}')), \
             patch.object(a, 'check_next20_execution_delta', return_value={}), \
             patch.object(a, 'replay_prepared_request', side_effect=[{}, ValueError('second replay failed')]), \
             patch.object(a, 'replace_canonicals', side_effect=AssertionError('must not construct')) as replace:
            with self.assertRaisesRegex(ValueError, 'second replay failed'):
                a.adopt_prepared_next20_plan(plan, 'a' * 64)
            replace.assert_not_called()

    def test_unrelated_lane_additions_do_not_relabel_runtime(self):
        current = Path(q.__file__).read_text()
        tree = ast.parse(current)
        next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'code_pins').body.append(ast.Pass())
        a.check_prepared_helper_compatibility(current, ast.unparse(ast.fix_missing_locations(tree)))
        a.check_prepared_helper_compatibility(current, current + '\n# Non-executable comment.\n')

    def test_import_and_global_rebinding_are_not_hidden_by_matching_function_ast(self):
        current = Path(q.__file__).read_text()
        for addition in ('\nimport json as hashlib\n', '\njson = None\n', '\ndef added_helper(): pass\n'):
            with self.subTest(addition=addition), self.assertRaises(ValueError):
                a.check_prepared_helper_compatibility(current, current + addition)

    def test_every_consumed_primitive_change_fails(self):
        original = Path(q.__file__).read_text()
        for name in ('encoded', 'sha', 'file_hash', 'unique', 'decode', 'read', 'canonical_tests_hash',
                     'exact', 'expected_type', 'packet', 'batches', 'source_interface'):
            tree = ast.parse(original)
            node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            node.body.append(ast.Pass())
            with self.subTest(name=name), self.assertRaises(ValueError):
                a.check_prepared_helper_compatibility(original, ast.unparse(ast.fix_missing_locations(tree)))

    def test_resource_changes_and_duplicate_helpers_fail(self):
        original = Path(q.__file__).read_text()
        for name in ('LIMITS', 'MAX_FILE', 'MAX_PACKET'):
            tree = ast.parse(original)
            node = next(n for n in tree.body if isinstance(n, ast.Assign) and
                        any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
            node.value = ast.Constant(value=0)
            with self.subTest(name=name), self.assertRaises(ValueError):
                a.check_prepared_helper_compatibility(original, ast.unparse(ast.fix_missing_locations(tree)))
        with self.assertRaises(ValueError):
            a.check_prepared_helper_compatibility(original, original + '\ndef sha(raw): return raw\n')

    def implementation(self, lane, pid):
        oracle = a.prepared_request_oracle(lane, pid)
        contract = {'reviewed_statement_contract': {'numeric_problem_id': pid, 'problem_id': f'leetcode:{pid}'},
                    'input_validator': {'lane': lane, 'module_sha256': a.sha(Path(oracle.__file__).read_bytes()),
                        'numeric_problem_id': pid, 'entrypoint': 'validate', 'required_before_candidate_execution': True}}
        return {'status': 'qualified', 'evidence_class': 'normative-typed-effects',
                'problem_contract_sha256': digest(contract), 'provenance': {'public_batch': {'problem_contract': contract}}}

    def test_existing_input_owner_supports_prepared_predicates(self):
        valid = {3514: [[1]], 3528: [[[0, 1, 1]]], 3566: [[1, 2, 3], 3], 3578: [[1, 1], 0],
                 3607: [1, [], [[1, 1]]], 3223: ['a'], 3232: [[1]],
                 3532: [1, [0], 0, [[0, 0]]], 3583: [[0, 0, 0]], 3612: ['a'],
                 3517: ['a'], 3531: [2, [[1, 1]]], 3567: [[[1]], 1], 3598: [['a']],
                 3618: [[1]], 3524: [[1], 1], 3551: [[1]], 3587: [[1]],
                 3608: [1, [], 1], 3619: [[[0]], 1],
                 3513: [[1]], 3522: [['add'], [1]], 3527: [[['a']]],
                 3546: [[[1, 1]]], 3572: [[1, 2, 3], [1, 1, 1]],
                 3227: ['a'], 3234: ['0'], 3556: ['2'], 3577: [[1, 2]], 3584: [[1], 1]}
        for lane in a.PREPARED_REQUESTS:
            for pid in a.prepared_request_owner(lane).IDS:
                with self.subTest(pid=pid):
                    result = a.validate_batch_inputs(self.implementation(lane, pid), valid[pid])
                    self.assertTrue(result['accepted'])
                    self.assertFalse(result['candidate_executed'])
                    with self.assertRaises(ValueError):
                        a.validate_batch_inputs(self.implementation(lane, pid), [])

    def test_normative_class_and_exact_oracle_bytes_required(self):
        original = self.implementation('request-next5-v1', 3514)
        for key, value in [('status', 'devtested'), ('evidence_class', 'frozen-admitted-typed-effects')]:
            changed = copy.deepcopy(original); changed[key] = value
            with self.assertRaises(ValueError):
                a.validate_batch_inputs(changed, [[1]])
        changed = copy.deepcopy(original)
        contract = changed['provenance']['public_batch']['problem_contract']
        contract['input_validator']['module_sha256'] = 'f' * 64
        changed['problem_contract_sha256'] = digest(contract)
        with self.assertRaises(ValueError):
            a.validate_batch_inputs(changed, [[1]])

    def test_code_population_checked_before_any_artifact_open(self):
        run = {'lane': 'request-next5-v1', 'native_bundle_root': '/native', 'artifact_root': '/local'}
        with patch.object(a, 'pinned', side_effect=AssertionError('must not read')):
            with self.assertRaises(ValueError):
                a.check_prepared_code(run, {'code': {}, 'additional_code': {}})


class PreparedNextTenTests(unittest.TestCase):
    def plan(self, runs=None):
        common = ('universe', 'catalogue', 'receipts', 'execution_catalogue',
                  'execution_receipts', 'predecessor_review', 'predecessor_authority_review',
                  'boundary_gate', 'qualification_service', 'qualification_boundary_gate')
        return {**{key: {} for key in common}, 'schema': 'gamma.prepared-next10-adoption-plan.v1',
                'runs': [{'lane': 'request-parallel10-v1'}] if runs is None else runs}

    def test_exact_next10_run_before_any_artifact_reads(self):
        for runs in ([], [{'lane': 'request-parallel15-v1'}],
                     [{'lane': 'request-parallel10-v1'}] * 2,
                     [{'lane': 'request-next5-v1'}, {'lane': 'request-parallel10-v1'}]):
            with self.subTest(runs=runs), patch.object(a, 'pinned', side_effect=AssertionError('must not read')), \
                 self.assertRaises(ValueError):
                a.adopt_prepared_next10_plan(self.plan(runs), 'a' * 64)

    def test_counts_are_not_a_predecessor_identity(self):
        raw = {key: b'{"qualified":968}' for key in ('execution_catalogue', 'execution_receipts',
               'catalogue', 'receipts', 'predecessor_review', 'predecessor_authority_review')}
        with patch.object(a, 'validate', side_effect=AssertionError('must not validate')), \
             self.assertRaisesRegex(ValueError, 'identity'):
            a.check_next10_execution_delta({}, raw)

    def test_next10_failure_never_constructs_partial_successor(self):
        with patch.object(a, 'pinned', return_value=({}, b'{}')), \
             patch.object(a, 'check_next10_execution_delta', return_value={}), \
             patch.object(a, 'replay_prepared_request', side_effect=ValueError('observation failed')), \
             patch.object(a, '_adopt_prepared_replays', side_effect=AssertionError('must not construct')) as build:
            with self.assertRaisesRegex(ValueError, 'observation failed'):
                a.adopt_prepared_next10_plan(self.plan(), 'a' * 64)
            build.assert_not_called()

    def test_next10_delta_failure_precedes_any_replay(self):
        with patch.object(a, 'pinned', return_value=({}, b'{}')), \
             patch.object(a, 'check_next10_execution_delta', side_effect=ValueError('old receipt changed')), \
             patch.object(a, 'replay_prepared_request', side_effect=AssertionError('must not replay')), \
             self.assertRaisesRegex(ValueError, 'old receipt changed'):
            a.adopt_prepared_next10_plan(self.plan(), 'a' * 64)

    def test_successful_replay_uses_existing_replacement_builder(self):
        replay = {'reviewed': 'synthetic'}
        with patch.object(a, 'pinned', return_value=({}, b'{}')), \
             patch.object(a, 'check_next10_execution_delta', return_value={'preserved': True}), \
             patch.object(a, 'replay_prepared_request', return_value=replay), \
             patch.object(a, '_adopt_prepared_replays', return_value={'sentinel': 1}) as build:
            self.assertEqual(a.adopt_prepared_next10_plan(self.plan(), 'a' * 64), {'sentinel': 1})
            self.assertEqual(build.call_args.args[-1], [replay])
            self.assertEqual(build.call_args.args[-2], {'preserved': True})

    def test_prepared_profile_requires_exact_native_code_before_reads(self):
        run = {'lane': 'request-parallel10-v1', 'native_bundle_root': '/native', 'artifact_root': '/local'}
        with patch.object(a, 'pinned', side_effect=AssertionError('must not read')), \
             self.assertRaisesRegex(ValueError, 'code population'):
            a.check_prepared_code(run, {'code': {}, 'additional_code': {}})

    def test_plan_dispatch_is_exact_and_not_the_old_lane(self):
        plan = self.plan()
        with patch.object(a, 'pinned', return_value=(plan, b'{}')), \
             patch.object(a, 'adopt_prepared_next10_plan', return_value='next10') as next10, \
             patch.object(a, 'adopt_prepared_next20_plan', side_effect=AssertionError('wrong owner')):
            self.assertEqual(a.adopt_plan('/synthetic/plan', 'a' * 64), 'next10')
            next10.assert_called_once_with(plan, 'a' * 64)

    def delta_fixture(self):
        # Tiny inert metadata fixture tests structural preservation, not real authority.
        old = {'problems': [{'problem_id': 'leetcode:1', 'implementations': {
            lang: {'status': 'blocked', 'reason': lang} for lang in a.LANGUAGES}},
            {'problem_id': 'leetcode:2', 'implementations': {
                lang: {'status': 'blocked', 'reason': 'unrelated'} for lang in a.LANGUAGES}}]}
        new = copy.deepcopy(old); old_receipts = {'retained': {'marker': 'unchanged'}}
        receipts = copy.deepcopy(old_receipts)
        for language in a.LANGUAGES:
            original = old['problems'][0]['implementations'][language]
            new['problems'][0]['implementations'][language] = {
                'status': 'qualified', 'evidence_class': 'normative-typed-effects', 'receipt_sha256': language,
                'provenance': {'previous_canonical': {'implementation': copy.deepcopy(original),
                    'implementation_sha256': digest(original)}}}
            receipts[language] = {'marker': language}
        values = {'universe': {}, 'execution_catalogue': old, 'catalogue': new,
                  'execution_receipts': old_receipts, 'receipts': receipts}
        raw = {key: key.encode() for key in ('execution_catalogue', 'execution_receipts',
               'catalogue', 'receipts', 'predecessor_review', 'predecessor_authority_review')}
        return values, raw, {key: a.sha(value) for key, value in raw.items()}

    def test_structural_delta_is_exact_reversible_and_nonmutating(self):
        values, raw, expected = self.delta_fixture(); before = copy.deepcopy(values)
        with patch.object(a, 'validate'):
            result = a._check_prepared_execution_delta(values, raw, expected, (1,))
        self.assertEqual(values, before)
        self.assertEqual(result['preserved_predecessor_receipts'], ['javascript', 'python'])
        self.assertEqual(result['original_receipts_preserved'], 1)
        self.assertEqual(result['unselected_execution_slots_unchanged'], 2)

    def test_delta_rejects_unrelated_slots_prior_receipts_and_missing_language(self):
        for mutation in ('unrelated', 'receipt', 'missing', 'archive', 'extra_receipt', 'class'):
            values, raw, expected = self.delta_fixture()
            if mutation == 'unrelated':
                values['catalogue']['problems'][1]['implementations']['python']['reason'] = 'changed'
            elif mutation == 'receipt':
                values['receipts']['retained']['marker'] = 'changed'
            elif mutation == 'missing':
                values['catalogue']['problems'][0]['implementations']['python'] = \
                    copy.deepcopy(values['execution_catalogue']['problems'][0]['implementations']['python'])
            elif mutation == 'archive':
                values['catalogue']['problems'][0]['implementations']['python']['provenance']['previous_canonical']['implementation']['reason'] = 'changed'
            elif mutation == 'extra_receipt':
                values['receipts']['unrelated'] = {'marker': 'extra'}
            else:
                values['catalogue']['problems'][0]['implementations']['python']['evidence_class'] = 'devtested'
            with self.subTest(mutation=mutation), patch.object(a, 'validate'), self.assertRaises(ValueError):
                a._check_prepared_execution_delta(values, raw, expected, (1,))


if __name__ == '__main__':
    unittest.main()
