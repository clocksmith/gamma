"""Fixed controls and real independent subprocess replay before corpus admission."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_argtokens_gate_v2 as gate
from tools import dualstream_grammar_gate_v1 as legacy_gate


class ArgumentGateTests(unittest.TestCase):
    def plan(self):
        return dict(schema=gate.driver.SCHEMA, candidate_id='fixture', stage='development',
                    population={'bytes':250000}, frame_size=65536,
                    arms=[dict(id=i, mode=m, config=dict(max_rule_length=4, grammar_budget=16, min_benefit=1, shortlist=4))
                          for i,m in [('P','plain'),('S','split'),('G','grammar'),('B','parameter'),('T','parameter')]],
                    resources=dict(cpus=[2],memory_bytes=1073741824,scratch_bytes=67108864,swap_bytes=0,wall_seconds=600),
                    phase_wall_seconds=20,phase_cpu_seconds=10,phase_address_bytes=536870912,
                    runtime_files=[{'path':'/frozen-by-corpus-plan'}])

    def test_fixed_baseline_and_treatment_cannot_be_dropped(self):
        plan = self.plan()
        gate.validate_plan(plan,'fixture')
        plan['arms'].pop(3)
        with self.assertRaises(gate.codec.CodecError):
            gate.validate_plan(plan,'fixture')
        self.assertEqual(legacy_gate.CODEC,'tools/dualstream_grammar_v1.py')

    def test_baseline_and_treatment_independently_invert_and_repeat(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / 'input'
            raw = b'<title>Oak</title><text>Oak town.</text>\r\n' * 4
            source.write_bytes(raw)
            marker = directory / 'phases'
            for arm in ['B','T']:
                archive, restored, repeat = [directory / (arm + suffix) for suffix in ['.d2g','.raw','.repeat']]
                for phase, operation, inp, out in [('encode','encode',source,archive),
                                                  ('decode','decode',archive,restored),
                                                  ('repeat','encode',restored,repeat)]:
                    argv = [sys.executable,str(ROOT / gate.driver.CODEC),operation,str(inp),str(out)]
                    if operation == 'encode': argv += ['--mode','parameter','--max-rule-length','4']
                    result = gate.run_phase(directory,arm+'-'+phase,argv,self.plan(),marker)
                    self.assertEqual(result['returncode'],0,result)
                    self.assertEqual(json.loads((directory / (arm+'-'+phase+'.stdout')).read_text())['result']['raw_bytes'],len(raw))
                self.assertEqual(restored.read_bytes(),raw)
                self.assertEqual(archive.read_bytes(),repeat.read_bytes())
                self.assertEqual(archive.read_bytes()[:8], b'D2GRAM01' if arm=='B' else b'D2GRAM02')


if __name__ == '__main__':
    unittest.main()
