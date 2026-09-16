"""Materialize the fixed native profile without a working-directory input.

Both reference and trimmed source receive the same correction. The explicit
frontend dictionary and pretraining remain unchanged. Native archive parity and
restricted decoding are required before release.
"""
import hashlib

SOURCE = 'src/models/fxcmv1.cpp'
BEFORE = b'    // Load dictionary\n    dosym();'
AFTER = (b'    // This fixed profile uses its explicit frontend dictionary only.\n'
         b'    // The historical native reference ran without ambient .dict.\n'
         b'    // Do not activate a different model from working-directory files.')


def materialize(source, expected_sha256):
    original = source[SOURCE]
    if hashlib.sha256(original).hexdigest() != expected_sha256:
        raise ValueError('fixed-profile source preimage differs')
    if original.count(BEFORE) != 1:
        raise ValueError('dictionary initialization anchor absent or ambiguous')
    result = dict(source)
    result[SOURCE] = original.replace(BEFORE, AFTER, 1)
    return result
