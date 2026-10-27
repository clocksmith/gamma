"""Synthetic fixed F/G/H preparation/replay tests; no candidate code executes."""
from contextlib import ExitStack
import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_parallel_fgh15_qualification as request


class FixedFGHTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.args = SimpleNamespace(config=self.root/'config.json', config_sha256='synthetic',
            selection_root=self.root/'selectors', statement_root=self.root/'definitions',
            source_root=self.root/'sources', evidence_root=self.root/'evidence', output=self.root/'freeze', node_runtime=None)
        self.gate = {'artifact_paths': {}, 'trusted_hashes': {}}
        q.write(self.root/'gate.json', self.gate)
        q.write(self.args.config, {'source_access': {'boundary_gate': {'path': str(self.root/'gate.json')}}})
        self.args.selection_root.mkdir(); self.args.evidence_root.mkdir()
        self.cases = {pid: [{'args': [pid], 'expected': pid, 'compare': 'return'}] for pid in request.IDS}
        self.categories = {pid: ['synthetic source-blind reference'] for pid in request.IDS}
        self.statements = {pid: f'Synthetic statement {pid}'.encode() for pid in request.IDS}
        self.sources, source_pins, selection_pins, provenance_pins = {}, {}, {}, {}
        for group, ids in request.GROUP_IDS.items():
            rows = []
            for pid in ids:
                source_pins[pid] = {}; sources = {}
                for language, suffix in (('javascript', 'js'), ('python', 'py')):
                    raw = f'Inert fixture {pid}/{language}; never executed'.encode()
                    p = self.args.source_root/language/f'{pid}.{suffix}'; p.parent.mkdir(exist_ok=True, parents=True); p.write_bytes(raw)
                    self.sources[(pid, language)] = p; source_pins[pid][language] = q.sha(raw)
                    sources[language] = {'path': f'{language}/{pid}.{suffix}', 'sha256': q.sha(raw)}
                rows.append({'problem_id': pid, 'parameters': list(request.oracle_for(pid).PARAMETERS[pid]),
                             'manifest': request.ORIGINAL_MANIFEST_METADATA[pid], 'source_files': sources})
                p = self.args.statement_root/str(pid); p.mkdir(parents=True)
                (p/'statement.tool-prefix.txt').write_bytes(self.statements[pid])
                value = {'problem_id': pid}
                if group == 'f': value.update(statement_prefix={'sha256': q.sha(self.statements[pid])}, original_statement_byte_equivalence_claimed=False, original_statement_byte_pin=None)
                elif group == 'g': value.update(statement={'sha256': q.sha(self.statements[pid])}, **{('original_statement_byte_equivalence_claimed' if pid == 3574 else 'original_statement_byte_equivalence'): False})
                else: value.update(statement_sha256=q.sha(self.statements[pid]), original_definition_byte_identity_available=False)
                q.write(p/'provenance.json', value); provenance_pins[pid] = q.file_hash(p/'provenance.json')
            # Retain the actual G ordering mismatch, testing identity-keyed comparison.
            if group == 'g': rows = rows[3:4]+rows[:3]+rows[4:]
            p = self.args.selection_root/request.SELECTOR_FILES[group]
            q.write(p, {'selected': rows, 'legacy_case_or_reasoning_fields_supplied_to_oracle_authors': False})
            selection_pins[group] = q.file_hash(p)
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        predecessor = b'# Inert archived fixture, never executed.\n'
        (self.args.evidence_root/'observer-predecessor.py').write_bytes(predecessor)
        for name, value in [('SOURCE_SHA256', source_pins), ('SELECTOR_SHA256', selection_pins), ('PROVENANCE_SHA256', provenance_pins),
                            ('PREDECESSOR_OBSERVER_SHA256', q.sha(predecessor)),
                            ('CATEGORIES_SHA256', {pid: q.sha(q.encoded(x)) for pid, x in self.categories.items()})]:
            self.stack.enter_context(patch.object(request, name, value))
        for group, ids in request.GROUP_IDS.items():
            oracle = request.oracle_for(ids[0])
            for name, value in [('STATEMENT_SHA256', {pid: q.sha(self.statements[pid]) for pid in ids}), ('CASE_COUNT', {pid: 1 for pid in ids}),
                                ('CASES_SHA256', {pid: q.sha(q.encoded(self.cases[pid])) for pid in ids})]:
                self.stack.enter_context(patch.object(oracle, name, value))
            self.stack.enter_context(patch.object(oracle, 'build_cases', side_effect=lambda pid, raw: (copy.deepcopy(self.cases[pid]), copy.deepcopy(self.categories[pid]))))
            self.stack.enter_context(patch.object(oracle, 'validate'))
        batch_pins = {pid: q.sha(q.encoded(request.batch_manifest(self.cases[pid], request.oracle_for(pid), original_group=request.group_for(pid)))) for pid in request.IDS}
        self.stack.enter_context(patch.object(request, 'BATCHES_SHA256', batch_pins))
        evidence_pins, index_pins = {}, {}
        for group, ids in request.GROUP_IDS.items():
            folder = self.args.evidence_root/group; folder.mkdir()
            q.write(folder/'definition-index.json', {'synthetic': group}); index_pins[group] = q.file_hash(folder/'definition-index.json')
            oracle = request.oracle_for(ids[0]); code = [{'path': oracle.__file__, 'sha256': q.file_hash(oracle.__file__)}]
            deps = [{'path': 'imported_qualification.py', 'sha256': q.sha(predecessor)},
                    {'path': 'imported_clean_domains.py', 'sha256': q.file_hash(Path(__file__).with_name('imported_clean_domains.py'))}]
            population = []
            for pid in ids:
                if group == 'f': row = {'problem_id': pid, 'cases': 1, 'cases_file': {'sha256': oracle.CASES_SHA256[pid]}, 'categories_file': {'sha256': request.CATEGORIES_SHA256[pid]}, 'batches_file': {'sha256': batch_pins[pid]}}
                elif group == 'g': row = {'problem_id': pid, 'case_count': 1, 'cases_sha256': oracle.CASES_SHA256[pid], 'categories_sha256': request.CATEGORIES_SHA256[pid], 'batches_sha256': batch_pins[pid]}
                else: row = {'problem_id': pid, 'cases': 1, 'case_sha256': oracle.CASES_SHA256[pid], 'artifacts': [{'path': f'{pid}.{name}.json', 'sha256': pin} for name, pin in [('categories', request.CATEGORIES_SHA256[pid]), ('batches', batch_pins[pid])]]}
                population.append(row)
            if group == 'f':
                q.write(folder/'preserved-author-freeze-v1.json', {'synthetic_original': True})
                frozen = {'problems': population, 'source_payload_reads_at_freeze': 0, 'candidate_executions': 0,
                          'oracle_module': code[0], 'serialization_dependency': deps[0], 'definition_index': {'sha256': index_pins[group]},
                          'preserved_author_freeze': {'sha256': q.file_hash(folder/'preserved-author-freeze-v1.json')}}
            else: frozen = {'ids': list(ids), 'cases': population, 'source_payload_reads': 0, 'candidate_executions': 0,
                            'code': code, 'dependencies': deps, 'definition_pins': {'sha256': index_pins[group]}}
            q.write(folder/'original-freeze.json', frozen)
            q.write(folder/'independent-review.json', {'reviewer': 'Synthetic fixture, not authority', 'candidate_executions': 0,
                    'pre_source_freeze' if group == 'f' else 'freeze': {'sha256': q.file_hash(folder/'original-freeze.json')}})
            base_rows = [{'problem_id': pid, 'language': lang, 'source_sha256': source_pins[pid][lang]} for pid in ids for lang in request.LANGUAGES]
            nested = [{'problem_id': pid, 'sources': [{'language': lang, 'sha256': source_pins[pid][lang]} for lang in request.LANGUAGES]} for pid in ids]
            for name in ('source-acquisition.json', 'first-static-review.json', 'second-static-review.json'):
                record = {'candidate_executions': 0}
                if group == 'g' and name == 'source-acquisition.json': record['operations'] = [{'problem_id': x['problem_id'], 'language': x['language'], 'sha256': x['source_sha256']} for x in reversed(base_rows)]
                elif (group == 'g' and name == 'first-static-review.json') or (group == 'f' and name == 'second-static-review.json'): record['problems'] = nested
                elif group == 'g': record['reviewed_sources'] = [{'problem_id': x['problem_id'], 'language': x['language'], 'source': {'sha256': x['source_sha256']}} for x in base_rows]
                elif group == 'h' and name == 'first-static-review.json': record['reviewed_sources'] = base_rows
                elif group == 'h' and name == 'second-static-review.json': record['implementations'] = base_rows
                else: record['rows'] = base_rows
                q.write(folder/name, record)
            if group == 'g': q.write(folder/'definition-accounting-clarification.json', {'problem_id': 3574, 'newly_written_statement_descriptor_hash_reads': 3, 'newly_written_transport_descriptor_hash_reads': 1, 'fresh_gate_rerun_immediately_before_each_of_these_four_local_hash_reads': False, 'source_payload_reads_before_oracle_approval': 0})
            evidence_pins[group] = {name: q.file_hash(folder/name) for name in request.ORIGINAL_EVIDENCE[group]}
        self.stack.enter_context(patch.object(request, 'DEFINITION_INDEX_SHA256', index_pins))
        self.stack.enter_context(patch.object(request, 'ORIGINAL_EVIDENCE', evidence_pins))
        self.stack.enter_context(patch.object(q, 'runtime', return_value={'synthetic': True}))
        self.stack.enter_context(patch.object(request.KnownSpecService, 'from_config'))
        self.boundary = self.stack.enter_context(patch.object(request, '_boundary_snapshot', return_value=SimpleNamespace(authorized={f'leetcode:{pid}' for pid in request.IDS})))
        self.gate_check = self.stack.enter_context(patch.object(request, 'authorize_before_open'))

    def prepare(self):
        request.prepare(self.args)
        return q.decode((self.args.output/'contract.json').read_bytes())

    def mutate_evidence(self, group, name, change):
        p = self.args.evidence_root/group/name; value = q.decode(p.read_bytes()); change(value); q.write(p, value)
        request.ORIGINAL_EVIDENCE[group][name] = q.file_hash(p)

    def test_all_thirty_sources_follow_complete_local_freeze_and_replay(self):
        original = q.read; opened = []
        def checked(path, *args):
            p = Path(path)
            if self.args.source_root in p.parents:
                self.gate_check.assert_called_with(f'leetcode:{p.stem}', {}, {}, language=p.parent.name)
                pre = q.decode((self.args.output/'pre-source-freeze.json').read_bytes())
                self.assertEqual(pre['source_payload_reads_at_freeze'], 0)
                self.assertFalse(pre['historical_manifest_payloads_loaded'])
                self.assertIn('does not restore global blindness', pre['read_count_scope'])
                self.assertEqual(set(pre['generated_cases']), {str(pid) for pid in request.IDS})
                opened.append(p)
            elif p.name == 'statement.tool-prefix.txt': self.gate_check.assert_called_with(f'leetcode:{p.parent.name}', {}, {}, language='python', payload_kind='statement')
            self.assertNotIn('manifest-batch', str(p))
            return original(path, *args)
        with patch.object(q, 'read', side_effect=checked): result = request.prepare(self.args)
        self.assertEqual((result['jobs'], result['checks'], len(opened)), (30, 30, 30))
        contract = q.decode((self.args.output/'contract.json').read_bytes()); request.verify_freeze(self.args.output, contract, self.gate)
        self.assertFalse(contract['automatic_promotion']); self.assertEqual(contract['limits'], q.LIMITS)

    def test_existing_loader_dispatches_fixed_successor(self):
        expected = self.prepare(); _, actual, gate = q.load_freeze(self.args.output)
        self.assertEqual(actual, expected); self.assertEqual(gate, self.gate)

    def test_denied_population_or_gate_precedes_payloads(self):
        self.boundary.return_value.authorized.remove('leetcode:3620')
        with patch.object(q, 'read', wraps=q.read) as read, self.assertRaises(PermissionError): request.prepare(self.args)
        self.assertEqual([Path(c.args[0]).name for c in read.call_args_list], ['config.json', 'gate.json'])
        self.boundary.return_value.authorized.add('leetcode:3620'); self.gate_check.side_effect = PermissionError('denied')
        with patch.object(q, 'read', wraps=q.read) as read, self.assertRaises(PermissionError): request.prepare(self.args)
        self.assertEqual(len(read.call_args_list), 2)

    def test_runtime_failure_precedes_any_metadata(self):
        with patch.object(q, 'runtime', side_effect=ValueError('runtime')), patch.object(q, 'read') as read, self.assertRaises(ValueError): request.prepare(self.args)
        read.assert_not_called(); self.assertFalse(self.args.output.exists())

    def test_missing_duplicate_extra_or_legacy_selector_rejected(self):
        p = self.args.selection_root/request.SELECTOR_FILES['g']; before = p.read_bytes()
        for kind in ('missing', 'duplicate', 'extra', 'legacy'):
            value = q.decode(before)
            if kind == 'missing': value['selected'].pop()
            elif kind == 'duplicate': value['selected'][1] = value['selected'][0]
            elif kind == 'extra': value['selected'].append(value['selected'][0])
            else: value['legacy_case_or_reasoning_fields_supplied_to_oracle_authors'] = True
            q.write(p, value); request.SELECTOR_SHA256['g'] = q.file_hash(p)
            with self.subTest(kind=kind), self.assertRaises(ValueError): request.prepare(self.args)
            self.assertFalse(self.args.output.exists())
        p.write_bytes(before)

    def test_selector_parameter_or_source_identity_drift(self):
        p = self.args.selection_root/request.SELECTOR_FILES['f']; before = p.read_bytes()
        for field in ('parameters', 'source_files'):
            value = q.decode(before)
            if field == 'parameters': value['selected'][0][field] = ['wrong']
            else: value['selected'][0][field]['javascript']['path'] = '../escape.js'
            q.write(p, value); request.SELECTOR_SHA256['f'] = q.file_hash(p)
            with self.assertRaises(ValueError): request.prepare(self.args)
            self.assertFalse(self.args.output.exists())
        p.write_bytes(before)

    def test_missing_source_precedes_statement_reads(self):
        self.sources[(3620, 'python')].unlink()
        with patch.object(q, 'read', wraps=q.read) as read, self.assertRaisesRegex(ValueError, 'locators'): request.prepare(self.args)
        self.assertFalse(any(Path(c.args[0]).name == 'statement.tool-prefix.txt' for c in read.call_args_list))

    def test_original_review_freeze_link_must_match(self):
        self.mutate_evidence('g', 'independent-review.json', lambda x: x['freeze'].update(sha256='0'*64))
        with self.assertRaisesRegex(ValueError, 'chronology'): request.prepare(self.args)

    def test_original_blindness_cannot_be_reset_by_later_refreeze(self):
        self.mutate_evidence('h', 'original-freeze.json', lambda x: x.update(source_payload_reads=1))
        self.mutate_evidence('h', 'independent-review.json', lambda x: x['freeze'].update(sha256=request.ORIGINAL_EVIDENCE['h']['original-freeze.json']))
        with self.assertRaisesRegex(ValueError, 'chronology'): request.prepare(self.args)

    def test_preserved_F_first_freeze_link_required(self):
        self.mutate_evidence('f', 'original-freeze.json', lambda x: x['preserved_author_freeze'].update(sha256='0'*64))
        self.mutate_evidence('f', 'independent-review.json', lambda x: x['pre_source_freeze'].update(sha256=request.ORIGINAL_EVIDENCE['f']['original-freeze.json']))
        with self.assertRaisesRegex(ValueError, 'preserved'): request.prepare(self.args)

    def test_G_accounting_cannot_be_retroactively_fresh_gated(self):
        self.mutate_evidence('g', 'definition-accounting-clarification.json', lambda x: x.update(fresh_gate_rerun_immediately_before_each_of_these_four_local_hash_reads=True))
        with self.assertRaisesRegex(ValueError, 'accounting'): request.prepare(self.args)

    def test_static_review_source_pin_and_duplicate_rejected(self):
        self.mutate_evidence('f', 'second-static-review.json', lambda x: x['problems'][0]['sources'][0].update(sha256='0'*64))
        with self.assertRaisesRegex(ValueError, 'source binding'): request.prepare(self.args)

    def test_explicit_static_blocker_rejected(self):
        self.mutate_evidence('h', 'second-static-review.json', lambda x: x['implementations'][0].update(static_blocker_found=True))
        with self.assertRaisesRegex(ValueError, 'blocking'): request.prepare(self.args)

    def test_archived_observer_not_replaced_by_successor(self):
        (self.args.evidence_root/'observer-predecessor.py').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError, 'archived'): request.prepare(self.args)

    def test_helper_drift_precedes_payloads(self):
        original = q.file_hash
        with patch.object(q, 'file_hash', side_effect=lambda p: '0'*64 if Path(p).name == 'imported_clean_domains.py' else original(p)), self.assertRaisesRegex(ValueError, 'helper'): request.prepare(self.args)
        self.assertFalse(self.args.output.exists())

    def test_case_category_or_group_drift_rejected(self):
        self.cases[3620][0]['expected'] = -1
        with self.assertRaisesRegex(ValueError, 'hard-pinned'): request.prepare(self.args)
        self.assertFalse(self.args.output.exists())

    def test_original_G_groups_preserved_and_compact_projection_additive(self):
        oracle = request.oracle_for(3525); old = request.batch_manifest(self.cases[3525], oracle, original_group='g')
        self.assertEqual(old, list(q.batches(self.cases[3525])))
        _, design, provenance = request.generated(3525, self.statements[3525])
        self.assertEqual(design['original_batches_sha256'], request.BATCHES_SHA256[3525])
        self.assertNotEqual(design['original_batches_sha256'], design['batch_projection_sha256'])
        self.assertIn('Additive', provenance['projection_scope'])

    def test_F_projection_drift_rejected(self):
        oracle = request.oracle_for(3537)
        with patch.object(oracle, 'expected_observation_bytes', return_value=1), self.assertRaisesRegex(ValueError, 'grouping'): request.prepare(self.args)
        self.assertFalse(self.args.output.exists())

    def test_source_hash_drift_retains_prefreeze_but_no_contract(self):
        self.sources[(3537, 'javascript')].write_bytes(b'wrong inert fixture')
        with self.assertRaisesRegex(ValueError, 'candidate bytes'): request.prepare(self.args)
        self.assertTrue((self.args.output/'pre-source-freeze.json').exists()); self.assertFalse((self.args.output/'contract.json').exists())

    def test_provenance_equivalence_claim_rejected(self):
        p = self.args.statement_root/'3574/provenance.json'; value = q.decode(p.read_bytes()); value['original_statement_byte_equivalence_claimed'] = True; q.write(p, value); request.PROVENANCE_SHA256[3574] = q.file_hash(p)
        with self.assertRaisesRegex(ValueError, 'representation'): request.definition_provenance(p, 3574)

    def test_fixed_population_interface_and_caps_before_reads(self):
        contract = self.prepare()
        for field, value in [('automatic_promotion', True), ('protected_access', True), ('max_packet_bytes', 2200000), ('additional_code', {}), ('pending', [1])]:
            bad = copy.deepcopy(contract); bad[field] = value
            with patch.object(q, 'read', side_effect=AssertionError('no payload')), self.assertRaises(ValueError): request.verify_freeze(self.args.output, bad, self.gate)
        for field, value in [('id', 3215), ('source_interface', 'global-solve-v1'), ('max_cases_per_batch', 1)]:
            bad = copy.deepcopy(contract); bad['jobs'][0][field] = value
            with patch.object(q, 'read', side_effect=AssertionError('no payload')), self.assertRaises(ValueError): request.verify_freeze(self.args.output, bad, self.gate)

    def test_replay_checks_original_selector_and_case_artifacts(self):
        contract = self.prepare()
        for name in ('pre-source-freeze.json', 'case-provenance.json', 'selectors/g-selection-v2.json', 'original-evidence/g/definition-accounting-clarification.json', 'original-evidence/f/original-freeze.json', 'statements/3574.provenance.json', 'statements/3525.md', 'tests/3620.json'):
            p = self.args.output/name; old = p.read_bytes(); p.write_bytes(old+b' ')
            with self.subTest(name=name), self.assertRaises(ValueError): request.verify_freeze(self.args.output, contract, self.gate)
            p.write_bytes(old)

    def test_denied_replay_precedes_payloads(self):
        contract = self.prepare(); self.gate_check.side_effect = PermissionError('denied')
        with patch.object(q, 'read', side_effect=AssertionError('no payload')), self.assertRaises(PermissionError): request.verify_freeze(self.args.output, contract, self.gate)


