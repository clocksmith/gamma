"""Four exact public-spec references; no candidate loading or execution."""
from collections import deque
from itertools import combinations,product
import ast,json,random,re
from . import imported_qualification as q
from .imported_clean_domains import integer,ints
IDS=(2812,2830,2844,2857)
PARAMETERS={2812:('grid',),2830:('n','offers'),2844:('num',),2857:('coordinates','k')}
STATEMENT_SHA256={2812:'5105e7eedc26bce186b410dbde672fc8a49e6a6195ab0afffe9e6396d82bbd08',2830:'f0aabaeb45945084201f8f76b77d7ea757810ce1d919c22f6321de6e6eae9b92',2844:'bbf63dc9011c0d778c13d0b26ba7c014866ec1318c3b75c37556db712e3183f7',2857:'32c9b4f6525112eff1622c02ef3d1825e7ff4864c5a7baca5f99b9c6a72784f3'}
EXAMPLE_COUNT={2812:3,2830:2,2844:3,2857:2}
CASE_COUNT={2812: 613, 2830: 336, 2844: 1116, 2857: 1548}
CASES_SHA256={2812: 'f70df107a860be03e5f30f0236569e06e902db1c8c3f797aabd3d916d530b603', 2830: '800710b9b26a8a0137208909784baeec2c3067c417fe0f6c424e4e05079d6b1c', 2844: 'd3632cc56ce0d172c2450eb1cb8b8b8927427ea0edbb4fb0c363b1c211b66afc', 2857: '1ceaa0c933fab904f80e6fe1215bf4b4b1ed69471101a159c68a3e921243ac6b'}
SEED_BASE=202610273003
OMITTED_MAXIMUM_SHAPES={2812:'Complete nonempty thief masks through3x3, seeded grids through8x8, selected analytic400x400 shapes. Arbitrary400x400 grids are not exhausted.',2830:'Offer-subset enumeration is bounded to18offers. Full100000offers use repeated compact intervals; full n100000 and gold1000 are separately present. Arbitrary100000offers of maximum-width numeric fields exceed unchanged MAX_PACKET1100000; no cap relaxation. Disjoint45000singletons and90000compact maximum-gold duplicates fit.',2844:'Complete small decimal alphabets, seeded strings through16digits and analytic100digit forms; arbitrary100digit subsequences not exhausted.',2857:'Pair enumeration is bounded to100coordinates. Full50000count and1000000coordinate values, k0/100, repeated/two-group/unique-line forms have independent combinatorial certificates; arbitrary maximum coordinate lists omitted.'}
CONTRACTS={2812:dict(domain='Square binary grid n1..400, with at least one thief.',result='Maximum over four-neighbor start-to-end paths of the minimum Manhattan distance to any thief along the path.',reference='Explicit all-thief Manhattan minima plus threshold reachability for n<=8.',complexity='Candidate near-quadratic in grid side with bounded storage; full-shape native runtime unmeasured.'),2830:dict(domain='n1..100000;1..100000offers [start,end,gold],0<=start<=end<n,gold1..1000; duplicates permitted.',result='Maximum profit from disjoint inclusive house intervals; houses may remain unsold.',reference='Enumerate every subset of at most18offers and test all interval intersections.',complexity='Candidate O((n+offers) log(n+offers)) or justified bounded equivalent; numeric maximum100000000 exact.'),2844:dict(domain='ASCII decimal string length1..100 with no leading zero except sole0.',result='Fewest digit deletions to reach an integer divisible25; deleting all digits yields0.',reference='Enumerate all retained subsequences through16digits, interpreting empty as0.',complexity='Candidate bounded polynomial or linear in length; no numeric parsing precision assumptions.'),2857:dict(domain='2..50000integer coordinate pairs, each component0..1000000;k0..100; duplicates permitted.',result='Count distinct index pairs i<j whose XOR-x plus XOR-y equals k.',reference='Enumerate every unordered index pair through100points.',complexity='Candidate O(n*(k+1)) expected with bounded map or comparable justified bound; maximum result1249975000 exact.')}
COMMON_CONTRACT=dict(exposure='Exposed development, never fresh holdout or candidate qualification.',interface='Official ordered single-call positional parameters only; actual candidate export and helpers remain unknown.',effects='Conservative service envelope preserves typed inputs/identity, forbids mutable return-input aliases and external IO or cross-call state; official challenge statements do not independently impose this envelope.',numeric='Exact integer results; input bool/float rejected. All outputs fit exact JavaScript Number, but implementation arithmetic is uninspected.',limits='Unchanged q.MAX_PACKET, q.MAX_FILE and q.LIMITS; expected values remain host-only.',native_gaps='No candidate timing, memory, complexity or effects have been measured. No native/stateful interface inferred.')

