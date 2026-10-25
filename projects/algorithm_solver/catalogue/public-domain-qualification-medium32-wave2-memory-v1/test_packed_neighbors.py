"""Host algebra controls only; never import or execute candidate JavaScript."""
import itertools,unittest
BASE=2**32
MASK=BASE-1
def signed(x):
 x&=MASK
 return x-BASE if x>=2**31 else x
class PackedAlgebra(unittest.TestCase):
 def test_endpoint_zero_negative_and_extremes(self):
  for neighbor in(-100000,-65536,-1,0,1,65536,100000):
   stored=neighbor&MASK
   self.assertLess(stored,BASE);self.assertEqual(signed(stored),neighbor)
   self.assertEqual(int(float(stored)),stored)
 def test_degree_two_marker_and_bidirectional_xor(self):
  values=list(range(-100,101))+[-100000,-65536,65536,100000]
  for left,right in itertools.permutations(values,2):
   packed=BASE+((left^right)&MASK)
   self.assertGreaterEqual(packed,BASE);self.assertLess(packed,2*BASE)
   self.assertEqual(int(float(packed)),packed)
   self.assertEqual(signed((packed-BASE)^left),right)
   self.assertEqual(signed((packed-BASE)^right),left)
 def test_edge_input_order_commutes(self):
  for left,right in itertools.permutations((-100000,-1,0,1,100000),2):
   first=left&MASK;second=right&MASK
   self.assertEqual(BASE+((first^right)&MASK),BASE+((second^left)&MASK))
 def test_zero_is_not_missing(self):
  stored=0
  self.assertIsNotNone(stored);self.assertEqual(signed(stored),0)
  self.assertGreaterEqual(BASE+((stored^-100000)&MASK),BASE)
if __name__=='__main__':unittest.main()
