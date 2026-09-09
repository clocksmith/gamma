"""Synthetic decode phases and exact event-ceiling regression checks."""
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_event_opportunity_decode250k_q0_v1 as gate
from tools.opcode_event_opportunity_observe_v1 import execute


class OpportunityDecodeTests(unittest.TestCase):
    def setUp(self):
        retained = os.environ.get('OPCODE_EVENT_UNIT_RETAIN')
        if retained:
            parent = Path(retained).resolve(); parent.mkdir(parents=True, exist_ok=True)
            self.base = parent/self._testMethodName; self.base.mkdir()
        else:
            temporary = tempfile.TemporaryDirectory(dir=ROOT/'results', prefix='opcode_opportunity_unit_')
            self.addCleanup(temporary.cleanup); self.base = Path(temporary.name)
        self.raw = b'<title>Oak</title><text>Oak Oak Oak.</text>\n'*3 + b'\0\xff'
        source = ROOT/'programs/opcode_field_compact_v1/p'
        archive, audit = execute(source.read_bytes(), 'encode', self.raw)
        raw_path, archive_path, audit_path = [self.base/n for n in ('input.raw', 'parent.arc', 'parent.audit.json')]
        raw_path.write_bytes(self.raw); archive_path.write_bytes(archive)
        audit_path.write_text(json.dumps(dict(parent=audit)))
        self.plan = dict(parent_source=gate.phase.artifact(source), parent_archive=gate.phase.artifact(archive_path),
                         parent_raw=gate.phase.artifact(raw_path), parent_audit=gate.phase.artifact(audit_path),
                         modeled_bytes=audit['modeled_bytes'], max_events=audit['modeled_bytes'], chunk_events=4,
                         source_files=[], runtime_files=[], evidence=[])
        self.plan_path = self.base/'inputs.json'; self.plan_path.write_text(json.dumps(self.plan))
        self.output = self.base/'output'; self.output.mkdir()
        self.marker = self.base/'phases.jsonl'
        self.limits = dict(phase_cpu_seconds=10, phase_wall_seconds=15, phase_address_bytes=536870912)

    def run_gate(self):
        return gate.run_comparison(self.output, self.plan_path, self.marker, self.limits)

    def test_three_fresh_decode_phases_inverse_audit_and_event_repeat(self):
        result = self.run_gate()
        self.assertTrue(result['correctness_pass'] and result['frozen_inputs_reverified'])
        self.assertEqual([r['phase'] for r in result['commands']], ['P', 'K', 'K-repeat'])
        for command in result['commands']:
            self.assertIn('--decode-phase', command['argv'])
            self.assertNotIn('encode', command['argv'])
        self.assertFalse((self.output/'P.events.bin').exists())
        summary = result['summary']; trace = (self.output/'K.events.bin').read_bytes()
        self.assertEqual(trace, (self.output/'K-repeat.events.bin').read_bytes())
        self.assertEqual(len(trace), 64*summary['event_count'])
        self.assertEqual(sum(summary['event_counts']), summary['event_count'])
        self.assertEqual(sum(map(sum, summary['transition_counts'])), summary['event_count'])
        self.assertEqual(sum(map(sum, summary['event_counts_by_modeled_third'])), summary['event_count'])
        self.assertGreater(summary['arithmetic_operations'], summary['event_count'])
        records = list(gate.RECORD.iter_unpack(trace))
        self.assertEqual(records[0][6], gate.SENTINEL)
        for index, row in enumerate(records):
            self.assertEqual(row[0], index)
            if index:
                self.assertEqual(row[6], records[index-1][7])
        for chunk in summary['upper_bound_chunks']:
            selected = records[chunk['first_event']:chunk['first_event']+chunk['events']]
            numerator = denominator = 1
            for row in selected:
                numerator *= row[11]; denominator *= row[8+row[7]]
            self.assertEqual(int(chunk['numerator_hex'], 16), numerator)
            self.assertEqual(int(chunk['denominator_hex'], 16), denominator)
            k = chunk['upper_bits']
            self.assertLessEqual(numerator, denominator << k)
            if k:
                self.assertGreater(numerator, denominator << (k-1))
        self.assertEqual(sum(c['upper_bits'] for c in summary['upper_bound_chunks']),
                         summary['ideal_event_saving_upper_bits'])

    def test_exact_ratio_ceiling_and_chunk_boundaries(self):
        for denominator in range(1, 32):
            for numerator in range(denominator, 96):
                expected = 0
                while denominator << expected < numerator:
                    expected += 1
                self.assertEqual(gate.ceil_log2_ratio(numerator, denominator), expected)
        with self.assertRaises(ValueError):
            gate.ceil_log2_ratio(1, 2)
        stream = io.BytesIO(); sink = gate.EventSink(stream, 6, 6, 2)
        counts = [1, 1, 1]
        for i in range(6):
            before = tuple(counts); counts[0] += 1
            sink(dict(index=i, position=i, key=(0, 0, 0, 0), previous_event=None if i == 0 else 0,
                      event=0, pre_counts=before, pre_total=sum(before), post_counts=tuple(counts), post_total=sum(counts)))
        summary = sink.finish()
        self.assertEqual([c['events'] for c in summary['upper_bound_chunks']], [2, 2, 2])
        self.assertEqual([c['third'] for c in summary['upper_bound_chunks']], [0, 1, 2])
        empty = gate.EventSink(io.BytesIO(), 0, 0, 4096).finish()
        self.assertEqual(empty['event_count'], 0)
        self.assertEqual(empty['ideal_event_saving_upper_bits'], 0)
        with self.assertRaises(ValueError):
            sink.finish()

    def test_parent_audit_divergence_and_existing_output_fail_closed(self):
        original = gate.phase.run_phase
        def corrupt(directory, label, *args):
            result = original(directory, label, *args)
            if label == 'K':
                p = directory/'K.audit.json'; data = gate.phase.read_json(p)
                data['modeled_bytes'] += 1; p.write_text(json.dumps(data))
            return result
        with patch.object(gate.phase, 'run_phase', side_effect=corrupt), self.assertRaises(ValueError):
            self.run_gate()
        self.assertTrue((self.output/'K-parent-audit.divergence.json').exists())
        with self.assertRaisesRegex(ValueError, 'already exists'):
            gate.decode_phase(self.plan, self.output, 'P')

    def test_source_mismatch_event_continuity_and_short_writes(self):
        bad = copy.deepcopy(self.plan); bad['parent_archive']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'changed file'):
            gate.decode_phase(bad, self.output, 'K')
        row = dict(index=0, position=0, key=(0, 0, 0, 0), previous_event=None, event=0,
                   pre_counts=(1, 1, 1), pre_total=3, post_counts=(2, 1, 1), post_total=4)
        for key, value in [('index', 1), ('previous_event', 0), ('post_counts', (1, 2, 1)),
                           ('pre_total', 4), ('position', 1), ('key', (7, 0, 0, 0))]:
            sink = gate.EventSink(io.BytesIO(), 2, 2, 1)
            with self.subTest(key=key), self.assertRaises(ValueError):
                sink(dict(row, **{key: value}))
        with self.assertRaisesRegex(ValueError, 'limit'):
            gate.EventSink(io.BytesIO(), 2, 0, 1)(row)
        class ShortWriter:
            def write(self, data): return len(data)-1
        with self.assertRaisesRegex(ValueError, 'short event write'):
            gate.EventSink(ShortWriter(), 2, 2, 1)(row)

    def test_missing_optional_telemetry_does_not_discard_exact_evidence(self):
        original = gate.phase.run_phase
        def missing(directory, label, *args):
            result = original(directory, label, *args)
            (directory/(label+'.stdout')).write_text('unavailable\n')
            return result
        with patch.object(gate.phase, 'run_phase', side_effect=missing):
            result = self.run_gate()
        self.assertTrue(result['correctness_pass'])
        self.assertTrue(all(row['codec_resources'] is None and row['missing_diagnostics']
                            for row in result['commands']))

    def test_canonical_plan_rejects_changed_population_scope_and_closure(self):
        plan = dict(schema=gate.SCHEMA, candidate_id=gate.CID, resources=gate.CAPS.copy(),
                    phase_resources=gate.PHASES.copy(), modeled_bytes=230968, max_events=230968,
                    chunk_events=4096, source_files=[dict(path=p) for p in sorted(gate.SOURCES)],
                    runtime_files=[dict(path=sys.executable)], evidence=[dict(path='evidence')])
        plan.update({k: dict(path=p, bytes=b, sha256=s) for k, (p, b, s) in gate.EXPECTED.items()})
        gate.validate_plan(plan)
        for key, value in [('max_events', 230969), ('chunk_events', 8192), ('source_files', []), ('evidence', [])]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                gate.validate_plan(dict(plan, **{key: value}))
        bad = copy.deepcopy(plan); bad['resources']['cpus'] = [2]
        with self.assertRaises(ValueError): gate.validate_plan(bad)
        bad = copy.deepcopy(plan); bad['parent_raw']['sha256'] = '0'*64
        with self.assertRaises(ValueError): gate.validate_plan(bad)


if __name__ == '__main__':
    unittest.main()
