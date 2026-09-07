"""Independent synthetic selector review on CPU3; no author's CPU4 child harness."""
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import unittest

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
os.environ.pop('GAMMA_PRECEDING_RETAIN', None)
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import test_causal_field_preceding_selector_v1 as author

subject, base = author.subject, author.base
PINS = {
    'tools/causal_field_preceding_selector_v1.py': 'd48c6ac00defe186b3c2f9982140d78d88036c3ff8d11386cbbf690ae1c4dda9',
    'tests/test_causal_field_preceding_selector_v1.py': '1ba384e278e67994c649dcb595ba104dec71491789823a78089716ff321dc29c',
    'operations/provenance/causal_field_preceding_synthetic_q0_v1_plan.json': 'ef4bbb7a566bfb913d58ccd7116b2708fc03d5a1fb4cf1f84f12ad56a56534c9',
}
EVIDENCE = []


def record(decoy, kind, value):
    return b'{{t|anchor=fixed|decoy=' + decoy + b'|kind=' + kind + b'|v=' + value + b'}}'


SEED = record(b'x', b'p', b'aaaaaaaa') + record(b'x', b'q', b'bbbbbbbb')
PREFIX = SEED + b'{{t|anchor=fixed|decoy=y|kind=p|v='
RAW = PREFIX + b'aaaaaaaa}}'
MODELED = b'\7' + author.literals(RAW)


def retain_phase(path, machine, report, archive=None, raw=None):
    path.mkdir(parents=True, exist_ok=False)
    for name, data in (('probabilities.q16', machine.probabilities), ('states.sha256', machine.states),
                       ('modeled.bin', machine.modeled)):
        (path / name).write_bytes(data)
    if archive is not None:
        (path / 'archive.bin').write_bytes(archive)
    if raw is not None:
        (path / 'inverse.raw').write_bytes(raw)
    (path / 'result.json').write_bytes(author.canonical(report))


