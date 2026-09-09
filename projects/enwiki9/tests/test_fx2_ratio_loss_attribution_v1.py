"""Synthetic alignment and half-conversion checks for retained-trace replay."""
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import fx2_ratio_loss_attribution_v1 as audit


class AttributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['FX2_AUDIT_TMP'])
        self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.library=ROOT/'results/fx2_residual_ratio_native_v1/attempt01/ratio.so'
        self.raw=bytes([2,3,2,4]);self.vocab=list(range(205))
        h=struct.unpack('<H',struct.pack('<e',1/205))[0];half=[h]*205
        native=audit.Native(audit.load_library(self.library),205,'D')
        try:
            with (self.root/'states').open('wb') as s,(self.root/'halves').open('wb') as f:
                def state(kind):
                    b=native.serialize();s.write(kind+struct.pack('<I',len(b))+b)
                state(b'I')
                for i,b in enumerate(self.raw):
                    if i:native.observe(b);state(b'O')
                    for kind in (b'I',b'O'):
                        f.write(kind+struct.pack('<HQ205H',205,i,*half))
                    native.predict(audit.converted(half));state(b'P')
        finally:native.close()
        records=b''.join(struct.pack('<7I',0,32768,0,0,0,0,(b>>k)&1) for b in self.raw for k in range(7,-1,-1))
        (self.root/'coder').write_bytes(records)

    def run_replay(self):
        return audit.replay(self.root/'halves',self.root/'coder',self.root/'coder',self.root/'states',self.vocab,self.library,4)

    def test_first_byte_and_last_prediction_alignment(self):
        r=self.run_replay()
        self.assertEqual(r['scored_symbols'],3);self.assertEqual(r['matched_calibration_states'],8)
        self.assertEqual(r['final_coder_ideal_bits_saved'],0)
        self.assertEqual(r['changed_q16_events'],0)

    def test_state_mismatch_rejected(self):
        p=self.root/'states';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b)
        with self.assertRaisesRegex(ValueError,'calibration-state divergence'):self.run_replay()

    def test_half_order_and_trailing_data_rejected(self):
        p=self.root/'halves';b=p.read_bytes();p.write_bytes(b'F'+b[1:])
        with self.assertRaisesRegex(ValueError,'half event order'):self.run_replay()
        p.write_bytes(b+b'\0')
        with self.assertRaisesRegex(ValueError,'trailing trace'):self.run_replay()

    def test_tail_conversion_preserves_original_quirk(self):
        row=audit.converted([1023]*205)
        self.assertEqual(audit.value(row[0]),2*audit.value(row[200]))
        self.assertEqual(audit.converted([0]*205),[audit.bits(1e-6)]*205)

    def test_coder_truth_mismatch_rejected(self):
        p=self.root/'other';b=bytearray((self.root/'coder').read_bytes());b[24]^=1;p.write_bytes(b)
        with self.assertRaisesRegex(ValueError,'coder truth'):audit.coder_comparison(self.root/'coder',p,4)


if __name__=='__main__':unittest.main()
