"""Five source-blind ordinary-call references, no candidate code or execution."""
from collections import deque
from functools import lru_cache
from itertools import product, combinations
from pathlib import Path
import ast,hashlib,json,random,re
from . import imported_qualification as q
from .imported_clean_domains import integer,ints
SUPPORT_SHA256='af18c04686c549f87f68c245710097bff563f587d116697783fb01bb0ebe3b5b'
# Reviewed publication-only helper compatibility; no runtime or future-hash approval.
PUBLICATION_SUPPORT_SHA256='d32268c3b9bd780d533d59c58cb6cd983b2b4de583bd35171e8bf03cdfb138a5'
if hashlib.sha256(Path(q.__file__).read_bytes()).hexdigest() not in (SUPPORT_SHA256,PUBLICATION_SUPPORT_SHA256):raise RuntimeError('queue10 frozen q support drift; explicitly bind historical snapshot')
IDS=(3185,3186,3191,3195,3196)
PARAMETERS={3185:('hours',),3186:('power',),3191:('nums',),3195:('grid',),3196:('nums',)}
STATEMENT_SHA256={3185:'b99e1c9f0165015918a941b0d9921f8a8d67aca21da5df0992994d9182d1385a',3186:'f280501fc3e387fb7de2dfef16ba223bc0a6591d9de18d99461ae8fff3656012',3191:'9a78810564ef8af70faaeb3792fc11ff74e2fc3f1af9e86b879093eb3bc5e6b9',3195:'b385751ee9c359ae09bc1d4cd7d34e068e8f591b8324e372815db07293d70f08',3196:'7665b0e3013d5df2ee2dd59badc7a5a547348077fe3936e71bd7af78522130f6'}
EXAMPLE_COUNT={3185:2,3186:2,3191:2,3195:2,3196:4}
CASE_COUNT={3185: 1198, 3186: 1196, 3191: 2124, 3195: 729, 3196: 3387}
CASES_SHA256={3185: 'c6aef8e4fbe983132aef38cb6650366f7a63a526b667dd1490839f8a2a807210', 3186: '782f1ea9afdf85434187948bccc06a5cb2ceb20919b0e79bb6c0c8327828e8e2', 3191: '251f0070386301dae6ab8f1901a1e98345387def24ced39c7b9585955c5021fa', 3195: 'd2d12ff08a84013e501053b684ef3137f2765f684e24fa994bf6389c9b008a57', 3196: 'c9c105644775d4d95a3628b0b4d4d3815179ac7737410b21355523c6d7f6da61'}
SEED_BASE=202610271002
COMMON_CONTRACT=dict(exposure='Exposed deterministic development only, not fresh holdout or qualification.',interface='Official ordered positional values only; actual candidate exports/helpers unknown.',effects='Chosen strict typed-input and identity preservation, no mutable return-input alias, external IO or persistent state; not a statement-derived mutation restriction.',numeric='Exact signed integers, bool/float rejected; largest domain totals at most1e14<2^53, but>32bit. Implementation arithmetic uninspected.',limits='Unchanged q.MAX_FILE/MAX_PACKET/batches/LIMITS; expected values host-only.',native_gaps='No candidate timing, resources, effects, complexity or interface pass; no native/stateful binding inferred.')
CONTRACTS={3185:dict(domain='Integer hours length1..500000, each1..1e9.',result='Number of unordered index pairs i<j with summed hours divisible24.',reference='Literal all-index pairs for length<=100.',complexity='Candidate O(n+24), bounded remainder counts; result<=124999750000.'),3186:dict(domain='Integer spell powers length1..100000, each1..1e9, duplicates permitted.',result='Max selected index sum with no two selected values differing1 or2; equal values compatible.',reference='Enumerate every selected index subset for length<=14.',complexity='Candidate O(n log n) with grouped values and weighted independent intervals or justified equivalent; result<=1e14.'),3191:dict(domain='Binary integer array length3..100000.',result='Minimum length3 contiguous flip operations to allones, or-1 if unreachable.',reference='BFS all binary array states from allones, through length12.',complexity='Candidate O(n) time/O(n) or O(1) auxiliary; preserve input under chosen envelope.'),3195:dict(domain='Rectangular binary grid1..1000 rows/cols with at least one1.',result='Minimum integer-cell area of axis-aligned rectangle containing all1 cells.',reference='Enumerate all row/column boundary rectangles for each dimension<=5.',complexity='Candidate O(rows*cols) time/O(1) auxiliary or justified bound; result1..1000000.'),3196:dict(domain='Integer array length1..100000, values-1e9..1e9.',result='Maximum sum of alternating costs over every complete contiguous partition, onepart allowed.',reference='Enumerate every inter-element cut mask for length<=16.',complexity='Candidate O(n) two-state DP or justified equivalent; signed cost magnitude<=1e14, no32bit truncation.')}
OMITTED_MAXIMUM_SHAPES={3185:'500000 maximum-width hours exceed packet; even500000 hours12 (all-pair maximum) exceeds. Full500000 ones gives0;360000 twelves gives64799820000, numeric max separately. Arbitrary full pairs omitted.',3186:'100000 values1e9 exceed1.1MB packet by envelope;100000 values999999999 and90000 values1e9 retained. Full index subsets not exhausted.',3191:'All binary inputs lengths3..10, seeded11/12, selected length100000 algebraic shapes. Arbitrary maximum bit arrays not exhausted.',3195:'1000x1000 grid exceeds packet even allzeros.1000x500 and500x1000 retain individual max dimensions; arbitrary million-cell shape omitted.',3196:'100000 max-width positive/negative values exceed packet. Full100000 low-width and999999999positive, large90000 maxmagnitude alternation retained. Arbitrary maximum partitions not enumerated.'}

