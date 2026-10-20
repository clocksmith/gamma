import random,struct,unittest
from bitpack import encode,decode,dictionary_bytes
class PacketTests(unittest.TestCase):
 def test_all_widths_lengths_and_extreme_ids(self):
  rng=random.Random(128)
  for bits in range(4,9):
   literals=[chr(0x400+i) for i in range(1<<bits)];dictionary=dictionary_bytes(literals)
   for size in range(130):
    sequence=[rng.randrange(len(literals)) for _ in range(size)]
    if size:sequence[-1]=len(literals)-1
    packet=encode(literals,sequence,bits)
    self.assertEqual(len(packet),41+(bits*size+7)//8)
    self.assertEqual(decode(dictionary,packet),''.join(literals[i] for i in sequence))
 def test_bad_framing_dictionary_id_and_padding(self):
  for bits in range(4,9):
   literals=['a','bc'];d=dictionary_bytes(literals);p=encode(literals,[1],bits)
   for bad in [p[:-1],p+b'\0',b'BAD!'+p[4:],p[:4]+b'\x03'+p[5:]]:
    with self.assertRaises(ValueError):decode(d,bad)
   with self.assertRaises(ValueError):decode(dictionary_bytes(['a','bd']),p)
   bad=p[:-1]+bytes([2<<(8-bits)])
   with self.assertRaises(ValueError):decode(d,bad)
   if bits<8:
    with self.assertRaises(ValueError):decode(d,p[:-1]+bytes([p[-1]|1]))
 def test_width_overflow_and_boolean_ids(self):
  for bits in range(4,9):
   with self.assertRaises(ValueError):encode([str(i) for i in range((1<<bits)+1)],[0],bits)
   with self.assertRaises(ValueError):encode(['x'],[True],bits)
if __name__=='__main__':unittest.main()
