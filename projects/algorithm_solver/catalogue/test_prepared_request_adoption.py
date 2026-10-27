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
    def test_fixed_twenty_ids_and_no_cross_lane_import(self):
        seen = []
        for lane in a.PREPARED_REQUESTS:
            owner = a.prepared_request_owner(lane)
            for pid in owner.IDS:
                oracle = a.prepared_request_oracle(lane, pid)
                self.assertIn(pid, oracle.IDS)
                self.assertEqual(len(oracle.CASES_SHA256[pid]), 64)
                seen.append(pid)
        self.assertEqual(len(seen), 20)
        self.assertEqual(len(set(seen)), 20)
        for lane in ('../../evil', '/tmp/owner.py', 'request-parallel10-v1', None, [], True):
            with self.subTest(lane=lane), self.assertRaises(ValueError):
                a.prepared_request_owner(lane)
        for lane, pid in [('request-next5-v1', 3223), ('request-parallel15-v1', 3514),
                          ('request-next5-v1', True), ('request-next5-v1', 3514.0)]:
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
                 3608: [1, [], 1], 3619: [[[0]], 1]}
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


if __name__ == '__main__':
    unittest.main()
