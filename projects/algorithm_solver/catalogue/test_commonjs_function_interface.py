"""Source-free loader contracts plus explicitly selected isolated controls.

The ordinary unit suite never executes a submitted algorithm. Native synthetic
loader controls run only when GAMMA_ISOLATED_LOADER_CONTROLS=1 is explicitly set
on an approved executor; sandbox failure is a failure, not a fallback request.
"""
import ast
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import public_batch_adapter as adapter
from . import verify_imported_qualification as verifier


class InterfaceBoundaryTests(unittest.TestCase):
    def test_new_mode_uses_only_existing_observer_and_new_named_loader(self):
        job = {'language': 'javascript', 'source_interface': 'commonjs-function-solve-v1'}
        self.assertEqual(q.observer_files(job), {
            'harness.cjs': q.read(q.COMMONJS_HARNESS.with_name('function-harness.cjs')),
            'observer.cjs': q.read(q.HARNESS / 'harness.cjs')})
        self.assertEqual(q.observer_files({'language': 'javascript', 'source_interface': 'commonjs-object-solve-v1'}), {
            'harness.cjs': q.read(q.COMMONJS_HARNESS), 'observer.cjs': q.read(q.HARNESS / 'harness.cjs')})

    def test_invalid_routes_fail_before_payloads_or_authorization(self):
        for changes in ({'language': 'python'}, {'node_identity': True}, {'source_interface': 'guess'}):
            job = {'id': 2110, 'language': 'javascript', 'source_interface': 'commonjs-function-solve-v1', **changes}
            with self.subTest(changes=changes), patch.object(q, 'read') as read, patch.object(q, 'authorize_before_open') as gate:
                with self.assertRaises(ValueError):
                    q.job_inputs(Path('/unused'), job, {})
                read.assert_not_called(); gate.assert_not_called()

    def test_code_pins_include_both_loaders_without_rewriting_old_observer(self):
        pins = q.code_pins()
        self.assertIn(str(q.COMMONJS_HARNESS.with_name('function-harness.cjs')), pins)
        self.assertEqual(pins[str(q.COMMONJS_HARNESS)], '55ff4173f9dab55de26dcfe502f60b33ecac96fd3ec9689b150cba58daa4b547')

    def test_added_mode_keeps_the_inputs_only_transport(self):
        cases = [{'args': [[3, 4]], 'expected': 987654321, 'compare': 'return'}]
        self.assertEqual(q.packet(cases)['calls'], [{'args': [[3, 4]]}])
        self.assertNotIn(b'987654321', q.encoded(q.packet(cases)))


