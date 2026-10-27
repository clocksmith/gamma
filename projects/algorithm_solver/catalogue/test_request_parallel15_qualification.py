"""Synthetic fixed-lane tests; no original source or private case access."""
from contextlib import ExitStack
import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_parallel15_qualification as request


class FixedParallelFifteenTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.args = SimpleNamespace(config=self.root / 'config.json', config_sha256='synthetic',
            manifest_batch2=self.root / 'batch2.json', manifest_batch3=self.root / 'batch3.json',
            statement_root=self.root / 'definitions', source_root=self.root / 'sources',
            evidence_root=self.root / 'evidence', output=self.root / 'freeze', node_runtime=None)
        self.gate = {'artifact_paths': {}, 'trusted_hashes': {}}
        q.write(self.root / 'gate.json', self.gate)
        q.write(self.args.config, {'source_access': {'boundary_gate': {'path': str(self.root / 'gate.json')}}})
        self.cases = {pid: [{'args': [pid], 'expected': pid, 'compare': 'return'}] for pid in request.IDS}
        self.categories = {pid: ['synthetic independent definition'] for pid in request.IDS}
        self.statements = {pid: f'Synthetic definition {pid}'.encode() for pid in request.IDS}
        self.sources, source_hashes, manifests = {}, {}, {2: [], 3: []}
        for pid in request.IDS:
            source_hashes[pid] = {}; files = {}
            for language, suffix in (('javascript', 'js'), ('python', 'py')):
                raw = f'Inert fixture {pid} {language}; not executable'.encode()
                target = self.args.source_root / language / f'{pid}.{suffix}'
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
                self.sources[(pid, language)] = target; source_hashes[pid][language] = q.sha(raw)
                files[language] = {'path': f'{language}/{pid}.{suffix}', 'sha256': q.sha(raw)}
            manifests[request.MANIFEST_BATCH[pid]].append({'problem_id': pid, 'source_files': files})
        manifest_pins = {}
        for batch in (2, 3):
            path = getattr(self.args, f'manifest_batch{batch}'); q.write(path, manifests[batch])
            manifest_pins[batch] = q.file_hash(path)
        provenance_pins = {}
        for pid in request.IDS:
            folder = self.args.statement_root / str(pid); folder.mkdir(parents=True)
            (folder / 'statement.tool-prefix.txt').write_bytes(self.statements[pid])
            common = {'problem_id': pid}
            if pid in request.IDS[:5]:
                common.update(statement={'sha256': q.sha(self.statements[pid])},
                    historical_statement_byte_equivalence_claimed=False, raw_html_equivalence_claimed=False,
                    numeric_heading_title_and_alias_checked=True)
            elif pid in request.IDS[5:10]:
                common.update(statement_prefix={'sha256': q.sha(self.statements[pid])},
                    original_statement_byte_equivalence_claimed=False, original_definition_byte_pin=None,
                    numeric_heading_checked=True, slug_title_checked=True,
                    original_manifest_sha256=manifest_pins[request.MANIFEST_BATCH[pid]])
            else:
                common.update(new_statement_prefix_sha256=q.sha(self.statements[pid]),
                    original_statement_equivalence_established=False, original_definition_prefix_sha256=None,
                    original_manifest_sha256=manifest_pins[request.MANIFEST_BATCH[pid]])
            q.write(folder / 'provenance.json', common); provenance_pins[pid] = q.file_hash(folder / 'provenance.json')
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        for name, value in [('SOURCE_SHA256', source_hashes), ('MANIFEST_SHA256', manifest_pins),
                ('PROVENANCE_SHA256', provenance_pins),
                ('CATEGORIES_SHA256', {pid: q.sha(q.encoded(categories)) for pid, categories in self.categories.items()})]:
            self.stack.enter_context(patch.object(request, name, value))
        for group_index in range(3):
            ids = request.IDS[group_index * 5:group_index * 5 + 5]; oracle = request.oracle_for(ids[0])
            for name, value in [('STATEMENT_SHA256', {pid: q.sha(self.statements[pid]) for pid in ids}),
                    ('CASE_COUNT', {pid: 1 for pid in ids}),
                    ('CASES_SHA256', {pid: q.sha(q.encoded(self.cases[pid])) for pid in ids})]:
                self.stack.enter_context(patch.object(oracle, name, value))
            self.stack.enter_context(patch.object(oracle, 'build_cases',
                side_effect=lambda pid, raw: (copy.deepcopy(self.cases[pid]), copy.deepcopy(self.categories[pid]))))
            self.stack.enter_context(patch.object(oracle, 'validate'))
        evidence_pins = {}
        for index, group in enumerate(('a', 'b', 'c')):
            folder = self.args.evidence_root / group; folder.mkdir(parents=True)
            ids = request.IDS[index * 5:index * 5 + 5]; oracle = request.oracle_for(ids[0])
            rows = []
            for pid in ids:
                rows.append({'id' if group == 'c' else 'problem_id': pid,
                    'case_count' if group == 'c' else 'cases': 1,
                    'cases_sha256': oracle.CASES_SHA256[pid], 'categories_sha256': request.CATEGORIES_SHA256[pid]})
            module_pin = {'path': str(Path(oracle.__file__)), 'sha256': q.file_hash(oracle.__file__)}
            frozen = {'problem_ids' if group == 'b' else 'ids': list(ids)}
            if group == 'a':
                frozen.update(cases=rows, code=[module_pin], candidate_source_reads=0,
                    definition_pins={'sha256': request.DEFINITION_INDEX_SHA256[group]},
                    dependencies=[{'path': str(Path(__file__).with_name('imported_clean_domains.py')),
                                   'sha256': q.file_hash(Path(__file__).with_name('imported_clean_domains.py'))}])
            elif group == 'b':
                frozen.update(cases=rows, oracle_module=module_pin, source_payload_reads_for_selected_ids_at_freeze=0,
                    new_definition_pins={'sha256': request.DEFINITION_INDEX_SHA256[group]})
            else:
                frozen.update(problems=rows, oracle_module=module_pin, source_payload_reads_at_freeze=0,
                    definition_index={'sha256': request.DEFINITION_INDEX_SHA256[group]})
            q.write(folder / 'original-freeze.json', frozen)
            freeze_pin = q.file_hash(folder / 'original-freeze.json')
            review = {'reviewer': 'Synthetic fixture, not actual approval', 'candidate_executions': 0,
                      'approved_freeze' if group == 'c' else 'freeze': {'sha256': freeze_pin}}
            q.write(folder / 'independent-review.json', review)
            evidence_pins[group] = {'original-freeze.json': freeze_pin,
                                   'independent-review.json': q.file_hash(folder / 'independent-review.json')}
        self.stack.enter_context(patch.object(request, 'ORIGINAL_EVIDENCE', evidence_pins))
        self.stack.enter_context(patch.object(q, 'runtime', return_value={'synthetic': True}))
        self.stack.enter_context(patch.object(request.KnownSpecService, 'from_config'))
        self.boundary = self.stack.enter_context(patch.object(request, '_boundary_snapshot',
            return_value=SimpleNamespace(authorized={f'leetcode:{pid}' for pid in request.IDS})))
        self.gate_check = self.stack.enter_context(patch.object(request, 'authorize_before_open'))

    def source_reads(self, calls):
        return [Path(call.args[0]) for call in calls if self.args.source_root in Path(call.args[0]).parents]

    def prepared(self):
        request.prepare(self.args)
        return q.decode((self.args.output / 'contract.json').read_bytes())

    def test_all_thirty_pins_exist_before_first_source_open_and_replay(self):
        original_read = q.read; opened = []
        def checked(path, *args):
            if self.args.source_root in Path(path).parents:
                pid, language = int(Path(path).stem), Path(path).parent.name
                self.gate_check.assert_called_with(f'leetcode:{pid}', {}, {}, language=language)
                pre = q.decode((self.args.output / 'pre-source-freeze.json').read_bytes())
                self.assertEqual(pre['source_payload_reads_at_freeze'], 0)
                self.assertIn('does not restore global blindness', pre['read_count_scope'])
                self.assertEqual(pre['problem_ids'], list(request.IDS))
                for pid in request.IDS:
                    self.assertEqual(pre['generated_cases'][str(pid)]['tests_raw_sha256'],
                                     q.file_hash(self.args.output / f'tests/{pid}.json'))
                opened.append(path)
            elif Path(path).name == 'statement.tool-prefix.txt':
                self.gate_check.assert_called_with(f'leetcode:{Path(path).parent.name}', {}, {},
                                                   language='python', payload_kind='statement')
            return original_read(path, *args)
        with patch.object(q, 'read', side_effect=checked): result = request.prepare(self.args)
        self.assertEqual((result['jobs'], result['checks'], len(opened)), (30, 30, 30))
        contract = q.decode((self.args.output / 'contract.json').read_bytes())
        request.verify_freeze(self.args.output, contract, self.gate)
        self.assertEqual(contract['limits'], q.LIMITS); self.assertFalse(contract['automatic_promotion'])
        self.assertEqual([(j['id'], j['language']) for j in contract['jobs']],
                         [(pid, language) for pid in request.IDS for language in request.LANGUAGES])

    def test_existing_loader_calls_fixed_parallel_fifteen_verifier(self):
        expected = self.prepared()
        _, contract, gate = q.load_freeze(self.args.output)
        self.assertEqual(contract, expected)
        self.assertEqual(gate, self.gate)

    def test_denied_population_or_gate_precedes_payloads(self):
        self.boundary.return_value.authorized.remove('leetcode:3619')
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaises(PermissionError): request.prepare(self.args)
        self.assertEqual([Path(call.args[0]).name for call in read.call_args_list], ['config.json', 'gate.json'])
        self.boundary.return_value.authorized.add('leetcode:3619')
        self.gate_check.side_effect = PermissionError('denied')
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaises(PermissionError): request.prepare(self.args)
        self.assertEqual([Path(call.args[0]).name for call in read.call_args_list], ['config.json', 'gate.json'])

    def test_missing_or_misassigned_manifest_id_precedes_source_reads(self):
        rows = q.decode(self.args.manifest_batch2.read_bytes()); rows.pop()
        q.write(self.args.manifest_batch2, rows)
        request.MANIFEST_SHA256[2] = q.file_hash(self.args.manifest_batch2)
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'missing'): request.prepare(self.args)
        self.assertFalse(self.source_reads(read.call_args_list)); self.assertFalse(self.args.output.exists())
        wrong = q.decode(self.args.manifest_batch3.read_bytes())
        q.write(self.args.manifest_batch2, wrong); request.MANIFEST_SHA256[2] = q.file_hash(self.args.manifest_batch2)
        with self.assertRaisesRegex(ValueError, 'wrong manifest batch'): request.read_manifest(self.args.manifest_batch2, 2)

    def test_missing_source_precedes_statements_and_other_sources(self):
        self.sources[(3619, 'python')].unlink()
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'locators'): request.prepare(self.args)
        self.assertFalse(self.source_reads(read.call_args_list))
        self.assertFalse(any('statement.tool-prefix' in str(call.args[0]) for call in read.call_args_list))

    def test_cross_review_must_bind_correct_original_freeze(self):
        path = self.args.evidence_root / 'a' / 'independent-review.json'
        value = q.decode(path.read_bytes()); value['freeze']['sha256'] = request.ORIGINAL_EVIDENCE['b']['original-freeze.json']
        q.write(path, value); request.ORIGINAL_EVIDENCE['a']['independent-review.json'] = q.file_hash(path)
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'does not bind its group'): request.prepare(self.args)
        self.assertFalse(self.source_reads(read.call_args_list)); self.assertFalse(self.args.output.exists())

    def test_original_domain_helper_drift_precedes_all_sources(self):
        original_hash = q.file_hash
        def changed(path):
            return 'f' * 64 if Path(path).name == 'imported_clean_domains.py' else original_hash(path)
        with patch.object(q, 'file_hash', side_effect=changed), patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'full-domain helper drift'): request.prepare(self.args)
        self.assertFalse(self.source_reads(read.call_args_list)); self.assertFalse(self.args.output.exists())

    def test_later_refreeze_cannot_replace_original_source_blind_record(self):
        folder = self.args.evidence_root / 'a'; path = folder / 'original-freeze.json'
        value = q.decode(path.read_bytes()); value['candidate_source_reads'] = 1; q.write(path, value)
        request.ORIGINAL_EVIDENCE['a']['original-freeze.json'] = q.file_hash(path)
        review_path = folder / 'independent-review.json'; review = q.decode(review_path.read_bytes())
        review['freeze']['sha256'] = q.file_hash(path); q.write(review_path, review)
        request.ORIGINAL_EVIDENCE['a']['independent-review.json'] = q.file_hash(review_path)
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'not source-blind'): request.prepare(self.args)
        self.assertFalse(self.source_reads(read.call_args_list)); self.assertFalse(self.args.output.exists())

    def test_case_or_category_drift_cannot_self_adopt_new_hash(self):
        for kind in ('case', 'category'):
            old_cases = copy.deepcopy(self.cases); old_categories = copy.deepcopy(self.categories)
            if kind == 'case': self.cases[3619][0]['expected'] = 0
            else: self.categories[3619][0] = 'different category'
            with self.subTest(kind=kind), patch.object(q, 'read', wraps=q.read) as read:
                with self.assertRaisesRegex(ValueError, 'hard-pinned'): request.prepare(self.args)
            self.assertFalse(self.source_reads(read.call_args_list)); self.assertFalse(self.args.output.exists())
            self.cases, self.categories = old_cases, old_categories

    def test_source_drift_retains_prefreeze_but_no_contract(self):
        self.sources[(3223, 'javascript')].write_bytes(b'different inert fixture')
        with self.assertRaisesRegex(ValueError, 'candidate bytes'): request.prepare(self.args)
        self.assertTrue((self.args.output / 'pre-source-freeze.json').is_file())
        self.assertFalse((self.args.output / 'contract.json').exists())

    def test_distinct_provenance_representations_cannot_claim_equivalence(self):
        for pid, field in [(3223, 'historical_statement_byte_equivalence_claimed'),
                           (3517, 'original_statement_byte_equivalence_claimed'),
                           (3524, 'original_statement_equivalence_established')]:
            path = self.args.statement_root / str(pid) / 'provenance.json'
            raw = path.read_bytes(); original_pin = request.PROVENANCE_SHA256[pid]
            value = q.decode(raw); value[field] = True; q.write(path, value)
            request.PROVENANCE_SHA256[pid] = q.file_hash(path)
            with self.subTest(pid=pid), self.assertRaisesRegex(ValueError, 'representation differs'):
                request.definition_provenance(path, pid)
            path.write_bytes(raw); request.PROVENANCE_SHA256[pid] = original_pin

    def test_wrong_population_interface_and_extra_batch_override_rejected_before_reads(self):
        contract = self.prepared(); changed = []
        for field, value in [('id', 3215), ('source_interface', 'global-solve-v1'), ('max_cases_per_batch', 1)]:
            bad = copy.deepcopy(contract); bad['jobs'][0][field] = value; changed.append(bad)
        bad = copy.deepcopy(contract); bad['jobs'].pop(); changed.append(bad)
        bad = copy.deepcopy(contract); bad['selected_problem_ids'].reverse(); changed.append(bad)
        for bad in changed:
            with patch.object(q, 'read', side_effect=AssertionError('no payloads')):
                with self.assertRaises(ValueError): request.verify_freeze(self.args.output, bad, self.gate)

    def test_replay_denied_gate_precedes_payloads(self):
        contract = self.prepared(); self.gate_check.side_effect = PermissionError('denied')
        with patch.object(q, 'read', side_effect=AssertionError('no payloads')):
            with self.assertRaises(PermissionError): request.verify_freeze(self.args.output, contract, self.gate)

    def test_replay_checks_all_original_and_new_pins(self):
        contract = self.prepared()
        for relative in ('pre-source-freeze.json', 'case-provenance.json', 'original-manifest-batch2.json',
                         'original-manifest-batch3.json', 'original-evidence/a/original-freeze.json',
                         'original-evidence/b/independent-review.json', 'original-evidence/c/original-freeze.json',
                         'statements/3223.provenance.json', 'statements/3517.md', 'tests/3619.json'):
            path = self.args.output / relative; raw = path.read_bytes(); path.write_bytes(raw + b' ')
            with self.subTest(path=relative), self.assertRaises(ValueError):
                request.verify_freeze(self.args.output, contract, self.gate)
            path.write_bytes(raw)

    def test_replay_rejects_scope_caps_code_and_approval_changes(self):
        contract = self.prepared()
        for field, value in [('automatic_promotion', True), ('protected_access', True),
                ('original_statement_byte_equivalence', True), ('max_packet_bytes', 2200000),
                ('additional_code', {}), ('pending', [{'id': 1}])]:
            bad = copy.deepcopy(contract); bad[field] = value
            with self.subTest(field=field), patch.object(q, 'read', side_effect=AssertionError('no payloads')):
                with self.assertRaises(ValueError): request.verify_freeze(self.args.output, bad, self.gate)


