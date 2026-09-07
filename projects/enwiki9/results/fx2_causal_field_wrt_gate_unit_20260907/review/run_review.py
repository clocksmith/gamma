#!/usr/bin/env python3
"""Independent synthetic-only gate review; no canonical payload access."""
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import resource
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path('/tmp/gamma-field-wrt-gate-review-20260907')
NAMES = ['tools/fx2_causal_field_wrt_replay250k_q0_v1.py',
         'tests/test_fx2_causal_field_wrt_gate_v1.py',
         'tools/fx2_causal_field_replay_v1.py',
         'tools/causal_field_wrt_adapter_v1.py',
         'tools/causal_field_parent_coder_v1.py',
         'tools/causal_field_dependency_v1.py', 'tools/wrt_exact.py']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def sources():
    return [{'path': name, 'bytes': (ROOT/name).stat().st_size,
             'sha256': sha((ROOT/name).read_bytes())} for name in NAMES]

before = sources()
expected = json.loads((OUT/'expected-sources.json').read_text())
assert before == expected
assert os.sched_getaffinity(0) == {4}
assert resource.getrlimit(resource.RLIMIT_AS)[0] == 512*1024**2
assert resource.getrlimit(resource.RLIMIT_CPU)[0] == 60
assert resource.getrlimit(resource.RLIMIT_FSIZE)[0] == 32*1024**2
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('author_gate_tests', ROOT/NAMES[1])
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
gate_tool = author.gate_tool
extra_cases = {'economic_combinations': 0, 'missing_report_fields': 0}

class IndependentReviewTests(unittest.TestCase):
    def test_all_activity_and_archive_order_combinations(self):
        for t, r, s, flags, source in itertools.product(
                (90, 120, 121), (80, 110, 140), (80, 110, 140),
                itertools.product((False, True), repeat=3), (0, 30)):
            rows = author.GateTests().comparison_reports()
            for arm, size, active in zip(('T', 'R', 'S'), (t, r, s), flags):
                rows[arm]['archive_bytes'] = size
                rows[arm]['changed_probability_bits'] = int(active)
                rows[arm]['adapter']['selected_values'] = int(active)
            value = gate_tool.scientific_comparison(rows, source, 999)
            expected_class = ('inconclusive_inactive_opportunities_or_controls'
                              if not all(flags) else 'failed_causal_controls'
                              if not (t < r and t < s) else 'weak_compression'
                              if t >= 120 else 'conditional_archive_gain')
            self.assertEqual(value['failure_class'], expected_class)
            self.assertEqual(value['local_source_paying'], 120-t > source)
            self.assertEqual(value['external_decode_dependency_bytes'], 999)
            self.assertEqual(value['objective_credit_bytes'], 0)
            self.assertIsNone(value['complete_package_bytes'])
            self.assertFalse(value['larger_gate_authorized'])
            extra_cases['economic_combinations'] += 1

    def test_every_mandatory_report_field_is_required(self):
        for name in gate_tool.MEANINGFUL:
            row = author.report()
            del row[name]
            with self.subTest(name=name), self.assertRaises(ValueError):
                gate_tool.checked_report(row, 'encode', 'T', {})
            extra_cases['missing_report_fields'] += 1

    def test_exact_reference_rejects_alias_and_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = b'synthetic source only\n'
            (root/'source.py').write_bytes(data)
            row = {'path': 'source.py', 'bytes': len(data), 'sha256': sha(data)}
            self.assertEqual(gate_tool.read_ref(root, row), data)
            (root/'alias.py').symlink_to(root/'source.py')
            with self.assertRaises(ValueError):
                gate_tool.read_ref(root, {**row, 'path': 'alias.py'})
            with self.assertRaises(ValueError):
                gate_tool.read_ref(root, {**row, 'bytes': len(data)+1})
            (root/'source.py').write_bytes(b'replaced bytes')
            with self.assertRaises(ValueError):
                gate_tool.read_ref(root, row)

suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromModule(author),
    unittest.defaultTestLoader.loadTestsFromTestCase(IndependentReviewTests),
])
started = time.monotonic()
result = unittest.TextTestRunner(verbosity=2).run(suite)
elapsed = time.monotonic()-started
after = sources()
self_usage = resource.getrusage(resource.RUSAGE_SELF)
child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
receipt = {'schema': 'independent-synthetic-gate-review.v1',
    'passed': result.wasSuccessful() and before == after,
    'tests_run': result.testsRun, 'errors': len(result.errors), 'failures': len(result.failures),
    'additional_case_counts': extra_cases, 'source_before': before,
    'source_after': after, 'sources_unchanged': before == after,
    'elapsed_seconds': elapsed,
    'self_cpu_seconds': self_usage.ru_utime+self_usage.ru_stime,
    'child_cpu_seconds': child_usage.ru_utime+child_usage.ru_stime,
    'maximum_self_or_child_rss_kib': max(self_usage.ru_maxrss, child_usage.ru_maxrss),
    'limits': {'cpus': sorted(os.sched_getaffinity(0)), 'address_space_bytes': 512*1024**2,
               'cpu_seconds': 60, 'outer_wall_seconds': 90, 'file_bytes': 32*1024**2,
               'scratch_bytes': 32*1024**2},
    'scope': 'Synthetic tests only; canonical admission mocked in test fixtures; no corpus, trained model, or historical truth payload opened. External parent Q16 remains a decoder dependency.',
    'review_findings_addressed_by_author': [
        'NativeGate eagerly buffered payloads before live ownership admission.',
        'Live controller identity and active resource guard must precede payload reads.',
        'Post-write receipt failure must not retain a positive published comparison.']}
(OUT/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
assert result.wasSuccessful()
assert before == after
