"""Fixture tests for the exact supplied-parent final-counts comparison."""
import os
import hashlib
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fx2_final_counts_replay_v1 import replay,project,Encoder


class Tests(unittest.TestCase):
    def setUp(self):
        self.raw=b'abcd abcd '*20
        self.modeled=b'\x07'+self.raw
        self.q16=struct.pack('<H',32768)*(8*len(self.modeled))
        self.prefix=b'GFV1\x07'+len(self.raw).to_bytes(4,'big')+((1<<39)+len(self.modeled)).to_bytes(5,'big')+b'\xff'*32
        self.library=Path(os.environ['FX2_FINAL_COUNTS_LIBRARY'])
        self.raw_sha=hashlib.sha256(self.raw).hexdigest()

    def run_arm(self,arm):
        a,raw,modeled,r=replay('encode',self.modeled,self.q16,self.prefix,[],arm,self.library,self.raw_sha)
        b,restored,decoded,s=replay('decode',a,self.q16,self.prefix,[],arm,self.library,self.raw_sha)
        c,_,_,t=replay('repeat',decoded,self.q16,self.prefix,[],arm,self.library,self.raw_sha)
        self.assertEqual(a,b);self.assertEqual(a,c);self.assertEqual(raw,self.raw);self.assertEqual(raw,restored)
        self.assertEqual(modeled,decoded);self.assertEqual(r,s);self.assertEqual(r,t)
        return a,r

    def test_all_arm_inverse_repeat_and_complete_state_agreement(self):
        results={arm:self.run_arm(arm) for arm in 'PKDS'}
        self.assertEqual(results['P'][0],results['K'][0])
        self.assertEqual(results['P'][1]['probability_sha256'],results['K'][1]['probability_sha256'])
        self.assertEqual(results['K'][1]['model_state_sha256'],results['D'][1]['model_state_sha256'])

    def test_projection_matches_exact_native_intervals(self):
        e=Encoder(max_bits=8*len(self.modeled));trace=bytearray()
        for value in self.modeled:
            for shift in range(7,-1,-1):
                y=(value>>shift)&1;lo,hi=e.low,e.high;e.encode(y,32768)
                trace.extend(struct.pack('<7I',0x3f000000,32768,lo,hi,e.low,e.high,y))
        archive=self.prefix+e.finish()
        self.assertEqual(project(trace,self.modeled,archive),self.q16)
        for offset in (4,8,16,24):
            broken=bytearray(trace);broken[offset]^=1
            with self.assertRaises(ValueError):project(broken,self.modeled,archive)
        with self.assertRaises(ValueError):project(trace[:-1],self.modeled,archive)

    def test_corrupt_payload_and_probability_rejected(self):
        a,_=self.run_arm('D')
        for bad in (a[:-1],a+b'\0',a[:46]+bytes([a[46]^128])+a[47:]):
            with self.assertRaises(ValueError):replay('decode',bad,self.q16,self.prefix,[],'D',self.library,self.raw_sha)
        for q in (self.q16[:-1],b'\0\0'+self.q16[2:]):
            with self.assertRaises(ValueError):replay('encode',self.modeled,q,self.prefix,[],'D',self.library,self.raw_sha)

    def test_framing_and_modeled_limits_rejected(self):
        for prefix in (self.prefix[:-1],b'X'+self.prefix[1:],self.prefix[:9]+b'\0'*5+self.prefix[14:]):
            with self.assertRaises(ValueError):replay('encode',self.modeled,self.q16,prefix,[],'D',self.library,self.raw_sha)
        with self.assertRaises(ValueError):replay('encode',self.modeled[:-1],self.q16,self.prefix,[],'D',self.library,self.raw_sha)


if __name__=='__main__':unittest.main()
