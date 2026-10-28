"""Independent finite cases plus exact analytic maximum-boundary shapes."""
import ast,html,json,random,re,string
from pathlib import Path
from itertools import product,permutations,combinations
import oracles as o


def official_examples(path):
 q=json.loads(Path(path).read_bytes())['data']['question']
 body=re.sub(r'</?(?:p|pre|div|li|ul|ol|br)[^>]*>','\n',q['content']);body=html.unescape(re.sub(r'<[^>]*>','',body));examples=[]
 for m in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*[0-9]+:|Constraints:|Follow up:|$)',body,re.S):
  node=ast.parse('f('+m[1].strip()+')',mode='eval').body
  assert isinstance(node,ast.Call)and not node.args and node.keywords
  args=[ast.literal_eval(k.value)for k in node.keywords];declared,_=json.JSONDecoder().raw_decode(m[2].strip());examples.append((args,declared))
 assert examples,q['questionFrontendId']
 return examples


def build(statements):
 rng=random.Random(2026102807);cases={pid:[]for pid in o.IDS};seen={pid:set()for pid in o.IDS}
 def add(pid,args,category):
  o.validate(pid,args);key=json.dumps(args,separators=(',',':'))
  if key in seen[pid]:return
  want=o.expected(pid,args)
  if pid==874:assert want<2**31
  if pid==945:assert want<2**31
  cases[pid].append({'args':args,'expected':want,'category':category});seen[pid].add(key)
 for pid in o.IDS:
  for args,declared in official_examples(Path(statements)/f'{pid}.json'):
   want=o.expected(pid,args);assert o.matches(pid,args,declared,want),(pid,args,declared,want)
   add(pid,args,'official-example-crosscheck')
 def balanced(pairs):
  def visit(s,left,right):
   if left==right==pairs:yield s
   if left<pairs:yield from visit(s+'(',left+1,right)
   if right<left:yield from visit(s+')',left,right+1)
  return visit('',0,0)
 for n in range(1,7):
  for s in balanced(n):add(856,[s],'exhaustive-balanced-up-to-six-pairs')
 for n in range(1,41):
  for q in range(1,n+1):add(858,[n,q],'exhaustive-small-positive-mirror-domain')
 for n in [*range(1,151),999,1000,10000,10**7,10**8]:add(866,[n],'prime-palindrome-values-and-large-search-gap')
 for k in range(30):
  for n in(2**k-1,2**k,2**k+1):
   if 1<=n<=10**9:add(869,[n],'power-and-neighbors')
 for n in range(1,8):
  for xs in product((0,1),repeat=n):
   add(926,[''.join(map(str,xs))],'exhaustive-binary-strings')
   add(930,[list(xs),n//2],'exhaustive-binary-subarrays')
   add(921,[''.join('('if v else')'for v in xs)],'exhaustive-parenthesis-edit-strings')
 for n in range(2,7):
  for xs in product((0,1,2),repeat=n):
   if n<=4:add(905,[list(xs)],'exhaustive-parity-inputs')
   if n%2==0 and n<=4:add(954,[list(xs)],'exhaustive-zero-and-positive-doubled-pairs')
 for cells in product((0,1),repeat=8):
  for n in(1,2,14,10**9):add(957,[list(cells),n],'all256states-four-day-count-strata')
 for n in range(2,10):
  for k in range(10):add(967,[n,k],'complete-n-digit-difference-parameter-domain')
 for n in range(1,21):add(935,[n],'knight-transition-geometry-small-lengths')
 for x in range(1,6):
  for y in range(1,6):
   for bound in(0,1,2,5,20,100):add(970,[x,y,bound],'small-power-bases-and-boundaries')
 def words(count,length,alphabet='abc'):return [''.join(rng.choices(alphabet,k=length))for _ in range(count)]
 for _ in range(64):
  target=rng.randint(8,30);n=rng.randint(1,7);positions=rng.sample(range(target),n);speeds=[rng.randint(1,20)for _ in positions];add(853,[target,positions,speeds],'independent-contiguous-fleet-enumeration')
  n=rng.randint(1,8);a=[rng.randrange(10)for _ in range(n)];b=[rng.randrange(10)for _ in range(n)];add(870,[a,b],'hall-deficiency-optimal-advantage')
  commands=rng.choices((-2,-1,1,2,3,9),k=rng.randint(1,12));obstacles=rng.sample([[x,y]for x in range(-3,4)for y in range(-3,4)],rng.randrange(8));add(874,[commands,obstacles],'segment-obstacle-reference')
  piles=[rng.randint(1,20)for _ in range(2*rng.randint(1,4))]
  if sum(piles)%2==0:piles[0]+=1
  add(877,[piles],'parity-strategy-domain')
  add(878,[rng.randint(1,1000),rng.randint(2,20),rng.randint(2,20)],'period-enumeration-magical-numbers')
  limit=rng.randint(1,20);add(881,[[rng.randint(1,limit)for _ in range(rng.randint(1,8))],limit],'exhaustive-minimum-pairing-reference')
  rows,cols=rng.randint(1,6),rng.randint(1,6);add(885,[rows,cols,rng.randrange(rows),rng.randrange(cols)],'closed-form-spiral-coordinate-rank')
  n=rng.randint(1,8);edges=rng.sample(list(combinations(range(1,n+1),2)),rng.randint(0,n*(n-1)//2));add(886,[n,list(map(list,edges))],'parity-double-DSU-constraints')
  a=[rng.randint(1,9)for _ in range(rng.randint(1,6))];b=[rng.randint(1,9)for _ in range(rng.randint(1,6))]
  try:o.validate(888,[a,b])
  except ValueError:pass
  else:add(888,[a,b],'all-valid-swap-pairs-reference')
  length=rng.randint(1,6);add(890,[words(rng.randint(1,8),length),words(1,length)[0]],'first-occurrence-pattern-equivalence')
  nums=[rng.randint(1,15)for _ in range(rng.randint(1,9))];add(891,[nums],'all-subsequence-widths')
  n=rng.randint(1,4);add(892,[[[rng.randrange(4)for _ in range(n)]for _ in range(n)]],'explicit-voxel-face-count')
  add(893,[words(rng.randint(1,9),rng.randint(1,7))],'parity-multiplicity-equivalence')
  add(898,[[rng.randrange(32)for _ in range(rng.randint(1,10))]],'all-subarray-ORs')
  add(907,[[rng.randint(1,20)for _ in range(rng.randint(1,10))]],'all-subarray-minima')
  n=rng.randint(2,5);board=[[-1]*n for _ in range(n)]
  for label in rng.sample(range(2,n*n),rng.randrange(min(7,n*n-2)+1)):
   band,c=divmod(label-1,n);r=n-1-band;c=c if band%2==0 else n-1-c;board[r][c]=rng.randint(1,n*n)
  add(909,[board],'dice-layer-reachability-reference')
  nums=[rng.randint(0,15)for _ in range(rng.randint(1,8))];add(910,[nums,rng.randrange(11)],'every-plus-minus-assignment')
  nums=[rng.randrange(12)for _ in range(rng.randint(1,9))]+[1000000];add(915,[nums],'all-valid-partition-splits')
  pool=sorted(set(words(12,rng.randint(1,5))));need=words(rng.randint(1,4),rng.randint(1,3));add(916,[pool,need],'per-word-submultiset-definition')
  nums=[rng.randint(-10,10)for _ in range(rng.randint(1,9))];add(918,[nums],'all-circular-intervals')
  nums=[rng.randrange(7)for _ in range(rng.randint(3,10))];add(923,[nums,rng.randrange(19)],'every-index-triple')
  n=rng.randint(1,5);add(931,[[[rng.randint(-10,10)for _ in range(n)]for _ in range(n)]],'recursive-path-reference')
  logs=[]
  for i in range(rng.randint(1,12)):
   content=' '.join(words(rng.randint(1,4),rng.randint(1,4)))if rng.randrange(2)else' '.join(str(rng.randrange(100))for _ in range(rng.randint(1,4)))
   logs.append(f'id{i} '+content)
  add(937,[logs],'lexicographic-contents-identifiers-and-digit-stability')
  points=rng.sample([[x,y]for x in range(6)for y in range(6)],rng.randint(1,12));add(939,[points],'column-intersection-minimal-rectangle')
  add(940,[words(1,rng.randint(1,10))[0]],'all-distinct-subsequence-strings')
  add(945,[[rng.randrange(7)for _ in range(rng.randint(1,6))]],'minimum-cost-injective-placement')
  stones=rng.sample([[x,y]for x in range(5)for y in range(5)],rng.randint(1,12));add(947,[stones],'coordinate-connected-components')
  add(948,[[rng.randrange(12)for _ in range(rng.randint(0,6))],rng.randrange(25)],'full-token-state-search')
  add(949,[[rng.randrange(10)for _ in range(4)]],'all1440clock-values')
  add(950,[rng.sample(range(1,1000),rng.randint(1,12))],'reverse-reveal-inversion')
  arr=[rng.randint(-6,6)for _ in range(2*rng.randint(1,4))];add(954,[arr],'perfect-doubling-matchings')
  n=rng.randint(2,8);values=rng.sample(range(100),n+1);arr=values[:n]+[values[-1]]*n;rng.shuffle(arr);add(961,[arr],'exact-multiplicity-definition')
  add(962,[[rng.randrange(20)for _ in range(rng.randint(2,12))]],'every-ordered-index-pair')
  dictionary=words(rng.randint(1,10),rng.randint(1,5),'aeioubcdfg');queries=words(rng.randint(1,10),rng.randint(1,5),'AEIOUbcdfg');queries+=dictionary[:2];add(966,[dictionary,queries],'tiered-first-match-case-and-vowels')
  points=[];distances=set()
  for p in rng.sample([[x,y]for x in range(-8,9)for y in range(-8,9)],20):
   distance=p[0]*p[0]+p[1]*p[1]
   if distance not in distances:points.append(p);distances.add(distance)
   if len(points)==rng.randint(3,8):break
  add(973,[points,rng.randint(1,len(points))],'unique-distance-point-multiset-and-alias')
  add(974,[[rng.randint(-10,10)for _ in range(rng.randint(1,12))],rng.randint(2,10)],'all-subarray-divisibility')
  add(978,[[rng.randint(0,15)for _ in range(rng.randint(1,12))]],'all-alternating-intervals')
  add(983,[sorted(rng.sample(range(1,80),rng.randint(1,15))),[rng.randint(1,30)for _ in range(3)]],'minimum-calendar-cover-path')
 # Legal domain maxima with independently derived exact expectations.
 add(853,[100000,list(range(100000)),[1]*100000],'maximum-car-count-no-catching')
 add(853,[100000,list(range(100000)),list(range(100000,0,-1))],'maximum-car-count-common-arrival')
 add(856,['('*25+')'*25],'maximum-depth')
 add(856,['()'*25],'maximum-length-flat')
 for p,q in((1000,1),(1000,1000),(999,998)):add(858,[p,q],'maximum-parameter-corners')
 add(869,[10**9],'maximum-input')
 add(870,[[10**9]*100000,[10**9-1]*100000],'maximum-score-and-input-count')
 add(874,[[1]*10000,[]],'maximum-command-count-valid-squared-distance')
 add(874,[[9],[[i,30000]for i in range(10000)]],'maximum-obstacle-count')
 add(877,[[1]*499+[2]],'maximum-pile-count-odd-total')
 add(878,[10**9,39999,40000],'maximum-n-and-near-coprime-denominators')
 add(881,[[1]*50000,2],'maximum-people-optimal-pairs')
 add(885,[100,100,99,0],'maximum-rectangle-and-corner-origin')
 add(886,[2000,[[i,j]for i in range(1,101)for j in range(101,201)]],'maximum-edge-count-bipartite')
 add(888,[[1]*10000,[1]*9998+[2,2]],'maximum-length-valid-swap')
 add(890,[['a'*20]*50,'z'*20],'maximum-pattern-and-word-count')
 add(891,[[1]*50000+[100000]*50000],'maximum-length-two-valued-width-count')
 add(892,[[[50]*50 for _ in range(50)]],'maximum-solid-cuboid')
 add(893,[['a'*20]*1000],'maximum-word-count-one-equivalence-class')
 add(898,[[10**9]*50000],'maximum-constant-subarray-OR')
 add(905,[list(range(5000))],'maximum-parity-array')
 for arr in([30000]*30000,list(range(1,30001)),list(range(30000,0,-1))):add(907,[arr],'maximum-subarray-minimum-count-and-values')
 add(909,[[[-1]*20 for _ in range(20)]],'maximum-board-without-jumps')
 add(910,[[10000]*10000,10000],'maximum-uniform-plus-minus-input')
 add(915,[[1000000]+[0]*99998+[1000000]],'maximum-late-partition')
 add(916,[['abcdefghij'],['a']*10000],'maximum-required-words-count')
 for value in(-30000,0,30000):add(918,[[value]*30000],'maximum-constant-circular-array')
 add(921,[')'*1000],'maximum-unmatched-parentheses')
 add(923,[[100]*3000,300],'maximum-triple-multiplicity')
 for s in('0'*100000,'10'*50000,'01'*50000):add(926,[s],'maximum-monotone-flip-domain')
 add(930,[[0]*30000,0],'maximum-zero-sum-subarray-count')
 for matrix in([[-100]*100 for _ in range(100)],[[0 if r==c else 100 for c in range(100)]for r in range(100)]):add(931,[matrix],'maximum-falling-path-domain')
 add(935,[5000],'maximum-knight-walk-length')
 add(937,[[f'id{i} '+('x'*94)for i in range(100)]],'maximum-log-count-and-length')
 add(939,[[[x,y]for x in range(20)for y in range(25)]],'500point-grid-minimum-area')
 for s in('a'*2000,'ab'*1000):add(940,[s],'maximum-distinct-subsequence-strings')
 add(945,[[0]*40000+list(range(40000,100000))],'maximum-input-count-valid-int32-minimum-cost')
 add(947,[[[0,y]for y in range(1000)]],'maximum-single-component-stones')
 add(948,[[0]*1000,0],'maximum-zero-cost-tokens')
 add(949,[[0,0,0,0]],'midnight-digits')
 add(950,[list(range(1000,0,-1))],'maximum-deck-reveal')
 for arr in([0]*30000,[1]*30000,[-1,-2]*15000):add(954,[arr],'maximum-doubled-pair-count')
 add(961,[list(range(5000))+[10000]*5000],'maximum-repeated-value-count')
 for arr in(list(range(50000)),list(range(50000,0,-1)),[0]*50000):add(962,[arr],'maximum-width-ramp-domain')
 add(966,[['KiTe']*5000,['keti']*5000],'maximum-first-vowel-match-count')
 add(970,[1,1,10**6],'unit-bases-and-maximum-bound')
 add(970,[2,3,10**6],'maximum-powerful-bound')
 add(973,[[[i,0]for i in range(10000)],10000],'maximum-returned-point-count')
 add(974,[[0]*30000,2],'maximum-divisible-subarray-count')
 for arr in([10**9]*40000,[0,10**9]*20000,list(range(40000))):add(978,[arr],'maximum-turbulence-domain')
 add(983,[list(range(1,366)),[1000,1000,1]],'complete-calendar-30day-minimal-cover')
 for pid in o.IDS:assert cases[pid],pid
 return cases
