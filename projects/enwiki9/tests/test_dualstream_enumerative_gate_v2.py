import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import dualstream_enumerative_gate_v2 as gate


class FailureRoutingTests(unittest.TestCase):
    def test_subprocess_failure_classifications(self):
        last = dict(timeout=False, error=None, argv=['missing'], returncode=1)
        cases = [(dict(last, error='No such file'), 'infrastructure-failure'),
                 (dict(last, timeout=True), 'budget-exhausted'),
                 (last, 'implementation-failure'),
                 (dict(last, returncode=-9), 'infrastructure-failure')]
        for record, expected in cases:
            self.assertEqual(gate.classify_failure(ValueError('phase failed'), record), expected)
        self.assertEqual(gate.classify_failure(OSError('absent'), None), 'infrastructure-failure')

    def test_new_identity_preserves_fixed_arms(self):
        self.assertEqual(gate.driver.SELF, 'tools/dualstream_enumerative_gate_v2.py')
        self.assertEqual([a['id'] for a in gate.ARMS], ['P', 'B', 'E', 'T', 'R'])


if __name__ == '__main__':
    unittest.main()
