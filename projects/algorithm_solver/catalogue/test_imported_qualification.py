"""Failure-oriented checks for the independent import execution boundary."""
import json
import io
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import imported_qualification as q


class VerificationTests(unittest.TestCase):
    def record(self, result=7, kind='int'):
        return {'i': 0, 'result': result, 'result_type': kind,
                'args_before': [3, 4], 'args_after': [3, 4], 'alias_edges': []}

    def test_numeric_bool_and_container_types(self):
        case = {'args': [3, 4], 'expected': 7}
        self.assertIsNone(q.compare(case, self.record(), 'python'))
        self.assertEqual(q.compare(case, self.record(True, 'bool'), 'python'), 'result_type')
        self.assertEqual(q.compare(case, self.record(7.0), 'python'), 'result_value')
        self.assertEqual(q.expected_type([], 'javascript'), 'object')

    def test_input_mutation_and_return_alias_are_failures(self):
        case = {'args': [3, 4], 'expected': 7}
        record = self.record(); record['args_after'] = [4, 3]
        self.assertEqual(q.compare(case, record, 'python'), 'input_effects')
        record = self.record(); record['alias_edges'] = [['result', 'args.0']]
        self.assertEqual(q.compare(case, record, 'python'), 'return_aliases')

    def test_complete_ordered_observation_protocol(self):
        cases = [{'args': [3, 4], 'expected': 7}]
        good = q.encoded(self.record()) + q.encoded({'done': 1})
        self.assertEqual(q.check_output(good, cases, 'python'), [])
        for bad in [q.encoded(self.record()), good + good, q.encoded({'done': 1}),
                    q.encoded(dict(self.record(), i=True)) + q.encoded({'done': 1})]:
            with self.assertRaises(ValueError):
                q.check_output(bad, cases, 'python')

    def test_duplicate_fields_and_nonfinite_are_rejected(self):
        for raw in [b'{"i":0,"i":1}', b'{"result":NaN}']:
            with self.assertRaises(ValueError):
                q.decode(raw)

    def test_packet_never_contains_expected_answers(self):
        cases = [{'args': [1], 'expected': 987654321, 'compare': 'return'}]
        value = q.packet(cases)
        self.assertEqual(value['calls'], [{'args': [1]}])
        self.assertNotIn('987654321', json.dumps(value))

    def test_oversize_case_is_not_silently_dropped(self):
        with self.assertRaisesRegex(ValueError, 'cap'):
            list(q.batches([{'args': ['x' * q.MAX_PACKET]}]))
        cases = [{'args': [i]} for i in range(65)]
        groups = list(q.batches(cases))
        self.assertEqual([o for o, _ in groups], [0, 32, 64])
        self.assertEqual([c for _, group in groups for c in group], cases)


