import struct
import tempfile
from pathlib import Path
import unittest
from projects.enwiki9.tools import fx2_ratio_coder_fixture50051_q0_v1 as gate


def trace(arm,modeled=2):
    out=bytearray()
    for i in range(2*modeled):
        ratio=b'GRR1'+struct.pack('<HBBQ',205,ord('D' if arm=='K' else arm),i%2,i//2)+bytes(12*205)
        state=b'GRD2'+struct.pack('<HBBH',205,ord(arm),int(i>0),2476)+ratio+bytes(17*205)
        event=b'I' if i==0 else b'P' if i%2 else b'O'
        out+=event+struct.pack('<I',len(state))+state
    return out


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def put(self,name,raw):
        p=self.root/name;p.write_bytes(raw);return p

    def test_complete_states_and_kd_identity(self):
        k=self.put('K',trace('K'));d=self.put('D',trace('D'))
        self.assertEqual(gate.validate_ratio_trace(d,'D',2)['records'],4)
        self.assertTrue(gate.compare_delivery_states(k,d,'K','D',2,True)['full_state_equal_except_arm'])

    def test_missing_record_wrong_position_and_wrong_embedded_arm_rejected(self):
        for offset in (None,5+10+6,5+10+8):
            raw=trace('D')
            if offset is None:raw=raw[:-1]
            else:raw[offset]^=1
            with self.assertRaises(ValueError):gate.validate_ratio_trace(self.put('bad',raw),'D',2)

    def test_cached_original_mass_drift_rejected(self):
        p=self.put('P',trace('P'));raw=trace('D');raw[5+2486+1]=1
        with self.assertRaisesRegex(ValueError,'original row'):
            gate.compare_delivery_states(p,self.put('D',raw),'P','D',2)

    def test_correction_state_drift_rejected_but_not_confused_with_parent_projection(self):
        k=self.put('K',trace('K'));raw=trace('D');raw[5+10+16]=1;d=self.put('D',raw)
        self.assertTrue(gate.compare_delivery_states(k,d,'K','D',2)['base_rows_identical'])
        with self.assertRaisesRegex(ValueError,'K/D correction'):
            gate.compare_delivery_states(k,d,'K','D',2,True)

    def test_original_prediction_drift_rejected_even_when_coded_counts_match(self):
        records=[(0x3f000000,32768,0,1,0,1,1)]*16
        p=self.put('P',b''.join(struct.pack('<7I',*r) for r in records))
        raw=bytearray(p.read_bytes());raw[0]^=1
        with self.assertRaisesRegex(ValueError,'original prediction'):
            gate.compare_parent_projection(p,self.put('D',raw),2)

    def test_changed_counts_and_ideal_loss_reported_separately(self):
        def records(q):return b''.join(struct.pack('<7I',0x3f000000,q,0,1,0,1,1) for _ in range(16))
        p=self.put('P',records(32768));d=self.put('D',records(49152))
        report=gate.compare_parent_projection(p,d,2)
        self.assertEqual(report['records'],16);self.assertEqual(report['changed_q16_events'],16)
        self.assertAlmostEqual(report['ideal_bits_saved'],16*gate.math.log2(1.5))
        self.assertTrue(all(v>0 for v in report['chronological_thirds']))


if __name__=='__main__':unittest.main()
