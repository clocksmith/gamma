"""Independent bounded synthetic integration review; no corpus access."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent / 'attempt_01'
PINS = {
    'tools/fx2_causal_field_preceding_gate_v2.py': '45fdf46247353a9c7889f9e216da4e5e204b133d6d8d89583252a0d3b7f6e29c',
    'tests/test_fx2_causal_field_preceding_gate_v2.py': '8c32d26a4759f45b9cc030b93a6561c206628d31561875c6ff8d165c55c10afc',
    'tools/causal_field_preceding_adapter250k_v1.py': '4beaf210662e37ffeee044738b6b820fecbd87f99ae4846f622e19f4eec56b42',
    'tools/fx2_causal_field_preceding_replay_v1.py': 'db81958de9edd98ebdb61158a8ceb3a7c117bbf024b423dd5d04bfea7564754a',
    'tests/test_fx2_causal_field_preceding_replay_v1.py': 'c72af77d3553ef2ee95ce22f8259c41c25d1252454b9b22e377f168ab553b997',
    'tools/causal_field_preceding_selector_v1.py': 'd48c6ac00defe186b3c2f9982140d78d88036c3ff8d11386cbbf690ae1c4dda9',
    'tools/causal_field_wrt_adapter_v1.py': '649acd80af3ac10e8c2273bde3c2007e07d677bd2941c939494bd0ab76f7c89a',
    'tools/causal_field_dependency_v1.py': 'f34a42054ba151219c67060cf3420e06fb1e1aff8ea9f01aa408e116b495ec0a',
    'tools/causal_field_parent_coder_v1.py': '6c6f8311b6fda0bbf5fdbd0a45a52ea9f145ebc1fe9d506e1af1923478d5abb8',
    'tools/wrt_exact.py': 'ae08246ee8b4708904f78aa5f694111834d6420deece34957c61d6fea3a9797a',
    'tools/fx2_causal_field_replay_v1.py': 'a722f84df5a6ddda454039bfcf859692217e24144b085b17349ca3ee300a36c3',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def emit(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(data)


assert os.sched_getaffinity(0) == {3}, 'review must use assigned CPU3'
OUT.mkdir(exist_ok=False)
(OUT / 'tmp').mkdir()
os.environ['TMPDIR'] = str(OUT / 'tmp')
tempfile.tempdir = str(OUT / 'tmp')
os.environ.pop('GAMMA_PRECEDING_INTEGRATION_RETAIN', None)
os.environ['GAMMA_PRECEDING_GATE_SYNTHETIC_RETAIN'] = str(OUT / 'gate-cli')
for name, expected in PINS.items():
    assert sha((ROOT / name).read_bytes()) == expected, name

# Resolve source text without importing candidate code. Snapshot every bound
# dynamic source as well as the static tools and shared driver closure.
resolver_name = 'tools/enwiki9_python_source_closure.py'
resolver = {'__file__': str(ROOT / resolver_name), '__name__': '_review_static_resolver'}
exec(compile((ROOT / resolver_name).read_bytes(), str(ROOT / resolver_name), 'exec'), resolver)
paths = set(resolver['local_source_closure']([
    ROOT / 'tools/fx2_causal_field_preceding_replay_v1.py', ROOT / 'tools/research_contracts.py']))
paths.update(ROOT / name for name in PINS)
paths.update((ROOT / 'lib').glob('*.py'))
paths.update(ROOT / name for name in [resolver_name, 'tools/enwiki9_lab.py',
    'tools/run_with_resource_guard_v3.py', 'operations/provenance/fx2_causal_preceding_wrt250k_q0_v1_plan.json'])
sources = []
for path in sorted(paths):
    name = path.relative_to(ROOT).as_posix()
    data = path.read_bytes()
    emit(OUT / 'source' / name, data)
    sources.append({'path': name, 'bytes': len(data), 'sha256': sha(data),
                    'author_or_predecessor_pin': name in PINS})
emit(OUT / 'sources-before.json', sources)
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools'), str(ROOT)]
import test_fx2_causal_field_preceding_gate_v2 as author_gate
import test_fx2_causal_field_preceding_replay_v1 as author_codec
gate, codec, old = author_gate.gate_tool, author_codec.codec, author_codec.old
FINDINGS = []


class IndependentTests(unittest.TestCase):
    def test_changed_sync_bytes_fail_even_when_complete_reports_agree(self):
        with tempfile.TemporaryDirectory() as tmp:
            stub = author_gate.SyntheticGate(tmp)
            item = gate.Codec(stub, {}, 'T', b'', b'', b'', b'xy')
            item.reports = {phase: author_gate.report() for phase in gate.PHASES}
            item.projections = copy.deepcopy(item.reports)
            item.syncs = {phase: b'a' * 64 for phase in gate.PHASES}
            item.syncs['decode'] = b'a' * 32 + b'b' + b'a' * 31
            with self.assertRaisesRegex(ValueError, 'differs at byte 32'):
                item.finish()
            diagnostic = json.loads((stub.result / 'first-divergence.json').read_bytes())
            self.assertEqual(diagnostic['first_record'], 1)
            self.assertEqual(diagnostic['first_byte'], 32)
            emit(OUT / 'independent/state-divergence.json', diagnostic)
            FINDINGS.append({'test': self.id(), 'rejected_first_record': 1})

    def test_source_payment_boundary_and_inactive_control_remain_nonqualifying(self):
        reports = author_gate.GateTests().comparison_reports()
        for source_bytes, expected in ((19, False), (18, True)):
            result = gate.scientific_comparison(reports, source_bytes, 10000000)
            self.assertEqual(result['local_source_paying'], expected)
            self.assertEqual(result['archive_saved_bytes'], 20)
            self.assertEqual(result['decoder_arm_option_bytes_per_archive'], 1)
            self.assertIsNone(result['complete_package_bytes'])
            self.assertEqual(result['objective_credit_bytes'], 0)
            self.assertFalse(result['larger_gate_authorized'])
        for arm in ('T', 'R', 'S'):
            inactive = copy.deepcopy(reports)
            inactive[arm]['adapter']['selected_values'] = 0
            result = gate.scientific_comparison(inactive, 0, 0)
            self.assertEqual(result['failure_class'], 'inconclusive_inactive_opportunities_or_controls')
        FINDINGS.append({'test': self.id(), 'external_dependency_bytes': 10000000,
                         'strict_one_byte_option_charge': True, 'required_control_cases': 3})

    def test_dictionary_two_and_three_byte_donors_with_active_original_control(self):
        words = [b'a'] * 3921
        words[80], words[3920] = b'moss', b'pine'
        def invocation(noise, kind, token):
            return (author_codec.literals(b'{{r|anchor=constant|noise=' + noise + b'|kind=' + kind + b'|v=')
                    + author_codec.code(64, *token, 6) + author_codec.literals(b'}}'))
        modeled = (b'\7' + invocation(b'x', b'p', (0xD0, 0x80))
                   + invocation(b'x', b'q', (0xF0, 0xD0, 0x80))
                   + invocation(b'y', b'p', (0xD0, 0x80)))
        raw = (b'{{r|anchor=constant|noise=x|kind=p|v=Moss}}'
               b'{{r|anchor=constant|noise=x|kind=q|v=Pine}}'
               b'{{r|anchor=constant|noise=y|kind=p|v=Moss}}')
        _, options = author_codec.fixture(raw, modeled=modeled, words=words)
        target = OUT / 'independent/multibyte'
        for name, data in (('raw.bin', raw), ('modeled.bin', modeled), ('q16.bin', options['q16']),
                           ('prefix.bin', options['prefix']), ('dictionary.bin', b'\n'.join(words) + b'\n')):
            emit(target / name, data)
        results = {}
        for arm in 'PKTORS':
            encoded = codec.replay('encode', modeled, arm=arm, **options)
            decoded = codec.replay('decode', encoded[0], arm=arm, **options)
            repeated = codec.replay('repeat', modeled, arm=arm, **options)
            self.assertEqual(decoded, (raw, encoded[1], encoded[2]))
            self.assertEqual(repeated, encoded)
            self.assertEqual(encoded[0][:46], options['prefix'])
            self.assertEqual(len(encoded[0]), 46 + encoded[2]['payload_bytes'])
            for phase, value in (('encode', encoded), ('decode', decoded), ('repeat', repeated)):
                for filename, data in zip(('output.bin', 'state-chain.bin', 'report.json'), value):
                    emit(target / arm / phase / filename, data)
            results[arm] = encoded[2]
            if arm in 'PO':
                previous = old.replay('encode', modeled, arm='P' if arm == 'P' else 'T', **options)
                self.assertEqual(previous[:2], encoded[:2])
                normalized = {key: value for key, value in encoded[2].items() if key not in author_codec.EXTRA}
                normalized['arm'] = 'P' if arm == 'P' else 'T'
                self.assertEqual(previous[2], normalized)
        self.assertEqual(results['P']['archive_sha256'], results['K']['archive_sha256'])
        self.assertGreater(results['O']['changed_probability_bits'], 0)
        self.assertGreater(results['T']['changed_probability_bits'], 0)
        self.assertNotEqual(results['O']['probability_digest'], results['T']['probability_digest'])
        FINDINGS.append({'test': self.id(), 'raw_bytes': len(raw), 'modeled_bytes': len(modeled),
                         'dictionary_bytes': (target / 'dictionary.bin').stat().st_size,
                         'dictionary_words': len(words), 'fresh_library_phases': 18,
                         'independent_processes': False,
                         'archive_bytes': {arm: value['archive_bytes'] for arm, value in results.items()},
                         'O_active_and_exact_original_T': True})

    def test_empty_raw_population_with_extreme_causal_parent_probabilities(self):
        modeled, options = author_codec.fixture(b'')
        self.assertEqual(modeled, b'\7')
        options['q16'] = b'\1\0\xff\xff' * 4
        archives = {}
        for arm in 'PKTORS':
            encoded = codec.replay('encode', modeled, arm=arm, **options)
            decoded = codec.replay('decode', encoded[0], arm=arm, **options)
            repeated = codec.replay('repeat', modeled, arm=arm, **options)
            self.assertEqual(decoded, (b'', encoded[1], encoded[2]))
            self.assertEqual(repeated, encoded)
            self.assertEqual(encoded[2]['changed_probability_bits'], 0)
            archives[arm] = encoded[0]
        self.assertEqual(len(set(archives.values())), 1)
        FINDINGS.append({'test': self.id(), 'raw_bytes': 0, 'modeled_bytes': 1,
                         'archive_bytes': len(archives['P']), 'all_arms_equal': True})


suite = unittest.TestSuite()
gate_tests = [
    'test_canonical_guard_metadata_uses_nul_separated_command_hash',
    'test_preflight_cannot_open_reserved_payload_through_antecedents',
    'test_policy_and_option_are_mandatory',
    'test_final_authentication_failure_publishes_no_positive_table',
    'test_post_write_fingerprint_failure_quarantines_comparison',
    'test_index_fingerprint_and_stage_write_failure_leave_no_published_table',
    'test_missing_admission_rejects_before_payload_reader_construction',
    'test_observed_outer_lab_controller_binding_and_orphan_rejection',
    'test_metadata_preflight_never_opens_payloads',
    'test_runtime_replacement_and_unbound_python_fail',
    'test_all_eighteen_real_cli_processes_and_unmodified_driver_rows',
]
for name in gate_tests:
    suite.addTest(author_gate.GateTests(name))
codec_tests = [
    'test_01_wrapper_bound_identity_and_factory_routes',
    'test_02_replay_loop_is_old_loop_with_explicit_factory_and_O_only',
]
for name in codec_tests:
    suite.addTest(author_codec.IntegrationTests(name))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentTests))
started, cpu = time.monotonic(), time.process_time()
result = unittest.TextTestRunner(verbosity=2).run(suite)
stable = all(sha((ROOT / row['path']).read_bytes()) == row['sha256'] for row in sources)
emit(OUT / 'independent-findings.json', FINDINGS)
emit(OUT / 'author-codec-proofs.json', author_codec.IntegrationTests.proofs)
emit(OUT / 'execution.json', {
    'tests': result.testsRun, 'root_gate_tests': len(gate_tests), 'author_codec_library_tests': len(codec_tests),
    'independent_tests': 4, 'passed': result.wasSuccessful(), 'failures': len(result.failures),
    'errors': len(result.errors), 'skipped': len(result.skipped), 'source_unchanged': stable,
    'wall_seconds': time.monotonic() - started, 'self_cpu_seconds': time.process_time() - cpu,
    'reported_self_peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'reported_child_peak_rss_kib': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
    'cpu_affinity': sorted(os.sched_getaffinity(0)), 'corpus_bytes_read': 0,
    'root_gate_real_CLI_phases': 18, 'author_CPU4_CLI_harness_executed': False,
    'source_inventory_entries': len(sources), 'qualification_authority': False,
    'timing_authority': 'shared-host synthetic diagnostic'
})
assert result.wasSuccessful() and stable
assert os.sched_getaffinity(0) == {3}
