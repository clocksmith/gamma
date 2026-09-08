"""Isolate wiki-slot reconstruction, causality and complete codec inversion."""
import copy
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import opcode_wiki_slot_observe_v1 as witness
import opcode_field_compact_observe_v1 as old


class SlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codec = witness.load(ROOT/'programs/opcode_wiki_slot_v1/program.py')
        cls.parent = old.load(ROOT/'programs/opcode_field_compact_v1/program.py')

    def test_all_arms_exact_and_parent_projection(self):
        fixtures = [b'', bytes(range(256))*2, b'\0\xff<broken\xc0\r\n',
                    (b'<title>Oak</title><text xml:space="preserve">'
                     b'{{cite|url=http://x|title=Oak}} [[Category:Trees]] '
                     b'[[Image:Oak.jpg]] <ref name="tree">Oak</ref></text>\n')*16]
        for raw in fixtures:
            with self.subTest(length=len(raw)):
                reference, reference_audit = old.execute(self.parent, 'encode', raw)
                arms = {}
                for arm in 'PKD':
                    arc, enc = witness.execute(self.codec, 'encode', raw, arm)
                    restored, dec = witness.execute(self.codec, 'decode', arc, arm)
                    repeat, rep = witness.execute(self.codec, 'encode', restored, arm)
                    self.assertEqual(restored, raw)
                    self.assertEqual(arc, repeat)
                    self.assertEqual(enc, dec)
                    self.assertEqual(enc, rep)
                    self.assertEqual(sum(map(sum, enc['mode_slot_byte_counts'])),enc['parent']['modeled_bytes'])
                    self.assertEqual(sum(enc['mode_changed_slot_bytes']),enc['changed_slot_bytes'])
                    self.assertEqual(self.codec.compress(raw, arm), arc)
                    arms[arm] = arc, enc
                self.assertEqual(reference, arms['P'][0])
                self.assertEqual(arms['P'][0], arms['K'][0])
                self.assertEqual(reference_audit, arms['P'][1]['parent'])
                self.assertEqual(arms['P'][1]['parent'], arms['K'][1]['parent'])

    def test_only_slot_is_exposed_and_opcode_prefix_is_causal(self):
        raw = b'<title>Oak</title>{{cite|title=Oak}}[[Category:Trees]]\0<ref name="x">x</ref>'
        spaces = [self.codec.namespace(arm) for arm in 'PKD']
        modeled = spaces[0]['oe'](raw)
        states = []
        for ns in spaces:
            ns['_limit'] = len(modeled)
            states.append(ns['GST']())
        differences = 0
        for byte in modeled:
            previous = copy.deepcopy(vars(states[2].raw_state))
            pending = states[2].raw_pending
            for state in states:state.up(byte)
            if byte == 0 and not pending:
                self.assertEqual(vars(states[2].raw_state), previous)
            for key in ('f','w','p','q','r','s','c','pg','col','tail','word','position','modeled_f'):
                self.assertEqual(getattr(states[0],key),getattr(states[1],key))
                self.assertEqual(getattr(states[0],key),getattr(states[2],key))
            self.assertEqual(states[0].slot, states[1].slot)
            self.assertEqual(states[2].slot, states[2].raw_state.slot)
            differences += states[0].slot != states[2].slot
        self.assertGreater(differences, 0)
        self.assertEqual(states[2].raw_position, len(raw))
        self.assertFalse(states[2].raw_pending)

    def test_raw_state_reconstructs_every_fixed_opcode_and_zero(self):
        ns = self.codec.namespace('D')
        raw = b'|'.join(ns['TT']) + b'\0\xff\r\n'
        modeled = ns['oe'](raw); ns['_limit'] = len(modeled)
        state, direct = ns['GST'](), ns['_GST']()
        for byte in modeled:state.up(byte)
        for byte in raw:direct.up(byte)
        self.assertEqual(vars(state.raw_state), vars(direct))
        self.assertEqual(state.raw_position, len(raw))

    def test_side_witness_covers_unused_and_predictive_state(self):
        ns=self.codec.namespace('K');ns['_limit']=100
        state=ns['GST']()
        initial=witness.side(state)
        state.raw_state.w=2
        self.assertNotEqual(initial,witness.side(state))
        state.raw_state.w=0;state.modeled_slot=3
        self.assertNotEqual(initial,witness.side(state))

    def test_malformed_bounds_and_repeat_fresh_state(self):
        raw=b'{{infobox|title=Oak}}\0'*16
        arc=self.codec.compress(raw)
        for bad in (b'',arc[:-3],arc+b'\0',struct.pack('>II',1000001,1)+arc[8:]):
            with self.assertRaises(ValueError):self.codec.decompress(bad)
        self.codec.compress(b'[[Category:Different]]'*8)
        self.assertEqual(arc,self.codec.compress(raw))
        with self.assertRaises(ValueError):self.codec.namespace('unknown')


if __name__ == '__main__':
    unittest.main(verbosity=2)
