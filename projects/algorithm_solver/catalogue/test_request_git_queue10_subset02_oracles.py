"""Independent source-free controls for queue10 subset02."""
import random,unittest
from collections import Counter
from itertools import product
from . import request_git_queue10_subset02_oracles as o
q=o.q
class Queue10Subset02Tests(unittest.TestCase):
 def test_examples(self):
  for pid,args,answer in [(3185,[[12,12,30,24,24]],2),(3185,[[72,48,24,3]],3),(3186,[[1,1,3,4]],6),(3186,[[7,1,6,6]],13),(3191,[[0,1,1,1,0,0]],3),(3191,[[0,1,1,1]],-1),(3195,[[[0,1,0],[1,0,1]]],6),(3195,[[[1,0],[0,0]]],1),(3196,[[1,-2,3,4]],10),(3196,[[1,-1,1,-1]],4),(3196,[[0]],0),(3196,[[1,-1]],2)]:self.assertEqual(o.expected(pid,args),answer)
 def test_pairs_against_remainder_groups(self):
  rng=random.Random(318510)
  for _ in range(200):
   a=rng.choices(range(1,101),k=rng.randrange(1,61));c=Counter(x%24 for x in a);want=sum(c[r]*c[24-r] for r in range(1,12))+c[0]*(c[0]-1)//2+c[12]*(c[12]-1)//2;self.assertEqual(o.expected(3185,[a]),want)
 def test_spell_subsets_against_weighted_value_intervals(self):
  rng=random.Random(318610)
  for _ in range(150):
   a=rng.choices(range(1,25),k=rng.randrange(1,13));counts=Counter(a);values=sorted(counts);dp=[0]
   for i,v in enumerate(values):
    j=0
    while j<i and values[j]<v-2:j+=1
    dp.append(max(dp[-1],v*counts[v]+dp[j]))
   self.assertEqual(o.expected(3186,[a]),dp[-1])
 def test_flip_bfs_against_unique_triangular_parity_solution(self):
  for n in range(3,11):
   for values in product((0,1),repeat=n):
    a=list(values);count=0
    for i in range(n-2):
     if a[i]==0:
      count+=1
      for j in range(i,i+3):a[j]^=1
    want=count if a[-2:]==[1,1] else -1;self.assertEqual(o.expected(3191,[list(values)]),want)
 def test_rectangles_against_extreme_occupied_coordinates(self):
  rng=random.Random(319510)
  for _ in range(200):
   rows=rng.randrange(1,6);cols=rng.randrange(1,6);a=[[rng.randrange(2) for _ in range(cols)] for _ in range(rows)];a[0][0]=1;coords=[(r,c) for r in range(rows) for c in range(cols) if a[r][c]];want=(max(r for r,c in coords)-min(r for r,c in coords)+1)*(max(c for r,c in coords)-min(c for r,c in coords)+1);self.assertEqual(o.expected(3195,[a]),want)
 def test_cut_masks_against_all_last_partition_dp(self):
  rng=random.Random(319610)
  for _ in range(200):
   a=rng.choices((-10**9,-7,-1,0,1,7,10**9),k=rng.randrange(1,15));dp=[0]
   for end in range(1,len(a)+1):dp.append(max(dp[start]+sum(a[i]*(-1)**(i-start) for i in range(start,end)) for start in range(end)))
   self.assertEqual(o.expected(3196,[a]),dp[-1])
 def test_large_signed_partition_certificates(self):
  for a,want in [([0]*100000,0),([1]*100000,100000),([-1]*100000,0),([-1]*99999,-1),([999999999]*100000,99999999900000),([10**9,-10**9]*45000,90000000000000),([-10**9,10**9]*45000,89998000000000)]:
   plus=a[0];minus=-10**30
   for v in a[1:]:plus,minus=max(plus,minus)+v,plus-v
   self.assertEqual(max(plus,minus),want)
 def test_domains_strict_and_reference_separate(self):
  bad=[(3185,[[0]]),(3185,[[1.0]]),(3185,[[True]]),(3186,[[]]),(3186,[[10**9+1]]),(3191,[[0,1]]),(3191,[[0,1,2]]),(3191,[[0,1,False]]),(3195,[[[0]]]),(3195,[[[1,0],[1]]]),(3195,[[[1.0]]]),(3196,[[]]),(3196,[[-10**9-1]]),(3196,[[False]])]
  for pid,args in bad:
   with self.assertRaises(ValueError):o.validate(pid,args)
  for pid,args in [(3185,[[1]*500000]),(3186,[[1]*100000]),(3191,[[1]*100000]),(3195,[[[1]*1000 for _ in range(1000)]]),(3196,[[0]*100000])]:
   o.validate(pid,args)
   with self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,args)
 def test_transport_and_safe_integer_boundaries(self):
  for pid,args in [(3185,[[12]*500000]),(3186,[[10**9]*100000]),(3195,[[[1]*1000 for _ in range(1000)]]),(3196,[[-10**9]*100000])]:
   o.validate(pid,args);self.assertGreater(len(q.encoded(q.packet([dict(args=args,expected=0,compare='return')]))),q.MAX_PACKET)
  self.assertLess(10**14,2**53);self.assertGreater(500000*499999//2,2**31)
 def test_host_expected_and_pinned_definition(self):
  c=dict(args=[[1]],expected=0,compare='return');self.assertEqual(q.packet([c])['calls'],[dict(args=c['args'])])
  for pid in o.IDS:
   with self.assertRaisesRegex(ValueError,'pinned'):o.public_examples(pid,b'wrong body')
  with self.assertRaises(ValueError):o.expected_observation_bytes([c],'invalid')
if __name__=='__main__':unittest.main()
