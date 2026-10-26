"""Numerical execution identity for prospective clause vectors; no model loading."""
import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


FIELDS = ('encoder_manifest_sha256', 'cpu_manifest_sha256', 'native_python_sha256',
          'adapter_sha256', 'threads', 'interop_threads', 'batch_size', 'device',
          'dtype', 'max_tokens', 'padding_side', 'pooling', 'query_instruction')


def numerical_profile(encoder):
    identity = encoder.identity()
    profile = {key: identity[key] for key in FIELDS}
    for key in FIELDS[:4]:
        value = profile[key]
        if not isinstance(value, str) or len(value) != 64 or any(
                c not in '0123456789abcdef' for c in value):
            raise ValueError('numerical profile digest')
    if type(profile['batch_size']) is not int or not 1 <= profile['batch_size'] <= 4:
        raise ValueError('explicit supported batch size required')
    if type(profile['threads']) is not int or profile['threads'] not in (1, 2):
        raise ValueError('explicit supported thread count required')
    if (profile['interop_threads'] != 1 or profile['device'] != 'cpu' or
            profile['dtype'] != 'float32' or profile['max_tokens'] != 1024 or
            profile['padding_side'] != 'left' or
            profile['pooling'] != 'last-token L2-normalized'):
        raise ValueError('unsupported numerical execution profile')
    return dict(schema='gamma.clause-numerical-profile.v1', **profile)


class ProfiledEncoder:
    """Retain the existing binding owner's validation, adding execution identity.

    Loader readiness is deliberately excluded: lazy loading is not a numerical
    profile change. Batch size is included even though exact vector differences
    are not assumed; no cross-profile cache equivalence is asserted.
    """
    def __init__(self, bound, expected_profile):
        self.bound = bound
        self._profile_bytes = json.dumps(expected_profile, sort_keys=True)
        if numerical_profile(bound.encoder) != expected_profile:
            raise ValueError('owner numerical profile mismatch')
        self.identity = dict(legacy_encoder_identity=bound.identity,
                             numerical_profile=json.loads(self._profile_bytes))
        self.encoder_sha256 = digest(self.identity)

    @property
    def calls(self):
        return self.bound.calls

    def check_profile(self):
        if numerical_profile(self.bound.encoder) != json.loads(self._profile_bytes):
            raise ValueError('numerical profile drift')
        if digest(self.identity) != self.encoder_sha256:
            raise ValueError('profile identity drift')

    def _invoke(self, method, *args):
        self.check_profile()
        rows = method(*args)
        self.check_profile()
        return [dict(row, encoder_sha256=self.encoder_sha256) for row in rows]

    def encode_records(self, records, query):
        return self._invoke(self.bound.encode_records, records, query)

    def request(self, text, span_records, expected_request_sha256):
        return self._invoke(self.bound.request, text, span_records, expected_request_sha256)


def construct(factory, kwargs, resources, expected_profile, binding, expected_identity):
    """Factory injection permits tests without importing torch or loading weights."""
    batch, threads = resources['batch_size'], resources['threads']
    if type(batch) is not int or not 1 <= batch <= 4:
        raise ValueError('explicit batch configuration')
    if type(threads) is not int or threads not in (1, 2):
        raise ValueError('explicit thread configuration')
    encoder = factory(**kwargs, batch_size=batch, threads=threads)
    bound = binding.BoundEncoder(encoder, expected_identity, binding.PROMPT_SHA256)
    return ProfiledEncoder(bound, expected_profile)
