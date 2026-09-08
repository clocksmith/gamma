import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.wrt_support_v1 import WrtSupport


def feed(state,data):
    forced=0
    for byte in data:
        for shift in range(7,-1,-1):
            bit=(byte>>shift)&1
            prediction=state.forced()
            if prediction is not None:
                assert prediction==bit
                forced+=1
            state.observe(bit)
    return forced


class SupportTests(unittest.TestCase):
    def test_all_dictionary_code_shapes(self):
        s=WrtSupport();feed(s,b'\x07');counts=[0,0,0]
        for index in range(44880):
            if index<80:code=bytes([128+index])
            elif index<3920:
                v=index-80;code=bytes([208+v//80,128+v%80])
            else:
                v=index-3920;code=bytes([240+v//2560,208+(v//80)%32,128+v%80])
            counts[len(code)-1]+=1
            feed(s,code);s.finish()
        self.assertEqual(counts,[80,3840,40960])

    def test_escape_and_disabled_do_not_constrain_literal(self):
        for byte in range(256):
            s=WrtSupport();feed(s,b'\x07\x0c')
            self.assertEqual(feed(s,bytes([byte])),0);s.finish()
        s=WrtSupport();feed(s,b'\0')
        self.assertEqual(feed(s,bytes(range(256))),0);s.finish()

    def test_short_long_and_third_support(self):
        for lead,low,high in [(b'\xd0',128,207),(b'\xf0',128,239),(b'\xff\xef',128,207)]:
            for byte in range(256):
                s=WrtSupport();feed(s,b'\x07'+lead)
                if low<=byte<=high:feed(s,bytes([byte]))
                else:
                    with self.assertRaises((ValueError,AssertionError)):feed(s,bytes([byte]))

    def test_prediction_is_pretruth_and_nonmutating(self):
        s=WrtSupport();feed(s,b'\x07\xd0');digest=s.state_digest()
        self.assertEqual(s.forced(),1);self.assertEqual(s.forced(),1)
        self.assertEqual(digest,s.state_digest())
        for bad in (False,2,-1,None):
            with self.assertRaises(ValueError):s.observe(bad)
            self.assertEqual(digest,s.state_digest())
        with self.assertRaises(ValueError):s.observe(0)
        self.assertEqual(digest,s.state_digest())

    def test_truncation(self):
        for data in (b'',b'\x07\x0c',b'\x07\xd0',b'\x07\xff',b'\x07\xff\xef'):
            s=WrtSupport();feed(s,data)
            with self.assertRaises(ValueError):s.finish()
        s=WrtSupport();feed(s,b'\x07');s.observe(1)
        with self.assertRaises(ValueError):s.finish()


if __name__=='__main__':unittest.main()