def validate(pid,args):
 if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=1:raise ValueError('unsupported identity or ordered args')
 a=args[0]
 if pid==3185:valid=ints(a,1,10**9,1,500000)
 elif pid==3186:valid=ints(a,1,10**9,1,100000)
 elif pid==3191:valid=ints(a,0,1,3,100000)
 elif pid==3196:valid=ints(a,-10**9,10**9,1,100000)
 else:
  valid=type(a) is list and 1<=len(a)<=1000 and type(a[0]) is list and 1<=len(a[0])<=1000 and all(ints(row,0,1,len(a[0]),len(a[0])) for row in a)
  if valid:valid=any(1 in row for row in a)
 if not valid:raise ValueError('outside complete pinned official domain')
@lru_cache(None)
def _flip_distances(n):
 target=(1<<n)-1;dist={target:0};todo=deque([target])
 while todo:
  value=todo.popleft()
  for start in range(n-2):
   nxt=value^(7<<start)
   if nxt not in dist:dist[nxt]=dist[value]+1;todo.append(nxt)
 return dist

def expected(pid,args):
 validate(pid,args);a=args[0];n=len(a)
 if pid==3185:
  if n>100:raise ValueError('all-pair reference budget')
  return sum((a[i]+a[j])%24==0 for i,j in combinations(range(n),2))
 if pid==3186:
  if n>14:raise ValueError('all spell-index subset reference budget')
  best=0
  for mask in range(1<<n):
   chosen=[a[i] for i in range(n) if mask>>i&1]
   if all(abs(x-y) not in (1,2) for x,y in combinations(chosen,2)):best=max(best,sum(chosen))
  return best
 if pid==3191:
  if n>12:raise ValueError('binary-state BFS reference budget')
  return _flip_distances(n).get(sum(v<<i for i,v in enumerate(a)),-1)
 if pid==3195:
  if n>5 or len(a[0])>5:raise ValueError('rectangle enumeration reference budget')
  m=len(a[0]);ones=[(r,c) for r in range(n) for c in range(m) if a[r][c]];answer=n*m
  for top in range(n):
   for bottom in range(top,n):
    for left in range(m):
     for right in range(left,m):
      if all(top<=r<=bottom and left<=c<=right for r,c in ones):answer=min(answer,(bottom-top+1)*(right-left+1))
  return answer
 if n>16:raise ValueError('complete cut-mask reference budget')
 best=-10**30
 for mask in range(1<<(n-1)):
  cost=a[0];sign=1
  for i in range(1,n):
   sign=1 if mask>>(i-1)&1 else -sign;cost+=sign*a[i]
  best=max(best,cost)
 return best

def public_examples(pid,raw):
 if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw)!=STATEMENT_SHA256[pid]:raise ValueError('exact pinned official statement required')
 out=[]
 for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)',raw.decode(),re.S):
  call=ast.parse('f('+match[1].strip()+')',mode='eval').body
  if not isinstance(call,ast.Call) or call.args or tuple(x.arg for x in call.keywords)!=PARAMETERS[pid]:raise ValueError('ordered public parameters differ')
  args=[ast.literal_eval(x.value) for x in call.keywords];answer=json.loads(match[2]);assert q.exact(expected(pid,args),answer);out.append(dict(args=args,expected=answer,compare='return'))
 if len(out)!=EXAMPLE_COUNT[pid]:raise ValueError('complete public examples required')
 return out

