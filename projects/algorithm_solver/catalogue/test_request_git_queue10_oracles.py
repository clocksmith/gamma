"""Source-free checks; no candidate engine, loader, wrappers, or source files."""
import random,unittest
from collections import Counter
from itertools import product
from math import comb
from . import request_git_queue10_oracles as o
q=o.q

class Queue10Tests(unittest.TestCase):
 def test_public_values(self):
  for pid,args,answer in [(3164,[[1,3,4],[1,3,4],1],5),(3164,[[1,2,4,12],[2,4],3],2),(3169,[10,[[5,7],[1,3],[9,10]]],2),(3169,[5,[[2,4],[1,3]]],1),(3169,[6,[[1,6]]],0),(3170,['aaba*'],'aab'),(3170,['abc'],'abc'),(3175,[[4,2,6,3,9],2],2),(3175,[[2,5,4],3],1),(3179,[4,5],56),(3179,[5,3],35),(3180,[[1,1,3,3]],4),(3180,[[1,6,4,3,2]],11),(3181,[[1,1,3,3]],4),(3181,[[1,6,4,3,2]],11)]:self.assertEqual(o.expected(pid,args),answer)
 def test_pair_counts_against_multiplicity_groups(self):
  rng=random.Random(316410)
  for _ in range(200):
   a=rng.choices(range(1,41),k=rng.randrange(1,20));b=rng.choices(range(1,11),k=rng.randrange(1,20));k=rng.randrange(1,12);ca,cb=Counter(a),Counter(b)
   want=sum(cx*cy for x,cx in ca.items() for y,cy in cb.items() if x%(y*k)==0)
   self.assertEqual(o.expected(3164,[a,b,k]),want)
 def test_occupied_days_against_endpoint_union(self):
  rng=random.Random(316910)
  for _ in range(200):
   days=rng.randrange(1,101);meetings=[]
   for _ in range(rng.randrange(1,20)):
    start=rng.randrange(1,days+1);meetings.append([start,rng.randrange(start,days+1)])
   end=0;busy=0
   for a,b in sorted(meetings):
    if b>end:busy+=b-max(end+1,a)+1;end=b
   self.assertEqual(o.expected(3169,[days,meetings]),days-busy)
 def test_star_all_choices_against_indexed_rightmost_ties(self):
  def other(s):
   indices=[[] for _ in range(26)];removed=set()
   for i,c in enumerate(s):
    if c!='*':indices[ord(c)-97].append(i)
    else:
     j=next(j for j in range(26) if indices[j]);removed.add(indices[j].pop())
   return ''.join(c for i,c in enumerate(s) if c!='*' and i not in removed)
  for n in range(1,8):
   for t in product('ab*',repeat=n):
    s=''.join(t)
    try:o.validate(3170,[s])
    except ValueError:continue
    self.assertEqual(o.expected(3170,[s]),other(s))
  self.assertEqual(o.expected(3170,['ab*a*']),'b')
 def test_queue_against_champion_scan(self):
  rng=random.Random(317510)
  for _ in range(400):
   skills=rng.sample(range(1,1000001),rng.randrange(2,13));k=rng.randrange(1,51);best=0;wins=0
   for i in range(1,len(skills)):
    if skills[i]>skills[best]:best=i;wins=1
    else:wins+=1
    if wins==k:break
   self.assertEqual(o.expected(3175,[skills,k]),best)
 def test_simultaneous_updates_against_exact_binomial(self):
  for n in range(1,41):
   for k in range(1,41):self.assertEqual(o.expected(3179,[n,k]),comb(n+k-1,k)%o.MOD)
  self.assertNotEqual(o.expected(3179,[4,5]),1)
 def test_reward_index_states_against_sorted_reachable_sums(self):
  rng=random.Random(318010)
  for pid in (3180,3181):
   for _ in range(200):
    values=rng.choices(range(1,50),k=rng.randrange(1,13));reachable={0}
    for value in sorted(values):reachable|={x+value for x in reachable if x<value}
    self.assertEqual(o.expected(pid,[values]),max(reachable))
   self.assertEqual(o.expected(pid,[[2,2,2]]),2)
   self.assertEqual(o.expected(pid,[[1,1,2]]),3)
 def test_large_reward_certificates_independent_bitsets(self):
  for top in (2000,50000):
   for values,want in [([top]*top,top),([1]*top,1),([top-1]*(top//2)+[top]*(top-top//2),2*top-1),(list(range(1,top+1)),2*top-1),([1]*(top-1)+[top],top+1)]:
    bits=1
    for value in sorted(set(values)):bits|=(bits&((1<<value)-1))<<value
    self.assertEqual(bits.bit_length()-1,want)
 def test_invalid_full_domains(self):
  bad=[(3164,[[],[1],1]),(3164,[[1],[0],1]),(3164,[[True],[1],1]),(3164,[[1],[1],1.0]),(3164,[[1],[1],1001]),(3169,[0,[[1,1]]]),(3169,[4,[[3,2]]]),(3169,[4,[[1,5]]]),(3169,[4,[]]),(3169,[4,[[True,2]]]),(3170,['*a']),(3170,['a**']),(3170,['']),(3170,['A*']),(3170,['é*']),(3170,['a'*100001]),(3175,[[1,1],2]),(3175,[[1],2]),(3175,[[1,2],0]),(3175,[[1,False],1]),(3179,[0,1]),(3179,[1,True]),(3179,[1001,1]),(3180,[[]]),(3180,[[2001]]),(3181,[[50001]]),(3181,[[1.0]])]
  for pid,args in bad:
   with self.subTest(pid=pid),self.assertRaises(ValueError):o.validate(pid,args)
 def test_reference_budgets_do_not_change_domain(self):
  for pid,args in [(3164,[[1]*100000,[1]*100000,1]),(3169,[10**9,[[1,1]]]),(3170,['a'*100000]),(3175,[list(range(1,100001)),10**9]),(3179,[1000,1000]),(3180,[[1]*2000]),(3181,[[50000]*50000])]:
   o.validate(pid,args)
   with self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,args)
 def test_maximum_transport_omissions(self):
  for pid,args,answer in [(3164,[[1000000]*100000,[1000000]*100000,1],10**10),(3169,[10**9,[[10**9,10**9]]*100000],10**9-1)]:
   o.validate(pid,args);self.assertGreater(len(q.encoded(q.packet([dict(args=args,expected=answer,compare='return')]))),q.MAX_PACKET)
 def test_host_only_expected_pin_checks_and_safe_numbers(self):
  c=dict(args=[[1],[1],1],expected=1,compare='return');self.assertEqual(q.packet([c])['calls'],[dict(args=c['args'])]);self.assertLess(10**10,2**53)
  for pid in o.IDS:
   with self.assertRaisesRegex(ValueError,'pinned'):o.public_examples(pid,b'wrong definition bytes')
  with self.assertRaises(ValueError):o.expected_observation_bytes([c],'bad')

if __name__=='__main__':unittest.main()