def validate(pid,args):
 if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):raise ValueError('unsupported identity or ordered args')
 if pid==2812:
  grid=args[0];valid=type(grid) is list and 1<=len(grid)<=400 and all(ints(row,0,1,len(grid),len(grid)) for row in grid)
  if valid:valid=any(1 in row for row in grid)
 elif pid==2830:
  n,offers=args;valid=integer(n,1,100000) and type(offers) is list and 1<=len(offers)<=100000 and all(type(o) is list and len(o)==3 and integer(o[0],0,n-1) and integer(o[1],o[0],n-1) and integer(o[2],1,1000) for o in offers)
 elif pid==2844:
  s=args[0];valid=type(s) is str and 1<=len(s)<=100 and all(c in '0123456789' for c in s) and (s=='0' or s[0]!='0')
 else:
  coords,k=args;valid=type(coords) is list and 2<=len(coords)<=50000 and all(ints(p,0,1000000,2,2) for p in coords) and integer(k,0,100)
 if not valid:raise ValueError('outside complete pinned official domain')

def expected(pid,args):
 validate(pid,args)
 if pid==2812:
  grid=args[0];n=len(grid)
  if n>8:raise ValueError('explicit Manhattan reference budget')
  thieves=[(r,c) for r in range(n) for c in range(n) if grid[r][c]]
  distance=[[min(abs(r-u)+abs(c-v) for u,v in thieves) for c in range(n)] for r in range(n)]
  for threshold in range(min(distance[0][0],distance[-1][-1]),-1,-1):
   seen={(0,0)};todo=deque([(0,0)])
   while todo:
    r,c=todo.popleft()
    for u,v in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
     if 0<=u<n and 0<=v<n and (u,v) not in seen and distance[u][v]>=threshold:seen.add((u,v));todo.append((u,v))
   if (n-1,n-1) in seen:return threshold
  raise AssertionError('threshold zero always connects')
 if pid==2830:
  offers=args[1];m=len(offers)
  if m>18:raise ValueError('offer subset reference budget')
  answer=0
  for mask in range(1<<m):
   chosen=[i for i in range(m) if mask>>i&1]
   if all(offers[i][1]<offers[j][0] or offers[j][1]<offers[i][0] for i,j in combinations(chosen,2)):answer=max(answer,sum(offers[i][2] for i in chosen))
  return answer
 if pid==2844:
  s=args[0];n=len(s)
  if n>16:raise ValueError('retained subsequence reference budget')
  answer=n
  for mask in range(1<<n):
   digits=''.join(s[i] for i in range(n) if mask>>i&1)
   if int(digits or '0')%25==0:answer=min(answer,n-len(digits))
  return answer
 coords,k=args
 if len(coords)>100:raise ValueError('all index-pair reference budget')
 return sum((coords[i][0]^coords[j][0])+(coords[i][1]^coords[j][1])==k for i,j in combinations(range(len(coords)),2))

def public_examples(pid,raw):
 if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw)!=STATEMENT_SHA256[pid]:raise ValueError('exact pinned official statement required')
 cases=[]
 for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)',raw.decode(),re.S):
  call=ast.parse('f('+match[1].strip()+')',mode='eval').body
  if not isinstance(call,ast.Call) or call.args or tuple(x.arg for x in call.keywords)!=PARAMETERS[pid]:raise ValueError('ordered public parameters differ')
  args=[ast.literal_eval(x.value) for x in call.keywords];answer=json.loads(match[2]);assert q.exact(expected(pid,args),answer)
  cases.append({'args':args,'expected':answer,'compare':'return'})
 if len(cases)!=EXAMPLE_COUNT[pid]:raise ValueError('complete public examples required')
 return cases

