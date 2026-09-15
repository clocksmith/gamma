import math
import struct
import unittest
from fractions import Fraction
from lib.fx2_residual_projection_v1 import Q,S,RADIUS,count,unpack,ln2_bounds,bounds,lower_bound,certificate

class ResidualTests(unittest.TestCase):
    def test_identity_domain_and_monotonicity(self):
        for c in range(1,Q):
            self.assertEqual(count(c,0),c)
            self.assertLessEqual(count(c,-RADIUS),c)
            self.assertGreaterEqual(count(c,RADIUS),c)
    def test_rational_rounding_and_error(self):
        for c in (1,2,17,32767,32768,32769,65534,65535):
            for k in (-RADIUS,-127,-1,0,1,127,RADIUS):
                q=Fraction(c)+Fraction(c*(Q-c)*k,Q*S)
                self.assertLessEqual(abs(count(c,k)-q),Fraction(1,2))
                self.assertEqual(count(c,k),max(1,min(Q-1,math.floor(q+Fraction(1,2)))))
    def test_probability_identity(self):
        for c in (1,13,30000,65535):
            for k in (-RADIUS,0,RADIUS):
                p=Fraction(c,Q);u=Fraction(k,S);q=p+p*(1-p)*u
                for y in (0,1):
                    self.assertEqual((q if y else 1-q)/(p if y else 1-p),1+u*(y-p))
    def test_feature_codes(self):
        self.assertEqual(unpack(9)[:3],[1,-1,0])
        with self.assertRaises(ValueError):unpack(3)
    def test_invalid_domains(self):
        for c,k in ((0,0),(Q,0),(1,RADIUS+1),(1,-RADIUS-1)):
            with self.assertRaises(ValueError):count(c,k)
        with self.assertRaises(ValueError):lower_bound([], [RADIUS]*32)
    def test_bounds_against_exhaustive_two_coordinate_family(self):
        rows=[(20000,1,[1,-1]+[0]*30),(50000,0,[-1,1]+[0]*30),(30000,1,[1,1]+[0]*30)]
        upper,data=bounds(rows)
        for a in range(-8,9):
            for b in range(-8,9):
                if abs(a)+abs(b)>8:continue
                theta=[a*(RADIUS//8),b*(RADIUS//8)]+[0]*30
                value=sum(math.log1p(sum(t*x for t,x in zip(theta,r))/(Q*S)) for r in data)
                self.assertLessEqual(float(lower_bound(data,theta)),value+1e-14)
                self.assertLessEqual(value,float(upper)+1e-14)
    def test_log_interval_nested(self):
        lo,hi=ln2_bounds();lo2,hi2=ln2_bounds(40)
        self.assertLess(lo,lo2);self.assertLess(hi2,hi)
        self.assertLess(hi-lo,Fraction(1,10**30))
    def test_causal_trace_alignment_and_zero_features(self):
        body=b'\xa5';feature=b'';coder=b''
        for i in range(8):
            y=(body[0]>>(7-i))&1
            feature+=struct.pack('<QHBB',0,32000,i,y)
            coder+=struct.pack('<7I',0,32000,0,0,0,0,y)
        result=certificate(feature,body,coder)
        self.assertEqual(result['rounded_upper_bits_diagnostic'],0)
        self.assertFalse(result['rounded_can_pay_coefficients'])
        bad=bytearray(feature);bad[10]=1
        with self.assertRaises(ValueError):certificate(bad,body,coder)
    def test_rounding_upper_inequality(self):
        for c in (1,2,19,1000,32000,65534,65535):
            for k in (-RADIUS,-21,-1,0,1,21,RADIUS):
                exact=Fraction(c)+Fraction(c*(Q-c)*k,Q*S)
                for y in (0,1):
                    z=exact if y else Q-exact;r=count(c,k) if y else Q-count(c,k);ct=c if y else Q-c
                    self.assertLessEqual(Fraction(r,z)-1,Fraction(Q,ct*(Q+ct)))

if __name__=='__main__':unittest.main()
