"""Source-free native2415 contracts and explicitly opt-in isolated controls.

Ordinary tests only inspect generic code, compare synthetic records, and mutate
trusted observer-owned Python nodes. They never load/execute imported sources or
probe isolation. GAMMA_ISOLATED_NATIVE2415_CONTROLS=1 is a separate approved run.
"""
import ast
import copy
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import imported_result_contracts as results
from . import node_identity_contracts as planner
from . import public_batch_adapter as adapter
from . import verify_imported_qualification as replay
from . import verify_imported_semantics as semantic
from . import verify_node_identity as independent


DIRECTORY = q.NODE_HARNESS.with_name('imported-node2415-observer-v1')
SPEC = importlib.util.spec_from_file_location('trusted_native2415_observer', DIRECTORY / 'harness.py')
OBSERVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OBSERVER)  # Generic observer definitions only; main is not invoked.


def job(language='python'):
    return {'id': 2415, 'language': language, 'node_identity': True, 'max_cases_per_batch': 1,
            'comparison_policy': 'problem:2415', 'source_interface':
            'native2415-global-solve-v1' if language == 'python' else 'native2415-commonjs-function-solve-v1'}


def fixture(values=None):
    values = [0, 1, 2, 3, 4, 5, 6] if values is None else values
    args = [{'__tree_node__': values}]
    native = OBSERVER.decode_args(args)
    return args, native, OBSERVER.capture_nodes(native)


def seven_record():
    args, native, finish = fixture()
    native[0].left.val, native[0].right.val = 2, 1
    record = {'i': 0, **finish(native[0])}
    return {'args': args, 'expected': {'__tree_node__': [0, 2, 1, 3, 4, 5, 6]}}, record


class InterfaceTests(unittest.TestCase):
    def test_exact_new_routes_and_historical_routes_remain_separate(self):
        for language, name in [('python', 'harness.py'), ('javascript', 'harness.cjs')]:
            self.assertEqual(q.observer_files(job(language)), {name: (DIRECTORY / name).read_bytes()})
            self.assertEqual(q.observer_files({'language': language, 'node_identity': True}),
                             {name: (q.NODE_HARNESS / name).read_bytes()})
            self.assertIn(str(DIRECTORY / name), q.code_pins())

    def test_invalid_profile_fails_before_source_case_or_gate_access(self):
        changes = [{'id': True}, {'id': '2415'}, {'id': 2326}, {'language': 'javascript'},
                   {'node_identity': 1}, {'node_identity': False}, {'max_cases_per_batch': True},
                   {'max_cases_per_batch': 2}, {'max_cases_per_batch': None}, {'comparison_policy': 'exact'},
                   {'source_interface': 'native2415-guess'}]
        for change in changes:
            with self.subTest(change=change), patch.object(q, 'read') as read, patch.object(q, 'authorize_before_open') as gate:
                with self.assertRaises(ValueError): q.job_inputs(Path('/unused'), {**job(), **change}, {})
                read.assert_not_called(); gate.assert_not_called()
        with self.assertRaises(ValueError): q.source_interface({**job('javascript'), 'language': 'python'})

    def test_fixed_owner_dispatch_rejects_other_interfaces_before_access(self):
        for changed in ({'id': 2326, 'source_interface': 'global-solve-v1'}, {'source_interface': 'global-solve-v1'}):
            with self.subTest(changed=changed), patch.object(q, 'read') as read, patch.object(q, 'authorize_before_open') as gate:
                with self.assertRaises(ValueError):
                    q.job_inputs(Path('/unused'), {**job(), 'domain_validator': 'request-native2415-v1', **changed}, {})
                read.assert_not_called(); gate.assert_not_called()

    def test_fixed_owner_additional_code_checked_before_service_or_payload(self):
        from . import request_native2415_qualification as owner
        contract = {'schema': 'gamma.imported-independent-execution.v1', 'code': {}, 'limits': q.LIMITS,
                    'jobs': [{'domain_validator': 'request-native2415-v1'}], 'additional_code': {}}
        with patch.object(q, 'read', return_value=b'{}') as read, patch.object(q, 'decode', return_value=contract), \
                patch.object(q, 'code_pins', return_value={}), patch.object(owner, 'additional_code', return_value={'owner': 'pin'}), \
                patch.object(q.KnownSpecService, 'from_config') as service:
            with self.assertRaisesRegex(ValueError, 'unapproved fixed native2415'): q.load_freeze(Path('/unused'))
            self.assertEqual(read.call_count, 1); service.assert_not_called()

    def versions(self):
        current = Path(q.__file__).read_text()
        tree = ast.parse(Path(adapter.__file__).read_text())
        checker = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'check_prepared_helper_compatibility')
        sources = []
        for name in ('approved_old', 'approved_new', 'approved_native'):
            template = next(n.value.value for n in ast.walk(checker) if isinstance(n, ast.Assign) and
                            any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
            replacements = {n.name: n for n in ast.parse(template).body}
            version = ast.parse(current)
            version.body = [replacements.get(n.name, n) if isinstance(n, ast.FunctionDef) else n for n in version.body]
            sources.append(ast.unparse(version))
        self.assertEqual(ast.dump(ast.parse(sources[-1])), ast.dump(ast.parse(current)))
        return sources

    def test_exact_forward_transitions_and_same_versions_only(self):
        versions = self.versions()
        for i, old in enumerate(versions):
            for j, new in enumerate(versions):
                if i <= j: adapter.check_prepared_helper_compatibility(old, new)
                else:
                    with self.assertRaises(ValueError): adapter.check_prepared_helper_compatibility(old, new)
        for old in versions[:-1]:
            for name in ('source_interface', 'observer_files'):
                tree = ast.parse(versions[-1])
                next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name).body.append(ast.Pass())
                with self.assertRaises(ValueError): adapter.check_prepared_helper_compatibility(old, ast.unparse(tree))
                partial = ast.parse(old)
                successor = next(n for n in ast.parse(versions[-1]).body if isinstance(n, ast.FunctionDef) and n.name == name)
                partial.body = [successor if isinstance(n, ast.FunctionDef) and n.name == name else n for n in partial.body]
                with self.assertRaises(ValueError): adapter.check_prepared_helper_compatibility(old, ast.unparse(partial))


