"""Queue06 subset02 public-spec references. No candidate loading or execution."""
from collections import Counter,deque
from functools import lru_cache
from itertools import combinations,product
import ast,json,random,re
from . import imported_qualification as q
from .imported_clean_domains import integer,ints,text
IDS=(2771,2786,2789,2791,2798,2800)
PARAMETERS={2771:('nums1','nums2'),2786:('nums','x'),2789:('nums',),2791:('parent','s'),2798:('hours','target'),2800:('a','b','c')}
STATEMENT_SHA256={2771:'cc9a1769cfab778b654a57473b6c078e96b25a3c9023c553810f0708aee19959',2786:'9f6649dc5d5fcf13a264ad1dea098b4ab9ae3925cac1302b58b2e91dda15dcd0',2789:'8dc3f771a572163719ed432d8bccf7cbfcd1d06e7ac67ce81a689251f92e5b7b',2791:'1a1a57d9d1bd1c1109a80ef74b54e4728e365a3d42a72655a7fc98461f9c202b',2798:'b327a2e9eb686d291600c7aa6f0f395ab0e6dc75b83c6f016ab132bb1905f00c',2800:'efba90f4862b3c6aa5519804c10300859671ad4aa3a4e3c9ac77c5f331612a90'}
EXAMPLE_COUNT={2771:3,2786:2,2789:2,2791:2,2798:2,2800:2}
CASE_COUNT={2771: 409, 2786: 1145, 2789: 1168, 2791: 970, 2798: 678, 2800: 293}
CASES_SHA256={2771: 'f3df3111252df46e7ab0ef6367e93986e666f82ee0ee74f8d4c0cc307fb55ad7', 2786: '4ae42b359cb26c17ff99777c735dc3486d758cde54d242d3b0d965189b8eafd4', 2789: 'ff97c58ae990033722e3825731902076418a5d2b849c877e92dc74999d8f9151', 2791: '946301fda9a75bbe8e7653c7433477586f590775bc48f0850dc35d40de750e55', 2798: 'e5e64d92e8d0bb01fb354410b5ef32c5d2247479da7bc7268e66da735082e99a', 2800: 'e13ec7c279f97d673275fb8b4f8a4182add65967756fe0893e6e181aa5509c67'}
SEED_BASE=202610272003
OMITTED_MAXIMUM_SHAPES={2771:'All-choice enumeration is bounded to12positions. Two length100000 arrays of10-digit values exceed the unchanged packet cap; equal maximum values use40000positions. Maximum length uses small values and an isolated maximum. No arbitrary full-array proof.',2786:'Subsequence enumeration is bounded to14positions; maximum length/value and parity-block shapes use direct analytic optima. Arbitrary maximum paths omitted.',2789:'Reachable-state enumeration is bounded to10positions; maximum equal,decreasing and fixed-barrier shapes have explicit merge proofs.',2791:'Explicit all-pair path counting is bounded to16nodes. Maximum chains,stars and26-label stars have combinatorial answers, not exhaustive maximum-tree validation. Parent labels need not precede their children.',2798:'Small exhaustive counts and selected maximum50-employee shapes; not every possible hours population.',2800:'Placement enumeration is bounded to total length18. Length100 strings use containment and nonoverlap certificates; arbitrary maximum texts omitted.'}

def _tree(parent):
 if type(parent) is not list or not 1<=len(parent)<=100000 or type(parent[0]) is not int or parent[0]!=-1:return False
 n=len(parent);groups=list(range(n))
 def root(x):
  while groups[x]!=x:groups[x]=groups[groups[x]];x=groups[x]
  return x
 for i,p in enumerate(parent[1:],1):
  if not integer(p,0,n-1) or p==i:return False
  a,b=root(i),root(p)
  if a==b:return False
  groups[a]=b
 return True

def validate(pid,args):
 if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):raise ValueError('unsupported identity or ordered args')
 if pid==2771:valid=ints(args[0],1,10**9,1,100000) and ints(args[1],1,10**9,len(args[0]),len(args[0]))
 elif pid==2786:valid=ints(args[0],1,10**6,2,100000) and integer(args[1],1,10**6)
 elif pid==2789:valid=ints(args[0],1,10**6,1,100000)
 elif pid==2791:valid=_tree(args[0]) and text(args[1],minimum=len(args[0]),maximum=len(args[0]))
 elif pid==2798:valid=ints(args[0],0,100000,1,50) and integer(args[1],0,100000)
 else:valid=all(text(s,minimum=1,maximum=100) for s in args)
 if not valid:raise ValueError('outside complete pinned official domain')