class ParallelFifteenDomainAndBatchTests(unittest.TestCase):
    def test_fixed_dispatch_and_full_domain_validation_without_sources(self):
        expected = ((3223, 3232, 3532, 3583, 3612), (3517, 3531, 3567, 3598, 3618),
                    (3524, 3551, 3587, 3608, 3619))
        for group in expected:
            oracle = request.oracle_for(group[0])
            self.assertEqual(oracle.IDS, group)
            for pid in group:
                self.assertIs(request.oracle_for(pid), oracle)
                with self.assertRaises(ValueError): request.validate(pid, [None])
        for pid in (True, '3223', 3215, 3514, 0):
            with self.assertRaises(ValueError): request.validate(pid, [])

    def test_existing_batches_keep_thirty_two_call_and_packet_caps(self):
        cases = [{'args': [0], 'expected': 0, 'compare': 'return'} for _ in range(65)]
        self.assertEqual([(offset, len(batch)) for offset, batch in q.batches(cases)], [(0, 32), (32, 32), (64, 1)])
        oversized = [{'args': ['a' * q.MAX_PACKET], 'expected': 0, 'compare': 'return'}]
        with self.assertRaisesRegex(ValueError, 'no silent truncation'): list(q.batches(oversized))

    def test_additional_identity_is_fixed_and_includes_domain_helper(self):
        names = {Path(path).name for path in request.additional_code()}
        self.assertEqual(names, {'request_parallel15_qualification.py', 'request_parallel_a_oracles.py',
            'request_parallel_b_oracles.py', 'request_parallel_c_oracles.py', 'imported_clean_domains.py'})

