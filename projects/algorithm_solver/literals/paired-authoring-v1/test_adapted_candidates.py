"""Adapter emission is source-as-data only; no execution."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import adapted_candidates as a
class AdapterTests(unittest.TestCase):
    def test_complete_source_and_adapter_accounting(self):
        source=b'class Solution { sample(x) { return x; } }\n'
        complete,adapter=a.emit(source,'sample')
        self.assertEqual(complete,source+adapter)
        self.assertIn(b'new Solution().sample(...args)',adapter)
        self.assertEqual(len(complete),len(source)+len(adapter))
        self.assertTrue(complete.startswith(source))
    def test_method_injection_rejected(self):
        for method in ('x);bad(', 'a.b', '', '1bad', 'x\n'):
            with self.assertRaises(ValueError):a.emit(b'',method)
if __name__=='__main__':unittest.main()
