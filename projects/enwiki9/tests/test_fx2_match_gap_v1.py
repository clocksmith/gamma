import math,random,struct,unittest
from lib.fx2_match_gap_v1 import Controller,perfect_bound,Q
from tools.causal_field_parent_coder_v1 import Encoder,Decoder
import hashlib
class GapTests(unittest.TestCase):
 def test_exact_power_bound(self):
  self.assertEqual(perfect_bound({32768:400}),400)
  self.assertEqual(perfect_bound({1:7}),112)
  self.assertEqual(perfect_bound({}),0)
 def test_bound_against_finite_enumeration(self):
  rng=random.Random(9047)
  for _ in range(80):
   h={rng.randrange(1,Q):rng.randrange(1,7) for i in range(5)}
   f=sum(n*math.log2(Q/c) for c,n in h.items());b=perfect_bound(h)
   self.assertGreaterEqual(b+1e-10,f);self.assertLess(b-f,1+1e-10)
 def test_disabled_exact_identity(self):
  c=Controller()
  for i in range(65535):
   self.assertEqual(c.predict(i+1,i%8,0,0),i+1);c.observe(i%2)
  self.assertEqual(c.total,[0]*8)
 def test_order_rejection(self):
  c=Controller()
  with self.assertRaises(ValueError):c.observe(0)
  c.predict(100,8,1,2)
  with self.assertRaises(ValueError):c.predict(100,8,1,2)
  with self.assertRaises(ValueError):c.state()
  c.observe(1)
  with self.assertRaises(ValueError):c.predict(0,9,1,2)
 def test_failed_prefix_returns_parent(self):
  c=Controller();c.predict(31000,8,0,0);c.observe(1)
  for i in range(1,8):self.assertEqual(c.predict(12345,8+i,0,0),12345);c.observe(0)
  self.assertEqual(c.total,[1,0,0,0,0,0,0,0])
 def test_decoder_reconstructs_learning(self):
  body=bytes([85]*128);enc=Encoder(max_bits=1024,max_payload_bytes=1024);c=Controller();probs=[];states=[]
  for i in range(1024):
   q=c.predict(32768,8+i%8,85,51);probs.append(q);y=(body[i//8]>>(7-i%8))&1;enc.encode(y,q);c.observe(y);states.append(c.state())
  data=enc.finish();self.assertLess(len(data),128)
  dec=Decoder(data,max_bits=1024,max_payload_bytes=1024,expected_payload_bytes=len(data),payload_sha256=hashlib.sha256(data).hexdigest());d=Controller();got=bytearray(128)
  for i in range(1024):
   q=d.predict(32768,8+i%8,85,51);self.assertEqual(q,probs[i]);y=dec.decode(q);got[i//8]=(got[i//8]<<1)|y;d.observe(y);self.assertEqual(d.state(),states[i])
  self.assertEqual(got,body)
if __name__=='__main__':unittest.main()
