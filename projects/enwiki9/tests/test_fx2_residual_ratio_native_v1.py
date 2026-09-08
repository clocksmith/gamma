"""Exact-rational reference versus native IEEE probability boundary."""
import ctypes
from fractions import Fraction
import hashlib
import os
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import unittest

from projects.enwiki9.lib import predictor as codec

ROOT = Path(__file__).resolve().parents[1]
Q=65536


def bits(x): return struct.unpack('<I',struct.pack('<f',x))[0]
def value(x): return struct.unpack('<f',struct.pack('<I',x))[0]


class Reference:
    def __init__(self,size,arm):
        self.n,self.arm,self.position=size,arm,0
        self.observed=[0]*size; self.expected=[0]*size; self.pending=None

    def predict(self,base):
        assert self.pending is None
        # Fraction.from_float uses the actual binary value, independently of
        # the native exponent-shift conversion into 2^-43 units.
        masses=[Fraction.from_float(value(x)) for x in base]; total=sum(masses)
        scaled=[x*Q/total for x in masses]
        count=[int(x) for x in scaled]
        order=sorted(range(self.n),key=lambda i:(-(scaled[i]-count[i]),i))
        for i in order[:Q-sum(count)]: count[i]+=1
        result=list(base)
        if self.arm in ('D','S'):
            for i,p in enumerate(masses):
                multiplier=max(Q//4,min(Q*4,(32*Q+self.observed[i])*Q//(32*Q+self.expected[i])))
                result[i]=bits(float(p*Fraction(multiplier,Q)))
        self.pending=count
        return result

    def observe(self,symbol):
        assert self.pending is not None
        if self.arm!='P':
            self.expected=[a+b for a,b in zip(self.expected,self.pending)]
            self.observed[(symbol+1)%self.n if self.arm=='S' else symbol]+=Q
            if (self.position+1)%256==0:
                self.observed=[x//2 for x in self.observed]; self.expected=[x//2 for x in self.expected]
        self.position+=1;self.pending=None

    def serialize(self):
        header=struct.pack('<4sHcBQ',b'GRR1',self.n,self.arm.encode(),self.pending is not None,self.position)
        return header+b''.join(struct.pack('<III',a,b,c) for a,b,c in zip(
            self.observed,self.expected,self.pending if self.pending is not None else [0]*self.n))


def load_library(path):
    lib=ctypes.CDLL(str(path))
    signatures={
        'ratio_new':([ctypes.c_uint,ctypes.c_char],ctypes.c_void_p),
        'ratio_delete':([ctypes.c_void_p],None),
        'ratio_predict':([ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)],ctypes.c_int),
        'ratio_observe':([ctypes.c_void_p,ctypes.c_uint],ctypes.c_int),
        'ratio_save':([ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint8)],ctypes.c_uint),
        'ratio_load':([ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint8),ctypes.c_uint],ctypes.c_int),
        'ratio_units':([ctypes.c_uint32],ctypes.c_uint64)}
    for name,(args,result) in signatures.items():
        function=getattr(lib,name);function.argtypes=args;function.restype=result
    return lib


class Native:
    def __init__(self,lib,n,arm):
        self.lib,self.n=lib,n;self.handle=lib.ratio_new(n,arm.encode())
        if not self.handle:raise ValueError('native configuration')
    def close(self):
        if self.handle:self.lib.ratio_delete(self.handle);self.handle=None
    def __del__(self):self.close()
    def predict(self,base):
        if len(base)!=self.n:raise ValueError('row size')
        row=(ctypes.c_uint32*self.n)(*base)
        if not self.lib.ratio_predict(self.handle,row):raise ValueError('native prediction')
        return list(row)
    def observe(self,symbol):
        if not self.lib.ratio_observe(self.handle,symbol):raise ValueError('native update')
    def serialize(self):
        output=(ctypes.c_uint8*3088)();n=self.lib.ratio_save(self.handle,output)
        return bytes(output[:n])
    def restore(self,payload):
        raw=(ctypes.c_uint8*len(payload)).from_buffer_copy(payload)
        if not self.lib.ratio_load(self.handle,raw,len(payload)):raise ValueError('native checkpoint')


