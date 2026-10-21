"""Synthetic text/CLI guards only. No private witnesses or helper runtime tests."""
import argparse
import ast
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import rewrite

COMPONENTS_PATH = None


class RewriteTests(unittest.TestCase):
    def test_unique_replacement_preserves_surroundings(self):
        self.assertEqual(rewrite.replace_exact('left\nTOKEN\nright\n', [('TOKEN', 'NEW')]), 'left\nNEW\nright\n')

    def test_missing_or_ambiguous_span_rejected(self):
        for source in ('absent', 'TOKEN TOKEN'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                rewrite.replace_exact(source, [('TOKEN', 'NEW')])

    def test_empty_span_rejected(self):
        with self.assertRaises(ValueError):
            rewrite.replace_exact('x', [('', 'y')])

    def test_synthetic_python_rewrite_preserves_exact_separators(self):
        before = b'def demonstration(value):\n    return value + 0\n'
        after = (rewrite.PY_HELPERS + 'def demonstration(value):\n    return value + 1\n').encode()
        actual = rewrite.rewrite_guarded(before, before_sha256=rewrite.digest(before),
            after_sha256=rewrite.digest(after), language='python', replacements=[('value + 0', 'value + 1')])
        self.assertEqual(actual, after)
        self.assertEqual([n.name for n in ast.parse(actual).body], ['count_read', 'count_increment', 'demonstration'])

    def test_synthetic_javascript_rewrite_keeps_full_helpers(self):
        before = b'function demonstration(value) { return value + 0; }\n'
        after = (rewrite.JS_HELPERS + 'function demonstration(value) { return value + 1; }\n').encode()
        self.assertEqual(rewrite.rewrite_guarded(before, before_sha256=rewrite.digest(before),
            after_sha256=rewrite.digest(after), language='javascript', replacements=[('value + 0', 'value + 1')]), after)

    def test_wrong_predecessor_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source identity'):
            rewrite.rewrite_guarded(b'x', before_sha256='0' * 64, after_sha256='0' * 64,
                                    language='python', replacements=[])

    def test_wrong_successor_hash_rejected(self):
        before = b'pass\n'
        with self.assertRaisesRegex(ValueError, 'successor identity'):
            rewrite.rewrite_guarded(before, before_sha256=rewrite.digest(before), after_sha256='0' * 64,
                                    language='python', replacements=[])

    def test_unsupported_language_rejected(self):
        before = b'x'
        with self.assertRaisesRegex(ValueError, 'language'):
            rewrite.rewrite_guarded(before, before_sha256=rewrite.digest(before), after_sha256='0' * 64,
                                    language='unknown', replacements=[])

    def test_oversize_witness_rejected_even_with_matching_hash(self):
        before = b'x' * (rewrite.MAX_WITNESS_BYTES + 1)
        with self.assertRaises(ValueError):
            rewrite.rewrite_guarded(before, before_sha256=rewrite.digest(before), after_sha256='0' * 64,
                                    language='javascript', replacements=[])

    def test_unknown_witness_key_rejected(self):
        with self.assertRaises(ValueError):
            rewrite.transform('unknown-python', b'pass\n')

    def test_increment_dependency_visible_in_python_ast(self):
        definitions = ast.parse(rewrite.PY_HELPERS).body
        increment = next(n for n in definitions if n.name == 'count_increment')
        calls = [n.func.id for n in ast.walk(increment) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        self.assertEqual(calls, ['count_read'])

    def test_existing_registry_api_idempotence_and_separator_accounting(self):
        registry = rewrite.load_component_registry(COMPONENTS_PATH)
        keys = set(registry.COMPONENTS)
        first = rewrite.register_component(registry)
        self.assertEqual(rewrite.register_component(registry), first)
        self.assertEqual(set(registry.COMPONENTS), keys)
        self.assertEqual(first['source'] + '\n', rewrite.PY_HELPERS)

    def test_registry_collision_is_not_overwritten(self):
        registry = rewrite.load_component_registry(COMPONENTS_PATH)
        with mock.patch.dict(registry.COMPONENTS, {rewrite.COMPONENT_NAME: {'source': 'different'}}):
            with self.assertRaises(ValueError):
                rewrite.register_component(registry)
            self.assertEqual(registry.COMPONENTS[rewrite.COMPONENT_NAME], {'source': 'different'})

    def test_wrong_registry_refused_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'components.py'
            path.write_text('raise RuntimeError("must never execute")\n')
            with self.assertRaisesRegex(ValueError, 'identity'):
                rewrite.load_component_registry(path)

    def test_validation_failure_creates_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'unqualified.py'
            path.write_bytes(b'pass\n')
            output = Path(directory) / 'output'
            with self.assertRaises(ValueError):
                rewrite.write_rewrites([('0560-python', path)], output)
            self.assertFalse(output.exists())
            self.assertEqual(path.read_bytes(), b'pass\n')

    def test_duplicate_key_rejected_before_file_reads(self):
        with self.assertRaises(ValueError):
            rewrite.write_rewrites([('0560-python', 'missing'), ('0560-python', 'missing')], Path('unused'))

    def test_existing_output_refused_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.py'
            source.write_bytes(b'synthetic')
            output = root / 'output'
            output.mkdir()
            retained = output / 'keep'
            retained.write_text('retained')
            with mock.patch.object(rewrite, 'transform', return_value=b'synthetic successor'):
                with self.assertRaises(FileExistsError):
                    rewrite.write_rewrites([('0560-python', source)], output)
            self.assertEqual(retained.read_text(), 'retained')
            self.assertEqual(source.read_bytes(), b'synthetic')

    def test_description_uses_explicit_registry_without_witnesses(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(rewrite.main(['--components', str(COMPONENTS_PATH), '--describe']), 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result['component']['name'], rewrite.COMPONENT_NAME)
        self.assertEqual(result['python_separator_bytes'], 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--components', type=Path, required=True,
                        help='Path to the public existing algsolve/synth/components.py; no private witnesses needed')
    args, remaining = parser.parse_known_args()
    COMPONENTS_PATH = args.components
    unittest.main(argv=[__file__, *remaining])
