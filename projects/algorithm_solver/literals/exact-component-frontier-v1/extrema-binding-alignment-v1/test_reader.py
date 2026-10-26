"""Public synthetic controls for linked linear-time metadata reader."""
import pathlib,tempfile,unittest
from verify_probe_v2 import read
class ReaderTests(unittest.TestCase):
 def test_regular_chunks(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'x';raw=b'public synthetic bytes\n'*50000;p.write_bytes(raw);self.assertEqual(read(p,len(raw)),raw)
 def test_size_cap(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'x';p.write_bytes(b'1234')
   with self.assertRaises(ValueError):read(p,3)
 def test_symlink(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'x';p.write_bytes(b'ok');q=pathlib.Path(d)/'link';q.symlink_to(p)
   with self.assertRaises(OSError):read(q)
 def test_directory(self):
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaises(ValueError):read(d)
if __name__=='__main__':unittest.main()
