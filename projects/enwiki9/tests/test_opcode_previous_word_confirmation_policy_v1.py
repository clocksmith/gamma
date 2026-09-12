"""Decision dimensions and existing comparison with the 1MB boundary wrapper."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import opcode_previous_word_confirmation_gate_v1 as gate
from tests.test_opcode_previous_word_transfer_gate_v1 import TransferGateTests

class PolicyTests(unittest.TestCase):
    def test_valid_measurements(self):
        for gp, gs, expected in [(1,1,'Predictive confirmation'), (0,1,'No archive improvement'),
                                  (-1,1,'Archive regression'), (1,0,'Parent improvement'), (1,-1,'Parent improvement')]:
            self.assertTrue(gate.decision(gp,gs,True,True,True,True).startswith(expected))
    def test_incomplete_never_invents_compression_loss(self):
        for complete, correct, repeat, resource in [(False,None,None,False),(False,None,None,None),
                (True,True,True,False),(True,True,False,True),(True,None,True,True)]:
            self.assertTrue(gate.decision(-1,-1,complete,correct,repeat,resource).startswith('Resource failure or incomplete'))
        self.assertTrue(gate.decision(-1,-1,True,False,True,True).startswith('Correctness or control failure'))
    def test_unchanged_seventeen_phase_comparison(self):
        fixture = TransferGateTests('test_seventeen_phases_and_fresh_release_dependency')
        fixture.setUp()
        try:
            result=gate.run_comparison(fixture.out, fixture.plan, fixture.snapshot,
                fixture.base/'phases.jsonl', fixture.limits)
            self.assertEqual(len(result['commands']),17)
            self.assertTrue(result['correctness_pass'])
            self.assertEqual((fixture.out/'controls/P.arc').read_bytes(),(fixture.out/'controls/K.arc').read_bytes())
            self.assertTrue((fixture.out/'completed-controls.json').is_file())
        finally:
            fixture.doCleanups()

if __name__ == '__main__': unittest.main()