def _placements(words):
 if sum(map(len,words))>18:raise ValueError('literal placement enumeration budget')
 for length in range(max(map(len,words)),sum(map(len,words))+1):
  found=set()
  for anchor in range(3):
   rest=[i for i in range(3) if i!=anchor]
   for starts in product(*(range(length-len(words[i])+1) for i in rest)):
    offsets=[0]*3
    for i,start in zip(rest,starts):offsets[i]=start
    if max(offsets[i]+len(words[i]) for i in range(3))!=length:continue
    cells=[None]*length;good=True
    for word,start in zip(words,offsets):
     for j,char in enumerate(word,start):
      if cells[j] is not None and cells[j]!=char:good=False;break
      cells[j]=char
     if not good:break
    if good and None not in cells:found.add(''.join(cells))
  if found:return min(found)
 raise AssertionError('concatenation must be feasible')

def expected(pid,args):
 validate(pid,args)
 if pid==2771:
  a,b=args;n=len(a)
  if n>12:raise ValueError('selection enumeration budget')
  answer=1
  for mask in range(1<<n):
   values=[b[i] if mask>>i&1 else a[i] for i in range(n)];run=1
   for i in range(1,n):run=run+1 if values[i]>=values[i-1] else 1;answer=max(answer,run)
  return answer
 if pid==2786:
  a,x=args;n=len(a)
  if n>14:raise ValueError('subsequence enumeration budget')
  answer=a[0]
  for mask in range(1<<(n-1)):
   chosen=[0]+[i for i in range(1,n) if mask>>(i-1)&1]
   score=sum(a[i] for i in chosen)-x*sum(a[u]%2!=a[v]%2 for u,v in zip(chosen,chosen[1:]));answer=max(answer,score)
  return answer
 if pid==2789:
  a=args[0]
  if len(a)>10:raise ValueError('reachable tuple enumeration budget')
  @lru_cache(None)
  def visit(values):
   best=max(values)
   for i in range(len(values)-1):
    if values[i]<=values[i+1]:best=max(best,visit(values[:i]+(values[i]+values[i+1],)+values[i+2:]))
   return best
  return visit(tuple(a))
 if pid==2791:
  parent,s=args;n=len(parent)
  if n>16:raise ValueError('all-pair literal path budget')
  graph=[[] for _ in range(n)]
  for i,p in enumerate(parent[1:],1):graph[i].append((p,s[i]));graph[p].append((i,s[i]))
  answer=0
  for start in range(n):
   prev={start:(None,None)};todo=deque([start])
   while todo:
    u=todo.popleft()
    for v,char in graph[u]:
     if v not in prev:prev[v]=(u,char);todo.append(v)
   for end in range(start+1,n):
    counts=Counter();v=end
    while v!=start:v,char0=prev[v];counts[char0]+=1
    answer+=sum(c%2 for c in counts.values())<=1
  return answer
 if pid==2798:return len([i for i,hours in enumerate(args[0]) if hours>=args[1]])
 return _placements(args)

