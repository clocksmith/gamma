import copy
import hashlib
import json
from pathlib import Path
import signal
import os
import threading
import sys
import tempfile
import unittest
from unittest import mock

from . import recognition_candidate as c
from . import test_boundary_policy


def unit(index=0):
    row = [0.] * 1024
    row[index] = 1.
    return row


class FakeEncoder:
    calls = []
    truncated = False
    invalid = False

    def __init__(self, plan):
        self.last_request_info = None

    def encode(self, texts, *, query=False):
        self.calls.append((texts, query))
        self.last_request_info = {'query': query, 'rows': len(texts),
            'truncated': [self.truncated] * len(texts)}
        rows = [unit(10 + i) for i in range(len(texts))]
        if self.invalid:
            rows[0][0] = float('nan')
        return rows


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'candidate'
        FakeEncoder.calls = []
        FakeEncoder.truncated = FakeEncoder.invalid = False
        self.ids = [f'leetcode:{i}' for i in range(1, 6)]
        raw, pins = test_boundary_policy.BoundaryPolicyTests().fixture()
        paths = {}
        for name, value in raw.items():
            p = self.root / (name + '.json')
            p.write_bytes(value)
            paths[name] = str(p)
        gate = self.write('gate.json', {'schema': 'gamma.boundary-gate-config.v1',
            'artifact_paths': paths, 'trusted_hashes': pins})
        encoder = self.write('encoder.json', {'files': []})
        cpu = self.write('cpu.json', {'packages': {}})
        base = Path(c.__file__).parent
        code = {name: {'path': str(base / name), 'sha256': c.sha(base / name)} for name in c.CODE_FILES}
        execution = {'model_manifest_sha256': encoder['sha256'], 'tokenizer_manifest_sha256': encoder['sha256'],
            'runtime_manifest_sha256': cpu['sha256'], 'adapter_sha256': code['cpu_encoder.py']['sha256'],
            'python_sha256': 'a' * 64, 'device': 'cpu', 'dtype': 'float32', 'threads': 2, 'interop_threads': 1,
            'batch_size': 2, 'padding_side': 'left', 'pooling': 'last-token',
            'normalization': 'L2; torch.nn.functional.normalize(hidden[:, -1].float(), dim=-1)', 'max_tokens': 1024,
            'truncation': 'enabled; right (pinned transformers default); max_length=1024', 'document_instruction': '',
            'query_instruction': 'Instruct: Given a programming problem, retrieve the identical problem\nQuery: ', 'dimension': 1024}
        self.hashes = [hashlib.sha256(f'Title {i}'.encode()).hexdigest() for i in range(5)]
        matrix = self.root / 'baseline.npy'
        matrix.write_bytes(c.matrix_bytes([unit(i) for i in range(5)]))
        matrix = {'path': str(matrix), 'sha256': c.sha(matrix)}
        rows = self.write('rows.json', c.baseline_metadata(matrix, self.ids, self.hashes, c.execution_identity(execution)))
        text = 'Permitted synthetic changed text'
        changed_hash = hashlib.sha256(text.encode()).hexdigest()
        documents = self.write('changed.json', {'schema': 'gamma.recognition-changed-documents.v1',
            'documents': [{'problem_id': self.ids[0], 'text': text, 'document_sha256': changed_hash}]})
        population = [{'problem_id': pid, 'document_sha256': changed_hash if i == 0 else self.hashes[i],
                       'action': 'embed' if i == 0 else 'reuse'} for i, pid in enumerate(self.ids)]
        self.plan = {'schema': c.SCHEMA, 'release_id': 'synthetic-candidate', 'execution': execution,
            'baseline': {'id': 'synthetic-original', 'matrix': matrix, 'rows': rows}, 'population': population,
            'changed_documents': documents, 'boundary_gate': gate,
            'encoder': {'python': sys.executable, 'model_root': str(self.root / 'model'),
                        'encoder_manifest': encoder, 'cpu_manifest': cpu}, 'code': code,
            'resources': {'wall_seconds': 2., 'cpu_seconds': 1, 'cpu_hard_seconds': 2,
                'address_space_bytes': 512 * 1024 ** 2, 'aggregate_rss_bytes': 128 * 1024 ** 2,
                'rss_sample_seconds': .01, 'minimum_available_bytes': 5 * c.GIB,
                'require_hard_aggregate_memory': True}}

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, sort_keys=True))
        return {'path': str(path), 'sha256': c.sha(path)}

    def build(self):
        return c.build_candidate(self.plan, self.output, encoder_factory=FakeEncoder)

    def test_build_reuses_all_frozen_protected_and_unknown_competitors(self):
        result = self.build()
        self.assertEqual(result['population'], 5)
        self.assertEqual(result['reused_vectors'], 4)
        self.assertEqual(result['generated_vectors_total'], 1)
        self.assertFalse(result['activation'])
        self.assertEqual(len(FakeEncoder.calls), 1)
        self.assertIs(FakeEncoder.calls[0][1], False)
        rows = c.read_matrix(result['vectors']['path'], result['vectors']['sha256'])
        self.assertEqual(rows[1:], [unit(i) for i in range(1, 5)])
        self.assertNotIn('text', json.dumps(result))

    def test_complete_resume_never_loads_encoder(self):
        self.build()
        with mock.patch.object(FakeEncoder, '__init__', side_effect=AssertionError('must not load')):
            result = self.build()
        self.assertEqual(result['generated_vectors_this_attempt'], 0)
        self.assertEqual(result['resumed_vectors'], 1)

    def test_no_changes_never_constructs_encoder(self):
        self.plan['population'][0].update(action='reuse', document_sha256=self.hashes[0])
        self.plan['changed_documents'] = self.write('changed.json', {'schema': 'gamma.recognition-changed-documents.v1', 'documents': []})
        with mock.patch.object(FakeEncoder, '__init__', side_effect=AssertionError('must not load')):
            result = self.build()
        self.assertEqual(result['reused_vectors'], 5)
        self.assertEqual(result['generated_vectors_total'], 0)

    def test_reserved_and_exterior_denied_before_changed_document_open(self):
        for i in (2, 3, 4):
            plan = copy.deepcopy(self.plan)
            plan['population'][0].update(action='reuse', document_sha256=self.hashes[0])
            plan['population'][i]['action'] = 'embed'
            plan['changed_documents'] = {'path': str(self.root / 'must-not-open'), 'sha256': 'a' * 64}
            with self.subTest(i=i), self.assertRaises(PermissionError):
                c.build_candidate(plan, self.output, encoder_factory=FakeEncoder)
        self.assertEqual(FakeEncoder.calls, [])

    def test_corrupt_published_cache_is_preserved_and_rejected(self):
        self.build()
        receipt = self.output / 'batches/batch-000000/receipt.json'
        receipt.unlink()
        with self.assertRaisesRegex(c.CandidateError, 'corrupt published batch'):
            self.build()
        self.assertTrue((self.output / 'batches/batch-000000/vectors.npy').exists())
        self.assertEqual(len(FakeEncoder.calls), 1)

    def test_interrupted_unpublished_batch_resumes_without_discarding_evidence(self):
        real = c.atomic_json
        def interrupt_receipt(path, value):
            if Path(path).name == 'receipt.json':
                raise InterruptedError('synthetic interruption after vector staging')
            return real(path, value)
        with mock.patch.object(c, 'atomic_json', interrupt_receipt):
            with self.assertRaises(InterruptedError):
                self.build()
        self.assertFalse((self.output / 'batches/batch-000000').exists())
        staging = list((self.output / 'batches').glob('.batch-*'))
        self.assertEqual(len(staging), 1)
        staged_bytes = (staging[0] / 'vectors.npy').read_bytes()
        result = self.build()
        self.assertEqual(result['generated_vectors_this_attempt'], 1)
        self.assertEqual(result['retained_unpublished_staging_directories'], 1)
        self.assertEqual((staging[0] / 'vectors.npy').read_bytes(), staged_bytes)
        self.assertTrue((self.output / 'batches/batch-000000/receipt.json').is_file())

    def test_vector_tamper_and_resume_plan_drift_rejected(self):
        self.build()
        path = self.output / 'batches/batch-000000/vectors.npy'
        path.write_bytes(c.matrix_bytes([unit(30)]))
        with self.assertRaisesRegex(c.CandidateError, 'matrix hash'):
            self.build()
        self.plan['release_id'] = 'changed-release'
        with self.assertRaisesRegex(c.CandidateError, 'resume plan'):
            self.build()

    def test_truncation_and_nonfinite_never_publish_batch(self):
        for field in ('truncated', 'invalid'):
            setattr(FakeEncoder, field, True)
            with self.subTest(field=field), self.assertRaises(c.CandidateError):
                self.build()
            self.assertFalse((self.output / 'batches/batch-000000/vectors.npy').exists())
            setattr(FakeEncoder, field, False)

    def test_mismatched_document_or_execution_provenance_rejected(self):
        self.plan['population'][1]['document_sha256'] = 'b' * 64
        with self.assertRaisesRegex(c.CandidateError, 'unproven document'):
            self.build()
        self.plan['population'][1]['document_sha256'] = self.hashes[1]
        self.plan['execution']['threads'] = 1
        with self.assertRaisesRegex(c.CandidateError, 'baseline execution'):
            self.build()

    def test_reordered_or_omitted_population_not_silently_accepted(self):
        self.plan['population'].pop()
        with self.assertRaisesRegex(c.CandidateError, 'complete pinned competitor'):
            self.build()

    def test_code_pin_mismatch_fails_before_encoder(self):
        self.plan['code']['cpu_encoder.py']['sha256'] = 'b' * 64
        with self.assertRaisesRegex(c.CandidateError, 'code changed'):
            self.build()
        self.assertEqual(FakeEncoder.calls, [])

    def test_hard_aggregate_request_fails_closed_without_model(self):
        with mock.patch.object(c, 'cgroup_memory_limits', return_value=[]):
            with self.assertRaises(c.HardAggregateMemoryUnavailable):
                c.preflight(self.plan)
        self.assertEqual(FakeEncoder.calls, [])

    def test_verified_inherited_cap_allows_preflight_without_loading_model(self):
        self.plan['resources']['aggregate_rss_bytes'] = 8 * c.GIB
        self.plan['execution']['python_sha256'] = c.sha(Path(sys.executable).resolve())
        limits = [{'path': '/sys/fs/cgroup/job', 'maximum_bytes': 8 * c.GIB,
                   'current_bytes': c.GIB}]
        with mock.patch.object(c, 'cgroup_memory_limits', return_value=limits), \
                mock.patch.object(c, 'available_memory_bytes', return_value=7 * c.GIB):
            self.assertEqual(c.preflight(self.plan), 7 * c.GIB)
            limits[0]['maximum_bytes'] = 9 * c.GIB
            with self.assertRaises(c.HardAggregateMemoryUnavailable):
                c.preflight(self.plan)
        self.assertEqual(FakeEncoder.calls, [])

    def test_nested_cgroup_headroom_includes_shared_ancestors(self):
        mount = self.root / 'cgroup'; group = mount / 'parent/job'
        group.mkdir(parents=True)
        for path, maximum, used in [(mount, 'max', 10),
                                    (group.parent, 512 * 1024**2, 300 * 1024**2),
                                    (group, 2 * c.GIB, 100 * 1024**2)]:
            (path / 'memory.max').write_text(str(maximum))
            (path / 'memory.current').write_text(str(used))
        metadata = {'/proc/self/cgroup': '0::/parent/job\n',
                    '/proc/self/mountinfo': f'1 0 0:1 / {mount} rw - cgroup2 cgroup2 rw\n',
                    '/proc/meminfo': 'MemAvailable: 8388608 kB\n'}
        read = Path.read_text
        def read_text(path, *args, **kwargs):
            return metadata[str(path)] if str(path) in metadata else read(path, *args, **kwargs)
        with mock.patch.object(Path, 'read_text', read_text):
            self.assertEqual(c.available_memory_bytes(), 212 * 1024**2)
            caps = c.require_memory_cap({'require_hard_aggregate_memory': True,
                                        'aggregate_rss_bytes': 512 * 1024**2})
            self.assertEqual(len(caps), 2)
            (group.parent / 'memory.current').write_text(str(c.GIB))
            self.assertEqual(c.available_memory_bytes(), 0)

    def test_cgroup_mount_root_and_escaped_paths(self):
        paths = c.memory_cgroup_paths('0::/tenant/job\n',
            r'1 0 0:1 /tenant /mounted\040group rw - cgroup2 cgroup2 rw')
        self.assertEqual(paths, [Path('/mounted group/job'), Path('/mounted group')])
        self.assertEqual(c.memory_cgroup_paths('1:memory:/job\n', ''), [])
        with self.assertRaises(c.CandidateError):
            c.memory_cgroup_paths('0::/../job\n', '')

    def test_insufficient_headroom_fails_before_worker(self):
        self.plan['resources']['require_hard_aggregate_memory'] = False
        with mock.patch.object(c, 'available_memory_bytes', return_value=3 * c.GIB):
            with self.assertRaisesRegex(c.CandidateError, 'headroom'):
                c.preflight(self.plan)

    def test_matrix_dtype_shape_finite_norm_and_hash_validation(self):
        for rows in ([[0.] * 1024], [[float('inf')] + [0.] * 1023], [[1.]]):
            with self.subTest(rows=rows[0][:1]), self.assertRaises(c.CandidateError):
                c.matrix_bytes(rows)
        with self.assertRaisesRegex(c.CandidateError, 'matrix hash'):
            c.read_matrix(self.plan['baseline']['matrix']['path'], 'b' * 64)

    def test_boundary_drift_during_encode_prevents_final_candidate(self):
        original = FakeEncoder.encode
        policy_path = Path(json.loads(Path(self.plan['boundary_gate']['path']).read_text())['artifact_paths']['policy'])
        def mutate(encoder, texts, *, query=False):
            value = original(encoder, texts, query=query)
            policy_path.write_bytes(policy_path.read_bytes() + b' ')
            return value
        with mock.patch.object(FakeEncoder, 'encode', mutate):
            with self.assertRaisesRegex(ValueError, 'anchor mismatch'):
                self.build()
        self.assertFalse((self.output / 'candidate.json').exists())
        self.assertFalse((self.output / 'vectors.npy').exists())

    def test_no_model_packages_imported_by_module(self):
        self.assertNotIn('torch', sys.modules)
        self.assertNotIn('transformers', sys.modules)


