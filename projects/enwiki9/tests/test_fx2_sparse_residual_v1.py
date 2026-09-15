from fractions import Fraction
import itertools
import math
import random
import unittest
from lib.fx2_sparse_residual_v1 import Q,RADIUS,quadratic_upper,pack,unpack_table,table_bits,paid_upper

class SparseResidualTests(unittest.TestCase):
    def test_curvature_against_discrete_objectives(self):
        rng=random.Random(9183)
        for _ in range(40):
            values=[rng.randrange(-Q+1,Q) for _ in range(17)]
            upper=quadratic_upper(sum(values),sum(v*v for v in values))
            for k in range(-RADIUS,RADIUS+1,256):
                exact=sum(math.log1p(k*v/(32768*Q)) for v in values)
                self.assertLessEqual(exact,float(upper)+1e-12)
    def test_zero_and_radius_endpoint(self):
        self.assertEqual(quadratic_upper(0,0),0)
        values=[Q-1]*7
        expected=Fraction(sum(values),2*Q)-Fraction(sum(v*v for v in values),18*Q*Q)
        self.assertEqual(quadratic_upper(sum(values),sum(v*v for v in values)),expected)
    def test_all_masks_and_endpoint_coefficients(self):
        for mask in range(256):
            rows=[(r*4,(-1 if r%2 else 1)*RADIUS) if mask&(1<<r) else None for r in range(8)]
            data=pack(rows);self.assertEqual(unpack_table(data),rows)
            self.assertEqual(len(data)*8,table_bits(mask.bit_count()))
        self.assertEqual(table_bits(0),16);self.assertEqual(table_bits(8),176)
    def test_malformed_tables(self):
        for data in (b'',b'\x01',b'\x02\x00',b'\x01\x00\x00',b'\x01\x80\x00\x00'):
            with self.assertRaises(ValueError):unpack_table(data)
        data=bytearray(pack([(0,1)]+[None]*7));data[-1]|=1
        with self.assertRaises(ValueError):unpack_table(data)
        with self.assertRaises(ValueError):pack([(0,0)]+[None]*7)
        with self.assertRaises(ValueError):pack([(0,RADIUS+1)]+[None]*7)
    def test_joint_paid_bound_matches_all_row_subsets(self):
        rng=random.Random(512)
        for _ in range(50):
            scores=[Fraction(rng.randrange(120),3) for r in range(8)]
            rows,best=paid_upper(scores)
            exact=max(sum((scores[r] for r in range(8) if mask&(1<<r)),Fraction())-table_bits(mask.bit_count()) for mask in range(256))
            found=rows[best]['paid_upper_bits'];self.assertEqual(exact,Fraction(int(found['numerator']),int(found['denominator'])))
    def test_no_signal_still_pays_header(self):
        rows,best=paid_upper([Fraction()]*8)
        self.assertEqual(best,0);self.assertEqual(rows[best]['paid_upper_bits_diagnostic'],-16)
    def test_invalid_moments(self):
        for g,h in ((1,0),(0,-1)):
            with self.assertRaises(ValueError):quadratic_upper(g,h)

if __name__=='__main__':unittest.main()
