import tempfile
from pathlib import Path
import unittest
from tools.fx2_residual_features250k_v2 import copy_or_verify

class Gate:
    def __init__(self):self.buffers={'asset':b'bound model bytes'};self.copies=0
    def copy(self,source,target):
        self.copies+=1
        with target.open('xb') as f:f.write(self.buffers[source])

class MaterializationTests(unittest.TestCase):
    def test_existing_bound_asset_verified_without_copy(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'asset';g=Gate();p.write_bytes(g.buffers['asset'])
            copy_or_verify(g,'asset',p);self.assertEqual(g.copies,0)
    def test_missing_asset_copied_once(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'asset';g=Gate();copy_or_verify(g,'asset',p)
            self.assertEqual(g.copies,1);self.assertEqual(p.read_bytes(),g.buffers['asset'])
    def test_wrong_asset_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'asset';g=Gate();p.write_bytes(b'wrong')
            with self.assertRaises(ValueError):copy_or_verify(g,'asset',p)
            self.assertEqual(p.read_bytes(),b'wrong')
    def test_alias_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'asset';q=Path(d)/'alias';g=Gate();p.write_bytes(g.buffers['asset']);q.symlink_to(p)
            with self.assertRaises(ValueError):copy_or_verify(g,'asset',q)

if __name__=='__main__':unittest.main()
