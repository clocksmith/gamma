import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import dualstream_enumerative_gate_v3 as adapter
from tools import dualstream_grammar_v1 as old
from tools import dualstream_grammar_argtokens_v2 as new


class IntegrationTests(unittest.TestCase):
    def test_complete_synthetic_five_arm_runner(self):
        gate = adapter.gate
        with tempfile.TemporaryDirectory(prefix='enum_inputs_', dir=gate.ROOT/'results') as inputs, \
             tempfile.TemporaryDirectory(prefix='enum_runner_', dir=gate.ROOT/'results') as output:
            inputs, output = Path(inputs), Path(output)
            raw = b'<title>Oak</title>Oak is a town.\xff\x00'
            model = old.Model(structure=(('call', 0),), arguments=(b'Oak',),
                              templates=((1, (b'<title>', old.Arg(0), b'</title>', old.Arg(0), b' is a town.\xff\x00')),))
            b = old.HEADER.pack(old.MAGIC, old.MAX_FRAME, 1, len(raw)) + old.frame_bytes(raw, 'parameter', model)[0]
            p = new.encode(raw, mode='plain')[0]
            for name, data in [('raw',raw),('B.d2g',b),('P.d2g',p)]:
                (inputs/name).write_bytes(data)
            plan = dict(phase_cpu_seconds=60, phase_wall_seconds=90, phase_address_bytes=536870912,
                        population=gate.driver.artifact(inputs/'raw'), selected_archives={
                            'old':gate.driver.artifact(inputs/'B.d2g'), 'plain':gate.driver.artifact(inputs/'P.d2g')})
            argv = ['gate','--candidate',output.name]
            with patch.object(gate,'authenticate',return_value=({}, {}, plan)), \
                 patch.object(sys,'argv',argv), patch.dict(os.environ, {'GAMMA_RESOURCE_PHASE_MARKERS':str(inputs/'phases.jsonl')}):
                self.assertEqual(gate.main(),0)
            stage = json.loads((output/'stage-decision.json').read_text())
            self.assertTrue(stage['correctness_pass'])
            self.assertEqual(stage['native_phases'],15)
            self.assertEqual((output/'P.d2g').read_bytes(),p)
            self.assertEqual((output/'B.d2g').read_bytes(),b)
            for arm in gate.ARMS:
                self.assertEqual((output/(arm['id']+'.raw')).read_bytes(), raw)
                self.assertEqual((output/(arm['id']+'.d2g')).read_bytes(),(output/(arm['id']+'.repeat.d2g')).read_bytes())

    def test_plain_arm_declares_new_frontend(self):
        self.assertEqual(adapter.gate.ARMS[0]['storage'],'new')
        self.assertEqual(adapter.gate.driver.SELF,'tools/dualstream_enumerative_gate_v3.py')


if __name__ == '__main__':
    unittest.main()