class ParallelFifteenRunnerBoundaryTests(unittest.TestCase):
    def test_wrong_identity_and_unapproved_domain_fail_before_any_payload(self):
        for pid, domain in [(3215, request.DOMAIN), (3514, request.DOMAIN),
                            (True, request.DOMAIN), (3223, 'request-parallel16-v1')]:
            job = {'id': pid, 'language': 'javascript', 'domain_validator': domain,
                   'source_interface': 'commonjs-object-solve-v1'}
            with patch.object(q, 'read', side_effect=AssertionError('no payload')) as opened:
                with self.assertRaises(ValueError): q.job_inputs(Path('/nonexistent'), job, {})
            opened.assert_not_called()

    def test_all_fixed_modules_and_helper_are_frozen_by_existing_runner(self):
        pins = q.code_pins()
        for path, expected in request.additional_code().items():
            self.assertEqual(pins[path], expected)
        # These older owners remain required, not replaced by the new lane.
        for name in ('request_qualification.py', 'request_next4_qualification.py',
                     'request_next4_oracles.py', 'request_next5_qualification.py', 'request_next5_oracles.py'):
            path = Path(q.__file__).with_name(name)
            self.assertEqual(pins[str(path)], q.file_hash(path))

    def test_unapproved_additional_path_rejected_before_caller_path_open(self):
        contract = {'schema': 'gamma.imported-independent-execution.v1', 'code': {'fixed': 'pin'},
            'limits': q.LIMITS, 'jobs': [{'domain_validator': request.DOMAIN}],
            'additional_code': {'/unapproved/source-or-case.py': 'attacker-pin'}}
        with patch.object(q, 'read', return_value=q.encoded(contract)), \
                patch.object(q, 'code_pins', return_value={'fixed': 'pin'}), \
                patch.object(request, 'additional_code', return_value={'/fixed/module.py': 'pin'}), \
                patch.object(q, 'file_hash', side_effect=AssertionError('unapproved path opened')) as opened:
            with self.assertRaisesRegex(ValueError, 'unapproved fixed parallel-fifteen'):
                q.load_freeze(Path('/synthetic'))
        opened.assert_not_called()

    def test_existing_reader_applies_each_real_full_domain_validator(self):
        examples = {3223: ['a'], 3232: [[1]], 3532: [1, [1], 0, [[0, 0]]],
            3583: [[0, 0, 0]], 3612: ['a'], 3517: ['a'], 3531: [2, [[1, 1]]],
            3567: [[[1]], 1], 3598: [['a']], 3618: [[1]], 3524: [[1], 1],
            3551: [[1]], 3587: [[1]], 3608: [1, [], 1], 3619: [[[0]], 1]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'sources').mkdir(); (root / 'tests').mkdir()
            for pid, valid in examples.items():
                source = b'Inert synthetic fixture, never executed.'
                (root / f'sources/{pid}.js').write_bytes(source)
                job = {'id': pid, 'language': 'javascript', 'source': f'sources/{pid}.js',
                    'tests': f'tests/{pid}.json', 'source_sha256': q.sha(source), 'case_count': 1,
                    'domain_validator': request.DOMAIN, 'source_interface': 'commonjs-object-solve-v1'}
                for args, accepted in [(valid, True), ([None], False)]:
                    cases = [{'args': args, 'expected': 0, 'compare': 'return'}]
                    raw = q.encoded(cases); (root / job['tests']).write_bytes(raw)
                    job['tests_raw_sha256'] = q.sha(raw)
                    with self.subTest(pid=pid, accepted=accepted), patch.object(q, 'authorize_before_open') as gate:
                        if accepted:
                            self.assertEqual(q.job_inputs(root, job, {'artifact_paths': {}, 'trusted_hashes': {}}), (source, cases))
                        else:
                            with self.assertRaises(ValueError): q.job_inputs(root, job, {'artifact_paths': {}, 'trusted_hashes': {}})
                        gate.assert_called_once_with(f'leetcode:{pid}', {}, {}, language='javascript')

    def test_denied_reader_gate_precedes_source_and_cases(self):
        job = {'id': 3223, 'language': 'javascript', 'source': 'sources/3223.js',
            'tests': 'tests/3223.json', 'domain_validator': request.DOMAIN,
            'source_interface': 'commonjs-object-solve-v1'}
        with patch.object(q, 'authorize_before_open', side_effect=PermissionError('denied')), \
                patch.object(q, 'read', side_effect=AssertionError('no payload')) as opened:
            with self.assertRaises(PermissionError): q.job_inputs(Path('/synthetic'), job, {'artifact_paths': {}, 'trusted_hashes': {}})
        opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