class SupervisorTests(unittest.TestCase):
    def run_child(self, source, *, wall=.15, memory=128 * 1024 ** 2):
        with tempfile.TemporaryDirectory() as tmp:
            limits = {'wall_seconds': wall, 'aggregate_rss_bytes': memory, 'rss_sample_seconds': .01}
            result = c.supervise([sys.executable, '-c', source], Path(tmp), limits)
            self.assertTrue(result['cleanup']['verified_no_live_owned_group_members'])
            records = list(Path(tmp).glob('supervisor-*.json'))
            self.assertEqual(len(records), 1)
            self.assertEqual(json.loads(records[0].read_text()), result)
            return result

    def test_wall_deadline_kills_worker_and_grandchild(self):
        source = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); time.sleep(30)"
        result = self.run_child(source)
        self.assertEqual(result['reason'], 'wall_deadline')
        self.assertLess(result['elapsed_seconds'], 3)

    def test_normal_exit_still_cleans_lingering_descendants(self):
        source = "import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])"
        result = self.run_child(source, wall=2)
        self.assertEqual(result['status'], 'completed')

    def test_worker_failure_still_cleans_lingering_descendants(self):
        source = "import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); sys.exit(7)"
        result = self.run_child(source, wall=2)
        self.assertEqual(result['reason'], 'worker_error')
        self.assertEqual(result['worker_returncode'], 7)

    def test_sampled_rss_cap_report_is_not_a_kernel_claim(self):
        result = self.run_child('import time; x=bytearray(32*1024*1024); time.sleep(30)', wall=2, memory=16 * 1024 ** 2)
        self.assertEqual(result['reason'], 'sampled_aggregate_rss_limit')
        self.assertFalse(result['aggregate_memory_kernel_hard_cap'])

    def test_removed_kernel_cap_kills_worker_and_reports_loss(self):
        limits = {'wall_seconds': 2, 'aggregate_rss_bytes': 128 * 1024**2,
                  'rss_sample_seconds': .01, 'require_hard_aggregate_memory': True}
        cap = [{'path': '/synthetic/job', 'maximum_bytes': 128 * 1024**2,
                'current_bytes': 0}]
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(c, 'cgroup_memory_limits', side_effect=[cap, []]):
            with self.assertRaises(c.HardAggregateMemoryUnavailable):
                c.supervise([sys.executable, '-c', 'import time;time.sleep(30)'], Path(tmp), limits)
            result = json.loads(next(Path(tmp).glob('supervisor-*.json')).read_text())
            self.assertFalse(result['aggregate_memory_kernel_hard_cap'])
            self.assertTrue(result['cleanup']['verified_no_live_owned_group_members'])

    def test_interruption_kills_group_and_retains_terminal_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            timer = threading.Timer(.05, lambda: os.kill(os.getpid(), signal.SIGTERM))
            timer.start()
            try:
                with self.assertRaises(InterruptedError):
                    c.supervise([sys.executable, '-c', 'import time;time.sleep(30)'], Path(tmp),
                        {'wall_seconds': 2, 'aggregate_rss_bytes': 128 * 1024 ** 2, 'rss_sample_seconds': .01})
            finally:
                timer.cancel()
                timer.join()
            result = json.loads(next(Path(tmp).glob('supervisor-*.json')).read_text())
            self.assertTrue(result['cleanup']['verified_no_live_owned_group_members'])
            self.assertEqual(result['reason'], 'interrupted_or_inspection_error')

    def test_inspection_uncertainty_kills_group(self):
        real = c.group_snapshot
        count = [0]
        def uncertain_once(pgid):
            count[0] += 1
            if count[0] == 1:
                raise PermissionError('synthetic inspection unavailable')
            return real(pgid)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(c, 'group_snapshot', uncertain_once):
            with self.assertRaises(PermissionError):
                c.supervise([sys.executable, '-c', 'import time;time.sleep(30)'], Path(tmp),
                    {'wall_seconds': 2, 'aggregate_rss_bytes': 128 * 1024 ** 2, 'rss_sample_seconds': .01})
            result = json.loads(next(Path(tmp).glob('supervisor-*.json')).read_text())
            self.assertTrue(result['cleanup']['verified_no_live_owned_group_members'])

    def test_signal_handlers_restored(self):
        before = signal.getsignal(signal.SIGTERM)
        self.run_child('pass', wall=2)
        self.assertEqual(signal.getsignal(signal.SIGTERM), before)


if __name__ == '__main__':
    unittest.main()
