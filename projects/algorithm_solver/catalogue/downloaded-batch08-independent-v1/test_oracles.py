import unittest,random,math
from itertools import product,combinations
from functools import lru_cache
import oracles as o

class ReferenceChecks(unittest.TestCase):
 def test_negative_radix_signed_identity(self):
  for n in range(-2000,2001):
   digits=o.negative_digits(n);self.assertTrue(set(digits)<={'0','1'});self.assertTrue(digits=='0'or digits[0]=='1');self.assertEqual(sum(int(v)*(-2)**i for i,v in enumerate(digits[::-1])),n)
 def test_clumsy_grouping_closed_residues(self):
  for n in range(1,501):
   want={1:1,2:2,3:6,4:7}.get(n,n+1 if n%4==0 else n+2 if n%4 in(1,2)else n-1)
   self.assertEqual(o.expected(1006,[n]),want)
 def test_multiplicative_order_against_full_repunits(self):
  for k in range(1,151):
   value=0;answer=-1
   for length in range(1,k+1):
    value=value*10+1
    if value%k==0:answer=length;break
   self.assertEqual(o.expected(1015,[k]),answer)
 def test_endpoint_state_graph_minimum_and_maximum(self):
  @lru_cache(None)
  def solve(state):
   a,b,c=state
   if c-a==2:return(0,0)
   states={tuple(sorted((*remaining,p)))for remaining in((b,c),(a,b))for p in range(a+1,c)if p!=b}
   values=[solve(v)for v in states];return(1+min(v[0]for v in values),1+max(v[1]for v in values))
  for state in combinations(range(1,10),3):self.assertEqual(o.expected(1033,list(state)),list(solve(state)))
 def test_signed_partition_against_actual_stone_smashes(self):
  @lru_cache(None)
  def smash(values):
   if len(values)<=1:return sum(values)
   return min(smash(tuple(sorted([v for k,v in enumerate(values)if k not in(i,j)]+([abs(a-b)]if a!=b else[]))))for i,a in enumerate(values)for j,b in enumerate(values)if i<j)
  for stones in product(range(1,4),repeat=5):self.assertEqual(o.expected(1049,[list(stones)]),smash(tuple(sorted(stones))))
 def test_lexical_subsequence_against_all_subsets(self):
  for size in range(1,8):
   for values in product('ab',repeat=size):
    s=''.join(values);want=min(''.join(s[i]for i in range(size)if mask>>i&1)for mask in range(1<<size)if len({s[i]for i in range(size)if mask>>i&1})==len(set(s))and mask.bit_count()==len(set(s)))
    self.assertEqual(o.expected(1081,[s]),want)
 def test_weighted_stats_against_expanded_samples(self):
  for small in product(range(4),repeat=4):
   if not sum(small)or small.count(max(small))!=1:continue
   count=list(small)+[0]*252;values=[i for i,n in enumerate(small)for _ in range(n)];n=len(values);want=[min(values),max(values),sum(values)/n,(values[(n-1)//2]+values[n//2])/2,small.index(max(small))]
   self.assertTrue(o.matches(1093,[count],o.expected(1093,[count]),want))
 def test_zigzag_paths_against_explicit_tree(self):
  labels={1:1};parents={1:0}
  for depth in range(1,7):
   row=list(range(2**depth,2**(depth+1)))
   if depth%2:row.reverse()
   for index,label in enumerate(row):labels[2**depth+index]=label;parents[label]=labels[(2**depth+index)//2]
  for label in parents:
   path=[];x=label
   while x:path.append(x);x=parents[x]
   self.assertEqual(o.expected(1104,[label]),path[::-1])
 def test_parenthesis_bound_against_all_assignments(self):
  for n in range(2,9,2):
   for chars in product('()',repeat=n):
    s=''.join(chars)
    if o.vps(s)is None:continue
    best=n
    for mask in range(1<<n):
     levels=[o.vps(''.join(c for i,c in enumerate(s)if((mask>>i)&1)==v))for v in(0,1)]
     if None not in levels:best=min(best,max(levels))
    self.assertEqual(o.expected(1111,[s]),best)
 def test_types_effects_freedom_and_domain_negatives(self):
  self.assertTrue(o.matches(1030,[2,2,0,0],[[0,0],[1,0],[0,1],[1,1]],[[0,0],[0,1],[1,0],[1,1]]))
  self.assertTrue(o.matches(1042,[3,[[1,2],[2,3]]],[4,3,4],3));self.assertFalse(o.matches(1042,[2,[[1,2]]],[True,2],2));self.assertFalse(o.matches(1042,[2,[[1,2]]],[1,1],2))
  self.assertFalse(o.matches(1093,[],[True,1,1.,1.,1],[0,1,1.,1.,1]));self.assertFalse(o.matches(1111,['()'],[0,1],1))
  args=[[0,1]];record={'result':[0,0],'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]};self.assertEqual(o.compare(1089,args,[0,0],record,'python'),(True,None));record['alias_edges']=[['r','a']];self.assertEqual(o.compare(1089,args,[0,0],record,'python'),(False,'mutable_return_alias'))
  for pid,args in [(1043,[[10**9]*500,500]),(1093,[[1,1]+[0]*254]),(1073,[[0,1],[0]]),(1042,[5,[[1,2],[1,3],[1,4],[1,5]]]),(1111,['())('])]:
   with self.subTest(pid=pid),self.assertRaises(ValueError):o.validate(pid,args)
if __name__=='__main__':unittest.main()
