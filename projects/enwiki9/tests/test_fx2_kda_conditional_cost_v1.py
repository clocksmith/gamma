import math
import struct
import unittest
from tools.fx2_kda_conditional_cost_v1 import Certificate, analyze, pieces, age_bin, TOKENS

def trace(byte,mass):
    return b''.join(struct.pack('<7I',0,mass if byte>>(7-b)&1 else 65536-mass,0,0,0,0,byte>>(7-b)&1) for b in range(8))

class ConditionalCost(unittest.TestCase):
    def test_hand_calculated_gain_and_bound(self):
        r=analyze(b'\x0f',{a:trace(15,m) for a,m in [('P',32768),('D',49152),('S',16384)]})
        self.assertAlmostEqual(r['ideal_bits_saved']['D'],8*math.log2(1.5))
        self.assertEqual(r['ideal_bits_saved']['S'],-8)
        self.assertEqual(r['PD_certificate']['ceiling_bits'],5)
        self.assertEqual(r['positive_D_pieces'],1)
        self.assertEqual(r['age_buckets'][0]['modeled_bytes'],1)
    def test_no_gain_is_zero(self):
        r=analyze(b'\0',{a:trace(0,32768) for a in 'PDS'})
        self.assertEqual(r['PDS_certificate']['ceiling_bits'],0)
        self.assertEqual(r['changed_probability_records'],dict(D=0,S=0))
    def test_last_bit_alignment_rejected(self):
        t={a:trace(0,32768) for a in 'PDS'}
        t['D']=t['D'][:-4]+struct.pack('<I',1)
        with self.assertRaisesRegex(ValueError,'truth/count'):analyze(b'\0',t)
    def test_certificate_chunk_boundary(self):
        c=Certificate()
        for _ in range(4097):c.add(2,1)
        r=c.result();self.assertEqual(r['ceiling_bits'],4097)
        self.assertEqual([x['events'] for x in r['chunks']],[4096,1])
    def test_decoded_boundary_and_maximum(self):
        self.assertEqual(pieces(b'aa!!z12345',b'!!',5),[0,4,9])
        self.assertEqual(pieces(b'aa!!',b'!!',5),[0])
        self.assertEqual(pieces(b'aa!!z',b'!!',5),[0,4])
        self.assertEqual([age_bin(n) for n in [0,1,3,4,15,16,63,64,255,256,1023,1024]], [0,1,1,2,2,3,3,4,4,5,5,6])
        self.assertEqual(len(TOKENS),205)

if __name__=='__main__':unittest.main()
