"""Adversarial causal-boundary tests; no corpus or fixture gain assertions."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
WHERE = ROOT/'programs/alias_context_fixture_q0_v1'
sys.path.insert(0,str(WHERE))
spec=importlib.util.spec_from_file_location('alias_fixture',WHERE/'program.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def feed(model, raw):
    for byte in raw:
        for shift in range(7,-1,-1):
            model.predict();model.update((byte>>shift)&1)


class CausalTests(unittest.TestCase):
    def test_definition_is_unavailable_until_complete(self):
        model=m.Model();feed(model,b'Alpha Beta (AB)')
        self.assertEqual(model.aliases,{})
        feed(model,b'\n');self.assertEqual(model.aliases,{b'AB':b'Alpha Beta'})
        feed(model,b'AB:');self.assertEqual(model.key()[0],b'Alpha Beta')

    def test_wrong_association_changes_edges_not_all_labels(self):
        d=m.Model('D');s=m.Model('S')
        for model in (d,s):feed(model,b'Alpha Beta (AB)\nCedar Dune (CD)\nAB:')
        self.assertEqual(d.key()[0],b'Alpha Beta');self.assertEqual(s.key()[0],b'Cedar Dune')
        for model in (d,s):feed(model,b'\nAlpha Beta:')
        self.assertEqual(d.key()[0],s.key()[0])

    def test_malformed_definition_and_overflow_fall_back(self):
        model=m.Model();feed(model,b'Alpha Beta (ZZ)\n'+b'Z'*140+b'Alpha Beta (AB)\n')
        self.assertFalse(model.aliases)
        raw=bytes(range(256))+b'\0\xff\r\n'
        archive=m.compress(raw);self.assertEqual(m.decompress(archive),raw)

    def test_parent_bookkeeping_identity_and_dictionary_bound(self):
        raw=b'Alpha Beta (AB)\nAlpha Beta:abcdef\nAB:abcdef\n'
        p=m.Model('P');k=m.Model('K')
        self.assertEqual(m.encode(raw,p),m.encode(raw,k))
        self.assertEqual(p.audit()['boundaries'],k.audit()['boundaries'])
        model=m.Model()
        for letter in b'ABCDEFGHIJKLMNOPQRST':
            feed(model,bytes([letter])+b'ster Beacon ('+bytes([letter])+b'B)\n')
        self.assertEqual(len(model.aliases),16)
        self.assertNotIn(b'AB',model.aliases)


if __name__=='__main__':unittest.main()