class HistoricalEffectHelperBridgeTests(unittest.TestCase):
    def transitions(self):
        return {
            'imported_result_contracts.py': ('b601c7d128a1a21e85d605766ad7456142852c6fbcf18c431ec268ab99330d28',
                                            'a7b1a824263d026f589eaeaeeedff122b16f4e9efbd2ddd0e8b7c904aabbdbd0'),
            'node_identity_contracts.py': ('b829437e895c88d6049aac5d8de32593fb324551488c525ef082797e0ecb33c3',
                                          'bb8df1349fc0f3ebaba115171fa63ff990d3b181ced45a9ce6d9062444cd4567')}

    def test_only_exact_reviewed_forward_hash_pairs_are_permitted(self):
        # Synthetic retained bytes exercise dispatch without loading archived
        # modules. Real retained-byte/pin checks remain the caller's first step.
        for name, (old_pin, new_pin) in self.transitions().items():
            raw = Path(q.__file__).with_name(name).read_bytes()
            self.assertEqual(q.sha(raw), new_pin)
            adapter.check_prepared_effect_helper_compatibility('catalogue/' + name, raw, raw)
            with patch.object(adapter, 'sha', side_effect=[old_pin, new_pin]):
                adapter.check_prepared_effect_helper_compatibility('catalogue/' + name, b'synthetic old', raw)
            for before, after in ((new_pin, old_pin), ('0'*64, new_pin), (old_pin, q.sha(raw+b'\n')),
                                  (old_pin, '0'*64)):
                with self.subTest(name=name, before=before, after=after), patch.object(adapter, 'sha', side_effect=[before, after]):
                    with self.assertRaises(ValueError):
                        adapter.check_prepared_effect_helper_compatibility('catalogue/' + name, b'left', b'right')

    def test_neither_unknown_helpers_nor_cross_module_pairs_are_exempt(self):
        with self.assertRaises(ValueError):
            adapter.check_prepared_effect_helper_compatibility('catalogue/unknown.py', b'identical', b'identical')
        pairs = list(self.transitions().items())
        for name, _ in pairs:
            other = next(pins for candidate, pins in pairs if candidate != name)
            with patch.object(adapter, 'sha', side_effect=other), self.assertRaises(ValueError):
                adapter.check_prepared_effect_helper_compatibility('catalogue/' + name, b'left', b'right')