def valid_answer(pid,args,value):
 if pid==2800:return text(value,minimum=max(map(len,args)),maximum=sum(map(len,args))) and all(s in value for s in args)
 high={2771:len(args[0]),2786:10**11,2789:10**11,2791:len(args[0])*(len(args[0])-1)//2,2798:len(args[0])}[pid]
 return integer(value,0 if pid in (2791,2798) else 1,high)

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
  if not valid_answer(pid,args,answer):raise ValueError('invalid typed expected answer')
  key=q.encoded(args)
  if key in seen:assert q.exact(seen[key],answer);return
  seen[key]=answer;cases.append({'args':args,'expected':answer,'compare':'return'});cats.append(category)
 for c in public_examples(pid,statement):add(c['args'],'pinned_public_example',c['expected'])
 if pid==2771:
  for n in range(1,5):
   for entries in product((1,2),repeat=2*n):add([list(entries[:n]),list(entries[n:])],'exhaustive_complete_selection_vectors')
  for _ in range(70):
   n=rng.randrange(1,11);add([[rng.choice((1,2,3,10**9)) for _ in range(n)] for _ in range(2)],'seeded_complete_selection_vectors')
  add([[1,2]*50000,[2,1]*50000],'analytic_maximum_switching_choices',100000)
  add([[1]*100000,[10**9]+[1]*99999],'analytic_maximum_length_isolated_high',100000)
  add([[10**9]*40000,[10**9]*40000],'analytic_large_equal_maximum_values',40000)
 elif pid==2786:
  for n in range(2,6):
   for a in product((1,2,3),repeat=n):
    for x in (1,3,8):add([list(a),x],'exhaustive_visit_subsequences')
  for _ in range(60):add([[rng.choice((1,2,999999,1000000)) for _ in range(rng.randrange(6,13))],rng.choice((1,2,999999,1000000))],'seeded_visit_subsequences_extremes')
  add([[1000000]*100000,1000000],'analytic_maximum_same_parity_sum',10**11)
  add([[1,2]*50000,1000000],'analytic_switch_penalty_exceeds_total_reward',50000)
  add([[1]*50000+[2]*50000,1],'analytic_two_positive_parity_blocks',149999)
 elif pid==2789:
  for n in range(1,7):
   for a in product((1,2,4),repeat=n):add([list(a)],'exhaustive_reachable_merge_states')
  for _ in range(70):add([[rng.choice((1,2,3,999999,1000000)) for _ in range(rng.randrange(7,10))]],'seeded_merge_state_numeric_edges')
  add([[1000000]*100000],'analytic_maximum_equal_values_merge_all',10**11)
  add([list(range(100000,0,-1))],'analytic_maximum_strict_descent_no_merge',100000)
  add([[1]*100000],'analytic_maximum_ones_merge_all',100000)
  add([[1000000]+[1]*99999],'analytic_unmergeable_left_barrier',1000000)
 elif pid==2791:
  for n in range(1,6):
   for parents in product(*(range(i) for i in range(1,n))):
    for chars in product('ab',repeat=n-1):
     for rootchar in 'az':add([[-1]+list(parents),rootchar+''.join(chars)],'exhaustive_small_parent_trees_literal_paths')
  for _ in range(80):
   n=rng.randrange(6,13);permutation=[0]+rng.sample(range(1,n),n-1);parent=[-1]*n;letters=['z']*n
   for i in range(1,n):parent[permutation[i]]=permutation[rng.randrange(i)];letters[permutation[i]]=rng.choice('abcz')
   add([parent,''.join(letters)],'seeded_non_topological_labels_literal_paths')
  n=100000;allpairs=n*(n-1)//2
  add([[-1]+list(range(n-1)),'a'*n],'analytic_maximum_chain_single_letter',allpairs)
  add([[-1]+[0]*(n-1),'z'*n],'analytic_maximum_star_single_letter',allpairs)
  labels=('abcdefghijklmnopqrstuvwxyz'*3847)[:n-1];counts=Counter(labels)
  add([[-1]+[0]*(n-1),'q'+labels],'analytic_maximum_star_all_twenty_six_letters',n-1+sum(k*(k-1)//2 for k in counts.values()))
 elif pid==2798:
  for n in range(1,5):
   for a in product((0,1,3),repeat=n):
    for target in range(5):add([list(a),target],'exhaustive_small_threshold_inclusion')
  for _ in range(70):add([[rng.choice((0,1,99999,100000)) for _ in range(rng.randrange(1,51))],rng.choice((0,1,99999,100000))],'seeded_threshold_boundaries')
  for a in ([0]*50,[100000]*50,[99999,100000]*25):
   for target in (0,100000):add([a,target],'maximum_employee_count_exact_threshold')
 else:
  words=('a','b','aa','ab','ba','bb')
  for a,b,c in product(words,repeat=3):add([a,b,c],'exhaustive_literal_offset_placements')
  for _ in range(70):add([''.join(rng.choices('abc',k=rng.randrange(1,5))) for _ in range(3)],'seeded_literal_offset_placements')
  add(['a'*100]*3,'analytic_maximum_identical_containment','a'*100)
  add(['a'*100,'b'*100,'c'*100],'analytic_maximum_disjoint_alphabet_blocks','a'*100+'b'*100+'c'*100)
  add(['a'*100,'a'*99,'a'],'analytic_maximum_nested_containment','a'*100)
  add(['ab'*50,'ab'*49,'b'],'analytic_maximum_periodic_containment','ab'*50)
  add(['z'*100,'a'*100,'z'*99],'analytic_maximum_two_nonoverlap_blocks_lex_tie','a'*100+'z'*100)
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
