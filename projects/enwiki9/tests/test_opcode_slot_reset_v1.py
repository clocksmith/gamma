"""Reset-only causality and independent arithmetic replay; synthetic inputs only."""
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_slot_reset_observe_v1 as witness
import opcode_field_compact_observe_v1 as old


class ResetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codec=witness.cli.load(ROOT/'programs/opcode_slot_reset_v1/program.py')
        cls.parent=old.load(ROOT/'programs/opcode_field_compact_v1/program.py')

    def states(self):
        states=[]
        for arm in 'PKD':
            ns=self.codec.namespace(arm);ns['_limit']=2000000
            states.append(ns['GST']())
        return states

    def test_completed_close_changes_only_slot(self):
        raw=b'<text xml:space="preserve">==References==\n</text><title>Next</title>'
        states=self.states();closes=0
        for byte in self.codec.namespace('P')['oe'](raw):
            close=states[0].field.pending and byte==2
            before=states[2].slot
            for state in states:state.up(byte)
            for key in ('f','w','p','q','r','s','c','pg','col','tail','word','position','modeled_f'):
                self.assertEqual(getattr(states[0],key),getattr(states[1],key))
                self.assertEqual(getattr(states[0],key),getattr(states[2],key))
            self.assertEqual(states[0].slot,states[1].slot)
            if close:
                closes+=1;self.assertEqual(before,9)
                self.assertEqual(states[0].slot,9);self.assertEqual(states[2].slot,0)
        self.assertEqual(closes,1)

    def test_prefix_escape_and_raw_markup_do_not_create_a_reset(self):
        state=self.states()[2]
        state.slot=9
        state.up(0);self.assertEqual(state.slot,9)
        state.up(255);state.up(2);self.assertEqual(state.slot,9)
        state.up(0);state.up(2);self.assertEqual(state.slot,0)
        p,k,d=self.states()
        for byte in b'[[Category:Trees]]':
            for s in (p,k,d):s.up(byte)
            self.assertEqual(p.slot,d.slot)

    def test_all_arms_inverse_repeat_and_parent_projection(self):
        fixtures=[b'',bytes(range(256))*2,b'\0\xff<broken\xc0\r\n',
            (b'<title>Oak</title><text xml:space="preserve">==References==\n'
             b'Oak is a tree. Oak is a tree.</text>\n')*12]
        activated=False
        for raw in fixtures:
            reference,reference_audit=old.execute(self.parent,'encode',raw)
            arms={}
            for arm in 'PKD':
                arc,enc=witness.execute(self.codec,'encode',raw,arm)
                inverse,dec=witness.execute(self.codec,'decode',arc,arm)
                repeat,rep=witness.execute(self.codec,'encode',inverse,arm)
                self.assertEqual(inverse,raw);self.assertEqual(arc,repeat)
                self.assertEqual(enc,dec);self.assertEqual(enc,rep)
                self.assertEqual(arc,self.codec.compress(raw,arm))
                self.assertEqual(sum(enc['slot_byte_counts']),enc['parent']['modeled_bytes'])
                self.assertEqual(sum(enc['mode_changed_slot_bytes']),enc['changed_slot_bytes'])
                arms[arm]=(arc,enc)
            self.assertEqual(arms['P'][0],reference);self.assertEqual(arms['P'][0],arms['K'][0])
            self.assertEqual(arms['P'][1]['parent'],reference_audit)
            self.assertEqual(arms['P'][1]['parent'],arms['K'][1]['parent'])
            activated|=arms['D'][1]['changed_slot_bytes']>0
        self.assertTrue(activated)

    def test_corruption_bounds_and_fresh_state(self):
        raw=b'<text xml:space="preserve">==References==\n</text>'*8
        arc=self.codec.compress(raw)
        for bad in (b'',arc[:-3],arc+b'\0',struct.pack('>II',1000001,1)+arc[8:]):
            with self.assertRaises(ValueError):self.codec.decompress(bad)
        self.codec.compress(b'{{other|field=value}}')
        self.assertEqual(arc,self.codec.compress(raw))
        with self.assertRaises(ValueError):self.codec.namespace('unknown')


if __name__=='__main__':unittest.main(verbosity=2)