def _generate_cases(pid,statement):
 cases=[];cats=[];seen={};rng=random.Random(SEED_BASE+pid);sentinel=object()
 def add(args,category,answer=sentinel):
  validate(pid,args);answer=expected(pid,args) if answer is sentinel else answer
  upper={2812:800,2830:100000000,2844:100,2857:1249975000}[pid]
  if not integer(answer,0,upper):raise ValueError('invalid typed expected value')
  key=q.encoded(args)
  if key in seen:assert q.exact(seen[key],answer);return
  seen[key]=answer;cases.append({'args':args,'expected':answer,'compare':'return'});cats.append(category)
 for c in public_examples(pid,statement):add(c['args'],'pinned_public_example',c['expected'])
 if pid==2812:
  for n in range(1,4):
   for mask in range(1,1<<(n*n)):add([[[int(bool(mask>>(r*n+c)&1)) for c in range(n)] for r in range(n)]],'exhaustive_nonempty_thief_masks')
  for _ in range(80):
   n=rng.randrange(4,9);grid=[[int(rng.random()<0.2) for _ in range(n)] for _ in range(n)];grid[rng.randrange(n)][rng.randrange(n)]=1;add([grid],'seeded_literal_manhattan_threshold_paths')
  n=400
  add([[[1]*n for _ in range(n)]],'analytic_maximum_all_thieves',0)
  for r,c,label,answer in [(0,0,'endpoint',0),(0,n-1,'top_right',n-1),(n-1,0,'bottom_left',n-1)]:
   grid=[[0]*n for _ in range(n)];grid[r][c]=1;add([grid],'analytic_maximum_single_thief_'+label,answer)
  grid=[[int(r==n//2) for _ in range(n)] for r in range(n)];add([grid],'analytic_maximum_thief_barrier',0)
 elif pid==2830:
  offers=[(0,0,1),(0,1,2),(1,1,3),(1,2,1),(2,2,2),(0,2,3)]
  for count in range(1,5):
   for indices in combinations(range(len(offers)+count-1),count):
    # Combinations with replacement via strictly increasing shifted indices.
    rows=[list(offers[v-i]) for i,v in enumerate(indices)];add([3,rows],'exhaustive_small_offer_multisets')
  for _ in range(120):
   n=rng.randrange(1,20);rows=[]
   for _ in range(rng.randrange(1,12)):
    start=rng.randrange(n);rows.append([start,rng.randrange(start,n),rng.choice((1,2,7,999,1000))])
   add([n,rows],'seeded_inclusive_interval_subset_profits')
  add([100000,[[0,0,1]]*100000],'analytic_maximum_offer_count_duplicates',1)
  add([100000,[[0,0,1000]]*90000],'analytic_large_maximum_gold_duplicates',1000)
  add([100000,[[i,i,1000] for i in range(45000)]],'analytic_large_disjoint_maximum_gold_singletons',45000000)
  add([100000,[[0,99999,1000]]*50000],'analytic_full_range_duplicate_offers',1000)
  add([100000,[[0,99999,1000],[0,0,1000],[99999,99999,1000]]],'analytic_maximum_endpoints_inclusive',2000)
 elif pid==2844:
  for length in range(1,6):
   for digits in product('0257',repeat=length):
    if length==1 or digits[0]!='0':add([''.join(digits)],'exhaustive_small_decimal_subsequences')
  for _ in range(80):
   length=rng.randrange(6,15);s=rng.choice('123456789')+''.join(rng.choices('0123456789',k=length-1));add([s],'seeded_decimal_subsequence_enumeration')
  for s,answer in [('1'*100,100),('9'*100,100),('1'*99+'0',99),('5'+'1'*98+'0',98),('1'*98+'00',0),('1'*98+'25',0),('1'*98+'50',0),('1'*98+'75',0),('2'+'1'*98+'5',98)]:add([s],'analytic_maximum_decimal_suffix_or_zero',answer)
 else:
  points=((0,0),(0,1),(1,0))
  for n in range(2,6):
   for coords in product(points,repeat=n):
    for k in range(4):add([[list(p) for p in coords],k],'exhaustive_small_coordinate_sequences')
  for _ in range(100):
   coords=[[rng.choice((0,1,2,3,999999,1000000)),rng.choice((0,1,2,3,999999,1000000))] for _ in range(rng.randrange(2,31))]
   add([coords,rng.choice((0,1,2,3,99,100))],'seeded_xor_duplicates_numeric_edges')
  n=50000
  for k,answer in [(0,n*(n-1)//2),(100,0)]:add([[[1000000,1000000]]*n,k],'analytic_maximum_identical_points',answer)
  coords=[[0,0]]*25000+[[100,0]]*25000
  add([coords,100],'analytic_maximum_two_group_cross_pairs',625000000)
  add([coords,0],'analytic_maximum_two_group_within_pairs',624975000)
  for k,answer in [(0,0),(1,25000)]:add([[[i,0] for i in range(n)],k],'analytic_maximum_unique_line_xor_pairs',answer)
 return cases,cats

def expected_observation_bytes(batch,language):
 if language not in ('javascript','python'):raise ValueError('unsupported language')
 return sum(len(q.encoded({'i':i,'result':c['expected'],'result_type':q.expected_type(c['expected'],language),'args_before':c['args'],'args_after':c['args'],'alias_edges':[]})) for i,c in enumerate(batch))+len(q.encoded({'done':len(batch)}))+(language=='python')

def build_cases(pid,statement):
 cases,cats=_generate_cases(pid,statement)
 if len(cases)!=CASE_COUNT.get(pid) or q.sha(q.encoded(cases))!=CASES_SHA256.get(pid):raise ValueError('immutable case count/hash drift')
 if len(q.encoded(cases))>q.MAX_FILE:raise ValueError('case file exceeds cap')
 for _,batch in q.batches(cases):
  if any(expected_observation_bytes(batch,lang)>q.LIMITS['max_output_bytes'] for lang in ('javascript','python')):raise ValueError('observation cap exceeded')
 return cases,cats
