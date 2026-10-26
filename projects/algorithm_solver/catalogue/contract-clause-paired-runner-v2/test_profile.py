"""Synthetic numerical-profile wiring and real cache invalidation controls."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from numerical_profile import construct, numerical_profile

BASE = Path(__file__).resolve().parent.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


binding = load('binding_test', BASE/'contract-clause-encoder-adapter-v1/encoder_binding.py')
cache = load('cache_test', BASE/'contract-clause-paired-development-v1/cache.py')
IDENTITY = dict(encoder_manifest_sha256='a'*64, cpu_manifest_sha256='b'*64,
                native_python_sha256='c'*64)


class Fake:
    created = []

    def __init__(self, *, batch_size, threads):
        self.batch_size, self.threads = batch_size, threads
        self.__dict__.update(IDENTITY)
        self.ready = False
        self.encoded = 0
        self.created.append(self)

    def identity(self):
        return dict(IDENTITY, adapter_sha256='d'*64, batch_size=self.batch_size,
                    threads=self.threads, interop_threads=1, device='cpu',
                    dtype='float32', max_tokens=1024, padding_side='left',
                    pooling='last-token L2-normalized', query_instruction='instruction',
                    runtime_loaded_and_checked=self.ready)

    def encode(self, texts, *, query):
        self.ready = True
        self.encoded += 1
        self.last_request_info = dict(rows=len(texts), query=query,
                                      truncated=[False]*len(texts))
        return [[1.] + [0.]*1023 for _ in texts]


def make(batch=4, threads=2, profile=None):
    expected = profile or numerical_profile(Fake(batch_size=batch, threads=threads))
    return construct(Fake, {}, dict(batch_size=batch, threads=threads), expected,
                     binding, IDENTITY)


def inputs():
    return binding.clause_inputs([dict(clause_id='synthetic', role='objective',
        text='test', authority_sha256='e'*64, field='result', field_sha256='f'*64,
        span=[0, 4])])


def cache_identity(encoder):
    return dict(encoder_sha256=encoder.encoder_sha256,
                prompt_sha256=binding.PROMPT_SHA256, dimension=1024,
                revision_sha256='1'*64)


class Tests(unittest.TestCase):
    def test_explicit_factory_configuration_and_lazy_constructor(self):
        for batch in (1, 2, 4):
            encoder = make(batch)
            self.assertEqual(encoder.bound.encoder.batch_size, batch)
            self.assertEqual(encoder.bound.encoder.encoded, 0)

    def test_batch_and_threads_change_vector_identity(self):
        self.assertEqual(make(2).encoder_sha256, make(2).encoder_sha256)
        self.assertNotEqual(make(2).encoder_sha256, make(4).encoder_sha256)
        self.assertNotEqual(make(2, 1).encoder_sha256, make(2, 2).encoder_sha256)

    def test_same_profile_cache_resume_and_cross_profile_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'cache'
            first = make(4)
            rows, job = cache.cached_clauses(inputs(), first, path,
                                            cache_identity(first), lambda _: None)
            same = make(4)
            restored, restored_job = cache.cached_clauses(inputs(), same, path,
                cache_identity(same), lambda _: None, resume=True)
            self.assertEqual((rows, job), (restored, restored_job))
            self.assertEqual(same.calls, 0)
            changed = make(2)
            with self.assertRaisesRegex(ValueError, 'cache identity drift'):
                cache.cached_clauses(inputs(), changed, path, cache_identity(changed),
                                    lambda _: None, resume=True)
            self.assertEqual(changed.calls, 0)

    def test_existing_unprofiled_cache_is_not_promoted(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'cache'
            old = binding.BoundEncoder(Fake(batch_size=4, threads=2), IDENTITY,
                                       binding.PROMPT_SHA256)
            cache.cached_clauses(inputs(), old, path, cache_identity(old), lambda _: None)
            new = make(4)
            with self.assertRaisesRegex(ValueError, 'cache identity drift'):
                cache.cached_clauses(inputs(), new, path, cache_identity(new),
                                    lambda _: None, resume=True)

    def test_batch_drift_before_encode_rejected(self):
        encoder = make(4)
        encoder.bound.encoder.batch_size = 2
        with self.assertRaisesRegex(ValueError, 'profile drift'):
            encoder.encode_records(inputs(), False)
        self.assertEqual(encoder.calls, 0)

    def test_cached_restore_checks_current_profile_before_read(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'cache'
            encoder = make(4)
            gate = lambda _: encoder.check_profile()
            cache.cached_clauses(inputs(), encoder, path, cache_identity(encoder), gate)
            encoder.bound.encoder.batch_size = 2
            with self.assertRaisesRegex(ValueError, 'profile drift'):
                cache.cached_clauses(inputs(), encoder, path, cache_identity(encoder),
                                    gate, resume=True)
            self.assertEqual(encoder.calls, 1)

    def test_profile_mismatch_and_invalid_resource_types(self):
        expected = numerical_profile(Fake(batch_size=4, threads=2))
        with self.assertRaisesRegex(ValueError, 'profile mismatch'):
            make(2, profile=expected)
        for batch in (True, 0, 5, '2'):
            with self.assertRaises(ValueError):
                construct(Fake, {}, dict(batch_size=batch, threads=2), expected,
                          binding, IDENTITY)

    def test_request_keeps_provenance_and_changes_binding(self):
        encoder = make(2)
        text = 'Return an integer.'
        rows = encoder.request(text, [], binding.sha(text.encode()))
        self.assertEqual(rows[0]['text'], text)
        self.assertEqual(rows[0]['encoder_sha256'], encoder.encoder_sha256)
        self.assertNotEqual(rows[0]['encoder_sha256'], encoder.bound.encoder_sha256)
        self.assertEqual(encoder.calls, 1)


if __name__ == '__main__':
    unittest.main()
