"""Four exact source-blind ordinary references; unordered3211 stays separate."""
from collections import deque
from itertools import product
from pathlib import Path
import ast,hashlib,json,random,re
from . import imported_qualification as q
from .imported_clean_domains import integer,ints
SUPPORT_SHA256='af18c04686c549f87f68c245710097bff563f587d116697783fb01bb0ebe3b5b'
# Reviewed publication-only helper compatibility; no runtime or future-hash approval.
PUBLICATION_SUPPORT_SHA256='d32268c3b9bd780d533d59c58cb6cd983b2b4de583bd35171e8bf03cdfb138a5'
if hashlib.sha256(Path(q.__file__).read_bytes()).hexdigest() not in (SUPPORT_SHA256,PUBLICATION_SUPPORT_SHA256):raise RuntimeError('queue10 frozen q support drift; explicitly bind historical snapshot')
IDS=(3201,3202,3207,3212)
PARAMETERS={3201:('nums',),3202:('nums','k'),3207:('enemyEnergies','currentEnergy'),3212:('grid',)}
STATEMENT_SHA256={3201:'0d2767ec0e6565b60bf8b5d84af3074dabe58edf5d9c1d60587750bc142ec5ed',3202:'3e3bbf192ef1ac96e7fa7f0f2812d60c4ec65781e822e1452b2f8e5544a642b5',3207:'5553487b6bb7352ebf113a224c52ca190d6abccaeb645229413ea98121a52429',3212:'14d739484b80c142892ad5c5fd3f5e13c29d49ebec255bf925a0d294a3b531dc'}
EXAMPLE_COUNT={3201:3,3202:2,3207:2,3212:3}
CASE_COUNT={3201: 1126, 3202: 1548, 3207: 821, 3212: 1638}
CASES_SHA256={3201: '2aa52f2b7e769f01bb2d42cd54d8b26d5fdfbfa13dde08ac695e2457a2766bd4', 3202: 'e7e646b9cdb550356776c612f27c6fe903f8e544e64eee05ea6cd193a63ca545', 3207: 'aad94c305b6c0c9e120939c4af395c7f483c4219ea776c6d55a5b2c7f9396b00', 3212: '7afbad0bbe41ae7071b72519dfce8b33effadf925e5ff9b859dfa22d103f4760'}
SEED_BASE=202610271003
COMMON_CONTRACT=dict(exposure='Exposed deterministic development only, not fresh holdout or qualification.',interface='Official ordinary-call positional parameters only; actual exports/helpers unknown.3211 any-order result excluded rather than ordered by inference.',effects='Chosen strict input preservation, no mutable return-input aliases/IO/persistent state; not a public-statement mandate.',numeric='Exact integers with bool/float excluded;3207 result<=1e14<2^53 but may exceed32bits.',limits='Unchanged q.MAX_FILE/MAX_PACKET/batches/LIMITS; expected values host-only.',native_gaps='No native resource, timing, complexity, effect or interface pass. Source bodies unopened.')
CONTRACTS={3201:dict(domain='Integer nums length2..200000, values1..1e7.',result='Longest index subsequence whose adjacent sums have equal remainder modulo2.',reference='Enumerate every retained index subset for length<=16.',complexity='Candidate O(n), bounded parity state or justified equivalent.'),3202:dict(domain='Integer nums length2..1000, values1..1e7;k1..1000.',result='Longest index subsequence with equal adjacent-sum remainders modulo k.',reference='Enumerate every retained index subset for length<=16, separate k/domain.',complexity='Candidate O(n*k) time/O(k*k) or justified bounded equivalent; actual numeric and allocation details uninspected.'),3207:dict(domain='Enemy integer energies length1..100000, values1..1e9; currentEnergy0..1e9.',result='Maximum points: attack unmarked affordable enemy repeatedly for1point costing energy, without marking it; with>=1point may mark an enemy to gain its energy without spending points.',reference='Explore operation states by marked mask and energy, retaining maximum points for identical states; n<=5,sum<=35,initial<=15.',complexity='Candidate O(n), total-energy conservation/minimum attack cost; not per-point looping for result1e14.'),3212:dict(domain='Rectangular character grid1..1000 rows/columns, every cell exactly X,Y,or dot.',result='Count top-left anchored submatrices with equal X/Y frequencies and at leastone X.',reference='Enumerate every anchored rectangle and count each cell literally, each dimension<=5.',complexity='Candidate O(rows*cols) prefix accumulation, bounded O(rows*cols) or O(cols) storage; full million-cell native cost unmeasured.')}
OMITTED_MAXIMUM_SHAPES={3201:'200000 maximum-width values exceed packet; full low-value200000 and100000 maximum-value entries retained. Arbitrary full subsequences omitted.',3202:'All scalar/list maximum shapes fitpacket; selected constant/two-residue/k1000 patterns only, not all1000^1000 residue sequences.',3207:'100000 maximum-width enemy values exceed packet. Full low-valuecount and90001 entries with90000 maximumenergy enemies retained. No huge per-point state exploration.',3212:'1000x1000 character-cell JSON exceeds packet.250x1000 and1000x250 retain separate maximum dimensions; arbitrary full grid omitted.3211 any-order output excluded, not forced into exact-return comparator.'}

