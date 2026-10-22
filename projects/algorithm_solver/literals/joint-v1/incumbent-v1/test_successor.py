"""Six-bit/UTF-8 incumbent and search scheduling evidence: synthetic strings only, never source execution.

Uses the unchanged canonical codec. These controls do not establish real-program
qualification, search superiority, or autonomous composition.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
from itertools import combinations
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load('successor_incumbent', HERE / 'incumbent.py')
o = load('successor_optimizer', HERE / 'optimizer.py')
c = m.codec


def bound_fixture():
    sources = {'1': {'base': 'λaλa\r\n', 'other': 'λλaa\r\n'},
               '2': {'base': 'aaλλ\r\n', 'other': 'aλλa\r\n'}}
    strings = sorted(['λ', 'a', '\r\n'])
    pool = strings + ['λλ', 'aa', 'λa']
    choices = {pid: 'base' for pid in sources}
    expected = dict(language='python', width=6, cohort_sha256='c' * 64,
                    pool_sha256='d' * 64, problem_ids=['1', '2'],
                    objective=m.OBJECTIVE.copy())
    dictionary = m.table_bytes(strings)
    fixed = {pid: {'base': variants['base']} for pid, variants in sources.items()}
    state = m.core.evaluate(fixed, strings, 6, mandatory=())
    manifest = {key: state[key] for key in ('coverage', 'denominator', 'uncovered',
                'selections', 'dictionary_bytes', 'packet_bytes', 'package_bytes')}
    manifest.update(language='python', width=6, policy='compression',
                    arm='dictionary-only', dictionary_sha256=m.sha(dictionary),
                    entries=len(strings), whole_program_entries=0,
                    implicit_helpers_imports_wrappers_or_operands=0, programs=[])
    packets = {}
    for pid, variants in fixed.items():
        source = variants['base'].encode('utf-8')
        sequence = [strings.index(piece) for piece in state['parsed'][(pid, 'base')]]
        packet = c.packet(sequence, 6, dictionary)
        packets[pid] = packet
        manifest['programs'].append(dict(
            problem_id=pid, variant='base', represented=True,
            source_sha256=m.sha(source), source_bytes=len(source),
            sequence=sequence, selections=len(sequence), selection_bits=6 * len(sequence),
            framing_bits=328, padding_bits=(-6 * len(sequence)) % 8,
            packet_bytes=len(packet), packet_sha256=m.sha(packet)))
    return sources, pool, choices, expected, dictionary, manifest, packets


class SuccessorTests(unittest.TestCase):
    def test_six_bit_dictionary_cap_is_64_not_65(self):
        characters = [chr(0x100 + i) for i in range(65)]
        sources = {'1': {'base': ''.join(characters[:64]) * 2}}
        m.validate_table(characters[:64], sources, characters, 6)
        state = m.core.evaluate(sources, characters[:64], 6, mandatory=())
        self.assertEqual(state['coverage'], 1)
        self.assertTrue(m.core.audit(sources, state, 6))
        with self.assertRaises(ValueError):
            m.validate_table(characters, sources, characters, 6)
        with self.assertRaises(ValueError):
            m.core.evaluate(sources, characters, 6, mandatory=())
        # Omitting the basis argument is not a legitimate six-bit fallback.
        with self.assertRaises(ValueError):
            m.core.evaluate(sources, characters[:64], 6)

    def test_six_bit_utf8_incumbent_packet_admission(self):
        sources, pool, choices, expected, dictionary, manifest, packets = bound_fixture()
        state, receipt = m.validate_payload(copy.deepcopy(expected), expected,
            manifest, dictionary, packets, sources, pool, choices)
        self.assertEqual(state['coverage'], 2)
        self.assertEqual(receipt['source_executions'], 0)
        self.assertEqual(state['dictionary_bytes'], len(dictionary))
        self.assertEqual(state['packet_bytes'], sum(map(len, packets.values())))
        self.assertGreater(sum(len(s.encode()) for s in state['vocab']),
                           sum(len(s) for s in state['vocab']))
        self.assertTrue(m.core.audit(sources, state, 6))

    def test_utf8_source_mutation_cannot_reuse_incumbent(self):
        sources, pool, choices, expected, dictionary, manifest, packets = bound_fixture()
        sources['1']['base'] = sources['1']['base'].replace('λ', 'μ')
        with self.assertRaisesRegex(ValueError, 'source hash / length mismatch'):
            m.validate_payload(expected, expected, manifest, dictionary, packets,
                               sources, pool, choices)

    def test_balanced_schedule_is_unique_deterministic_and_bounded(self):
        additions = ['a0', 'a1', 'a2', 'a3', 'ignored']
        removals = ['r0', 'r1', 'r2', 'r3']
        result = o.swap_schedule(additions, removals, 'balanced')
        self.assertEqual(result, o.swap_schedule(additions, removals, 'balanced'))
        self.assertEqual(len(result), 8)
        self.assertEqual(len(set(result)), 8)
        self.assertEqual({a for a, _ in result}, set(additions[:4]))
        self.assertEqual({r for _, r in result}, set(removals))
        self.assertEqual({a for a, _ in o.swap_schedule(additions, removals)},
                         set(additions[:2]))
        for add_count in range(5):
            for remove_count in range(5):
                pairs = o.swap_schedule(additions[:add_count], removals[:remove_count], 'balanced')
                self.assertEqual(len(pairs), min(8, add_count * remove_count))
                self.assertEqual(len(set(pairs)), len(pairs))
        with self.assertRaises(ValueError):
            o.swap_schedule(additions, removals, 'unknown')

    def full_cap(self):
        characters = [chr(0x100 + i) for i in range(64)]
        source = ''.join(characters) * 2
        sources = {'1': {'base': source}}
        pool = characters + [''.join(characters[i:i + 2]) for i in range(5)]
        initial = o.core.evaluate(sources, characters, 6, mandatory=())
        return sources, pool, initial

    def test_full_cap_optimizer_reaches_entire_addition_shortlist(self):
        sources, pool, initial = self.full_cap()
        additions = o.rank_additions(initial, o.core.Occurrences(sources), pool)[:4]
        for policy, expected in [('legacy', set(additions[:2])), ('balanced', set(additions))]:
            _, detail = o.optimize(sources, initial, pool, {}, 6, lambda: False,
                                  max_rounds=1, max_trials=14, swap_policy=policy)
            attempts = detail['trace'][0]['attempts']
            swaps = [row for row in attempts if len(row['add']) == len(row['remove']) == 1]
            self.assertEqual(len(swaps), 8)
            self.assertEqual({row['add'][0] for row in swaps}, expected)
            self.assertFalse(any(row['add'] and not row['remove'] for row in attempts))
            self.assertEqual(detail['trials'], 14)
            self.assertEqual(detail['exact_evaluations'], 28)
            self.assertEqual(detail['trim_evaluations'], 0)

    def test_optimizer_trial_bounds_and_default_legacy(self):
        sources, pool, initial = self.full_cap()
        for limit in (0, 1, 6, 10, 14):
            for policy in ('legacy', 'balanced'):
                result, detail = o.optimize(sources, initial, pool, {}, 6, lambda: False,
                    max_rounds=2, max_trials=limit, swap_policy=policy)
                self.assertLessEqual(detail['trials'], limit)
                self.assertLessEqual(o.core.cost(result), o.core.cost(initial))
                self.assertTrue(o.core.audit(sources, result, 6))
        default, default_detail = o.optimize(sources, initial, pool, {}, 6, lambda: False,
                                            max_rounds=1, max_trials=14)
        legacy, legacy_detail = o.optimize(sources, initial, pool, {}, 6, lambda: False,
            max_rounds=1, max_trials=14, swap_policy='legacy')
        self.assertEqual(o.core.comparable(default), o.core.comparable(legacy))
        self.assertEqual(default_detail['trace'], legacy_detail['trace'])

    def test_trim_evaluations_are_charged_separately(self):
        sources = {'1': {'base': 'abab'}}
        initial = o.core.evaluate(sources, ['a', 'b', 'unused'], 6, mandatory=())
        _, detail = o.optimize(sources, initial, ['a', 'b', 'unused', 'ab'], {}, 6,
                              lambda: False, max_rounds=1, max_trials=96)
        self.assertEqual(detail['trim_evaluations'], 2)
        self.assertEqual(detail['exact_evaluations'],
                         2 * detail['trials'] + detail['trim_evaluations'])

    def test_cached_full_parity_source_choice_and_unreachable_transitions(self):
        sources = {'1': {'a-base': 'abXabY', 'z-alt': 'ccXccY'},
                   '2': {'a-base': 'abYa', 'z-alt': 'zzYz'},
                   '3': {'base': 'zzYz'}}
        base = ['a', 'b', 'X', 'Y', 'ab', 'c']
        parent = o.core.evaluate(sources, base, 6, mandatory=())
        self.assertEqual(parent['chosen']['1'], 'a-base')
        self.assertEqual(parent['uncovered'], ['3'])
        index = o.core.Occurrences(sources)
        for vocabulary in (base + ['z'], base + ['ccXcc'], base + ['bXab'],
                           [p for p in base if p != 'ab'], ['ab', 'Y'], base):
            cached = o.core.evaluate(sources, vocabulary, 6, parent, (), index)
            full = o.core.evaluate(sources, vocabulary, 6, mandatory=())
            self.assertEqual(o.core.comparable(cached), o.core.comparable(full))
            self.assertTrue(o.core.audit(sources, cached, 6))
        enabled = o.core.evaluate(sources, base + ['z'], 6, parent, (), index)
        self.assertEqual(enabled['coverage'], 3)
        alternate = o.core.evaluate(sources, base + ['ccXcc'], 6, parent, (), index)
        self.assertEqual(alternate['chosen']['1'], 'z-alt')
        crossing = o.core.evaluate(sources, base + ['bXab'], 6, parent, (), index)
        self.assertEqual(len(crossing['parsed'][('1', 'a-base')]), 3)

    def test_cached_full_parity_bounded_dictionary_grid(self):
        sources = {'1': {'base': 'abab', 'alt': 'baba'}, '2': {'base': 'aaab'}}
        pool = ['a', 'b', 'ab', 'ba']
        dictionaries = [subset for size in range(1, 5) for subset in combinations(pool, size)]
        index = o.core.Occurrences(sources)
        for before in dictionaries:
            parent = o.core.evaluate(sources, before, 6, mandatory=())
            for after in dictionaries:
                cached = o.core.evaluate(sources, after, 6, parent, (), index)
                full = o.core.evaluate(sources, after, 6, mandatory=())
                self.assertEqual(o.core.comparable(cached), o.core.comparable(full))
                self.assertTrue(o.core.audit(sources, cached, 6))

    def test_six_bit_utf8_incumbent_survives_worse_terminal_state(self):
        sources, pool, choices, expected, dictionary, manifest, packets = bound_fixture()
        initial, _ = m.validate_payload(expected, expected, manifest, dictionary,
                                        packets, sources, pool, choices)
        better = m.core.evaluate(sources, pool, 6, mandatory=())
        worse = m.core.evaluate(sources, ['λ'], 6, mandatory=())
        self.assertLess(m.core.cost(better), m.core.cost(initial))
        def trajectory(*args, **kwargs):
            kwargs['observe'](better, 'synthetic-better')
            kwargs['observe'](worse, 'synthetic-worse')
            return worse, {'synthetic': True}
        retained, terminal, _, detail = m.search_with_incumbent(sources, pool, 6,
            initial, trajectory, lambda: False, max_rounds=1, max_trials=2)
        self.assertEqual(m.core.comparable(retained), m.core.comparable(better))
        self.assertEqual(terminal['coverage'], 0)
        costs = [tuple(row['retained_cost']) for row in detail['history']]
        self.assertTrue(all(a >= b for a, b in zip(costs, costs[1:])))

    def test_both_schedules_retain_six_bit_utf8_incumbent(self):
        sources, pool, choices, expected, dictionary, manifest, packets = bound_fixture()
        initial, _ = m.validate_payload(expected, expected, manifest, dictionary,
                                        packets, sources, pool, choices)
        for policy in ('legacy', 'balanced'):
            def optimize(*args, **kwargs):
                return o.optimize(*args, **kwargs, swap_policy=policy)
            retained, _, detail, _ = m.search_with_incumbent(sources, pool, 6,
                initial, optimize, lambda: False, max_rounds=2, max_trials=32)
            self.assertEqual(retained['coverage'], 2)
            self.assertLessEqual(m.core.cost(retained), m.core.cost(initial))
            self.assertLessEqual(detail['trials'], 32)

    def test_codec_literal_golden_packets_all_widths(self):
        dictionary = b'LTD1\x00\x00\x00\x03\x00\x00\x00\x01a\x00\x00\x00\x01b\x00\x00\x00\x01c'
        for width, payload in [(6, b'\x04\x20'), (7, b'\x02\x08'), (8, b'\x01\x02')]:
            golden = (b'LTV1' + bytes([width]) + hashlib.sha256(dictionary).digest()
                      + b'\x00\x00\x00\x02' + payload)
            self.assertEqual(c.packet([1, 2], width, dictionary), golden)
            c.verify_packet(golden, dictionary, [b'a', b'b', b'c'], b'bc')

    def test_codec_cap_and_zero_count_are_not_ambiguous(self):
        entries = [str(i) for i in range(65)]
        dictionary = m.table_bytes(entries)
        with self.assertRaises(AssertionError):
            c.verify_packet(c.packet([0], 6, dictionary), dictionary,
                            [s.encode() for s in entries], b'0')
        small = m.table_bytes(['a'])
        for width in (6, 7, 8):
            packet = c.packet([], width, small)
            self.assertEqual(len(packet), 41)
            c.verify_packet(packet, small, [b'a'], b'')
            with self.assertRaises(AssertionError):
                c.verify_packet(packet + b'\x00', small, [b'a'], b'')


if __name__ == '__main__':
    unittest.main(verbosity=2)
