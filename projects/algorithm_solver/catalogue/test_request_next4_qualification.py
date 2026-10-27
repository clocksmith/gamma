"""Synthetic fixed-population admission tests; no original candidate execution."""
from contextlib import ExitStack
import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_next4_oracles as oracle
from . import request_next4_qualification as request


class FixedNextFourPrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.args = SimpleNamespace(config=self.root / 'config.json', config_sha256='synthetic',
            manifest=self.root / 'manifest.json', statement_root=self.root / 'definitions',
            source_root=self.root / 'sources', output=self.root / 'freeze', node_runtime=None)
        self.gate = {'artifact_paths': {}, 'trusted_hashes': {}}
        q.write(self.root / 'gate.json', self.gate)
        q.write(self.args.config, {'source_access': {'boundary_gate': {'path': str(self.root / 'gate.json')}}})
        self.cases = {pid: [{'args': [pid], 'expected': pid, 'compare': 'return'}] for pid in request.IDS}
        self.statements = {pid: f'Synthetic definition {pid}'.encode() for pid in request.IDS}
        self.sources, source_hashes, rows = {}, {}, []
        for pid in request.IDS:
            source_hashes[pid] = {}; files = {}
            for lang, suffix in (('javascript', 'js'), ('python', 'py')):
                raw = f'Inert synthetic {lang} fixture {pid}'.encode()
                target = self.args.source_root / lang / f'{pid}.{suffix}'
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
                self.sources[(pid, lang)] = target; source_hashes[pid][lang] = q.sha(raw)
                files[lang] = {'path': f'{lang}/{pid}.{suffix}', 'sha256': q.sha(raw)}
            rows.append({'problem_id': pid, 'source_files': files})
        q.write(self.args.manifest, rows)
        manifest_sha = q.file_hash(self.args.manifest)
        provenance_hashes = {}
        for pid in request.IDS:
            folder = self.args.statement_root / str(pid); folder.mkdir(parents=True)
            (folder / 'statement.tool-prefix.txt').write_bytes(self.statements[pid])
            q.write(folder / 'provenance.json', {'problem_id': pid, 'original_manifest_sha256': manifest_sha,
                'new_statement_prefix_sha256': q.sha(self.statements[pid]),
                'original_statement_equivalence_established': False, 'original_statement_byte_pin_present': False})
            provenance_hashes[pid] = q.file_hash(folder / 'provenance.json')
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        for name, value in [('SOURCE_SHA256', source_hashes), ('MANIFEST_SHA256', manifest_sha),
                            ('PROVENANCE_SHA256', provenance_hashes)]:
            self.stack.enter_context(patch.object(request, name, value))
        for name, value in [('STATEMENT_SHA256', {pid: q.sha(raw) for pid, raw in self.statements.items()}),
                            ('CASE_COUNT', {pid: 1 for pid in request.IDS}),
                            ('CASES_SHA256', {pid: q.sha(q.encoded(cases)) for pid, cases in self.cases.items()})]:
            self.stack.enter_context(patch.object(oracle, name, value))
        self.stack.enter_context(patch.object(oracle, 'build_cases',
            side_effect=lambda pid, raw: (copy.deepcopy(self.cases[pid]), ['synthetic_definition_oracle'])))
        self.stack.enter_context(patch.object(oracle, 'validate'))
        self.stack.enter_context(patch.object(q, 'runtime', return_value={'synthetic': True}))
        self.stack.enter_context(patch.object(request.KnownSpecService, 'from_config'))
        self.boundary = self.stack.enter_context(patch.object(request, '_boundary_snapshot',
            return_value=SimpleNamespace(authorized={f'leetcode:{pid}' for pid in request.IDS})))
        self.gate_check = self.stack.enter_context(patch.object(request, 'authorize_before_open'))

    def payload_reads(self, calls):
        return [Path(call.args[0]) for call in calls if self.args.source_root in Path(call.args[0]).parents]

    def test_denied_population_never_reads_statement_or_source(self):
        self.boundary.return_value.authorized.remove('leetcode:3597')
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaises(PermissionError): request.prepare(self.args)
        self.assertEqual([Path(call.args[0]).name for call in read.call_args_list], ['config.json', 'gate.json'])
        self.assertFalse(self.args.output.exists())

    def test_denied_per_open_gate_stops_before_manifest_or_payload(self):
        self.gate_check.side_effect = PermissionError('denied')
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaises(PermissionError): request.prepare(self.args)
        self.assertEqual([Path(call.args[0]).name for call in read.call_args_list], ['config.json', 'gate.json'])

    def test_missing_exact_source_or_manifest_id_fails_before_payload(self):
        self.sources[(3597, 'python')].unlink()
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'locators'): request.prepare(self.args)
        self.assertFalse(self.payload_reads(read.call_args_list)); self.assertFalse(self.args.output.exists())
        q.write(self.args.manifest, [])
        with patch.object(request, 'MANIFEST_SHA256', q.file_hash(self.args.manifest)), patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'missing'): request.prepare(self.args)
        self.assertFalse(self.payload_reads(read.call_args_list))

    def test_all_case_and_code_pins_exist_before_every_source_read(self):
        original_read = q.read; opened = []
        def checked(path, *args):
            if self.args.source_root in Path(path).parents:
                pre = q.decode((self.args.output / 'pre-source-freeze.json').read_bytes())
                self.assertEqual(pre['source_payload_reads_at_freeze'], 0)
                self.assertFalse(pre['original_statement_byte_equivalence'])
                self.assertEqual(pre['problem_ids'], list(request.IDS))
                for pid in request.IDS:
                    self.assertEqual(pre['generated_cases'][str(pid)]['tests_raw_sha256'],
                                     q.file_hash(self.args.output / f'tests/{pid}.json'))
                opened.append(path)
            return original_read(path, *args)
        with patch.object(q, 'read', side_effect=checked): result = request.prepare(self.args)
        self.assertEqual((result['jobs'], result['checks'], len(opened)), (8, 8, 8))
        contract = q.decode((self.args.output / 'contract.json').read_bytes())
        self.assertEqual([(j['id'], j['language']) for j in contract['jobs']],
                         [(pid, lang) for pid in request.IDS for lang in request.LANGUAGES])
        self.assertFalse(contract['automatic_promotion']); self.assertEqual(contract['limits'], q.LIMITS)

    def test_generator_drift_cannot_self_adopt_new_hash_before_sources(self):
        self.cases[3597][0]['expected'] = 0
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'hard-pinned'): request.prepare(self.args)
        self.assertFalse(self.payload_reads(read.call_args_list)); self.assertFalse(self.args.output.exists())

    def test_source_drift_retains_prefreeze_without_contract(self):
        self.sources[(3228, 'javascript')].write_bytes(b'not the pinned source')
        with self.assertRaisesRegex(ValueError, 'candidate bytes'): request.prepare(self.args)
        self.assertTrue((self.args.output / 'pre-source-freeze.json').exists())
        self.assertFalse((self.args.output / 'contract.json').exists())

    def prepared(self):
        request.prepare(self.args)
        return q.decode((self.args.output / 'contract.json').read_bytes())

    def test_wrong_population_or_interface_replay_never_reads_payload(self):
        contract = self.prepared()
        changes = []
        for field, value in [('id', 3215), ('source_interface', 'global-solve-v1'), ('max_cases_per_batch', 1)]:
            bad = copy.deepcopy(contract); bad['jobs'][0][field] = value; changes.append(bad)
        bad = copy.deepcopy(contract); bad['jobs'].pop(); changes.append(bad)
        bad = copy.deepcopy(contract); bad['selected_problem_ids'] = list(reversed(request.IDS)); changes.append(bad)
        for bad in changes:
            with patch.object(q, 'read', side_effect=AssertionError('No payload reads allowed')):
                with self.assertRaises(ValueError): request.verify_freeze(self.args.output, bad, self.gate)

    def test_replay_denied_gate_precedes_any_statement_case_or_source_read(self):
        contract = self.prepared()
        self.gate_check.side_effect = PermissionError('denied replay')
        with patch.object(q, 'read', side_effect=AssertionError('No payload reads allowed')):
            with self.assertRaises(PermissionError): request.verify_freeze(self.args.output, contract, self.gate)

    def test_replay_checks_actual_cases_provenance_statement_and_manifest(self):
        contract = self.prepared(); request.verify_freeze(self.args.output, contract, self.gate)
        for relative in ('pre-source-freeze.json', 'case-provenance.json', 'original-manifest.json',
                         'statements/3228.provenance.json', 'statements/3228.md', 'tests/3597.json'):
            path = self.args.output / relative; raw = path.read_bytes(); path.write_bytes(raw + b' ')
            with self.subTest(path=relative), self.assertRaises(ValueError):
                request.verify_freeze(self.args.output, contract, self.gate)
            path.write_bytes(raw)

    def test_replay_rejects_permission_scope_and_caps_changes(self):
        contract = self.prepared()
        for field, value in [('automatic_promotion', True), ('protected_access', True),
                             ('original_statement_byte_equivalence', True), ('max_packet_bytes', 2200000),
                             ('additional_code', {}), ('pending', [{'id': 1}])]:
            bad = copy.deepcopy(contract); bad[field] = value
            with self.subTest(field=field), patch.object(q, 'read', side_effect=AssertionError('No payload reads allowed')):
                with self.assertRaises(ValueError): request.verify_freeze(self.args.output, bad, self.gate)


if __name__ == '__main__':
    unittest.main()
