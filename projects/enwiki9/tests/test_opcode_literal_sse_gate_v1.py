"""Fresh-process gate replay, relocation and deliberate control divergence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_literal_sse_gate_v1 as gate
from tools import opcode_literal_sse_build_v1 as build
from tools import opcode_literal_sse_corpus_v1 as codec
from tools import opcode_field_compact_observe_v1 as parent


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT/'results', prefix='literal_sse_gate_test_')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.snapshot = self.base/'codec'; build.write_bundle(self.snapshot)
        self.raw = b'alpha beta gamma delta\n'*12+b'alpha beta delta gamma\n'*8+b'\0\xff\r\n<broken'
        source, arc, audit = [self.base/name for name in ('input.raw','parent.arc','parent.json')]
        source.write_bytes(self.raw)
        encoded, observed = parent.execute(parent.load(ROOT/'programs/opcode_field_compact_v1/program.py'),
                                           'encode', self.raw)
        arc.write_bytes(encoded); audit.write_text(json.dumps(observed))
        self.plan = dict(input=dict(path=str(source)), parent_archive=dict(path=str(arc)), parent_audit=dict(path=str(audit)))
        self.out = self.base/'output'; self.out.mkdir()
        self.limits = dict(phase_cpu_seconds=15, phase_wall_seconds=20, phase_address_bytes=536870912)

    def test_ten_fresh_phases_and_unchanged_parse(self):
        r = gate.run_comparison(self.out, self.plan, self.snapshot, self.base/'phases.jsonl', self.limits)
        self.assertEqual(len(r['commands']), 10)
        self.assertTrue(r['matching_arm_decoders'] and r['non_sse_state_equal'] and r['parse_events_equal'])
        self.assertFalse(r['original_decoder_all_arms'])
        self.assertGreater(sum(r['arms']['D']['audit']['updates_by_mode'][1:]), 0)
        for row in r['arms'].values():
            self.assertEqual((ROOT/row['artifacts']['restored']['path']).read_bytes(), self.raw)
        print(json.dumps(dict(archives={a:r['archive_bytes'] for a,r in r['arms'].items()},
                             package_bytes=sum(v['bytes'] for v in build.write_bundle(self.base/'repeat-package').values()))))

    def test_bundle_relocation_and_repeat(self):
        second = self.base/'relocated'; build.write_bundle(second)
        for name in ('p','v','program.py'):
            self.assertEqual((self.snapshot/name).read_bytes(), (second/name).read_bytes())
        for arm in 'PKD':
            original, audit = codec.execute(parent.load(self.snapshot/'program.py'), 'encode', self.raw, arm)
            restored, other = codec.execute(parent.load(second/'program.py'), 'decode', original, arm)
            self.assertEqual(restored, self.raw); self.assertEqual(audit, other)

    def test_projection_divergence_is_rejected(self):
        fake = dict(arms={a:dict(audit=dict(non_sse='same',parse_sha256='same',parse_events=2,updates_by_mode=[1,2,3])) for a in 'PKD'})
        fake['arms']['D']['audit']['parse_sha256']='different'
        with patch.object(gate, '_comparison', return_value=fake):
            with self.assertRaises(ValueError):
                gate.run_comparison(self.out,self.plan,self.snapshot,self.base/'phases.jsonl',self.limits)


if __name__ == '__main__':
    unittest.main()
