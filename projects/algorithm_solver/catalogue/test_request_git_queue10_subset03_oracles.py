"""Independent source-free controls; historical support loaded by caller."""
import random,unittest
from itertools import product
from . import request_git_queue10_subset03_oracles as o
q=o.q
class Queue10Subset03Tests(unittest.TestCase):
 def test_public_examples(self):
  for pid,args,want in [(3201,[[1,2,3,4]],4),(3201,[[1,2,1,1,2,1,2]],6),(3201,[[1,3]],2),(3202,[[1,2,3,4,5],2],5),(3202,[[1,4,2,3,1,4],3],4),(3207,[[3,2,2],2],3),(3207,[[2],10],5),(3212,[[['X','Y','.'],['Y','.','.']]],3),(3212,[[['X','X'],['X','Y']]],0),(3212,[[['.','.'],['.','.']]],0)]:self.assertEqual(o.expected(pid,args),want)
 def test_parity_subsets_against_counts_and_runs(self):
  for n in range(2,10):
   for a in product((1,2),repeat=n):
    even=sum(v%2==0 for v in a);runs=1+sum(a[i]%2!=a[i-1]%2 for i in range(1,n));self.assertEqual(o.expected(3201,[list(a)]),max(even,n-even,runs))
 @staticmethod
 def residues(a,k):
  best=0
  for target in range(k):
   dp=[0]*k
   for v in a:
    r=v%k;dp[r]=max(dp[r],1+dp[(target-r)%k]);best=max(best,dp[r])
  return best
 def test_modular_subsets_against_target_residue_dp(self):
  rng=random.Random(320210)
  for _ in range(250):
   a=rng.choices((1,2,3,7,10000000),k=rng.randrange(2,13));k=rng.choice((1,2,3,7,20));self.assertEqual(o.expected(3202,[a,k]),self.residues(a,k))
  for a,k,want in [([10000000]*1000,1000,1000),(list(range(1,1001)),1,1000),([1,999]*500,1000,1000),([1]*500+[999]*500,1000,500),([1,2]*500,1000,1000),(list(range(1,1001)),1000,2)]:self.assertEqual(self.residues(a,k),want)
 def test_enemy_states_against_conservation_construction(self):
  for n in range(1,5):
   for a in product((1,2,4),repeat=n):
    for energy in range(6):
     want=0 if energy<min(a) else (energy+sum(a)-min(a))//min(a);self.assertEqual(o.expected(3207,[list(a),energy]),want)
  self.assertEqual(o.expected(3207,[[1],15]),15)
  self.assertEqual(o.expected(3207,[[2,5],2]),3)
  self.assertEqual(o.expected(3207,[[3,6],2]),0)
 def test_grid_literals_against_two_prefix_counts(self):
  rng=random.Random(321210)
  for _ in range(300):
   rows=rng.randrange(1,6);cols=rng.randrange(1,6);g=[[rng.choice('XY.') for _ in range(cols)] for _ in range(rows)];prefix={c:[[0]*(cols+1) for _ in range(rows+1)] for c in 'XY'}
   for r in range(rows):
    for col in range(cols):
     for c in 'XY':prefix[c][r+1][col+1]=prefix[c][r][col+1]+prefix[c][r+1][col]-prefix[c][r][col]+(g[r][col]==c)
   want=sum(prefix['X'][r][c]>0 and prefix['X'][r][c]==prefix['Y'][r][c] for r in range(1,rows+1) for c in range(1,cols+1));self.assertEqual(o.expected(3212,[g]),want)
 def test_checkerboard_and_origin_requirement(self):
  for rows in range(1,6):
   for cols in range(1,6):
    g=[['X' if (r+c)%2==0 else 'Y' for c in range(cols)] for r in range(rows)];self.assertEqual(o.expected(3212,[g]),rows*cols-((rows+1)//2)*((cols+1)//2))
  self.assertEqual(o.expected(3212,[[['.','X'],['.','Y']]]),1)
  self.assertEqual(o.expected(3212,[[['Y','X']]]),1)
 def test_strict_domains(self):
  bad=[(3201,[[1]]),(3201,[[0,1]]),(3201,[[True,2]]),(3202,[[1,2],0]),(3202,[[1,2],1001]),(3202,[[1.0,2],2]),(3207,[[],0]),(3207,[[0],0]),(3207,[[1],-1]),(3207,[[1],True]),(3212,[[['x']]]),(3212,[[['X','Y'],['X']]]),(3212,[[['XX']]]),(3212,[[[False]]])]
  for pid,args in bad:
   with self.assertRaises(ValueError):o.validate(pid,args)
 def test_reference_budgets_not_domains(self):
  for pid,args in [(3201,[[1]*200000]),(3202,[[1]*1000,1000]),(3207,[[10**9]*100000,10**9]),(3212,[[['X']*1000 for _ in range(1000)]])]:
   o.validate(pid,args)
   with self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,args)
 def test_transport_omissions_and_numeric_envelope(self):
  for pid,args in [(3201,[[10**7]*200000]),(3207,[[10**9]*100000,10**9]),(3212,[[['.']*1000 for _ in range(1000)]])]:
   o.validate(pid,args);self.assertGreater(len(q.encoded(q.packet([dict(args=args,expected=0,compare='return')]))),q.MAX_PACKET)
  self.assertLess(10**14,2**53)
 def test_host_expected_and_statement_pins(self):
  c=dict(args=[[1,2]],expected=2,compare='return');self.assertEqual(q.packet([c])['calls'],[dict(args=c['args'])])
  for pid in o.IDS:
   with self.assertRaisesRegex(ValueError,'pinned'):o.public_examples(pid,b'wrong snapshot')
  with self.assertRaises(ValueError):o.expected_observation_bytes([c],'bad')
if __name__=='__main__':unittest.main()