class PhysicalObservationTests(unittest.TestCase):
    def test_singleton_and_valid_value_only_changes(self):
        case, record = seven_record()
        self.assertIsNone(results.compare(2415, case, record, 'python'))
        self.assertIsNone(semantic.compare(2415, case, record, 'python'))
        args, native, finish = fixture([100000])
        self.assertEqual(finish(native[0])['args_after'], args)

    def test_duplicate_value_replacement_subtree_swap_root_cycle_extra_fields(self):
        for corruption in ('replacement', 'swap', 'root', 'cycle', 'extra', 'class', 'wrong-value-type'):
            with self.subTest(corruption=corruption):
                _, native, finish = fixture([5] * 7); root = native[0]; result = root
                if corruption == 'replacement': root.left = OBSERVER.TreeNode(5, root.left.left, root.left.right)
                elif corruption == 'swap': root.left, root.right = root.right, root.left
                elif corruption == 'root': result = OBSERVER.TreeNode(5, root.left, root.right)
                elif corruption == 'cycle': root.left.left = root
                elif corruption == 'extra': root.__dict__['hidden'] = 1
                elif corruption == 'class':
                    class Replacement: pass
                    root.__class__ = Replacement
                elif corruption == 'wrong-value-type': root.val = True
                with self.assertRaises((ValueError, TypeError)): finish(result)

    def test_class_descriptor_changes_fail_without_invoking_accessor(self):
        for key, value in [('val', property(lambda self: self.__dict__['val'])),
                           ('hidden', 1), ('__getattribute__', lambda self, key: object.__getattribute__(self, key))]:
            with self.subTest(key=key):
                _, native, finish = fixture()
                setattr(OBSERVER.TreeNode, key, value)
                try:
                    with self.assertRaises(TypeError): finish(native[0])
                finally: delattr(OBSERVER.TreeNode, key)

    def test_type_managed_class_metadata_changes_are_not_hidden(self):
        for key in ('__name__', '__qualname__'):
            with self.subTest(key=key):
                _, native, finish = fixture(); original = getattr(OBSERVER.TreeNode, key)
                setattr(OBSERVER.TreeNode, key, 'Replacement')
                try:
                    with self.assertRaises(TypeError): finish(native[0])
                finally: setattr(OBSERVER.TreeNode, key, original)

    def test_domain_rejections(self):
        for values in ([], [1, 2], [1, None, 2], [True], [1.0], [-1], [100001], [0] * 32767):
            with self.subTest(size=len(values)), self.assertRaises(ValueError): OBSERVER.decode_args([{'__tree_node__': values}])
        for args in ([], [{'__tree_node__': [1], 'extra': 2}], [{'__list_node__': [1]}]):
            with self.assertRaises(ValueError): OBSERVER.decode_args(args)

    def test_full_domain_transport_is_bounded_without_executing_a_solution(self):
        # An equal-valued perfect tree needs no candidate transformation. This
        # tests the generic representation only, not runtime qualification.
        args, native, finish = fixture([100000] * 16383)
        record = {'i': 0, **finish(native[0])}; case = {'args': args, 'expected': args[0]}
        self.assertEqual(len(record['node_identity']['after']), 16383)
        self.assertIsNone(results.compare(2415, case, record, 'python'))
        self.assertIsNone(semantic.compare(2415, case, record, 'python'))
        self.assertLess(len(q.encoded(q.packet([case], True))), q.MAX_PACKET)
        self.assertLess(len(q.encoded(record)) + len(q.encoded({'done': 1})), q.LIMITS['max_output_bytes'])
        self.assertNotIn(b'expected', q.encoded(q.packet([case], True)))


class HostEffectsTests(unittest.TestCase):
    def test_multiple_odd_levels_and_independent_pairing(self):
        args = [{'__tree_node__': list(range(31))}]
        expected = [0, 2, 1, 3, 4, 5, 6, 14, 13, 12, 11, 10, 9, 8, 7] + list(range(15, 31))
        witness = planner.plan(2415, args)
        self.assertEqual([n['value'] for n in witness['after']], expected)
        record = {'node_identity': witness, 'result': {'__tree_node__': expected}, 'args_before': args, 'args_after': [{'__tree_node__': expected}],
                  'alias_edges': [['result', 'args.0']], 'node_integrity': {
                      'schema': 'gamma.native2415-node-integrity.v1', 'node_count': 31,
                      'class_or_prototype_unchanged': True, 'own_field_descriptors_unchanged': True}}
        with patch.object(planner, 'plan', side_effect=AssertionError('independent verifier imported execution planner')):
            self.assertIsNone(independent.check(2415, args, record))

    def test_forged_or_inconsistent_records_fail_both_owners(self):
        for corruption in ('missing-integrity', 'false-prototype', 'false-descriptor', 'extra-integrity', 'boolean-count',
                           'changed-edge', 'boolean-edge', 'extra-node', 'missing-node', 'root', 'value', 'before', 'alias', 'args-after', 'result-padding'):
            case, record = seven_record()
            if corruption == 'missing-integrity': del record['node_integrity']
            elif corruption == 'false-prototype': record['node_integrity']['class_or_prototype_unchanged'] = False
            elif corruption == 'false-descriptor': record['node_integrity']['own_field_descriptors_unchanged'] = False
            elif corruption == 'extra-integrity': record['node_integrity']['unreviewed'] = True
            elif corruption == 'boolean-count': record['node_integrity']['node_count'] = True
            elif corruption == 'changed-edge': record['node_identity']['after'][0]['left'] = 2
            elif corruption == 'boolean-edge': record['node_identity']['after'][0]['left'] = True
            elif corruption == 'extra-node': record['node_identity']['after'].append(copy.deepcopy(record['node_identity']['after'][-1]))
            elif corruption == 'missing-node': record['node_identity']['after'].pop()
            elif corruption == 'root': record['node_identity']['result_root'] = False
            elif corruption == 'value': record['node_identity']['after'][1]['value'] = 1
            elif corruption == 'before': record['node_identity']['before'][0]['value'] = 2
            elif corruption == 'alias': record['alias_edges'] = []
            elif corruption == 'args-after': record['args_after'] = case['args']
            elif corruption == 'result-padding': record['result']['__tree_node__'].append(None)
            for compare in (results.compare, semantic.compare):
                with self.subTest(corruption=corruption, owner=compare.__module__):
                    self.assertIsNotNone(compare(2415, case, record, 'python'))

    def test_legacy_type_value_and_error_failures_stay_explicit(self):
        case, original = seven_record()
        for change, failure in [({'result_type': 'dict'}, 'result_type'), ({'result': {'__tree_node__': [0]}}, 'result_value'),
                                ({'error': 'physical corruption'}, 'candidate_error')]:
            for compare in (results.compare, semantic.compare):
                self.assertEqual(compare(2415, case, {**original, **change}, 'python'), failure)