class HistoricalInterfaceBridgeTests(unittest.TestCase):
    def pair(self):
        current = Path(q.__file__).read_text()
        checker = ast.parse(Path(adapter.__file__).read_text())
        function = next(n for n in checker.body if isinstance(n, ast.FunctionDef) and n.name == 'check_prepared_helper_compatibility')
        old_template = next(n.value.value for n in ast.walk(function) if isinstance(n, ast.Assign)
                            and any(isinstance(t, ast.Name) and t.id == 'approved_old' for t in n.targets))
        replacements = {n.name: n for n in ast.parse(old_template).body}
        legacy = ast.parse(current)
        legacy.body = [replacements.get(n.name, n) if isinstance(n, ast.FunctionDef) else n for n in legacy.body]
        return ast.unparse(legacy), current

    def changed(self, source, name):
        tree = ast.parse(source)
        next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name).body.append(ast.Pass())
        return ast.unparse(ast.fix_missing_locations(tree))

    def test_exact_atomic_transition_and_same_version_are_accepted(self):
        old, new = self.pair()
        for left, right in ((old, old), (new, new), (old, new), (old, ast.unparse(ast.parse(new)))):
            adapter.check_prepared_helper_compatibility(left, right)

    def test_reverse_partial_and_mutated_interfaces_are_not_accepted(self):
        old, new = self.pair()
        old_tree, new_tree = ast.parse(old), ast.parse(new)
        replacement = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'source_interface')
        old_tree.body = [replacement if isinstance(n, ast.FunctionDef) and n.name == 'source_interface' else n for n in old_tree.body]
        for left, right in ((new, old), (old, ast.unparse(old_tree)),
                            (old, self.changed(new, 'source_interface')), (old, self.changed(new, 'observer_files'))):
            with self.assertRaises(ValueError):
                adapter.check_prepared_helper_compatibility(left, right)

    def test_only_original_three_dispatch_exemptions_survive(self):
        old, new = self.pair()
        for name in ('code_pins', 'load_freeze', 'job_inputs'):
            adapter.check_prepared_helper_compatibility(old, self.changed(new, name))
        for name in ('encoded', 'sha', 'decode', 'read', 'exact', 'packet', 'batches', 'run_batch', 'runtime', 'execute'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                adapter.check_prepared_helper_compatibility(old, self.changed(new, name))
        for addition in ('\nimport json as hashlib\n', '\njson=None\n', '\ndef new_helper(): pass\n'):
            with self.subTest(addition=addition), self.assertRaises(ValueError):
                adapter.check_prepared_helper_compatibility(old, new + addition)


def synthetic_fixtures():
    """Synthetic interface controls, never imported problem candidates."""
    direct = 'commonjs-function-solve-v1'; obj = 'commonjs-object-solve-v1'
    rows = [
        ('strict-receiver', direct, '"use strict";module.exports=function(a,b){if(this!==undefined)throw Error("receiver");return a+b;};', [3, 4], 7, None),
        ('pure-array', direct, 'module.exports=function(a){return a[0]+a[1];};', [[3, 4]], 7, None),
        ('mutation', direct, 'module.exports=function(a){a[0]=8;return 7;};', [[3, 4]], 7, 'input_effects'),
        ('alias', direct, 'module.exports=function(a){return a;};', [[3, 4]], [3, 4], 'return_aliases'),
        ('bool', direct, 'module.exports=function(){return true;};', [], 1, 'result_type'),
        ('unsafe-number', direct, 'module.exports=function(){return 9007199254740992;};', [], 0, 'candidate_error'),
        ('old-mode-rejects-function', obj, 'module.exports=function(a){return a;};', [7], 7, 'execution'),
        ('old-object-receiver', obj, 'module.exports={base:3,solve:function(a){return this.base+a;}};', [4], 7, None),
    ]
    for label, source in [('object', 'module.exports={solve:function(a){return a;}};'),
                          ('null', 'module.exports=null;'), ('scalar', 'module.exports=7;'), ('empty', 'module.exports={};')]:
        rows.append(('reject-' + label, direct, source, [], 0, 'execution'))
    return rows


@unittest.skipUnless(os.environ.get('GAMMA_ISOLATED_LOADER_CONTROLS') == '1',
                     'explicit approved isolated-control invocation required')
class IsolatedSyntheticControls(unittest.TestCase):
    def test_synthetic_exports_effects_types_and_old_mode(self):
        route = os.environ.get('GAMMA_PINNED_NODE_RUNTIME')
        node_runtime = Path(route) if route else None
        identity = q.runtime(node_runtime)
        for name, interface, source, args, expected, failure in synthetic_fixtures():
            with self.subTest(name=name):
                case = {'args': args, 'expected': expected, 'compare': 'return'}
                files = {'program.js': source.encode(), **q.observer_files({'language': 'javascript', 'source_interface': interface}),
                         'inputs.json': q.encoded(q.packet([case]))}
                result = q.run_batch('javascript', files, identity, node_runtime)
                # A blocked isolation setup cannot masquerade as a negative
                # export result. All accepted controls must run successfully.
                if failure == 'execution':
                    self.assertFalse(result.ok)
                    self.assertFalse(result.timed_out)
                    self.assertFalse(result.output_limit_exceeded)
                    self.assertIn(b'interface requires', result.stderr)
                else:
                    self.assertTrue(result.ok, result.stderr.decode(errors='replace'))
                    actual = q.check_output(result.stdout, [case], 'javascript')
                    independent = verifier.independent_failures(result.stdout, [case], 'javascript')
                    wanted = [] if failure is None else [{'index': 0, 'reason': failure}]
                    self.assertEqual(actual, wanted); self.assertEqual(independent, wanted)
        q.verify_runtime({'runtime': identity}, node_runtime)
