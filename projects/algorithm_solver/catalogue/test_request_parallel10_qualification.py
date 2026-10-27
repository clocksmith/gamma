"""Synthetic fixed D/E preparer tests; no original source or historical case access."""
from contextlib import ExitStack
import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_parallel10_qualification as request


class FixedParallelTenTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.args = SimpleNamespace(config=self.root / 'config.json', config_sha256='synthetic',
            manifest_batch4=self.root / 'batch4.json', statement_root=self.root / 'definitions',
            source_root=self.root / 'sources', evidence_root=self.root / 'evidence',
            output=self.root / 'freeze', node_runtime=None)
        self.gate = {'artifact_paths': {}, 'trusted_hashes': {}}
        q.write(self.root / 'gate.json', self.gate)
        q.write(self.args.config, {'source_access': {'boundary_gate': {'path': str(self.root / 'gate.json')}}})
        self.cases = {pid: [{'args': [pid], 'expected': pid, 'compare': 'return'}] for pid in request.IDS}
        self.categories = {pid: ['synthetic independent definition'] for pid in request.IDS}
        self.statements = {pid: f'Synthetic definition {pid}'.encode() for pid in request.IDS}
        self.sources, source_hashes, manifest = {}, {}, []
        for pid in request.IDS:
            source_hashes[pid] = {}; files = {}
            for language, suffix in (('javascript', 'js'), ('python', 'py')):
                raw = f'Inert fixture {pid} {language}; not executable'.encode()
                target = self.args.source_root / language / f'{pid}.{suffix}'
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
                self.sources[(pid, language)] = target; source_hashes[pid][language] = q.sha(raw)
                files[language] = {'path': f'{language}/{pid}.{suffix}', 'sha256': q.sha(raw)}
            manifest.append({'problem_id': pid, 'source_files': files})
        q.write(self.args.manifest_batch4, manifest); manifest_pins = {4: q.file_hash(self.args.manifest_batch4)}
        provenance_pins = {}
        for pid in request.IDS:
            folder = self.args.statement_root / str(pid); folder.mkdir(parents=True)
            (folder / 'statement.tool-prefix.txt').write_bytes(self.statements[pid])
            value = {'problem_id': pid}
            if pid in request.IDS[:5]:
                value.update(statement_prefix={'sha256': q.sha(self.statements[pid])},
                    original_statement_byte_equivalence_claimed=False, original_statement_byte_pin=None,
                    numeric_heading_checked=True, slug_title_checked=True, original_manifest_sha256=manifest_pins[4])
            else:
                value.update(statement_sha256=q.sha(self.statements[pid]),
                    original_definition_byte_identity_available=False, original_manifest_provenance={'identity_verified': pid})
            q.write(folder / 'provenance.json', value); provenance_pins[pid] = q.file_hash(folder / 'provenance.json')
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        batch_pins = {pid: q.sha(q.encoded(request.batch_manifest(self.cases[pid], request.oracle_for(pid)))) for pid in request.IDS}
        self.args.evidence_root.mkdir()
        predecessor = b'# Synthetic retained predecessor; not executable.\n'
        (self.args.evidence_root / 'observer-predecessor.py').write_bytes(predecessor)
        for name, value in [('SOURCE_SHA256', source_hashes), ('MANIFEST_SHA256', manifest_pins),
                ('PROVENANCE_SHA256', provenance_pins), ('BATCHES_SHA256', batch_pins),
                ('PREDECESSOR_OBSERVER_SHA256', q.sha(predecessor)),
                ('CATEGORIES_SHA256', {pid: q.sha(q.encoded(categories)) for pid, categories in self.categories.items()})]:
            self.stack.enter_context(patch.object(request, name, value))
        for offset in (0, 5):
            ids = request.IDS[offset:offset + 5]; oracle = request.oracle_for(ids[0])
            for name, value in [('STATEMENT_SHA256', {pid: q.sha(self.statements[pid]) for pid in ids}),
                    ('CASE_COUNT', {pid: 1 for pid in ids}),
                    ('CASES_SHA256', {pid: q.sha(q.encoded(self.cases[pid])) for pid in ids})]:
                self.stack.enter_context(patch.object(oracle, name, value))
            self.stack.enter_context(patch.object(oracle, 'build_cases',
                side_effect=lambda pid, raw: (copy.deepcopy(self.cases[pid]), copy.deepcopy(self.categories[pid]))))
            self.stack.enter_context(patch.object(oracle, 'validate'))
        evidence_pins = {}
        for index, group in enumerate(('d', 'e')):
            folder = self.args.evidence_root / group; folder.mkdir()
            ids = request.IDS[index * 5:index * 5 + 5]; oracle = request.oracle_for(ids[0])
            rows = [{'problem_id': pid, 'cases': 1, 'cases_sha256': oracle.CASES_SHA256[pid],
                     'categories_sha256': request.CATEGORIES_SHA256[pid],
                     **({'batch_file': {'sha256': batch_pins[pid]}} if group == 'd' else {'batches_sha256': batch_pins[pid]})}
                    for pid in ids]
            frozen = {'problem_ids' if group == 'd' else 'ids': list(ids), 'cases': rows,
                'source_payload_reads_for_selected_ids_at_freeze' if group == 'd' else 'source_payload_reads': 0,
                'definition_pins': {'sha256': request.DEFINITION_INDEX_SHA256[group]},
                'code': [{'path': str(Path(oracle.__file__)), 'sha256': q.file_hash(oracle.__file__)}],
                'dependencies': [{'path': 'imported_qualification.py', 'sha256': q.sha(predecessor)},
                    {'path': 'imported_clean_domains.py', 'sha256': q.file_hash(Path(__file__).with_name('imported_clean_domains.py'))}]}
            q.write(folder / 'original-freeze.json', frozen)
            review = {'reviewer': 'Synthetic fixture, not actual approval', 'candidate_executions': 0,
                      'author_freeze': {'sha256': q.file_hash(folder / 'original-freeze.json')}}
            q.write(folder / 'independent-review.json', review)
            for name in ('source-acquisition.json', 'first-static-review.json', 'second-static-review.json'):
                q.write(folder / name, {'candidate_executions': 0, 'rows': [
                    {'problem_id': pid, 'language': language, 'source_sha256': source_hashes[pid][language]}
                    for pid in ids for language in request.LANGUAGES]})
            evidence_pins[group] = {name: q.file_hash(folder / name) for name in request.ORIGINAL_EVIDENCE[group]}
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

    def test_all_twenty_pins_exist_before_first_source_open_and_replay(self):
        original_read = q.read; opened = []
        def checked(path, *args):
            if self.args.source_root in Path(path).parents:
                pid, language = int(Path(path).stem), Path(path).parent.name
                self.gate_check.assert_called_with(f'leetcode:{pid}', {}, {}, language=language)
                pre = q.decode((self.args.output / 'pre-source-freeze.json').read_bytes())
                self.assertEqual(pre['source_payload_reads_at_freeze'], 0)
                self.assertIn('does not restore global blindness', pre['read_count_scope'])
                self.assertEqual(pre['problem_ids'], list(request.IDS))
                for target in request.IDS:
                    self.assertEqual(pre['generated_cases'][str(target)]['tests_raw_sha256'], q.file_hash(self.args.output / f'tests/{target}.json'))
                    self.assertEqual(pre['generated_cases'][str(target)]['batches_sha256'], request.BATCHES_SHA256[target])
                opened.append(path)
            elif Path(path).name == 'statement.tool-prefix.txt':
                self.gate_check.assert_called_with(f'leetcode:{Path(path).parent.name}', {}, {}, language='python', payload_kind='statement')
            return original_read(path, *args)
        with patch.object(q, 'read', side_effect=checked): result = request.prepare(self.args)
        self.assertEqual((result['jobs'], result['checks'], len(opened)), (20, 20, 20))
        contract = q.decode((self.args.output / 'contract.json').read_bytes())
        request.verify_freeze(self.args.output, contract, self.gate)
        self.assertEqual(contract['limits'], q.LIMITS); self.assertFalse(contract['automatic_promotion'])

    def test_existing_loader_calls_fixed_twenty_job_verifier(self):
        expected = self.prepared(); _, contract, gate = q.load_freeze(self.args.output)
        self.assertEqual(contract, expected); self.assertEqual(gate, self.gate)

    def test_denied_population_or_gate_precedes_payloads(self):
        self.boundary.return_value.authorized.remove('leetcode:3584')
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaises(PermissionError): request.prepare(self.args)
        self.assertEqual([Path(call.args[0]).name for call in read.call_args_list], ['config.json', 'gate.json'])
        self.boundary.return_value.authorized.add('leetcode:3584'); self.gate_check.side_effect = PermissionError('denied')
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaises(PermissionError): request.prepare(self.args)
        self.assertFalse(self.source_reads(read.call_args_list))

    def test_missing_manifest_id_precedes_source_reads(self):
        rows = q.decode(self.args.manifest_batch4.read_bytes()); rows.pop(); q.write(self.args.manifest_batch4, rows)
        request.MANIFEST_SHA256[4] = q.file_hash(self.args.manifest_batch4)
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'missing'): request.prepare(self.args)
        self.assertFalse(self.source_reads(read.call_args_list)); self.assertFalse(self.args.output.exists())

    def test_missing_source_precedes_statement_payloads(self):
        self.sources[(3584, 'python')].unlink()
        with patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'locators'): request.prepare(self.args)
        self.assertFalse(self.source_reads(read.call_args_list))
        self.assertFalse(any('statement.tool-prefix' in str(c.args[0]) for c in read.call_args_list))

    def test_original_approval_must_bind_original_freeze(self):
        p = self.args.evidence_root / 'd/independent-review.json'; v = q.decode(p.read_bytes())
        v['author_freeze']['sha256'] = '0' * 64; q.write(p, v)
        request.ORIGINAL_EVIDENCE['d']['independent-review.json'] = q.file_hash(p)
        with self.assertRaisesRegex(ValueError, 'chronology'): request.prepare(self.args)
        self.assertFalse(self.args.output.exists())

    def test_refreeze_cannot_reset_original_exposure(self):
        p = self.args.evidence_root / 'e/original-freeze.json'; v = q.decode(p.read_bytes()); v['source_payload_reads'] = 1; q.write(p, v)
        request.ORIGINAL_EVIDENCE['e']['original-freeze.json'] = q.file_hash(p)
        p = self.args.evidence_root / 'e/independent-review.json'; v = q.decode(p.read_bytes())
        v['author_freeze']['sha256'] = request.ORIGINAL_EVIDENCE['e']['original-freeze.json']; q.write(p, v)
        request.ORIGINAL_EVIDENCE['e']['independent-review.json'] = q.file_hash(p)
        with self.assertRaisesRegex(ValueError, 'source-blind chronology'): request.prepare(self.args)
        self.assertFalse(self.args.output.exists())

    def test_archived_observer_required_without_relabeling_prior_freeze(self):
        (self.args.evidence_root / 'observer-predecessor.py').write_bytes(b'different')
        with self.assertRaisesRegex(ValueError, 'archived pre-source observer'): request.prepare(self.args)
        self.assertFalse(self.args.output.exists())

    def test_source_static_review_cannot_bind_other_bytes(self):
        p = self.args.evidence_root / 'e/second-static-review.json'; v = q.decode(p.read_bytes()); v['rows'][0]['source_sha256'] = '0' * 64; q.write(p, v)
        request.ORIGINAL_EVIDENCE['e']['second-static-review.json'] = q.file_hash(p)
        with self.assertRaisesRegex(ValueError, 'static review differs'): request.prepare(self.args)
        self.assertFalse(self.args.output.exists())

    def test_original_helper_drift_precedes_sources(self):
        original = q.file_hash
        with patch.object(q, 'file_hash', side_effect=lambda p: 'f' * 64 if Path(p).name == 'imported_clean_domains.py' else original(p)):
            with self.assertRaisesRegex(ValueError, 'frozen helper drift'): request.prepare(self.args)
        self.assertFalse(self.args.output.exists())

    def test_case_or_category_drift_cannot_self_adopt(self):
        for kind in ('case', 'category'):
            old_cases = copy.deepcopy(self.cases); old_categories = copy.deepcopy(self.categories)
            if kind == 'case': self.cases[3584][0]['expected'] = 0
            else: self.categories[3584][0] = 'different'
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'hard-pinned'): request.prepare(self.args)
            self.assertFalse(self.args.output.exists()); self.cases, self.categories = old_cases, old_categories

    def test_batch_projection_drift_rejected_without_source_reads(self):
        oracle = request.oracle_for(3584)
        with patch.object(oracle, 'expected_observation_bytes', return_value=1), patch.object(q, 'read', wraps=q.read) as read:
            with self.assertRaisesRegex(ValueError, 'batch grouping'): request.prepare(self.args)
        self.assertFalse(self.source_reads(read.call_args_list)); self.assertFalse(self.args.output.exists())

    def test_source_drift_keeps_prefreeze_but_no_contract(self):
        self.sources[(3513, 'javascript')].write_bytes(b'different inert fixture')
        with self.assertRaisesRegex(ValueError, 'candidate bytes'): request.prepare(self.args)
        self.assertTrue((self.args.output / 'pre-source-freeze.json').is_file()); self.assertFalse((self.args.output / 'contract.json').exists())

    def test_provenance_cannot_claim_historical_equivalence(self):
        for pid, field in [(3513, 'original_statement_byte_equivalence_claimed'), (3227, 'original_definition_byte_identity_available')]:
            p = self.args.statement_root / str(pid) / 'provenance.json'; old = p.read_bytes(); v = q.decode(old); v[field] = True; q.write(p, v)
            old_pin = request.PROVENANCE_SHA256[pid]; request.PROVENANCE_SHA256[pid] = q.file_hash(p)
            with self.subTest(pid=pid), self.assertRaisesRegex(ValueError, 'representation'): request.definition_provenance(p, pid)
            p.write_bytes(old); request.PROVENANCE_SHA256[pid] = old_pin

    def test_fixed_population_interface_extra_override_rejected_before_reads(self):
        contract = self.prepared(); variants = []
        for field, value in [('id', 3215), ('source_interface', 'global-solve-v1'), ('max_cases_per_batch', 1)]:
            bad = copy.deepcopy(contract); bad['jobs'][0][field] = value; variants.append(bad)
        bad = copy.deepcopy(contract); bad['jobs'].pop(); variants.append(bad)
        bad = copy.deepcopy(contract); bad['selected_problem_ids'].reverse(); variants.append(bad)
        for bad in variants:
            with patch.object(q, 'read', side_effect=AssertionError('no payload')):
                with self.assertRaises(ValueError): request.verify_freeze(self.args.output, bad, self.gate)

    def test_replay_denied_gate_precedes_payloads(self):
        contract = self.prepared(); self.gate_check.side_effect = PermissionError('denied')
        with patch.object(q, 'read', side_effect=AssertionError('no payload')):
            with self.assertRaises(PermissionError): request.verify_freeze(self.args.output, contract, self.gate)

    def test_replay_checks_original_and_generated_pins(self):
        contract = self.prepared()
        for relative in ('pre-source-freeze.json', 'case-provenance.json', 'original-manifest-batch4.json',
                         'original-evidence/observer-predecessor.py', 'original-evidence/d/original-freeze.json',
                         'original-evidence/e/second-static-review.json', 'statements/3513.provenance.json',
                         'statements/3227.md', 'tests/3584.json'):
            p = self.args.output / relative; old = p.read_bytes(); p.write_bytes(old + b' ')
            with self.subTest(path=relative), self.assertRaises(ValueError): request.verify_freeze(self.args.output, contract, self.gate)
            p.write_bytes(old)

    def test_scope_caps_code_and_approval_rejected_before_reads(self):
        contract = self.prepared()
        for field, value in [('automatic_promotion', True), ('protected_access', True),
                ('original_statement_byte_equivalence', True), ('max_packet_bytes', 2200000),
                ('additional_code', {}), ('pending', [{'id': 1}])]:
            bad = copy.deepcopy(contract); bad[field] = value
            with self.subTest(field=field), patch.object(q, 'read', side_effect=AssertionError('no payload')):
                with self.assertRaises(ValueError): request.verify_freeze(self.args.output, bad, self.gate)