class PinnedRuntimeRouteTests(unittest.TestCase):
    def identity(self):
        return {'schema': q.PINNED_RUNTIME_SCHEMA, 'host': {'host': 'pinned'},
                'node': {'approved': 'manifest'}}

    def test_explicit_route_reuses_adapter_and_never_looks_for_system_node(self):
        node = Path('/approved/node')
        with patch.object(q.pinned_runtime, 'freeze_runtime', return_value={'approved': 'manifest'}) as freeze, \
                patch.object(q.subprocess, 'run', return_value=SimpleNamespace(stdout='')) as ldd, \
                patch.object(q, 'file_hash', return_value='hash'):
            value = q.runtime(node)
        freeze.assert_called_once_with(node)
        self.assertEqual(value['schema'], q.PINNED_RUNTIME_SCHEMA)
        self.assertEqual(value['node'], {'approved': 'manifest'})
        self.assertNotIn('/usr/bin/node', value['host'])
        self.assertEqual({call.args[0][1] for call in ldd.call_args_list},
                         {'/usr/bin/python3', '/usr/bin/bwrap', '/usr/bin/prlimit'})

    def test_default_route_has_no_implicit_pinned_fallback(self):
        with patch.object(q.subprocess, 'run', side_effect=FileNotFoundError('missing runtime')), \
                patch.object(q.pinned_runtime, 'freeze_runtime') as pinned:
            with self.assertRaises(FileNotFoundError):
                q.runtime()
        pinned.assert_not_called()

    def test_frozen_route_and_all_identities_are_checked(self):
        identity = self.identity()
        with patch.object(q, 'runtime', return_value=identity) as current:
            q.verify_runtime({'runtime': identity}, Path('/approved/node'))
            current.assert_called_once_with(Path('/approved/node'))
        for frozen, path in [(identity, None), ({'/usr/bin/node': {}}, Path('/approved/node')),
                             ({'schema': 'unknown'}, None)]:
            with self.subTest(frozen=frozen, path=path), patch.object(q, 'runtime') as current:
                with self.assertRaisesRegex(ValueError, 'route differs'):
                    q.verify_runtime({'runtime': frozen}, path)
                current.assert_not_called()
        with patch.object(q, 'runtime', return_value={**identity, 'host': {'drift': True}}):
            with self.assertRaisesRegex(ValueError, 'runtime drift'):
                q.verify_runtime({'runtime': identity}, Path('/approved/node'))

    def test_node_dispatch_preserves_limits_arguments_and_exact_files(self):
        files = {'program.js': b'inert', 'inputs.json': b'{}', 'harness.cjs': b'inert'}
        identity = self.identity()
        with patch.object(q.pinned_runtime, 'run_node', return_value='isolated') as pinned, \
                patch.object(q.sandbox, 'run') as legacy:
            self.assertEqual(q.run_batch('javascript', files, identity, Path('/approved/node')), 'isolated')
        pinned.assert_called_once_with(Path('/approved/node'), manifest=identity['node'], files=files,
                                       limits=q.sandbox.Limits(**q.LIMITS), node_args=q.NODE_ARGS)
        legacy.assert_not_called()

    def test_python_and_legacy_node_keep_existing_sandbox(self):
        with patch.object(q.sandbox, 'run') as legacy, patch.object(q.pinned_runtime, 'run_node') as pinned:
            q.run_batch('python', {}, self.identity(), Path('/approved/node'))
            self.assertEqual(legacy.call_args.args[0], ['/usr/bin/python3', '-I', '-S', 'harness.py'])
            q.run_batch('javascript', {}, {})
            self.assertEqual(legacy.call_args.args[0], ['/usr/bin/node', *q.NODE_ARGS])
        pinned.assert_not_called()

    def test_batch_cannot_silently_change_runtime_route(self):
        for identity, path in [(self.identity(), None), ({}, Path('/approved/node')),
                               ({'schema': 'unknown'}, None)]:
            with self.subTest(identity=identity, path=path), \
                    patch.object(q.sandbox, 'run') as legacy, patch.object(q.pinned_runtime, 'run_node') as pinned:
                with self.assertRaisesRegex(ValueError, 'route differs'):
                    q.run_batch('javascript', {}, identity, path)
                legacy.assert_not_called(); pinned.assert_not_called()

    def test_runtime_failure_precedes_payload_access_and_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(freeze=Path(directory) / 'freeze', output=Path(directory) / 'out',
                                   node_runtime=Path('/approved/node'), max_wall=10)
            with patch.object(q, 'load_freeze', return_value=(b'{}', {'runtime': self.identity()}, {})), \
                    patch.object(q, 'verify_runtime', side_effect=ValueError('runtime drift')), \
                    patch.object(q, 'job_inputs') as inputs:
                with self.assertRaisesRegex(ValueError, 'runtime drift'):
                    q.execute(args)
                inputs.assert_not_called()
                self.assertFalse(args.output.exists())

    def test_prepare_runtime_failure_precedes_service_or_case_access(self):
        from . import prepare_fresh_qualification as fresh
        for prepare in (q.prepare, fresh.prepare):
            with self.subTest(prepare=prepare.__module__), \
                    patch.object(q, 'runtime', side_effect=ValueError('unapproved runtime')), \
                    patch.object(q.KnownSpecService, 'from_config') as service:
                with self.assertRaisesRegex(ValueError, 'unapproved runtime'):
                    prepare(SimpleNamespace(node_runtime=Path('/unapproved/node')))
                service.assert_not_called()

    def test_execution_rechecks_runtime_and_retains_nonpromotion(self):
        identity = self.identity()
        job = {'id': 1, 'language': 'javascript'}
        contract = {'runtime': identity, 'jobs': [job]}
        cases = [{'args': [3, 4], 'expected': 7}]
        record = {'i': 0, 'result': 7, 'result_type': 'number',
                  'args_before': [3, 4], 'args_after': [3, 4], 'alias_edges': []}
        result = q.sandbox.SandboxResult(0, None, q.encoded(record) + q.encoded({'done': 1}), b'', 0.1)
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(freeze=Path(directory) / 'freeze', output=Path(directory) / 'out',
                                   node_runtime=Path('/approved/node'), max_wall=10)
            with patch.object(q, 'load_freeze', return_value=(q.encoded(contract), contract, {})), \
                    patch.object(q, 'job_inputs', return_value=(b'inert source', cases)), \
                    patch.object(q, 'verify_runtime') as verify, patch.object(q, 'run_batch', return_value=result) as run, \
                    redirect_stdout(io.StringIO()):
                outcome = q.execute(args)
            self.assertEqual(outcome, {'status': 'completed', 'passed': 1, 'total': 1})
            self.assertEqual(verify.call_count, 2)
            files = run.call_args.args[1]
            self.assertEqual(q.decode(files['inputs.json']), q.packet(cases))
            self.assertNotIn('expected', q.decode(files['inputs.json']))
            self.assertEqual(q.decode((args.output / 'report.json').read_bytes())['new_qualifications'], 0)