class IndependentTests(unittest.TestCase):
    def test_four_fields_force_adjacent_T_and_active_original_O_to_disagree(self):
        wanted = {'P': None, 'K': author.literals(b'aaaaaaaa'), 'T': author.literals(b'aaaaaaaa'),
                  'O': author.literals(b'bbbbbbbb'), 'R': author.literals(b'bbbbbbbb'),
                  'S': author.literals(b'bbbbbbbb')}
        observed = {}
        for arm in 'PKTORS':
            adapter = subject.Adapter([], arm, len(RAW))
            self.assertEqual(author.feed(adapter, b'\7' + author.literals(PREFIX)), PREFIX)
            self.assertEqual(adapter.donor, wanted[arm], arm)
            if arm != 'P':
                self.assertEqual(adapter.completed_invocations, 2)
                self.assertEqual(adapter.serial, 6)
            if arm in 'KTRS':
                self.assertIn((b't', b'kind', b'p', b'v'), adapter.table)
                self.assertNotIn((b't', b'decoy', b'x', b'v'), adapter.table)
                self.assertNotIn((b't', b'anchor', b'fixed', b'v'), adapter.table)
            observed[arm] = {'donor_hex': None if adapter.donor is None else adapter.donor.hex(),
                             'state_sha256': adapter.state_digest(), 'completed': adapter.completed_invocations,
                             'serial': adapter.serial}
        EVIDENCE.append({'test': self.id(), 'raw_prefix_hex': PREFIX.hex(), 'observations': observed})

    def test_four_field_archives_inverse_repeat_probabilities_states_and_framing(self):
        target = OUT / 'four-field'
        target.mkdir()
        (target / 'input.raw').write_bytes(RAW)
        (target / 'input.modeled').write_bytes(MODELED)
        dictionary = author.dictionary_bytes([])
        (target / 'dictionary.json').write_bytes(dictionary)
        self.assertEqual(dictionary, b'[]')
        self.assertEqual(author.HEADER.size, 81)
        costs, archives, reports = {}, {}, {}
        for arm in 'PKTORS':
            archive, encoded, report = author.encode(MODELED, [], len(RAW), arm)
            inverse, decoded, inverse_report = author.decode(archive, [], arm)
            repeated_archive, repeated, repeat_report = author.encode(bytes(decoded.modeled), [], len(inverse), arm)
            self.assertEqual(inverse, RAW)
            self.assertEqual(archive, repeated_archive)
            self.assertEqual(report, inverse_report)
            self.assertEqual(report, repeat_report)
            for machine in (decoded, repeated):
                self.assertEqual(encoded.probabilities, machine.probabilities)
                self.assertEqual(encoded.states, machine.states)
            self.assertEqual(decoded.interval_checks, 8 * len(MODELED))
            fields = author.HEADER.unpack_from(archive)
            self.assertEqual(fields[:4], (b'CFP1', author.MODE[arm], len(RAW), len(MODELED)))
            self.assertEqual(fields[4], hashlib.sha256(RAW).digest())
            self.assertEqual(fields[5], hashlib.sha256(dictionary).digest())
            self.assertEqual(fields[6], len(archive) - 81)
            self.assertEqual(report['frame_bytes'] + report['payload_bytes'], len(archive))
            self.assertEqual(report['dictionary_input_bytes'], 2)
            self.assertEqual(report['decoder_arm_option_bytes'], 1)
            self.assertIsNone(report['complete_package_bytes'])
            retain_phase(target / arm / 'encode', encoded, report, archive=archive)
            retain_phase(target / arm / 'decode', decoded, inverse_report, raw=inverse)
            retain_phase(target / arm / 'repeat', repeated, repeat_report, archive=repeated_archive)
            archives[arm], reports[arm] = archive, report
            costs[arm] = {'archive_bytes': len(archive), 'frame_bytes': 81,
                          'dictionary_bytes': 2, 'arm_option_bytes': 1,
                          'framed_archive_plus_decoder_data_and_option_bytes': len(archive) + 3,
                          'changed_probability_bits': report['changed_probability_bits']}
        self.assertEqual(archives['P'], archives['K'])
        self.assertEqual(reports['P']['probability_sha256'], reports['K']['probability_sha256'])
        ordinary, ordinary_machine, _ = author.decode(archives['K'], [], 'P')
        self.assertEqual(ordinary, RAW)
        self.assertEqual(ordinary_machine.adapter.serial, 0)
        self.assertGreater(reports['K']['adapter']['associations_committed'], 0)
        for arm in 'TORS':
            self.assertGreater(reports[arm]['changed_probability_bits'], 0)
        EVIDENCE.append({'test': self.id(), 'raw_bytes': len(RAW), 'modeled_bytes': len(MODELED),
                         'fresh_machine_phases': 18, 'separate_processes': False, 'costs': costs,
                         'source_and_runtime_package_not_included': True})

    def test_only_adjacent_span_alignment_controls_lookup(self):
        wanted = {'P': None, 'K': None, 'T': None, 'O': author.literals(b'bbbbbbbb'), 'R': None, 'S': None}
        # The preceding field is inside an opaque WRT event; the first remains aligned.
        words = [b'kind=p|']
        prefix = b'\7' + author.literals(SEED + b'{{t|anchor=fixed|decoy=y|') + author.token(0) + author.literals(b'v=')
        for arm in 'PKTORS':
            adapter = subject.Adapter(words, arm)
            author.feed(adapter, prefix)
            self.assertEqual(adapter.donor, wanted[arm], arm)
            if arm != 'P':
                self.assertTrue(adapter.completed_spans[b'anchor']['aligned'])
                self.assertFalse(adapter.completed_spans[b'kind']['aligned'])
        # Reverse which span is unaligned: adjacency survives, original policy abstains.
        words = [b'anchor=fixed|']
        prefix = b'\7' + author.literals(SEED + b'{{t|') + author.token(0) + author.literals(b'decoy=y|kind=p|v=')
        for arm, donor in (('T', b'aaaaaaaa'), ('O', None)):
            adapter = subject.Adapter(words, arm)
            author.feed(adapter, prefix)
            self.assertEqual(adapter.donor, None if donor is None else author.literals(donor))
        EVIDENCE.append({'test': self.id(), 'alignment_directions': 2, 'passed': True})

    def test_overwrite_changes_recency_without_changing_fifo_rotation_order(self):
        update = record(b'y', b'p', b'cccccccc')
        prefix = SEED + update + b'{{t|anchor=fixed|decoy=z|kind=q|v='
        for arm, donor in (('T', b'bbbbbbbb'), ('R', b'cccccccc'), ('S', b'cccccccc')):
            adapter = subject.Adapter([], arm)
            author.feed(adapter, b'\7' + author.literals(prefix))
            self.assertEqual(adapter.donor, author.literals(donor))
            route = [key for key in adapter.table if (key[0], key[1], key[3]) == (b't', b'kind', b'v')]
            self.assertEqual([key[2] for key in route], [b'p', b'q'])
            self.assertGreater(adapter.table[route[0]]['serial'], adapter.table[route[1]]['serial'])
        EVIDENCE.append({'test': self.id(), 'FIFO_route_values': ['p', 'q'],
                         'T_donor': 'b8', 'R_and_S_donor': 'c8'})

    def test_active_original_and_adjacent_prefixes_ignore_future_and_reject_partial_commits(self):
        common = b'\7' + author.literals(PREFIX)
        suffixes = [b'aaaaaaaa}}', b'bbbbbbbb}}', b'aaaaaaaa|anchor=duplicate}}',
                    b'{{nested}}}}', b'x' * 65 + b'}}', b'aaaaaaaa}', b'']
        boundaries = 0
        for arm in 'PKTORS':
            baseline = None
            for suffix in suffixes:
                machine = author.Machine(arm, [], 8192, author.MAX_MODELED)
                for value in common:
                    machine.byte(value)
                state = (bytes(machine.probabilities), bytes(machine.states), machine.adapter.state_digest(),
                         machine.mixture.export(), machine.encoder.low, machine.encoder.high)
                if baseline is None:
                    baseline = state
                self.assertEqual(state, baseline)
                before = machine.adapter.serial
                for value in author.literals(suffix):
                    machine.byte(value)
                self.assertEqual(machine.adapter.serial - before,
                                 3 if arm != 'P' and suffix in suffixes[:2] else 0)
                boundaries += len(common)
        EVIDENCE.append({'test': self.id(), 'prefix_boundaries': boundaries, 'suffix_count': len(suffixes)})

    def test_exact_framed_arbitrary_bytes_remain_literal_on_invalid_syntax(self):
        raw = bytes(range(256)) + b'{{t|k=' + bytes([255, 0, 128, 64]) + b'|v=x}}'
        modeled = b'\7' + author.literals(raw)
        for arm in 'PKTORS':
            archive, encoded, report = author.encode(modeled, [], len(raw), arm)
            inverse, decoded, inverse_report = author.decode(archive, [], arm)
            self.assertEqual(inverse, raw)
            self.assertEqual(report, inverse_report)
            self.assertEqual(encoded.states, decoded.states)
            self.assertEqual(encoded.probabilities, decoded.probabilities)
        EVIDENCE.append({'test': self.id(), 'raw_bytes': len(raw), 'all_256_byte_values': True})


