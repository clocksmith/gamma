"""Trusted synthetic preparation and interface checks; no candidate execution."""
from contextlib import ExitStack
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_qualification as request

STATEMENT = b'''Input: a = [1], b = [2], c = [3] Output: 1 Explanation: first.
Input: a = [1,1], b = [2,3], c = [1,5] Output: 4 Explanation: second.'''


class DomainAndOracleTests(unittest.TestCase):
    def test_strict_domain_rejects_wrong_ids_types_shapes_and_bounds(self):
        request.validate(3215, [[0], [10**9], [2**29 + 1]])
        invalid = [[], [[0]], [[0], [0]], [[0], [0], [0], [0]],
                   [[], [0], [0]], [[-1], [0], [0]], [[10**9 + 1], [0], [0]],
                   [[True], [0], [0]], [[1.0], [0], [0]], [[0] * 100001, [0], [0]],
                   [(0,), [0], [0]]]
        for args in invalid:
            with self.subTest(args=str(args)[:50]), self.assertRaises(ValueError):
                request.validate(3215, args)
        for pid in (True, '3215', 3216):
            with self.assertRaises(ValueError):
                request.validate(pid, [[0], [0], [0]])

    def test_cartesian_oracle_counts_duplicate_positions_and_high_bits(self):
        self.assertEqual(request.expected([[1, 1], [2, 3], [1, 5]]), 4)
        values = (0, 1, 2**29, 2**29 + 1, 10**9 - 1, 10**9)
        for a in values:
            for b in values:
                for c in values:
                    parity = sum(((a // 2**bit) + (b // 2**bit) + (c // 2**bit)) % 2 for bit in range(30)) % 2
                    self.assertEqual(request.expected([[a], [b], [c]]), int(parity == 0))
        with self.assertRaisesRegex(ValueError, 'budget'):
            request.expected([[0] * 100, [0] * 100, [0] * 100])

    def test_generator_keeps_exact_population_and_existing_packet_cap(self):
        with patch.object(request, 'STATEMENT_SHA256', q.sha(STATEMENT)):
            cases, categories = request.build_cases(STATEMENT)
        self.assertEqual(len(cases), 815)
        self.assertEqual(len(categories), len(cases))
        self.assertEqual(categories.count('high_bit_cartesian_oracle'), 216)
        self.assertEqual(cases[-5]['expected'], 10**15)
        self.assertEqual(cases[-3]['expected'], 99999**3 + 3 * 99999)
        groups = list(q.batches(cases))
        self.assertEqual(sum(len(batch) for _, batch in groups), 815)
        self.assertLessEqual(max(len(q.encoded(q.packet(batch))) for _, batch in groups), q.MAX_PACKET)

    def test_definition_pin_and_both_public_examples_are_required(self):
        with self.assertRaisesRegex(ValueError, 'prefix'):
            request.public_examples(STATEMENT)
        bad = STATEMENT.replace(b'Output: 4', b'Output: 3')
        with patch.object(request, 'STATEMENT_SHA256', q.sha(bad)):
            with self.assertRaisesRegex(ValueError, 'disagrees'):
                request.public_examples(bad)


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.args = SimpleNamespace(config=self.root / 'config.json', config_sha256='synthetic',
                                    manifest=self.root / 'manifest.json', statement=self.root / 'statement.md',
                                    source_root=self.root / 'input', output=self.root / 'freeze', node_runtime=None)
        self.gate = {'artifact_paths': {}, 'trusted_hashes': {}}
        q.write(self.root / 'gate.json', self.gate)
        q.write(self.args.config, {'source_access': {'boundary_gate': {'path': str(self.root / 'gate.json')}}})
        self.args.statement.write_bytes(STATEMENT)
        self.sources = {'javascript': b'trusted inert JS fixture', 'python': b'trusted inert Python fixture'}
        self.hashes = {language: q.sha(raw) for language, raw in self.sources.items()}
        files = {}
        for language, suffix in (('javascript', 'js'), ('python', 'py')):
            relative = f'{language}/3215.{suffix}'
            target = self.args.source_root / relative
            target.parent.mkdir(parents=True)
            target.write_bytes(self.sources[language])
            files[language] = {'path': relative, 'sha256': self.hashes[language]}
        q.write(self.args.manifest, [{'problem_id': 3215, 'source_files': files,
                                     'definition_provenance': {'definition_prefix_sha256': q.sha(STATEMENT)}}])
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        synthetic_cases = [{'args': [[0], [0], [0]], 'expected': 1, 'compare': 'return'}]
        for name, value in [('MANIFEST_SHA256', q.file_hash(self.args.manifest)),
                            ('STATEMENT_SHA256', q.sha(STATEMENT)), ('SOURCE_SHA256', self.hashes),
                            ('CASE_COUNT', 1), ('CASES_SHA256', q.sha(q.encoded(synthetic_cases)))]:
            self.stack.enter_context(patch.object(request, name, value))
        self.stack.enter_context(patch.object(q, 'runtime', return_value={'synthetic': True}))
        self.stack.enter_context(patch.object(request.KnownSpecService, 'from_config'))
        self.boundary = self.stack.enter_context(patch.object(request, '_boundary_snapshot',
                return_value=SimpleNamespace(authorized={'leetcode:3215'})))
        self.gate_check = self.stack.enter_context(patch.object(request, 'authorize_before_open'))
        self.stack.enter_context(patch.object(request, 'build_cases', return_value=(synthetic_cases, ['synthetic_oracle'])))

    def test_denied_target_reads_no_statement_or_sources(self):
        self.boundary.return_value = SimpleNamespace(authorized=set())
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaises(PermissionError):
                request.prepare(self.args)
        self.assertEqual([Path(c.args[0]).name for c in read.call_args_list], ['config.json', 'gate.json'])
        self.assertFalse(self.args.output.exists())

    def test_missing_source_fails_before_statement_or_source_payload_access(self):
        (self.args.source_root / 'python/3215.py').unlink()
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'locators'):
                request.prepare(self.args)
        self.assertNotIn(self.args.statement, [c.args[0] for c in read.call_args_list])
        self.assertFalse(self.args.output.exists())

    def test_missing_target_manifest_fails_before_statement_access(self):
        q.write(self.args.manifest, [])
        with patch.object(request, 'MANIFEST_SHA256', q.file_hash(self.args.manifest)), patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'missing'):
                request.prepare(self.args)
        self.assertNotIn(self.args.statement, [c.args[0] for c in read.call_args_list])

    def test_cases_and_code_freeze_precede_every_candidate_read(self):
        original_read = q.read
        reads = []
        def checked(path, *args):
            if self.args.source_root in Path(path).parents:
                self.assertTrue((self.args.output / 'pre-source-freeze.json').is_file())
                frozen = q.decode((self.args.output / 'pre-source-freeze.json').read_bytes())
                self.assertEqual(frozen['source_payload_reads_at_freeze'], 0)
                self.assertEqual(frozen['tests_raw_sha256'], q.file_hash(self.args.output / 'tests/3215.json'))
                reads.append(path)
            return original_read(path, *args)
        with patch.object(q, 'read', side_effect=checked):
            result = request.prepare(self.args)
        self.assertEqual(result['jobs'], 2)
        self.assertEqual(len(reads), 2)
        contract = q.decode((self.args.output / 'contract.json').read_bytes())
        self.assertFalse(contract['automatic_promotion'])
        self.assertEqual(contract['selected_problem_ids'], [3215])
        self.assertEqual([job['source_interface'] for job in contract['jobs']],
                         ['commonjs-object-solve-v1', 'global-solve-v1'])
        self.assertEqual(contract['limits'], q.LIMITS)

    def test_source_drift_preserves_prefreeze_but_creates_no_contract(self):
        (self.args.source_root / 'javascript/3215.js').write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError, 'candidate bytes'):
            request.prepare(self.args)
        self.assertTrue((self.args.output / 'pre-source-freeze.json').exists())
        self.assertFalse((self.args.output / 'contract.json').exists())

    def test_execution_and_replay_verify_all_pilot_evidence_pins(self):
        request.prepare(self.args)
        contract = q.decode((self.args.output / 'contract.json').read_bytes())
        request.verify_freeze(self.args.output, contract, self.gate)
        for name, error in [('pre-source-freeze.json', 'artifact drift'),
                            ('case-provenance.json', 'artifact drift'), ('statement.md', 'statement drift')]:
            path = self.args.output / name
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with self.subTest(artifact=name), self.assertRaisesRegex(ValueError, error):
                request.verify_freeze(self.args.output, contract, self.gate)
            path.write_bytes(original)
        contract['jobs'][0]['source_interface'] = 'global-solve-v1'
        with self.assertRaisesRegex(ValueError, 'interface evidence'):
            request.verify_freeze(self.args.output, contract, self.gate)


