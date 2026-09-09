"""Synthetic integer oracle, causal ordering, full-state and checkpoint checks."""
import ctypes
from fractions import Fraction
import os
import random
import struct
import unittest

Q=65536
SIZE=4612


class Reference:
    def __init__(self,arm):
        self.arm=arm;self.prefix=1;self.position=0;self.parent=0
        self.rows=[[0]*5 for _ in range(255)]

    def predict(self,p):
        o1,e1,o0,e0,_=self.rows[self.prefix-1]
        s1=max(Q//4,min(4*Q,(32*Q+o1)*Q//(32*Q+e1)))
        s0=max(Q//4,min(4*Q,(32*Q+o0)*Q//(32*Q+e0)))
        self.parent=p
        return p if self.arm in 'PK' else max(1,min(Q-1,round(Fraction(Q*p*s1,p*s1+(Q-p)*s0))))

    def observe(self,y):
        if self.arm!='P':
            c=self.rows[self.prefix-1];label=1-y if self.arm=='S' else y
            c[0]+=Q*label;c[1]+=self.parent;c[2]+=Q*(1-label);c[3]+=Q-self.parent;c[4]+=1
            if c[4]==256:c[:]=[v//2 for v in c[:4]]+[0]
        self.prefix=self.prefix*2+y
        if self.prefix>=256:self.prefix=1
        self.position+=1;self.parent=0

    def state(self):
        return (b'GFC1'+struct.pack('<cBBBQHI',self.arm.encode(),1,bool(self.parent),0,
                                  self.position,self.prefix,self.parent)
                +b''.join(struct.pack('<IIIIH',*c) for c in self.rows))


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib=ctypes.CDLL(os.environ['FX2_FINAL_COUNTS_LIBRARY'])
        signatures={'model_new':([ctypes.c_char],ctypes.c_void_p),
                    'model_delete':([ctypes.c_void_p],None),
                    'model_predict':([ctypes.c_void_p,ctypes.c_uint],ctypes.c_int),
                    'model_observe':([ctypes.c_void_p,ctypes.c_uint],ctypes.c_int),
                    'model_state':([ctypes.c_void_p,ctypes.c_void_p],ctypes.c_uint),
                    'model_restore':([ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint],ctypes.c_int)}
        for name,(args,result) in signatures.items():
            f=getattr(cls.lib,name);f.argtypes=args;f.restype=result

    def new(self,arm):
        m=self.lib.model_new(arm.encode());self.assertTrue(m);self.addCleanup(self.lib.model_delete,m);return m

    def state(self,m):
        out=ctypes.create_string_buffer(SIZE);self.assertEqual(self.lib.model_state(m,out),SIZE);return out.raw

    def test_seeded_exact_rational_oracle_and_every_state(self):
        rng=random.Random('fx2_final_residual_counts_v1')
        events=[(rng.randrange(1,Q),rng.randrange(2)) for _ in range(5000)]
        for arm in 'PKDS':
            m=self.new(arm);r=Reference(arm)
            for p,y in events:
                self.assertEqual(self.lib.model_predict(m,p),r.predict(p));self.assertEqual(self.state(m),r.state())
                self.assertEqual(self.lib.model_observe(m,y),1);r.observe(y);self.assertEqual(self.state(m),r.state())

    def test_bookkeeping_and_treatment_learn_identical_state(self):
        k,d=self.new('K'),self.new('D')
        for i in range(2200):
            self.assertEqual(self.lib.model_predict(k,10000),10000);self.lib.model_predict(d,10000)
            self.assertEqual(self.state(k)[:4]+self.state(k)[5:],self.state(d)[:4]+self.state(d)[5:])
            self.lib.model_observe(k,i%2);self.lib.model_observe(d,i%2)

    def test_pending_checkpoint_and_independent_replay(self):
        a,b=self.new('D'),self.new('D')
        for i in range(4097):
            self.lib.model_predict(a,1 if i%2 else 65535)
            snapshot=self.state(a);self.assertEqual(self.lib.model_restore(b,snapshot,len(snapshot)),1)
            self.lib.model_observe(a,i%2);self.lib.model_observe(b,i%2)
            self.assertEqual(self.state(a),self.state(b))

    def test_invalid_calls_and_checkpoints_are_transactional(self):
        m=self.new('D');before=self.state(m)
        for p in (0,Q):self.assertEqual(self.lib.model_predict(m,p),-1);self.assertEqual(self.state(m),before)
        self.assertEqual(self.lib.model_observe(m,0),0)
        self.lib.model_predict(m,123);pending=self.state(m)
        self.assertEqual(self.lib.model_predict(m,123),-1);self.assertEqual(self.lib.model_observe(m,2),0)
        self.assertEqual(self.state(m),pending)
        for offset,value in ((0,0),(4,ord('S')),(5,0),(6,2),(7,1),(16,0),(18,0),(39,255)):
            bad=bytearray(pending);bad[offset]=value
            self.assertEqual(self.lib.model_restore(m,bytes(bad),len(bad)),0)
            self.assertEqual(self.state(m),pending)
        self.assertEqual(self.lib.model_restore(m,pending[:-1],len(pending)-1),0)

    def test_repeated_residual_has_expected_direction_and_decay(self):
        d,s=self.new('D'),self.new('S');r=Reference('D')
        for _ in range(8192):
            q=self.lib.model_predict(d,32768);self.lib.model_predict(s,32768);r.predict(32768)
            self.lib.model_observe(d,1);self.lib.model_observe(s,1);r.observe(1)
        self.assertEqual(self.state(d),r.state())
        self.assertGreater(self.lib.model_predict(d,32768),32768)
        self.assertLess(self.lib.model_predict(s,32768),32768)


if __name__=='__main__':unittest.main()