class SourceInterfaceTests(unittest.TestCase):
    def test_default_observers_are_unchanged(self):
        self.assertEqual(q.observer_files({'language': 'python'}), {'harness.py': q.read(q.HARNESS / 'harness.py')})
        self.assertEqual(q.observer_files({'language': 'javascript'}), {'harness.cjs': q.read(q.HARNESS / 'harness.cjs')})

    def test_commonjs_reuses_exact_existing_typed_effect_helper(self):
        files = q.observer_files({'language': 'javascript', 'source_interface': 'commonjs-object-solve-v1'})
        self.assertEqual(files, {'harness.cjs': q.read(q.COMMONJS_HARNESS),
                                 'observer.cjs': q.read(q.HARNESS / 'harness.cjs')})

    def test_invalid_combinations_fail_before_payload_or_gate_reads(self):
        for changes in ({'source_interface': 'guess'},
                        {'source_interface': 'commonjs-object-solve-v1', 'language': 'python'},
                        {'source_interface': 'commonjs-object-solve-v1', 'node_identity': True},
                        {'id': 3216, 'domain_validator': 'request3215-v1'},
                        {'id': 3215, 'domain_validator': 'request-next4-v1'},
                        {'domain_validator': 'not-approved'}):
            job = {'id': 3215, 'language': 'javascript', **changes}
            with self.subTest(job=job), patch.object(q, 'read') as read, patch.object(q, 'authorize_before_open') as gate:
                with self.assertRaises(ValueError):
                    q.job_inputs(Path('/unused'), job, {})
                read.assert_not_called(); gate.assert_not_called()