class NativeFixture(codec.Predictor):
    def __init__(self,lib,arm):
        super().__init__(codec.RAW_MSB);self.native=Native(lib,256,arm)
        self.prefix=1;self.weights=None
        self.probabilities=hashlib.sha256();self.boundaries=hashlib.sha256()
    def _predict(self):
        if self.prefix==1:
            row=self.native.predict([bits(1/256)]*256)
            self.weights=[int(Fraction.from_float(value(x))*(1<<45)) for x in row]
        depth=self.prefix.bit_length()-1;width=1<<(8-depth)
        start=(self.prefix-(1<<depth))*width
        total=sum(self.weights[start:start+width]);one=sum(self.weights[start+width//2:start+width])
        p=max(1,min(65535,one*Q//total));self.probabilities.update(struct.pack('<H',p));return p
    def _update(self,bit):
        self.prefix=self.prefix*2+bit
        if self.prefix>=256:self.native.observe(self.prefix-256);self.prefix=1;self.weights=None
        self.boundaries.update(self.serialize())
    def _export_state(self):return dict(native=self.native.serialize().hex(),prefix=self.prefix,weights=self.weights)
    @classmethod
    def restore(cls,payload,frontend=codec.RAW_MSB):
        raise ValueError('use native component checkpoints; fixture wrapper is test-only')


class NativeRatioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=None
        supplied=os.environ.get('GAMMA_RATIO_TEST_LIBRARY')
        if supplied: cls.library=Path(supplied)
        else:
            cls.tmp=tempfile.TemporaryDirectory(); cls.library=Path(cls.tmp.name)/'ratio.so'
            command=['g++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',
                     '-shared','-fPIC',str(ROOT/'tests/fx2_residual_ratio_native_bridge_v1.cpp'),'-o',str(cls.library)]
            subprocess.run(command,check=True,capture_output=True,timeout=30)
        cls.lib=load_library(cls.library)
    @classmethod
    def tearDownClass(cls):
        if cls.tmp:cls.tmp.cleanup()

    def test_float_mapping_and_invalid_values(self):
        for raw in (bits(1e-6),bits(2**-14),bits(1/205),bits(1),0x35800000,0,0x80000000,0x7f800000,0x7fc00000):
            expected=int(Fraction.from_float(value(raw))*(1<<43)) if bits(1e-6)<=raw<=bits(1) else 0
            self.assertEqual(self.lib.ratio_units(raw),expected)

    def test_exact_reference_outputs_and_complete_states(self):
        rng=random.Random('fx2-residual-ratio-native-v1')
        for n in (3,205):
            for arm in ('P','K','D','S'):
                native=Native(self.lib,n,arm);reference=Reference(n,arm)
                for t in range(520):
                    raw=[rng.randint(bits(1e-6),bits(1)) for _ in range(n)] if t%3 else [bits(1/n)]*n
                    self.assertEqual(native.predict(raw),reference.predict(raw))
                    self.assertEqual(native.serialize(),reference.serialize())
                    if t in (0,255,256,511):
                        copy=Native(self.lib,n,arm);copy.restore(native.serialize())
                        self.assertEqual(copy.serialize(),reference.serialize());copy.close()
                    symbol=rng.randrange(n);native.observe(symbol);reference.observe(symbol)
                    self.assertEqual(native.serialize(),reference.serialize())
                native.close()

    def test_invalid_transitions_and_checkpoints_are_atomic(self):
        m=Native(self.lib,3,'D');before=m.serialize()
        with self.assertRaises(ValueError):m.observe(0)
        with self.assertRaises(ValueError):m.predict([0,bits(1),bits(1)])
        self.assertEqual(m.serialize(),before)
        m.predict([bits(1/3)]*3);before=m.serialize()
        with self.assertRaises(ValueError):m.predict([bits(1/3)]*3)
        with self.assertRaises(ValueError):m.observe(3)
        for bad in (before[:-1],before+b'\0',b'BAD!'+before[4:],before[:7]+b'\x02'+before[8:],
                    before[:6]+b'S'+before[7:],Reference(2,'D').serialize()):
            with self.assertRaises(ValueError):m.restore(bad)
            self.assertEqual(m.serialize(),before)
        m.close()

    def test_native_fixture_inverse_repeat_and_bookkeeping_identity(self):
        for raw in (b'',b'A'*300,bytes(range(256))):
            arcs={}
            for arm in ('P','K','D','S'):
                enc,dec,rep=(NativeFixture(self.lib,arm) for _ in range(3))
                arcs[arm]=codec.encode(raw,enc)
                self.assertEqual(codec.decode(arcs[arm],dec),raw)
                self.assertEqual(codec.encode(raw,rep),arcs[arm])
                self.assertEqual(enc.serialize(),dec.serialize());self.assertEqual(enc.serialize(),rep.serialize())
                self.assertEqual(enc.probabilities.digest(),dec.probabilities.digest());self.assertEqual(enc.probabilities.digest(),rep.probabilities.digest())
                self.assertEqual(enc.boundaries.digest(),dec.boundaries.digest());self.assertEqual(enc.boundaries.digest(),rep.boundaries.digest())
                for obj in (enc,dec,rep):obj.native.close()
            self.assertEqual(arcs['P'],arcs['K'])


if __name__=='__main__':unittest.main()
