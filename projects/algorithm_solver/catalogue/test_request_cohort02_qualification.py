"""Source-free fixed42 request/evidence/batching boundaries; no sandbox probes."""
from copy import deepcopy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_cohort02_qualification as owner


class Cohort02RequestTests(unittest.TestCase):
    def test_population_is_exact_dual_reviewed_ordinary_cohort(self):
        self.assertEqual(len(owner.IDS), 42)
        self.assertEqual(tuple(sorted(owner.BINDINGS)), owner.IDS)
        self.assertEqual(sum(len(ids) for ids in owner.SOURCE_GROUPS.values()), 42)
        self.assertEqual(set().union(*(set(ids) for ids in owner.SOURCE_GROUPS.values())), set(owner.IDS))
        for ids in owner.HELD_OUTSIDE_POPULATION.values():
            self.assertTrue(set(owner.IDS).isdisjoint(ids))
        self.assertEqual(sum(row['case_count'] for row in owner.BINDINGS.values()), 74825)
        self.assertEqual(sum(row['batch_count'] for row in owner.BINDINGS.values()), 2381)
        for pid in owner.IDS:
            spec = owner.binding(pid)
            self.assertEqual(set(spec['source_sha256']), set(owner.LANGUAGES))
            self.assertIn(pid, owner.oracle_for(pid).IDS)
            self.assertEqual(list(owner.oracle_for(pid).PARAMETERS[pid]), spec['parameters'])
        self.assertEqual(len(owner.additional_code()), 12)

    def test_held_unknown_and_boolean_ids_fail_before_access(self):
        invalid = [True, '2585', 2415, 999999] + [x for ids in owner.HELD_OUTSIDE_POPULATION.values() for x in ids]
        for pid in invalid:
            with self.subTest(pid=pid), patch.object(owner, 'read_payload') as read:
                with self.assertRaises(ValueError):
                    owner.source_bytes('/unused', pid, 'python', {}, receipt_path='/unused-log')
                read.assert_not_called()

    def test_invalid_language_and_denial_fail_before_source_return(self):
        with patch.object(owner, 'read_payload') as read:
            with self.assertRaises(ValueError):
                owner.source_bytes('/unused', owner.IDS[0], 'ruby', {}, receipt_path='/unused-log')
            read.assert_not_called()
        with tempfile.TemporaryDirectory() as root, patch.object(owner, 'read_payload', side_effect=PermissionError('closed')) as read:
            log = Path(root) / 'access.jsonl'
            with self.assertRaises(PermissionError):
                owner.source_bytes('/unused', owner.IDS[0], 'python',
                                   {'artifact_paths': {}, 'trusted_hashes': {}}, receipt_path=log)
            read.assert_called_once()
            record = q.decode(log.read_bytes())
            self.assertEqual(record['status'], 'failed')
            self.assertEqual(record['exception_type'], 'PermissionError')
            self.assertIsNone(record['receipt'])
            self.assertIn('unknown', record['payload_open_attempts'])

    def test_hash_oid_and_length_are_delegated_with_unchanged_source_bound(self):
        raw = b'inert synthetic byte-identity control\n'; pid = owner.IDS[0]
        spec = owner.binding(pid); gate = {'artifact_paths': {}, 'trusted_hashes': {}}
        receipt = {'identity_verified': True, 'sha256': q.sha(raw), 'payload_read_count': 1}
        with tempfile.TemporaryDirectory() as root, patch.object(owner, 'read_payload', return_value=(raw, receipt)) as read:
            log = Path(root) / 'access.jsonl'
            self.assertEqual(owner.source_bytes('/unused', pid, 'python', gate, receipt_path=log), raw)
            read.assert_called_once_with('/unused', problem_id=f'leetcode:{pid}', language='python',
                payload_kind='source', artifact_paths={}, trusted_hashes={},
                expected_sha256=spec['source_sha256']['python'], maximum_bytes=1024 * 1024,
                expected_size=spec['source_bytes']['python'], expected_git_blob_oid=spec['git_blob_oid']['python'])
            self.assertEqual(q.decode(log.read_bytes())['receipt'], receipt)

    def test_statement_read_uses_shared_helper_and_original_file_bound(self):
        pid = owner.IDS[0]; raw = b'inert definition'; receipt = {'identity_verified': True}
        with tempfile.TemporaryDirectory() as root, patch.object(owner, 'read_payload', return_value=(raw, receipt)) as read:
            log = Path(root) / 'access.jsonl'
            self.assertEqual(owner.statement_bytes('/unused', pid, {'artifact_paths': {}, 'trusted_hashes': {}}, receipt_path=log), raw)
            read.assert_called_once_with('/unused', problem_id=f'leetcode:{pid}', language='python', payload_kind='statement',
                artifact_paths={}, trusted_hashes={}, expected_sha256=owner.binding(pid)['statement_sha256'], maximum_bytes=q.MAX_FILE)
            self.assertEqual(q.decode(log.read_bytes())['receipt'], receipt)

    def test_identity_failure_retains_receipt_and_does_not_return_bytes(self):
        from .gated_payload_read import PayloadIdentityError
        receipt = {'mismatches': ['sha256'], 'payload_read_count': 1, 'identity_verified': False}
        with tempfile.TemporaryDirectory() as root, patch.object(owner, 'read_payload', side_effect=PayloadIdentityError(receipt)) as read:
            log = Path(root) / 'access.jsonl'
            with self.assertRaises(PayloadIdentityError):
                owner.statement_bytes('/unused', owner.IDS[0], {'artifact_paths': {}, 'trusted_hashes': {}}, receipt_path=log)
            read.assert_called_once()
            record = q.decode(log.read_bytes())
            self.assertEqual(record['receipt'], receipt)
            self.assertNotIn('payload_open_attempts', record)

    def test_private_acquisition_log_appends_and_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            log = Path(root) / 'access.jsonl'
            owner.record_payload_read(log, {'record': 1})
            owner.record_payload_read(log, {'record': 2})
            self.assertEqual([q.decode(line) for line in log.read_bytes().splitlines()], [{'record': 1}, {'record': 2}])
            link = Path(root) / 'link'; link.symlink_to(log)
            with self.assertRaises(OSError): owner.record_payload_read(link, {'record': 3})
            self.assertEqual(len(log.read_bytes().splitlines()), 2)

    def test_private_log_rejects_parent_symlink_and_noncanonical_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'A').mkdir(); (root / 'B').mkdir()
            (root / 'A/redirect').symlink_to(root / 'B', target_is_directory=True)
            with self.assertRaises(OSError): owner.record_payload_read(root / 'A/redirect/access.jsonl', {})
            self.assertFalse((root / 'B/access.jsonl').exists())
            for path in ('relative', '/', str(root) + '//log', str(root) + '/./log',
                         str(root) + '/../log', str(root) + '/log/', str(root) + '/\0log'):
                with self.subTest(path=path), patch.object(owner.os, 'open') as opener:
                    with self.assertRaises(ValueError): owner.record_payload_read(path, {})
                    opener.assert_not_called()

    def test_mutable_access_sidecar_does_not_change_immutable_payloads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            retained = {name: b'inert immutable ' + name.encode() for name in ('contract.json', 'cases.json', 'source.txt')}
            for name, raw in retained.items(): (root / name).write_bytes(raw)
            log = root / owner.MUTABLE_ACCESS_LOG
            owner.record_payload_read(log, {'record': 1})
            owner.record_payload_read(log, {'record': 2})
            self.assertEqual({name: (root / name).read_bytes() for name in retained}, retained)
            self.assertNotIn(str(log), owner.additional_code())

    def test_access_log_bound_nonregular_and_write_failure_are_fail_closed(self):
        import os
        from .gated_payload_read import PayloadIdentityError
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); log = root / 'access.jsonl'; log.write_bytes(b'12345')
            with patch.object(owner, 'MAX_ACCESS_LOG_BYTES', 5), self.assertRaises(ValueError):
                owner.record_payload_read(log, {})
            self.assertEqual(log.read_bytes(), b'12345')
            fifo = root / 'fifo'; os.mkfifo(fifo)
            with self.assertRaises((OSError, ValueError)): owner.record_payload_read(fifo, {})
            receipt = {'mismatches': ['sha256']}; failure = PayloadIdentityError(receipt)
            with patch.object(owner, 'read_payload', side_effect=failure), \
                    patch.object(owner, 'record_payload_read', side_effect=OSError('log unavailable')):
                with self.assertRaises(OSError) as caught:
                    owner.statement_bytes('/unused', owner.IDS[0], {'artifact_paths': {}, 'trusted_hashes': {}}, receipt_path=log)
                self.assertIs(caught.exception.__context__, failure)
                self.assertEqual(caught.exception.__context__.receipt, receipt)
            with patch.object(owner, 'read_payload', return_value=(b'inert', {})), \
                    patch.object(owner, 'record_payload_read', side_effect=OSError('log unavailable')):
                with self.assertRaises(OSError):
                    owner.statement_bytes('/unused', owner.IDS[0], {'artifact_paths': {}, 'trusted_hashes': {}}, receipt_path=log)

    def test_fixed_jobs_use_existing_ordinary_interfaces_only(self):
        for pid in owner.IDS:
            for language in owner.LANGUAGES:
                job = owner.make_job(Path('/unused'), pid, language, [], '/original')
                self.assertEqual(job['comparison_policy'], 'exact')
                self.assertEqual(job['domain_validator'], 'request-cohort02-v1')
                self.assertEqual(job['source_sha256'], owner.binding(pid)['source_sha256'][language])
                self.assertNotIn('node_identity', job)
                self.assertEqual(q.source_interface(job), 'commonjs-function-solve-v1' if language == 'javascript' else 'global-solve-v1')

    def test_fixed_domain_rejects_wrong_identity_or_interface_before_access(self):
        base = owner.make_job(Path('/unused'), owner.IDS[0], 'python', [], '/original')
        for change in ({'id': 2415}, {'id': True}, {'source_interface': 'commonjs-function-solve-v1'},
                       {'source_interface': 'native2415-global-solve-v1'}, {'comparison_policy': 'problem:2415'},
                       {'node_identity': True}, {'node_identity': 0}):
            with self.subTest(change=change), patch.object(q, 'read') as read, patch.object(q, 'authorize_before_open') as gate:
                with self.assertRaises(ValueError): q.job_inputs(Path('/unused'), {**base, **change}, {})
                read.assert_not_called(); gate.assert_not_called()

    def test_fixed_owner_code_closure_checked_before_service_or_payload(self):
        contract = {'schema': 'gamma.imported-independent-execution.v1', 'code': {}, 'limits': q.LIMITS,
                    'jobs': [{'domain_validator': owner.DOMAIN}], 'additional_code': {}}
        with patch.object(q, 'read', return_value=b'{}') as read, patch.object(q, 'decode', return_value=contract), \
                patch.object(q, 'code_pins', return_value={}), patch.object(owner, 'additional_code', return_value={'owner': 'pin'}), \
                patch.object(q.KnownSpecService, 'from_config') as service:
            with self.assertRaisesRegex(ValueError, 'unapproved fixed cohort02'): q.load_freeze(Path('/unused'))
            self.assertEqual(read.call_count, 1); service.assert_not_called()

    def test_execution_source_read_uses_same_fixed_owner_helper(self):
        pid = owner.IDS[0]; cases = [{'args': [1], 'expected': 2, 'compare': 'return'}]
        source = b'inert synthetic dispatch bytes'; raw = q.encoded(cases)
        job = owner.make_job(Path('/unused'), pid, 'python', cases, '/original')
        job.update(source_sha256=q.sha(source), tests_raw_sha256=q.sha(raw), case_count=1)
        with patch.object(owner, 'source_bytes', return_value=source) as source_read, \
                patch.object(q, 'read', return_value=raw) as read, patch.object(owner, 'validate') as validate, \
                patch.object(q, 'authorize_before_open') as legacy_gate:
            self.assertEqual(q.job_inputs(Path('/unused'), job, {}), (source, cases))
            source_read.assert_called_once_with(Path('/unused')/job['source'], pid, 'python', {},
                                                receipt_path=Path('/unused/payload-acquisition.jsonl'))
            read.assert_called_once_with(Path('/unused')/job['tests'])
            validate.assert_called_once_with(pid, [1]); legacy_gate.assert_not_called()

    def evidence_fixture(self):
        values = {name: {} for name in owner.EVIDENCE_SHA256}
        for group, ids in owner.SOURCE_GROUPS.items():
            for review in ('first', 'second'):
                schema, key, nested = owner.REVIEW_SCHEMAS[group][review]; rows = []
                for pid in ids:
                    for lang in owner.LANGUAGES:
                        spec = owner.binding(pid)
                        source = {'sha256' if nested else 'source_sha256': spec['source_sha256'][lang],
                                  'git_blob_oid': spec['git_blob_oid'][lang], 'bytes': spec['source_bytes'][lang]}
                        rows.append({'problem_id': pid, 'language': lang, **({'source': source} if nested else source)})
                values[f'{group}-{review}-review.json'] = {'schema': schema, key: rows}
        return values

    def test_both_source_reviews_must_cover_each_exact_identity_once(self):
        base = self.evidence_fixture()
        with patch.object(owner, 'pinned', side_effect=lambda path, pin: q.encoded(base[Path(path).name])):
            self.assertEqual(len(owner.evidence(Path('/unused'))), len(owner.EVIDENCE_SHA256))
        for group in owner.SOURCE_GROUPS:
            for review in ('first', 'second'):
                schema, key, nested = owner.REVIEW_SCHEMAS[group][review]
                for damage in ('missing', 'duplicate', 'hash', 'oid', 'length', 'schema'):
                    bad = deepcopy(base); value = bad[f'{group}-{review}-review.json']; rows = value[key]
                    if damage == 'missing': rows.pop()
                    elif damage == 'duplicate': rows[-1] = deepcopy(rows[0])
                    elif damage == 'schema': value['schema'] = 'unreviewed'
                    else:
                        source = rows[0]['source'] if nested else rows[0]
                        source[{'hash': 'sha256' if nested else 'source_sha256', 'oid': 'git_blob_oid', 'length': 'bytes'}[damage]] = 'wrong'
                    with self.subTest(group=group, review=review, damage=damage), \
                            patch.object(owner, 'pinned', side_effect=lambda path, pin: q.encoded(bad[Path(path).name])):
                        with self.assertRaises(ValueError): owner.evidence(Path('/unused'))

    def test_original_batch_schemas_are_preserved_and_expected_stays_on_host(self):
        cases = [{'args': [1], 'expected': 987654321, 'compare': 'return'}] * 33
        for group, ids in owner.SOURCE_GROUPS.items():
            rows = owner.batch_manifest(ids[0], cases)
            self.assertEqual([(r['offset'], r['count']) for r in rows], [(0, 32), (32, 1)])
            expected_fields = {'offset', 'count', 'packet_bytes'}
            expected_fields.add('projected_output_bytes' if group == 'q05s02' else 'expected_observation_bytes')
            if group.startswith(('q07', 'q08')): expected_fields.add('packet_sha256')
            self.assertEqual(set(rows[0]), expected_fields)
            self.assertNotIn(b'987654321', q.encoded(q.packet(cases)))
        for pid in owner.SOURCE_GROUPS['q07s01']:
            self.assertNotEqual(owner.binding(pid)['original_batch_manifest_sha256'], owner.binding(pid)['batches_sha256'])

    def test_statement_mismatch_precedes_oracle_regeneration(self):
        pid = owner.IDS[0]
        with patch.object(owner.oracle_for(pid), 'build_cases') as build:
            with self.assertRaisesRegex(ValueError, 'statement'): owner.generated(pid, b'not a definition', {})
            build.assert_not_called()

    def test_generated_checks_each_original_schema_without_normalizing_cases(self):
        statement = b'inert synthetic statement binding control'
        for group, ids in owner.SOURCE_GROUPS.items():
            pid = ids[0]; case = {'args': [1], 'expected': 2}
            if group != 'q07s01': case['compare'] = 'return'
            cases, categories = [case], ['synthetic']; spec = deepcopy(owner.binding(pid))
            groups = owner.batch_manifest(pid, cases)
            spec.update(statement_sha256=q.sha(statement), case_count=1, cases_sha256=q.sha(q.encoded(cases)),
                        categories_sha256=q.sha(q.encoded(categories)), batch_count=1, batches_sha256=q.sha(q.encoded(groups)))
            if group == 'q07s01': spec['original_batch_manifest_sha256'] = q.canonical_tests_hash(groups)
            row = {'batch_plan': groups, 'batches': groups, 'batches_sha256': q.sha(q.encoded(groups))}
            with self.subTest(group=group), patch.dict(owner.BINDINGS, {pid: spec}), \
                    patch.object(owner.oracle_for(pid), 'build_cases', return_value=(cases, categories)), \
                    patch.object(owner, 'frozen_row', return_value=row), patch.object(owner, 'validate') as validate:
                actual = owner.generated(pid, statement, {})
                self.assertIs(actual[0], cases); self.assertEqual(actual, (cases, categories))
                self.assertEqual(set(actual[0][0]), {'args', 'expected'} if group == 'q07s01' else {'args', 'expected', 'compare'})
                validate.assert_called_once_with(pid, [1])
                spec['categories_sha256'] = '0'*64
                with self.assertRaisesRegex(ValueError, 'case/category'): owner.generated(pid, statement, {})

    def test_original943_base_and_population_are_fail_closed(self):
        with self.assertRaises(ValueError):
            owner.original_base({'catalogue': {'sha256': '0'*64}, 'verified_receipts': {'sha256': '0'*64}})
        with patch.object(owner, 'evidence') as evidence:
            for jobs in ([], [{'id': owner.IDS[0], 'language': 'python'}], [{'id': 2415, 'language': 'javascript'}]):
                with self.assertRaises(ValueError): owner.verify_freeze(Path('/unused'), {'jobs': jobs}, {})
            evidence.assert_not_called()

    def test_runtime_failure_does_not_read_payloads_or_create_output(self):
        with tempfile.TemporaryDirectory() as root:
            args = SimpleNamespace(output=Path(root)/'freeze')
            with patch.object(q, 'runtime', side_effect=ValueError('not approved')), patch.object(owner, 'evidence') as evidence:
                with self.assertRaises(ValueError): owner.prepare(args)
                evidence.assert_not_called()
            self.assertFalse(args.output.exists())

    def test_post_source_interface_requires_every_explicit_approval_flag(self):
        contract = q.encoded(owner.interface_contract())
        flags = ('independent_review', 'approved', 'original_candidate_bytes_unchanged', 'effects_and_domain_unchanged',
                 'cases_unchanged', 'runtime_bounds_unchanged', 'original_pre_source_gaps_preserved',
                 'historical_support_not_reclassified_as_live_approval', 'exposure_and_omissions_preserved')
        valid = {'schema': 'gamma.cohort02-ordinary-interface-review.v1', 'reviewer': 'independent synthetic reviewer',
                 'contract_sha256': q.sha(contract), 'old_object_loader_sha256': owner.OLD_LOADER_SHA256,
                 'function_loader_sha256': owner.FUNCTION_LOADER_SHA256, **{key: True for key in flags}}
        for key, bad in [(key, False) for key in flags] + [('contract_sha256', '0'*64), ('reviewer', ''),
                                                         ('function_loader_sha256', '0'*64)]:
            with self.subTest(key=key), patch.object(owner, 'pinned', side_effect=[contract, q.encoded({**valid, key: bad})]):
                with self.assertRaises(ValueError): owner.approved_interface(Path('/unused'), 'synthetic pin')
        with patch.object(owner, 'pinned', side_effect=[contract, q.encoded(valid)]):
            self.assertEqual(owner.approved_interface(Path('/unused'), 'synthetic pin'), (contract, q.encoded(valid)))


if __name__ == '__main__': unittest.main()
