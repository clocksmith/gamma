import copy,math,unittest
from collections import deque,Counter
from itertools import product,permutations
import oracles as o

class ReferenceChecks(unittest.TestCase):
 def test_hall_advantage_against_every_permutation(self):
  for n in range(1,4):
   arrays=list(product(range(3),repeat=n))
   for a in arrays:
    for b in arrays:
     best=max(sum(x>y for x,y in zip(p,b))for p in permutations(a))
     self.assertEqual(o.expected(870,[list(a),list(b)]),best)
 def test_spiral_rank_against_direct_walk(self):
  for rows in range(1,5):
   for cols in range(1,5):
    for rs in range(rows):
     for cs in range(cols):
      r,c=rs,cs;walk=[[r,c]];directions=((0,1),(1,0),(0,-1),(-1,0));length,turn=1,0
      while len(walk)<rows*cols:
       for _ in range(2):
        dr,dc=directions[turn%4]
        for _ in range(length):
         r+=dr;c+=dc
         if 0<=r<rows and 0<=c<cols:walk.append([r,c])
        turn+=1
       length+=1
      self.assertEqual(o.expected(885,[rows,cols,rs,cs]),walk)
 def test_prime_palindrome_generator_against_integer_scan(self):
  for n in range(1,151):
   v=n
   while str(v)!=str(v)[::-1]or not o.prime(v):v+=1
   self.assertEqual(o.expected(866,[n]),v)
 def test_mirror_unfolding_against_parity_reduction(self):
  for p in range(1,80):
   for q in range(1,p+1):
    a,b=p,q
    while a%2==0 and b%2==0:a//=2;b//=2
    want=0 if b%2==0 else 2 if a%2==0 else 1
    self.assertEqual(o.expected(858,[p,q]),want)
 def test_prison_function_powers_against_literal_days(self):
  for cells in product((0,1),repeat=8):
   current=list(cells)
   for day in range(1,35):
    current=[0]+[int(current[i-1]==current[i+1])for i in range(1,7)]+[0]
    self.assertEqual(o.expected(957,[list(cells),day]),current)
 def test_doubled_matching_against_every_ordering(self):
  for values in product((-2,-1,0,1,2),repeat=4):
   want=any(v[1]==2*v[0]and v[3]==2*v[2]for v in permutations(values))
   self.assertEqual(o.expected(954,[list(values)]),want)
 def test_unique_cost_against_breadth_first_search(self):
  for values in product(range(3),repeat=3):
   queue=deque([(tuple(sorted(values)),0)]);seen=set()
   while queue:
    state,cost=queue.popleft()
    if len(set(state))==len(state):break
    if state in seen:continue
    seen.add(state)
    for i in range(len(state)):
     nxt=list(state);nxt[i]+=1;queue.append((tuple(sorted(nxt)),cost+1))
   self.assertEqual(o.expected(945,[list(values)]),cost)
 def test_domain_negative_controls(self):
  invalid=[(858,[2,0]),(856,['())']), (877,[[1,1]]),(888,[[1],[1]]),(915,[[2,1]]),(967,[1,0]),(973,[[[1,0],[0,1]],1]),(945,[[0]*100000]),(874,[[9]*10000,[]])]
  for pid,args in invalid:
   with self.subTest(pid=pid),self.assertRaises(ValueError):o.validate(pid,args)
 def test_output_freedom_types_mutation_and_alias_controls(self):
  self.assertTrue(o.matches(870,[[2,3],[0,1]],[3,2],2))
  self.assertFalse(o.matches(870,[[2,3],[1,2]],[2,3,4],2))
  self.assertTrue(o.matches(905,[[1,2,3,4]],[4,2,3,1],Counter([1,2,3,4])))
  self.assertFalse(o.matches(905,[[1,2,3,4]],[2,1,4,3],Counter([1,2,3,4])))
  args=[[[1,0]],1];record={'result':[[1,0]],'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]}
  self.assertEqual(o.compare(973,args,[[1,0]],record,'python'),(True,None))
  aliased=copy.deepcopy(record);aliased['alias_edges']=[['result.0','args.0.0']]
  self.assertEqual(o.compare(973,args,[[1,0]],aliased,'python'),(False,'mutable_return_alias'))
  bad=copy.deepcopy(record);bad['result']=[[True,0]]
  self.assertEqual(o.compare(973,args,[[1,0]],bad,'python'),(False,'result_value'))
if __name__=='__main__':unittest.main()