@unittest.skipUnless(os.environ.get('GAMMA_ISOLATED_NATIVE2415_CONTROLS') == '1',
                     'explicit approved isolated native2415 controls required')
class IsolatedSyntheticControls(unittest.TestCase):
    def run_control(self, language, source, values, failure):
        route = os.environ.get('GAMMA_PINNED_NODE_RUNTIME'); node_runtime = Path(route) if route else None
        identity = q.runtime(node_runtime)
        case = {'args': [{'__tree_node__': values}], 'expected': {'__tree_node__': values}, 'compare': 'return'}
        name = 'program.py' if language == 'python' else 'program.js'
        files = {name: source.encode(), **q.observer_files(job(language)), 'inputs.json': q.encoded(q.packet([case], True))}
        observed = q.run_batch(language, files, identity, node_runtime)
        self.assertTrue(observed.ok, observed.stderr.decode(errors='replace'))
        wanted = [] if failure is None else [{'index': 0, 'reason': failure}]
        self.assertEqual(q.check_output(observed.stdout, [case], language, 'problem:2415'), wanted)
        self.assertEqual(replay.independent_failures(observed.stdout, [case], language, 'problem:2415'), wanted)
        q.verify_runtime({'runtime': identity}, node_runtime)

    def test_javascript_physical_corruptions(self):
        bodies = ['root.left={...root.left};', '[root.left,root.right]=[root.right,root.left];',
                  'return {...root};', 'Object.setPrototypeOf(root, {});',
                  'Object.defineProperty(root,"val",{writable:false});',
                  'Object.defineProperty(root,"val",{enumerable:false});',
                  'Object.defineProperty(root,"left",{configurable:false});',
                  'Object.defineProperty(root,"val",{get(){return 5;}});',
                  'Object.defineProperty(root,"hidden",{value:1});', 'root[Symbol("hidden")]=1;',
                  'Object.prototype.native2415Extra=1;', 'root.left.left=root;', 'root.extra=1;']
        for body in bodies:
            with self.subTest(body=body):
                self.run_control('javascript', 'module.exports=function(root){'+body+'return root;};', [5]*7, 'candidate_error')

    def test_python_physical_corruptions(self):
        bodies = ['root.left=type(root)(5,root.left.left,root.left.right)', 'root.left,root.right=root.right,root.left',
                  'return type(root)(5,root.left,root.right)', 'root.__class__=type("Other",(),{})',
                  'type(root).val=property(lambda self:5)', 'type(root).hidden=1',
                  'type(root).__name__="Replacement"', 'type(root).__qualname__="Replacement"',
                  'root.left.left=root', 'root.extra=1']
        for body in bodies:
            with self.subTest(body=body):
                self.run_control('python', 'def solve(root):\n    '+body+'\n    return root\n', [5]*7, 'candidate_error')

    def test_valid_maximum_tree_in_each_language(self):
        for language, source in [('python', 'def solve(root):\n    return root\n'),
                                 ('javascript', '"use strict";module.exports=function(root){if(this!==undefined)throw Error("receiver");return root;};')]:
            with self.subTest(language=language): self.run_control(language, source, [100000]*16383, None)