class NextFourBoundaryTests(unittest.TestCase):
    def job(self, pid=3228, language='javascript'):
        source = b'inert synthetic source; never executed'
        cases = [{'args': ['0'], 'expected': 0, 'compare': 'return'}]
        raw = q.encoded(cases)
        suffix = 'js' if language == 'javascript' else 'py'
        return {'id': pid, 'language': language, 'domain_validator': 'request-next4-v1',
                'source_interface': 'commonjs-object-solve-v1' if language == 'javascript' else 'global-solve-v1',
                'source': f'sources/{pid}.{suffix}', 'tests': f'tests/{pid}.json',
                'source_sha256': q.sha(source), 'tests_raw_sha256': q.sha(raw),
                'case_count': 1}, source, raw, cases

    def test_denied_gate_does_not_open_source_or_cases(self):
        job, _, _, _ = self.job()
        with patch.object(q, 'authorize_before_open', side_effect=PermissionError('denied')), \
                patch.object(q, 'read') as read:
            with self.assertRaises(PermissionError):
                q.job_inputs(Path('/unused'), job, {'artifact_paths': {}, 'trusted_hashes': {}})
            read.assert_not_called()

    def test_fixed_ids_dispatch_every_case_to_existing_new_oracle_owner(self):
        from . import request_next4_oracles as oracle
        for pid in (3228, 3523, 3558, 3597):
            for language in ('javascript', 'python'):
                job, source, raw, cases = self.job(pid, language)
                with self.subTest(pid=pid, language=language), \
                        patch.object(q, 'authorize_before_open') as gate, \
                        patch.object(q, 'read', side_effect=[source, raw]), \
                        patch.object(oracle, 'validate') as validate:
                    self.assertEqual(q.job_inputs(Path('/unused'), job,
                        {'artifact_paths': {}, 'trusted_hashes': {}}), (source, cases))
                    validate.assert_called_once_with(pid, cases[0]['args'])
                    gate.assert_called_once()

    def test_next_four_freeze_calls_its_fixed_owner_before_payload_reads(self):
        from . import request_next4_qualification as owner
        contract = {'schema': 'gamma.imported-independent-execution.v1', 'code': {},
                    'limits': q.LIMITS, 'service_config': '/config',
                    'service_config_sha256': 'a' * 64,
                    'additional_code': owner.additional_code(),
                    'jobs': [{'id': 3228, 'language': 'javascript', 'domain_validator': 'request-next4-v1'}]}
        config = {'source_access': {'boundary_gate': {'path': '/gate'}}}
        with patch.object(q, 'read', side_effect=[q.encoded(contract), q.encoded(config), b'{}']) as read, \
                patch.object(q, 'code_pins', return_value={}), \
                patch.object(q.KnownSpecService, 'from_config'), \
                patch.object(owner, 'verify_freeze', side_effect=ValueError('fixed population denied')) as verify:
            with self.assertRaisesRegex(ValueError, 'fixed population denied'):
                q.load_freeze(Path('/freeze'))
            verify.assert_called_once_with(Path('/freeze'), contract, {})
            self.assertEqual([str(c.args[0]) for c in read.call_args_list],
                             ['/freeze/contract.json', '/config', '/gate'])

    def test_foreign_additional_code_path_is_rejected_without_opening_it(self):
        from . import request_next4_qualification as owner
        contract = {'schema': 'gamma.imported-independent-execution.v1', 'code': {},
                    'limits': q.LIMITS, 'additional_code': {'/foreign/payload': 'a' * 64},
                    'jobs': [{'id': 3228, 'language': 'javascript', 'domain_validator': 'request-next4-v1'}]}
        with patch.object(q, 'read', return_value=q.encoded(contract)), \
                patch.object(q, 'code_pins', return_value={}), \
                patch.object(owner, 'additional_code', return_value={'/fixed/owner.py': 'b' * 64}), \
                patch.object(q, 'file_hash') as file_hash, \
                patch.object(q.KnownSpecService, 'from_config') as service:
            with self.assertRaisesRegex(ValueError, 'unapproved fixed request code paths'):
                q.load_freeze(Path('/freeze'))
            file_hash.assert_not_called()
            service.assert_not_called()

    def test_successor_code_never_relabels_an_earlier_execution_contract(self):
        contract = {'schema': 'gamma.imported-independent-execution.v1',
                    'code': {'prior-runner': 'a' * 64}, 'limits': q.LIMITS}
        with patch.object(q, 'read', return_value=q.encoded(contract)) as read, \
                patch.object(q, 'code_pins', return_value={'successor-runner': 'b' * 64}), \
                patch.object(q.KnownSpecService, 'from_config') as service:
            with self.assertRaisesRegex(ValueError, 'execution freeze drift'):
                q.load_freeze(Path('/freeze'))
            read.assert_called_once_with(Path('/freeze/contract.json'))
            service.assert_not_called()


if __name__ == '__main__':
    unittest.main()
