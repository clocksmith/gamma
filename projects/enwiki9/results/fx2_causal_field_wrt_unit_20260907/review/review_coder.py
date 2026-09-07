#!/usr/bin/env python3
"""Independent bounded checks; all fixtures are constructed here, never corpus."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import resource
import signal
import sys
import time
import traceback
import unittest
from fractions import Fraction

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
EXPECTED = {
    'tools/causal_field_parent_coder_v1.py': '6c6f8311b6fda0bbf5fdbd0a45a52ea9f145ebc1fe9d506e1af1923478d5abb8',
    'tests/test_causal_field_parent_coder_v1.py': '0604ba6a648fc7e3bc9d3605cf5876878c7a635bf68988b8df2f6896562a8021',
}
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_FSIZE, (33554432, 33554432))
signal.alarm(90)
started = time.monotonic()
receipt = {'status': 'running', 'synthetic_only': True, 'corpus_bytes': 0,
           'command': ['taskset', '-c', '3', 'python3', '-B', str(Path(__file__))],
           'cwd': str(ROOT), 'source_hashes': EXPECTED,
           'cpu_affinity': sorted(os.sched_getaffinity(0)),
           'limits': {'address_space_bytes': 536870912, 'cpu_seconds': 60,
                      'wall_seconds': 90, 'scratch_bytes': 33554432, 'raw_bytes_max': 8192},
           'coder_cases': [], 'posterior_cases': []}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def bits(raw):
    return [(byte >> shift) & 1 for byte in raw for shift in range(7, -1, -1)]

try:
    for name, expected in EXPECTED.items():
        assert sha((ROOT / name).read_bytes()) == expected, name
    os.environ['GAMMA_PARENT_CODER_TEST_ARTIFACTS'] = str(OUT / 'coder-author-tests')
    spec = importlib.util.spec_from_file_location('field_parent_independent_tests', ROOT / 'tests/test_causal_field_parent_coder_v1.py')
    unit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(unit)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(unit))
    receipt['unit_tests'] = {'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors)}
    assert result.wasSuccessful()
    from causal_field_parent_coder_v1 import Encoder, Decoder, ParentMixture

    # Fixed goldens follow the inclusive native interval and high-byte flush.
    for name, truth, probabilities, expected in (
        ('empty', [], [], b'\xff'),
        ('half_one', [1], [32768], b'\x7f'),
        ('half_zero', [0], [32768], b'\xff'),
        ('rare_one', [1], [1], b'\0\0\xff'),
        ('rare_zero', [0], [65535], b'\xff\xff\xff'),
    ):
        e = Encoder(max_bits=len(truth))
        for bit, q in zip(truth, probabilities):
            e.encode(bit, q)
        assert e.finish() == expected, name
        receipt['coder_cases'].append({'name': name, 'bits': len(truth), 'payload_hex': expected.hex()})

    # Exercise the default worst-case payload/work bound using exactly 8 KiB.
    for name, raw, q in (('max_rare_ones', b'\xff' * 8192, 1),
                         ('max_rare_zeros', b'\0' * 8192, 65535)):
        truth = bits(raw)
        e = Encoder(max_bits=len(truth))
        states = []
        for bit in truth:
            e.encode(bit, q)
            states.append((e.low, e.high))
        payload = e.finish()
        d = Decoder(payload, max_bits=len(truth), expected_payload_bytes=len(payload), payload_sha256=sha(payload))
        repeat = Encoder(max_bits=len(truth))
        for bit, expected_state in zip(truth, states):
            observed = d.decode(q)
            assert observed == bit and (d.low, d.high) == expected_state
            repeat.encode(observed, q)
        assert repeat.finish() == payload
        for function in (lambda: e.encode(0, q), lambda: d.decode(q)):
            try:
                function()
            except ValueError:
                pass
            else:
                raise AssertionError('closed/work cap did not reject')
        target = OUT / (name + '.payload')
        target.write_bytes(payload)
        receipt['coder_cases'].append({'name': name, 'raw_bytes': len(raw), 'raw_sha256': sha(raw),
            'bits': len(truth), 'q16': q, 'payload': str(target), 'payload_bytes': len(payload), 'payload_sha256': sha(payload)})

    rng = random.Random(20260907)
    posterior_checks = 0
    for case, donor, mismatch, profile in (
        ('maximum_ones_rare_parent', b'\xff' * 256, None, 'one'),
        ('maximum_zeros_rare_parent', b'\0' * 256, None, 'almost_one'),
        ('varying_parent', bytes(range(256)), None, 'varying'),
        ('late_mismatch', bytes(range(256)), 2047, 'varying'),
        ('early_mismatch', bytes(range(256)), 0, 'varying'),
    ):
        truth = bits(donor)
        if mismatch is not None:
            truth[mismatch] ^= 1
        truth += [0, 1] * 64  # Explicit parent-only continuation after exhaustion.
        qs = [1 if profile == 'one' else 65535 if profile == 'almost_one' else rng.randrange(1, 65536) for _ in truth]
        model = ParentMixture(max_bits=len(truth))
        model.reset(donor)
        donor_bits = bits(donor)
        parent_weight = donor_weight = Fraction(1, 2)
        predictions = bytearray()
        for index, (bit, q) in enumerate(zip(truth, qs)):
            parent_p = Fraction(q, 65536)
            active = index < len(donor_bits) and donor_weight > 0
            mixed = ((parent_weight * parent_p + donor_weight * donor_bits[index]) /
                     (parent_weight + donor_weight)) if active else parent_p
            expected_q = max(1, min(65535, (mixed.numerator * 65536) // mixed.denominator))
            found = model.predict(q)
            assert found == expected_q, (case, index, found, expected_q)
            predictions.extend(found.to_bytes(2, 'little'))
            model.observe(bit)
            if active:
                parent_weight *= parent_p if bit else 1 - parent_p
                donor_weight *= int(bit == donor_bits[index])
            state = model.export()
            actual_ratio = Fraction(int(state['donor_mass_hex'], 16), int(state['parent_mass_hex'], 16))
            assert actual_ratio == donor_weight / parent_weight
            posterior_checks += 1
        target = OUT / (case + '.fixture.json')
        fixture = {'donor_hex': donor.hex(), 'truth_bits': truth, 'parent_q16': qs,
                   'probability_sha256': sha(predictions), 'final_state': model.export()}
        target.write_text(json.dumps(fixture, sort_keys=True) + '\n')
        receipt['posterior_cases'].append({'name': case, 'fixture': str(target), 'fixture_sha256': sha(target.read_bytes()),
                                         'checks': len(truth), 'final_state_digest': model.state_digest()})
    receipt['posterior_reference_checks'] = posterior_checks
    for name, expected in EXPECTED.items():
        assert sha((ROOT / name).read_bytes()) == expected, name
    receipt['status'] = 'passed'
except BaseException as error:
    receipt['status'] = 'failed'
    receipt['error'] = repr(error)
    traceback.print_exc()
finally:
    receipt['elapsed_seconds'] = time.monotonic() - started
    receipt['self_max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt['child_max_rss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    receipt['script_sha256'] = sha(Path(__file__).read_bytes())
    with (OUT / 'coder-review.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({'status': receipt['status'], 'receipt': str(OUT / 'coder-review.json')}, sort_keys=True))
sys.exit(0 if receipt['status'] == 'passed' else 1)