def main():
    assert os.sched_getaffinity(0) == {3}
    assert Path(os.environ['TMPDIR']) == OUT / 'tmp'
    for name, digest in PINS.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    sources = author.source_rows() + [{'path': name, 'bytes': (ROOT / name).stat().st_size,
        'sha256': digest} for name, digest in PINS.items() if not name.endswith('.py')]
    for row in sources:
        path = OUT / 'source' / row['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / row['path']).read_bytes())
    author_names = [name for name in unittest.defaultTestLoader.getTestCaseNames(author.SelectorTests)
                    if not name.startswith('test_14_')]
    assert len(author_names) == 13
    suite = unittest.TestSuite([author.SelectorTests(name) for name in author_names])
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentTests))
    started, cpu = time.monotonic(), time.process_time()
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)
    elapsed, used_cpu = time.monotonic() - started, time.process_time() - cpu
    assert os.sched_getaffinity(0) == {3}
    for row in sources:
        assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
    (OUT / 'source-inventory.json').write_bytes(author.canonical(sources))
    (OUT / 'independent-evidence.json').write_bytes(author.canonical(EVIDENCE))
    (OUT / 'author-library-checks.json').write_bytes(author.canonical(author.SelectorTests.checks))
    report = {'tests': result.testsRun, 'author_library_tests': 13, 'independent_tests': 6,
        'passed': result.wasSuccessful(), 'failures': len(result.failures), 'errors': len(result.errors),
        'source_unchanged': True, 'cpu_affinity': sorted(os.sched_getaffinity(0)),
        'wall_seconds': elapsed, 'cpu_seconds': used_cpu,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'maximum_retained_independent_raw_bytes': max(row.get('raw_bytes', 0) for row in EVIDENCE),
        'corpus_bytes': 0,
        'no_author_CPU4_child_harness_executed': True,
        'scope': 'Independent direct-library synthetic review with fresh encoder/decoder/repeat machines; not separate processes or corpus evidence.'}
    (OUT / 'review-execution.json').write_bytes(author.canonical(report))
    assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) < 33554432
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