def _generate_cases(pid,statement):
 cases=[];cats=[];seen={};rng=random.Random(SEED_BASE+pid);sentinel=object()
 def add(args,category,answer=sentinel):
  validate(pid,args);answer=expected(pid,args) if answer is sentinel else answer
  if not integer(answer,-10**14 if pid==3196 else -1 if pid==3191 else 1 if pid==3195 else 0,10**14):raise ValueError('invalid typed expected')
  key=q.encoded(args)
  if key in seen:assert q.exact(seen[key],answer);return
  seen[key]=answer;cases.append(dict(args=args,expected=answer,compare='return'));cats.append(category)
 for c in public_examples(pid,statement):add(c['args'],'pinned_public_example',c['expected'])
 if pid==3185:
  for n in range(1,7):
   for a in product((1,12,23),repeat=n):add([list(a)],'exhaustive_small_hour_sequences')
  for _ in range(100):add([[rng.choice((1,2,12,23,24,25,999999999,10**9)) for _ in range(rng.randrange(1,61))]],'seeded_residue_and_numeric_edges')
  for a,answer in [([1]*500000,0),([12]*360000,360000*359999//2),([24]*360000,360000*359999//2),([1]*200000+[23]*200000,40000000000),([10**9]*90000,0),([999999984]*100000,100000*99999//2)]:add([a],'analytic_large_residue_groups',answer)
 elif pid==3186:
  for n in range(1,7):
   for a in product((1,2,4),repeat=n):add([list(a)],'exhaustive_small_spell_subsets')
  for _ in range(100):add([[rng.choice((1,2,3,4,6,7,999999998,999999999,10**9)) for _ in range(rng.randrange(1,13))]],'seeded_spell_conflicts_duplicates')
  for a,answer in [([1]*100000,100000),([999999999]*100000,99999999900000),([10**9]*90000,90000000000000),([1]*50000+[2]*50000,100000),(list(range(1,300001,3)),sum(range(1,300001,3))),([1]*33333+[2]*33333+[4]*33334,33333+4*33334)]:add([a],'analytic_large_compatible_or_conflicting_groups',answer)
 elif pid==3191:
  for n in range(3,11):
   for a in product((0,1),repeat=n):add([list(a)],'exhaustive_binary_state_graph')
  for _ in range(80):add([[rng.randrange(2) for _ in range(rng.choice((11,12)))]],'seeded_larger_binary_state_graph')
  n=100000;add([[1]*n],'analytic_maximum_already_target',0);add([[0]+[1]*(n-1)],'analytic_maximum_single_unreachable_bit',-1)
  for starts in (range(0,n-2,3),range(n-2)):
   a=[1]*n
   for start in starts:
    for j in range(start,start+3):a[j]^=1
   add([a],'analytic_maximum_injective_flip_mask',len(starts))
 elif pid==3195:
  for rows in range(1,4):
   for cols in range(1,4):
    for mask in range(1,1<<(rows*cols)):add([[[int(bool(mask>>(r*cols+c)&1)) for c in range(cols)] for r in range(rows)]],'exhaustive_nonempty_small_binary_grids')
  for _ in range(80):
   rows=rng.randrange(1,6);cols=rng.randrange(1,6);a=[[rng.randrange(2) for _ in range(cols)] for _ in range(rows)];a[rng.randrange(rows)][rng.randrange(cols)]=1;add([a],'seeded_rectangle_enumeration')
  for rows,cols in ((1000,500),(500,1000)):
   add([[[1]*cols for _ in range(rows)]],'analytic_largest_transport_full_rectangle',rows*cols)
   a=[[0]*cols for _ in range(rows)];a[0][0]=a[-1][-1]=1;add([a],'analytic_largest_transport_opposite_corners',rows*cols)
  a=[[0]*1000 for _ in range(500)];a[250][500]=1;add([a],'analytic_largest_transport_singleton',1)
 else:
  for n in range(1,8):
   for a in product((-1,0,1),repeat=n):add([list(a)],'exhaustive_small_complete_partitions')
  for _ in range(100):add([[rng.choice((-10**9,-7,-1,0,1,7,10**9)) for _ in range(rng.randrange(8,15))]],'seeded_signed_cut_masks')
  for a,answer in [([0]*100000,0),([1]*100000,100000),([-1]*100000,0),([-1]*99999,-1),([999999999]*100000,99999999900000),([10**9,-10**9]*45000,90000000000000),([-10**9,10**9]*45000,89998000000000)]:add([a],'analytic_maximum_signed_partition_shape',answer)
 return cases,cats

def expected_observation_bytes(batch,language):
 if language not in ('javascript','python'):raise ValueError('unsupported language')
 return sum(len(q.encoded(dict(i=i,result=c['expected'],result_type=q.expected_type(c['expected'],language),args_before=c['args'],args_after=c['args'],alias_edges=[]))) for i,c in enumerate(batch))+len(q.encoded({'done':len(batch)}))+(language=='python')

def build_cases(pid,statement):
 cases,cats=_generate_cases(pid,statement)
 if len(cases)!=CASE_COUNT.get(pid) or q.sha(q.encoded(cases))!=CASES_SHA256.get(pid):raise ValueError('immutable case count/hash drift')
 if len(q.encoded(cases))>q.MAX_FILE:raise ValueError('case file exceeds cap')
 for _,batch in q.batches(cases):
  if any(expected_observation_bytes(batch,lang)>q.LIMITS['max_output_bytes'] for lang in ('javascript','python')):raise ValueError('observation cap exceeded')
 return cases,cats
