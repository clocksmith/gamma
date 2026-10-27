"""Source-free stdlib reference tests, without statement-file or candidate reads."""
from collections import Counter
from itertools import product
import copy,random,unittest
from . import request_git_queue06_subset02_oracles as o
class Subset02Tests(unittest.TestCase):
 def test_examples(self):
  cases=[(2771,[[2,3,1],[1,2,1]],2),(2771,[[1,3,2,1],[2,2,3,4]],4),(2771,[[1,1],[2,2]],2),(2786,[[2,3,6,1,9,2],5],13),(2786,[[2,4,6,8],3],20),(2789,[[2,3,7,9,3]],21),(2789,[[5,3,3]],11),(2791,[[-1,0,0,1,1,2],'acaabc'],8),(2791,[[-1,0,0,0,0],'aaaaa'],10),(2798,[[0,1,2,3,4],2],3),(2798,[[5,1,4,2,2],6],0),(2800,['abc','bca','aaa'],'aaabca'),(2800,['ab','ba','aba'],'aba')]
  for pid,args,want in cases:
   with self.subTest(pid=pid):self.assertEqual(o.expected(pid,args),want)
 def test_selection_against_last_choice_dp(self):
  for n in range(1,5):
   for entries in product((1,3),repeat=2*n):
    a,b=list(entries[:n]),list(entries[n:]);dp=[1,1];answer=1
    for i in range(1,n):
     old=dp;dp=[max([1]+[old[k]+1 for k,v in enumerate((a[i-1],b[i-1])) if v<=cur]) for cur in (a[i],b[i])];answer=max(answer,*dp)
    self.assertEqual(o.expected(2771,[a,b]),answer)
 def test_visit_subsequences_against_position_dag(self):
  rng=random.Random(602)
  for _ in range(100):
   a=[rng.randrange(1,20) for _ in range(rng.randrange(2,11))];x=rng.randrange(1,25);dp=[a[0]]
   for i in range(1,len(a)):dp.append(a[i]+max(dp[j]-(x if a[i]%2!=a[j]%2 else 0) for j in range(i)))
   self.assertEqual(o.expected(2786,[a,x]),max(dp))
 def test_merges_against_interval_feasibility(self):
  rng=random.Random(603)
  for _ in range(100):
   a=[rng.randrange(1,8) for _ in range(rng.randrange(1,9))];n=len(a);can={(i,i+1) for i in range(n)};best=max(a)
   for length in range(2,n+1):
    for left in range(n-length+1):
     right=left+length
     if any((left,mid) in can and (mid,right) in can and sum(a[left:mid])<=sum(a[mid:right]) for mid in range(left+1,right)):
      can.add((left,right));best=max(best,sum(a[left:right]))
   self.assertEqual(o.expected(2789,[a]),best)
 def test_literal_tree_paths_against_root_parities(self):
  rng=random.Random(604)
  for _ in range(100):
   n=rng.randrange(1,13);parent=[-1]+[rng.randrange(i) for i in range(1,n)];s=''.join(rng.choices('abcz',k=n));masks=[0]*n
   for i in range(1,n):masks[i]=masks[parent[i]]^(1<<(ord(s[i])-97))
   want=sum((masks[i]^masks[j]).bit_count()<=1 for i in range(n) for j in range(i+1,n))
   self.assertEqual(o.expected(2791,[parent,s]),want)
  self.assertEqual(o.expected(2791,[[-1,2,0],'abc']),o.expected(2791,[[-1,2,0],'zbc']))
 def test_placement_against_all_binary_strings(self):
  words=('a','b','aa','ab','ba','bb')
  for args in product(words,repeat=3):
   want=None
   for n in range(max(map(len,args)),sum(map(len,args))+1):
    for letters in product('ab',repeat=n):
     s=''.join(letters)
     if all(w in s for w in args):want=s;break
    if want is not None:break
   self.assertEqual(o.expected(2800,list(args)),want)
 def test_employee_exact_threshold(self):
  self.assertEqual(o.expected(2798,[[0,0],0]),2)
  self.assertEqual(o.expected(2798,[[99999,100000],100000]),1)
 def test_input_preservation(self):
  for pid,args in [(2771,[[2,1],[1,2]]),(2786,[[1,2,1],3]),(2789,[[3,2,1]]),(2791,[[-1,2,0],'zab']),(2798,[[1,2],1]),(2800,['ab','ba','b'])]:
   old=copy.deepcopy(args);o.expected(pid,args);self.assertEqual(args,old)
 def test_complete_validators_and_reference_budgets(self):
  tests=[(2771,[[10**9]*100000,[1]*100000]),(2786,[[10**6]*100000,10**6]),(2789,[[10**6]*100000]),(2791,[[-1]+list(range(99999)),'z'*100000]),(2800,['a'*100]*3)]
  for pid,args in tests:
   o.validate(pid,args)
   with self.assertRaisesRegex(ValueError,'budget'):o.expected(pid,args)
  o.validate(2791,[[-1,3,0,2],'abcd']);o.validate(2791,[[-1],'a'])
 def test_invalid_domains(self):
  bad=[(2771,[[],[]]),(2771,[[1],[1,2]]),(2771,[[True],[1]]),(2771,[[1.0],[1]]),(2786,[[1],1]),(2786,[[1,2],0]),(2786,[[1,2],1000001]),(2789,[[0]]),(2789,[[True]]),(2791,[[-1,1],'ab']),(2791,[[-1,2,1],'abc']),(2791,[[0],'a']),(2791,[[-1,False],'ab']),(2791,[[-1,0],'a']),(2791,[[-1],'A']),(2798,[[],0]),(2798,[[0],-1]),(2798,[[1]*51,0]),(2798,[[False],0]),(2800,['a','','b']),(2800,['a','B','b']),(2800,['a','é','b']),(2800,['a'*101,'b','c'])]
  for pid,args in bad:
   with self.subTest(pid=pid,args=args),self.assertRaises(ValueError):o.validate(pid,args)
 def test_bad_pins_and_answer_types(self):
  with self.assertRaises(ValueError):o.public_examples(2800,b'not a statement')
  self.assertFalse(o.valid_answer(2791,[[-1],'a'],False));self.assertFalse(o.valid_answer(2798,[[1],1],1.0));self.assertFalse(o.valid_answer(2800,['a','b','c'],'ab'))
if __name__=='__main__':unittest.main()
