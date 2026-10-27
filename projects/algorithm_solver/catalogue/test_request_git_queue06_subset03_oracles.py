"""Focused source-free checks with structurally separate small models."""
import heapq,random,unittest
from collections import Counter,deque
from itertools import product
from . import request_git_queue06_subset03_oracles as o
from . import imported_qualification as q

class Queue06Subset03Tests(unittest.TestCase):
 def test_public_example_values(self):
  examples=[(2812,[[[1,0,0],[0,0,0],[0,0,1]]],0),(2812,[[[0,0,1],[0,0,0],[0,0,0]]],2),(2812,[[[0,0,0,1],[0,0,0,0],[0,0,0,0],[1,0,0,0]]],2),(2830,[5,[[0,0,1],[0,2,2],[1,3,2]]],3),(2830,[5,[[0,0,1],[0,2,10],[1,3,2]]],10),(2844,['2245047'],2),(2844,['2908305'],3),(2844,['10'],1),(2857,[[[1,2],[4,2],[1,3],[5,2]],5],2),(2857,[[[1,3]]*5,0],10)]
  for pid,args,want in examples:self.assertEqual(o.expected(pid,args),want)
 def test_safeness_against_multisource_distance_widest_path(self):
  def other(grid):
   n=len(grid);dist={};todo=deque()
   for r in range(n):
    for c in range(n):
     if grid[r][c]:dist[r,c]=0;todo.append((r,c))
   while todo:
    r,c=todo.popleft()
    for u,v in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
     if 0<=u<n and 0<=v<n and (u,v) not in dist:dist[u,v]=dist[r,c]+1;todo.append((u,v))
   todo=[(-dist[0,0],0,0)];seen=set()
   while todo:
    neg,r,c=heapq.heappop(todo)
    if (r,c) in seen:continue
    seen.add((r,c))
    if (r,c)==(n-1,n-1):return -neg
    for u,v in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
     if (u,v) in dist and (u,v) not in seen:heapq.heappush(todo,(-min(-neg,dist[u,v]),u,v))
  for mask in range(1,512):
   grid=[[int(bool(mask>>(r*3+c)&1)) for c in range(3)] for r in range(3)]
   self.assertEqual(o.expected(2812,[grid]),other(grid))
 def test_offer_subsets_against_house_prefix_dp(self):
  rng=random.Random(283006)
  for _ in range(160):
   n=rng.randrange(1,12);offers=[]
   for _ in range(rng.randrange(1,10)):
    a=rng.randrange(n);offers.append([a,rng.randrange(a,n),rng.randrange(1,1001)])
   dp=[0]*(n+1)
   for house in range(n):dp[house+1]=max([dp[house]]+[dp[a]+gold for a,b,gold in offers if b==house])
   self.assertEqual(o.expected(2830,[n,offers]),dp[n])
  self.assertEqual(o.expected(2830,[2,[[0,1,5],[1,1,4],[0,0,4]]]),8)
 def test_decimal_subsequences_against_remainder_length_dp(self):
  def other(s):
   best=[-1000]*25;best[0]=0
   for c in s:
    nxt=best.copy()
    for r,length in enumerate(best):
     if length>=0:nxt[(10*r+int(c))%25]=max(nxt[(10*r+int(c))%25],length+1)
    best=nxt
   return len(s)-best[0]
  for value in range(400):self.assertEqual(o.expected(2844,[str(value)]),other(str(value)))
  rng=random.Random(284406)
  for _ in range(60):
   s=rng.choice('123456789')+''.join(rng.choices('0123456789',k=rng.randrange(1,13)));self.assertEqual(o.expected(2844,[s]),other(s))
  for s,want in [('1'*100,100),('9'*100,100),('1'*99+'0',99),('5'+'1'*98+'0',98),('2'+'1'*98+'5',98),('1'*98+'00',0),('1'*98+'25',0),('1'*98+'50',0),('1'*98+'75',0)]:self.assertEqual(other(s),want)
 def test_xor_pairs_against_grouped_coordinates(self):
  rng=random.Random(285706)
  for _ in range(150):
   coords=[[rng.randrange(8),rng.randrange(8)] for _ in range(rng.randrange(2,50))];k=rng.randrange(20);counts=Counter(map(tuple,coords));want=0
   for (x,y),amount in counts.items():
    for dx in range(k+1):
     other=(x^dx,y^(k-dx))
     if (x,y)==other:want+=amount*(amount-1)
     else:want+=amount*counts.get(other,0)
   self.assertEqual(o.expected(2857,[coords,k]),want//2)
 def test_inclusive_duplicates_and_zero_semantics(self):
  self.assertEqual(o.expected(2812,[[[1]]]),0)
  self.assertEqual(o.expected(2830,[1,[[0,0,2],[0,0,3],[0,0,3]]]),3)
  self.assertEqual(o.expected(2844,['0']),0)
  self.assertEqual(o.expected(2844,['1']),1)
  self.assertEqual(o.expected(2844,['1001']),1)
  self.assertEqual(o.expected(2857,[[[0,0],[1,1]],2]),1)
 def test_reject_invalid_full_domains(self):
  bad=[(2812,[[[0]]]),(2812,[[[True]]]),(2812,[[[1,0],[0]]]),(2812,[[[1.0]]]),(2812,[[[1]*401 for _ in range(401)]]),(2830,[1,[]]),(2830,[1,[[0,1,1]]]),(2830,[2,[[1,0,1]]]),(2830,[True,[[0,0,1]]]),(2830,[1,[[0,0,1001]]]),(2830,[1,[[0,0,True]]]),(2844,['']), (2844,['00']),(2844,['01']),(2844,['０']),(2844,['1'*101]),(2844,[0]),(2857,[[[0,0]],0]),(2857,[[[0,0],[0,0]],True]),(2857,[[[0,0],[1000001,0]],0]),(2857,[[[0,False],[0,0]],0]),(2857,[[[0,0],[0,0]],101]),(2857,[[[0,0,0],[0,0]],0])]
  for pid,args in bad:
   with self.subTest(pid=pid),self.assertRaises(ValueError):o.validate(pid,args)
 def test_domain_and_reference_budget_are_separate(self):
  for pid,args in [(2812,[[[1]*400 for _ in range(400)]]),(2830,[100000,[[0,0,1]]*100000]),(2844,['1'*100]),(2857,[[[1000000,1000000]]*50000,100])]:
   o.validate(pid,args)
   with self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,args)
 def test_packet_limits_are_not_full_domain_limits(self):
  args=[100000,[[99999,99999,1000]]*100000];o.validate(2830,args)
  self.assertGreater(len(q.encoded(q.packet([dict(args=args,expected=1000,compare='return')]))),q.MAX_PACKET)
 def test_host_only_expected_and_pinned_examples(self):
  c=dict(args=['10'],expected=1,compare='return');self.assertEqual(q.packet([c])['calls'],[dict(args=['10'])])
  for pid in o.IDS:
   with self.assertRaisesRegex(ValueError,'pinned'):o.public_examples(pid,b'not the official snapshot')
  with self.assertRaises(ValueError):o.expected_observation_bytes([c],'unknown')

if __name__=='__main__':unittest.main()
