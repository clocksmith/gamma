"""Run the unchanged synthetic suite plus zero-byte runtime regressions."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_event_opportunity_decode250k_q0_v2 as gate

base_path = ROOT/'tests/test_opcode_event_opportunity_decode250k_q0_v1.py'
if hashlib.sha256(base_path.read_bytes()).hexdigest() != '1cfcc0ab6d8cf726edbe342c97e0d33350e4365da14ae54d2d1196463853d3b8':
    raise ValueError('immutable v1 synthetic tests differ')
spec = importlib.util.spec_from_file_location('opcode_opportunity_v1_tests', base_path)
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)


class OpportunityDecodeV2Tests(base.OpportunityDecodeTests):
    def setUp(self):
        replace = patch.object(base, 'gate', gate); replace.start(); self.addCleanup(replace.stop)
        super().setUp()

    def test_empty_runtime_and_nonempty_mutations_fail_closed(self):
        empty = self.base/'empty.py'; empty.write_bytes(b'')
        reference = dict(path=str(empty), bytes=0, sha256=hashlib.sha256(b'').hexdigest())
        self.assertEqual(gate.check_runtime_file(reference), empty)
        plan = copy.deepcopy(self.plan); plan['runtime_files'] = [reference]
        gate.verify_inputs(plan)
        empty.write_bytes(b'x')
        with self.assertRaisesRegex(ValueError, 'changed empty'):
            gate.verify_inputs(plan)
        nonempty = dict(reference, bytes=1, sha256=hashlib.sha256(b'x').hexdigest())
        self.assertEqual(gate.check_runtime_file(nonempty), empty)
        empty.write_bytes(b'y')
        with self.assertRaisesRegex(ValueError, 'changed file'):
            gate.check_runtime_file(nonempty)
        for bad in (dict(reference, path='relative.py'), dict(reference, bytes=False),
                    dict(reference, path=str(self.base/'../empty.py'))):
            with self.assertRaises(ValueError):
                gate.check_runtime_file(bad)

    def test_v1_authentication_and_unchanged_science(self):
        bad = self.base/'wrong_source.py'; bad.write_text('raise RuntimeError("must not execute")')
        with self.assertRaisesRegex(ValueError, 'source differs'):
            gate.load_original(bad)
        self.assertIs(gate.EventSink, gate.original.EventSink)
        self.assertIs(gate.decode_phase, gate.original.decode_phase)
        self.assertIs(gate.ceil_log2_ratio, gate.original.ceil_log2_ratio)
        self.assertIs(gate.run_comparison.__code__, gate.original.run_comparison.__code__)
        self.assertEqual(gate.original.CID, 'opcode_event_opportunity_decode250k_q0_v1')
        self.assertEqual(gate.run_comparison.__globals__['SELF'], gate.SELF)


if __name__ == '__main__':
    unittest.main()