def validate(pid,args):
 if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):raise ValueError('unsupported identity or ordered args')
 if pid==3201:valid=ints(args[0],1,10**7,2,200000)
 elif pid==3202:valid=ints(args[0],1,10**7,2,1000) and integer(args[1],1,1000)
 elif pid==3207:valid=ints(args[0],1,10**9,1,100000) and integer(args[1],0,10**9)
 else:
  a=args[0];valid=type(a) is list and 1<=len(a)<=1000 and type(a[0]) is list and 1<=len(a[0])<=1000 and all(type(row) is list and len(row)==len(a[0]) and all(type(v) is str and v in ('X','Y','.') for v in row) for row in a)
 if not valid:raise ValueError('outside complete pinned official domain')

def expected(pid,args):
 validate(pid,args)
 if pid in (3201,3202):
  nums=args[0];n=len(nums);k=2 if pid==3201 else args[1]
  if n>16:raise ValueError('all index-subsequence reference budget')
  best=1
  for mask in range(1,1<<n):
   if mask.bit_count()<=best:continue
   sub=[nums[i] for i in range(n) if mask>>i&1]
   if len({(sub[i]+sub[i+1])%k for i in range(len(sub)-1)})<=1:best=len(sub)
  return best
 if pid==3207:
  enemies,energy=args;n=len(enemies)
  if n>5 or sum(enemies)>35 or energy>15:raise ValueError('literal enemy-operation state reference budget')
  states={(0,energy):0};todo=deque([(0,energy)]);answer=0
  while todo:
   mask,current=todo.popleft();points=states[mask,current];answer=max(answer,points)
   for i,cost in enumerate(enemies):
    if mask>>i&1:continue
    changes=[]
    if current>=cost:changes.append(((mask,current-cost),points+1))
    if points>=1:changes.append(((mask|(1<<i),current+cost),points))
    for key,value in changes:
     if value>states.get(key,-1):states[key]=value;todo.append(key)
  return answer
 grid=args[0];rows=len(grid);cols=len(grid[0])
 if max(rows,cols)>5:raise ValueError('literal anchored-rectangle reference budget')
 answer=0
 for bottom in range(rows):
  for right in range(cols):
   x=y=0
   for r in range(bottom+1):
    for c in range(right+1):x+=grid[r][c]=='X';y+=grid[r][c]=='Y'
   answer+=x==y and x>0
 return answer

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
  if not integer(answer,0,10**14):raise ValueError('invalid typed expected')
  key=q.encoded(args)
  if key in seen:assert q.exact(seen[key],answer);return
  seen[key]=answer;cases.append(dict(args=args,expected=answer,compare='return'));cats.append(category)
 for c in public_examples(pid,statement):add(c['args'],'pinned_public_example',c['expected'])
 if pid==3201:
  for n in range(2,10):
   for a in product((1,2),repeat=n):add([list(a)],'exhaustive_small_parity_subsequences')
  for _ in range(100):add([[rng.choice((1,2,3,9999999,10000000)) for _ in range(rng.randrange(10,17))]],'seeded_full_numeric_subsequences')
  for a,answer in [([1]*200000,200000),([1,2]*100000,200000),([1]*100000+[2]*100000,100000),([10000000]*100000,100000)]:add([a],'analytic_maximum_parity_shapes',answer)
 elif pid==3202:
  for n in range(2,6):
   for a in product((1,2,3),repeat=n):
    for k in (1,2,3,4):add([list(a),k],'exhaustive_small_modular_subsequences')
  for _ in range(100):add([[rng.choice((1,2,3,7,9999999,10000000)) for _ in range(rng.randrange(6,15))],rng.choice((1,2,3,7,999,1000))],'seeded_modular_and_numeric_edges')
  for a,k,answer in [([10000000]*1000,1000,1000),(list(range(1,1001)),1,1000),([1,999]*500,1000,1000),([1]*500+[999]*500,1000,500),([1,2]*500,1000,1000),(list(range(1,1001)),1000,2)]:add([a,k],'analytic_maximum_modular_shapes',answer)
 elif pid==3207:
  for n in range(1,5):
   for a in product((1,2,4),repeat=n):
    for energy in range(6):add([list(a),energy],'exhaustive_small_enemy_operation_states')
  for _ in range(100):add([[rng.randrange(1,7) for _ in range(rng.randrange(1,6))],rng.randrange(16)],'seeded_mark_attack_state_orders')
  for a,energy,answer in [([1]*100000,0,0),([1]*100000,1,100000),([1]*100000,10**9,10**9+99999),([1]+[10**9]*90000,10**9,90001000000000),([10**9]*90000,10**9-1,0),([10**9]*90000,10**9,90000),([2],10**9,500000000)]:add([a,energy],'analytic_maximum_energy_and_enemy_shapes',answer)
 else:
  for rows,cols in ((1,1),(1,2),(2,1),(2,2),(2,3),(3,2)):
   for cells in product('XY.',repeat=rows*cols):add([[[cells[r*cols+c] for c in range(cols)] for r in range(rows)]],'exhaustive_small_anchored_character_grids')
  for _ in range(100):
   rows=rng.randrange(1,6);cols=rng.randrange(1,6);add([[[rng.choice('XY.') for _ in range(cols)] for _ in range(rows)]],'seeded_literal_anchored_rectangles')
  for rows,cols in ((250,1000),(1000,250)):
   add([[['X' if (r+c)%2==0 else 'Y' for c in range(cols)] for r in range(rows)]],'analytic_largest_transport_checkerboard',rows*cols-((rows+1)//2)*((cols+1)//2))
   add([[['.']*cols for _ in range(rows)]],'analytic_largest_transport_no_X',0)
  add([[['X' if c%2==0 else 'Y' for c in range(1000)] for _ in range(250)]],'analytic_largest_transport_paired_columns',250*500)
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