class FGHRunnerBoundaryTests(unittest.TestCase):
    def test_unknown_domain_or_foreign_id_before_reads(self):
        for pid, domain in [(3215, request.DOMAIN), (True, request.DOMAIN), (3537, 'request-fgh16-v1')]:
            job = {'id': pid, 'language': 'javascript', 'domain_validator': domain, 'source_interface': 'commonjs-object-solve-v1'}
            with patch.object(q, 'read', side_effect=AssertionError('no payload')), self.assertRaises(ValueError): q.job_inputs(Path('/synthetic'), job, {})

    def test_new_pins_add_only_existing_fixed_owner_files(self):
        expected = {'request_parallel_fgh15_qualification.py', 'request_parallel_f_oracles.py', 'request_parallel_g_oracles.py', 'request_parallel_h_oracles.py', 'imported_clean_domains.py'}
        self.assertEqual({Path(p).name for p in request.additional_code()}, expected)
        pins = q.code_pins()
        for p, value in request.additional_code().items(): self.assertEqual(pins[p], value)

    def test_unapproved_additional_path_rejected_before_open(self):
        contract = {'schema': 'gamma.imported-independent-execution.v1', 'code': {'fixed': 'pin'}, 'limits': q.LIMITS,
                    'jobs': [{'domain_validator': request.DOMAIN}], 'additional_code': {'/unapproved/source.py': 'pin'}}
        with patch.object(q, 'read', return_value=q.encoded(contract)), patch.object(q, 'code_pins', return_value={'fixed': 'pin'}), patch.object(request, 'additional_code', return_value={'/fixed/module.py': 'pin'}), patch.object(q, 'file_hash', side_effect=AssertionError('unapproved open')), self.assertRaisesRegex(ValueError, 'unapproved fixed F/G/H'): q.load_freeze(Path('/synthetic'))

    def test_reader_dispatches_all_fifteen_full_domain_validators(self):
        examples = {3537: [0], 3542: [[0]], 3573: [[1, 2], 1], 3576: [[1], 1], 3614: ['a', 0],
                    3525: [[1], 1, [[0, 1, 0, 0]]], 3552: [['.']], 3561: ['a'], 3574: [[1], 1], 3599: [[1], 1],
                    3534: [1, [0], 0, [[0, 0]]], 3568: [['S'], 1], 3600: [2, [[0, 1, 1, 0]], 0],
                    3613: [1, [], 1], 3620: [[], [True, True], 0]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'sources').mkdir(); (root/'tests').mkdir()
            for pid, valid in examples.items():
                source = b'Inert reader fixture; never executed.'; (root/f'sources/{pid}.js').write_bytes(source)
                job = {'id': pid, 'language': 'javascript', 'source': f'sources/{pid}.js', 'tests': f'tests/{pid}.json',
                       'source_sha256': q.sha(source), 'case_count': 1, 'domain_validator': request.DOMAIN, 'source_interface': 'commonjs-object-solve-v1'}
                for args, accepted in [(valid, True), ([None], False)]:
                    cases = [{'args': args, 'expected': 0, 'compare': 'return'}]; raw = q.encoded(cases)
                    (root/job['tests']).write_bytes(raw); job['tests_raw_sha256'] = q.sha(raw)
                    with self.subTest(pid=pid, accepted=accepted), patch.object(q, 'authorize_before_open') as gate:
                        if accepted: self.assertEqual(q.job_inputs(root, job, {'artifact_paths': {}, 'trusted_hashes': {}}), (source, cases))
                        else:
                            with self.assertRaises(ValueError): q.job_inputs(root, job, {'artifact_paths': {}, 'trusted_hashes': {}})
                        gate.assert_called_once_with(f'leetcode:{pid}', {}, {}, language='javascript')

    def test_reader_denied_gate_precedes_sources_and_cases(self):
        job = {'id': 3537, 'language': 'javascript', 'source': 'sources/3537.js', 'tests': 'tests/3537.json',
               'domain_validator': request.DOMAIN, 'source_interface': 'commonjs-object-solve-v1'}
        with patch.object(q, 'authorize_before_open', side_effect=PermissionError('denied')), patch.object(q, 'read') as read, self.assertRaises(PermissionError):
            q.job_inputs(Path('/synthetic'), job, {'artifact_paths': {}, 'trusted_hashes': {}})
        read.assert_not_called()

    def test_limits_and_group_domain_identity_unchanged(self):
        for group, ids in request.GROUP_IDS.items():
            self.assertEqual(request.oracle_for(ids[0]).IDS, ids)
            for pid in ids:
                with self.assertRaises(ValueError): request.validate(pid, [None])
        cases = [{'args': [0], 'expected': 0, 'compare': 'return'}]*65
        self.assertEqual([(offset, len(batch)) for offset, batch in q.batches(cases)], [(0,32),(32,32),(64,1)])
        with self.assertRaisesRegex(ValueError, 'no silent truncation'): list(q.batches([{'args': ['a'*q.MAX_PACKET], 'expected': 0, 'compare': 'return'}]))


if __name__ == '__main__':
    unittest.main()