class ParallelTenRunnerBoundaryTests(unittest.TestCase):
    def test_fixed_domains_and_unknown_identity(self):
        for ids in (request.IDS[:5], request.IDS[5:]):
            oracle = request.oracle_for(ids[0]); self.assertEqual(oracle.IDS, ids)
            for pid in ids:
                self.assertIs(request.oracle_for(pid), oracle)
                with self.assertRaises(ValueError): request.validate(pid, [None])
        for pid in (True, '3513', 3215, 3514, 0):
            with self.assertRaises(ValueError): request.validate(pid, [])

    def test_unknown_job_before_any_payload(self):
        for pid, domain in [(3215, request.DOMAIN), (True, request.DOMAIN), (3513, 'request-parallel11-v1')]:
            job = {'id': pid, 'language': 'javascript', 'domain_validator': domain, 'source_interface': 'commonjs-object-solve-v1'}
            with patch.object(q, 'read', side_effect=AssertionError('no payload')) as read:
                with self.assertRaises(ValueError): q.job_inputs(Path('/nonexistent'), job, {})
            read.assert_not_called()

    def test_all_fixed_code_pins_preserve_existing_owners(self):
        pins = q.code_pins()
        names = {Path(p).name for p in request.additional_code()}
        self.assertEqual(names, {'request_parallel10_qualification.py', 'request_parallel_d_oracles.py', 'request_parallel_e_oracles.py', 'imported_clean_domains.py'})
        for path, expected in request.additional_code().items(): self.assertEqual(pins[path], expected)
        for name in ('request_qualification.py', 'request_next4_qualification.py', 'request_next5_qualification.py', 'request_parallel15_qualification.py'):
            p = Path(q.__file__).with_name(name); self.assertEqual(pins[str(p)], q.file_hash(p))

    def test_unapproved_additional_path_before_caller_path_open(self):
        contract = {'schema': 'gamma.imported-independent-execution.v1', 'code': {'fixed': 'pin'},
            'limits': q.LIMITS, 'jobs': [{'domain_validator': request.DOMAIN}],
            'additional_code': {'/unapproved/source.py': 'attacker-pin'}}
        with patch.object(q, 'read', return_value=q.encoded(contract)), patch.object(q, 'code_pins', return_value={'fixed': 'pin'}), \
                patch.object(request, 'additional_code', return_value={'/fixed/module.py': 'pin'}), \
                patch.object(q, 'file_hash', side_effect=AssertionError('unapproved path opened')) as opened:
            with self.assertRaisesRegex(ValueError, 'unapproved fixed parallel-ten'): q.load_freeze(Path('/synthetic'))
        opened.assert_not_called()

    def test_reader_uses_all_full_domain_validators(self):
        examples = {3513: [[1]], 3522: [['add'], [1]], 3527: [[['a']]], 3546: [[[1, 1]]],
                    3572: [[1, 2, 3], [1, 1, 1]], 3227: ['a'], 3234: ['1'], 3556: ['2'], 3577: [[1, 2]], 3584: [[1], 1]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'sources').mkdir(); (root / 'tests').mkdir()
            for pid, valid in examples.items():
                source = b'Inert synthetic fixture; never executed.'; (root / f'sources/{pid}.js').write_bytes(source)
                job = {'id': pid, 'language': 'javascript', 'source': f'sources/{pid}.js', 'tests': f'tests/{pid}.json',
                    'source_sha256': q.sha(source), 'case_count': 1, 'domain_validator': request.DOMAIN, 'source_interface': 'commonjs-object-solve-v1'}
                for args, accepted in [(valid, True), ([None], False)]:
                    cases = [{'args': args, 'expected': 0, 'compare': 'return'}]; raw = q.encoded(cases)
                    (root / job['tests']).write_bytes(raw); job['tests_raw_sha256'] = q.sha(raw)
                    with self.subTest(pid=pid, accepted=accepted), patch.object(q, 'authorize_before_open') as gate:
                        if accepted: self.assertEqual(q.job_inputs(root, job, {'artifact_paths': {}, 'trusted_hashes': {}}), (source, cases))
                        else:
                            with self.assertRaises(ValueError): q.job_inputs(root, job, {'artifact_paths': {}, 'trusted_hashes': {}})
                        gate.assert_called_once_with(f'leetcode:{pid}', {}, {}, language='javascript')

    def test_denied_reader_gate_precedes_source_and_case(self):
        job = {'id': 3513, 'language': 'javascript', 'source': 'sources/3513.js', 'tests': 'tests/3513.json',
               'domain_validator': request.DOMAIN, 'source_interface': 'commonjs-object-solve-v1'}
        with patch.object(q, 'authorize_before_open', side_effect=PermissionError('denied')), patch.object(q, 'read') as read:
            with self.assertRaises(PermissionError): q.job_inputs(Path('/synthetic'), job, {'artifact_paths': {}, 'trusted_hashes': {}})
        read.assert_not_called()

    def test_unchanged_batch_and_packet_limits(self):
        cases = [{'args': [0], 'expected': 0, 'compare': 'return'} for _ in range(65)]
        self.assertEqual([(i, len(b)) for i, b in q.batches(cases)], [(0, 32), (32, 32), (64, 1)])
        with self.assertRaisesRegex(ValueError, 'no silent truncation'):
            list(q.batches([{'args': ['a' * q.MAX_PACKET], 'expected': 0, 'compare': 'return'}]))


if __name__ == '__main__':
    unittest.main()
