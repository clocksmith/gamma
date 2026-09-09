"""Independent big-integer oracle for final-coder residual delivery."""
import ctypes
from fractions import Fraction
import os
import random
import struct
import unittest

UNIT=1<<45


def reference(parent,prefix,vocabulary,base,corrected):
    if not vocabulary:return parent
    depth=prefix.bit_length()-1;width=1<<(8-depth);start=(prefix-(1<<depth))*width
    p=[0,0];q=[0,0]
    for v,b,c in zip(vocabulary,base,corrected):
        if start<=v<start+width:
            bit=int(v>=start+width//2);p[bit]+=b;q[bit]+=c
    if not all(p):return parent
    a=parent*q[1]*p[0];b=(65536-parent)*p[1]*q[0]
    return max(1,min(65535,round(Fraction(65536*a,a+b))))


class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib=ctypes.CDLL(os.environ['FX2_DELIVERY_LIBRARY'])
        cls.lib.delivery_correct.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.POINTER(ctypes.c_uint8),
                                          ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_uint64),ctypes.c_uint]
        cls.lib.delivery_correct.restype=ctypes.c_int
        cls.lib.delivery_units.argtypes=[ctypes.c_uint32,ctypes.c_int]
        cls.lib.delivery_units.restype=ctypes.c_uint64

    def native(self,p,prefix,v,b,c):
        n=len(v)
        return self.lib.delivery_correct(p,prefix,(ctypes.c_uint8*n)(*v),
                                        (ctypes.c_uint64*n)(*b),(ctypes.c_uint64*n)(*c),n)

    def test_every_parent_count_identity_and_proportionality(self):
        for p in range(1,65536):
            self.assertEqual(self.native(p,1,[0,255],[7,11],[21,33]),p)

    def test_seeded_prefixes_against_exact_rationals(self):
        rng=random.Random('fx2_ratio_coder_delivery_v1')
        for _ in range(2000):
            v=sorted(rng.sample(range(256),rng.randint(2,256)))
            b=[rng.randint(1,UNIT) for _ in v];c=[rng.randint(1,4*UNIT) for _ in v]
            p=rng.randint(1,65535);prefix=rng.randint(1,255)
            self.assertEqual(self.native(p,prefix,v,b,c),reference(p,prefix,v,b,c))

    def test_extreme_products_and_probability_clamps(self):
        v=list(range(256));b=[UNIT]*256;c=[1]*128+[4*UNIT]*128
        for p in (1,2,32768,65534,65535):
            for prefix in (1,2,3,64,127,128,255):
                self.assertEqual(self.native(p,prefix,v,b,c),reference(p,prefix,v,b,c))
        self.assertEqual(self.native(65535,1,[0,255],[UNIT,UNIT],[1,4*UNIT]),65535)
        self.assertEqual(self.native(1,1,[0,255],[UNIT,UNIT],[4*UNIT,1]),1)

    def test_midpoint_ties_round_to_even(self):
        # p=1 and base0=base1: choose q1/q0 so ideal counts are k+1/2.
        for k in (1,2,32766,32767,32768):
            q1=(2*k+1)*65535;q0=131072-(2*k+1)
            expected=max(1,min(65535,k+(k&1)))
            self.assertEqual(self.native(1,1,[0,255],[1,1],[q0,q1]),expected)

    def test_sparse_or_initial_support_is_neutral(self):
        self.assertEqual(self.native(4567,1,[],[],[]),4567)
        self.assertEqual(self.native(4567,1,[0,1],[4,7],[1,20]),4567)
        self.assertEqual(self.native(4567,255,[0,1],[4,7],[1,20]),4567)

    def test_invalid_inputs_rejected(self):
        for p,prefix in ((0,1),(65536,1),(1,0),(1,256)):
            self.assertEqual(self.native(p,prefix,[0,255],[1,1],[1,1]),-1)
        for v,b,c in (([0],[1],[1]),([1,0],[1,1],[1,1]),([0,0],[1,1],[1,1]),
                      ([0,255],[0,1],[1,1]),([0,255],[UNIT+1,1],[1,1]),
                      ([0,255],[1,1],[0,1]),([0,255],[1,1],[4*UNIT+1,1])):
            self.assertEqual(self.native(100,1,v,b,c),-1)

    def test_native_float_mass_conversion(self):
        rng=random.Random('delivery-units')
        for corrected,low,high in ((0,0x358637bd,0x3f800000),(1,0x348637bd,0x40800000)):
            for raw in [low,high]+[rng.randint(low,high) for _ in range(1000)]:
                value=struct.unpack('<f',struct.pack('<I',raw))[0]
                exact=Fraction.from_float(value)*UNIT
                self.assertEqual(exact.denominator,1)
                self.assertEqual(self.lib.delivery_units(raw,corrected),exact.numerator)
            for raw in (0,low-1,high+1,0x7f800000,0x7fc00000,0xbf800000):
                self.assertEqual(self.lib.delivery_units(raw,corrected),0)


if __name__=='__main__':unittest.main()