@unittest.skipUnless(shutil.which('node'), 'Node is required for trusted synthetic loader tests')
class CommonJSObserverTests(unittest.TestCase):
    def run_fixture(self, source, args):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'program.js').write_text(source)
            (root / 'harness.cjs').write_bytes(q.read(q.COMMONJS_HARNESS))
            (root / 'observer.cjs').write_bytes(q.read(q.HARNESS / 'harness.cjs'))
            q.write(root / 'inputs.json', {'entry': 'solve', 'calls': [{'args': args}]})
            return subprocess.run([shutil.which('node'), 'harness.cjs'], cwd=root, capture_output=True, timeout=10)

    def test_native_module_receiver_and_wrapper_return(self):
        result = self.run_fixture('module.exports = {n: 3, solve(x) { return this.n + x; }}; return 99;', [4])
        self.assertEqual(result.returncode, 0, result.stderr)
        record, done = map(json.loads, result.stdout.splitlines())
        self.assertEqual((record['result'], record['result_type']), (7, 'number'))
        self.assertEqual(record['args_before'], [4])
        self.assertEqual(record['args_after'], [4])
        self.assertEqual(record['alias_edges'], [])
        self.assertEqual(done, {'done': 1})

    def test_mutation_and_alias_observations_are_not_dropped(self):
        result = self.run_fixture('module.exports = {solve(xs) { xs.push(2); return xs; }};', [[1]])
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout.splitlines()[0])
        self.assertEqual(record['args_before'], [[1]])
        self.assertEqual(record['args_after'], [[1, 2]])
        self.assertTrue(record['alias_edges'])

    def test_wrong_export_shape_is_rejected(self):
        for source in ('module.exports = () => 1;', 'module.exports = {solve: 1};'):
            result = self.run_fixture(source, [])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'own callable solve', result.stderr)


if __name__ == '__main__':
    unittest.main()
