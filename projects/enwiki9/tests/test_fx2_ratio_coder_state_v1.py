"""Native delivery state versus the independent ratio and integer references."""
import ctypes
from fractions import Fraction
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]))
sys.path.insert(0,str(ROOT/'tools'))
from test_fx2_residual_ratio_native_v1 import Reference, bits, value
from test_fx2_ratio_coder_delivery_v1 import reference, UNIT
from fx2_ratio_coder_native_adapter_v1 import build_adapter


class StateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib=ctypes.CDLL(os.environ['FX2_STATE_LIBRARY'])
        for name,(args,result) in {
            'state_new':([ctypes.c_uint,ctypes.c_char,ctypes.POINTER(ctypes.c_int)],ctypes.c_void_p),
            'state_delete':([ctypes.c_void_p],None),
            'state_predict':([ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)],ctypes.c_int),
            'state_observe':([ctypes.c_void_p,ctypes.c_uint],ctypes.c_int),
            'state_correct':([ctypes.c_void_p,ctypes.c_uint,ctypes.c_uint],ctypes.c_int),
            'state_save':([ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint8)],ctypes.c_uint),
        }.items():
            f=getattr(cls.lib,name);f.argtypes=args;f.restype=result

    def make(self,arm,vocab=None):
        vocab=list(range(205)) if vocab is None else vocab
        p=self.lib.state_new(len(vocab),arm.encode(),(ctypes.c_int*len(vocab))(*vocab))
        if p:self.addCleanup(self.lib.state_delete,p)
        return p

    def save(self,p):
        b=(ctypes.c_uint8*8192)();n=self.lib.state_save(p,b);return bytes(b[:n])

    def predict(self,p,row):
        b=(ctypes.c_uint32*256)(*row)
        before=bytes(b);result=self.lib.state_predict(p,b)
        self.assertEqual(bytes(b),before,'original expert row changed')
        return result

    def test_parent_and_live_bookkeeping_preserve_q16(self):
        p,k,d=[self.make(a) for a in 'PKD'];ref=Reference(205,'D')
        row=[bits(1/205)]*205;base=[int(Fraction.from_float(value(v))*UNIT) for v in row]
        for handle in (p,k,d):self.assertEqual(self.lib.state_correct(handle,12345,1),12345)
        for i in range(257):
            corrected=ref.predict(row);q=[int(Fraction.from_float(value(v))*UNIT) for v in corrected]
            for handle in (p,k,d):self.assertEqual(self.predict(handle,row),1)
            sk,sd=self.save(k),self.save(d)
            self.assertEqual(len(sd),5971)
            self.assertEqual(sk[:6]+b'D'+sk[7:],sd)
            self.assertEqual(sd[10:10+2476],ref.serialize())
            for prefix in (1,2,3,42,127,128,204,255):
                for handle in (p,k):self.assertEqual(self.lib.state_correct(handle,12345,prefix),12345)
                self.assertEqual(self.lib.state_correct(d,12345,prefix),reference(12345,prefix,list(range(205)),base,q))
            symbol=i%3
            for handle in (p,k,d):self.assertEqual(self.lib.state_observe(handle,symbol),1)
            ref.observe(symbol)
            self.assertEqual(self.save(d)[10:10+2476],ref.serialize())

    def test_update_order_and_invalid_rows_preserve_state(self):
        p=self.make('D');initial=self.save(p)
        self.assertEqual(self.lib.state_observe(p,0),0)
        self.assertEqual(self.predict(p,[0]*205),0);self.assertEqual(self.save(p),initial)
        row=[bits(1/205)]*205;self.assertEqual(self.predict(p,row),1);pending=self.save(p)
        self.assertEqual(self.predict(p,row),0);self.assertEqual(self.save(p),pending)
        self.assertEqual(self.lib.state_observe(p,205),0);self.assertEqual(self.save(p),pending)
        self.assertEqual(self.lib.state_observe(p,0),1)
        self.assertEqual(self.lib.state_correct(p,32768,1),-1)

    def test_rotated_control_matches_reference(self):
        p=self.make('S');ref=Reference(205,'S');row=[bits(1/205)]*205
        for _ in range(3):
            ref.predict(row);self.assertEqual(self.predict(p,row),1)
            self.assertEqual(self.save(p)[10:10+2476],ref.serialize())
            self.lib.state_observe(p,204);ref.observe(204)
            self.assertEqual(self.save(p)[10:10+2476],ref.serialize())

    def test_invalid_configuration_rejected(self):
        for arm,v in [('X',[0,1]),('D',[0]),('D',[1,1]),('D',[-1,1]),('D',[0,256])]:
            self.assertFalse(self.make(arm,v))


class AdapterTests(unittest.TestCase):
    def test_both_coders_keep_raw_parent_prediction_and_apply_after_discretization(self):
        adapter=build_adapter()
        for name in ('src/coder/encoder.cpp','src/coder/decoder.cpp'):
            row=next(r for r in adapter['files'] if r['source_path']==name)
            body='\n'.join(r['after'] for r in row['replacements'])
            self.assertEqual(body.count('p_->Predict()'),1)
            self.assertIn('p_->GammaFinalProbability(Discretize(gamma_probability))',body)
            self.assertIn('Record gamma_record(gamma_probability, p,',body)

    def test_original_expert_row_and_shared_state_class_bound(self):
        a=build_adapter();h=next(x for x in a['files'] if x['source_path']=='src/predictor.h')
        self.assertIn('gamma_ratio_delivery::State',str(h['replacements']))
        p=next(x for x in a['files'] if x['source_path']=='src/predictor.cpp')
        self.assertIn('byte_mixer_->SetProbs(probs_scratch_.data())',str(p['replacements']))
        self.assertEqual(len(a['added_files']),4)


if __name__=='__main__':unittest.main()
