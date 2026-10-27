"""Seven frozen public-spec references; no candidate code loading or execution."""
from collections import deque
from functools import lru_cache
from itertools import product, combinations_with_replacement, permutations
from math import comb
from pathlib import Path
import ast, hashlib, json, random, re
from . import imported_qualification as q
from .imported_clean_domains import integer, ints
SUPPORT_SHA256='af18c04686c549f87f68c245710097bff563f587d116697783fb01bb0ebe3b5b'
# Reviewed publication-only helper compatibility; no runtime or future-hash approval.
PUBLICATION_SUPPORT_SHA256='d32268c3b9bd780d533d59c58cb6cd983b2b4de583bd35171e8bf03cdfb138a5'
if hashlib.sha256(Path(q.__file__).read_bytes()).hexdigest() not in (SUPPORT_SHA256,PUBLICATION_SUPPORT_SHA256):
 raise RuntimeError('queue10 frozen q support drift; explicitly bind the historical snapshot')
IDS=(3164,3169,3170,3175,3179,3180,3181)
PARAMETERS={3164:('nums1','nums2','k'),3169:('days','meetings'),3170:('s',),3175:('skills','k'),3179:('n','k'),3180:('rewardValues',),3181:('rewardValues',)}
STATEMENT_SHA256={3164:'84e29e3c0e76c9aeb43269635e6cdc261f71e0029e0820a0258d757bea0cf884',3169:'60ac27af2ced4371e42f66a2b1a2e1777980344298476296c5a18df5868ef7e6',3170:'f3ab16aabc40a7da4d8449c35040e67f8c4521bc876df371edbfa4abe1c6121d',3175:'ad11cefc29967bc0bd599931bca7f9b6756a3dfb786eeed36fc043ec717f5b61',3179:'a47e3adc1bbe268a93b5f897953a9aa720a02ff4d6a6aeafca38526bf5be7702',3180:'463115c983ab6ad6b082638bd779a95ad592c1c6cc1f2c7286e85b314203b9ba',3181:'734ad043d7fe74304188e0ffa2a6114a251d3b690310a2595a6b3acc98472ddb'}
EXAMPLE_COUNT={3164:2,3169:3,3170:2,3175:2,3179:2,3180:2,3181:2}
CASE_COUNT={3164: 4670, 3169: 617, 3170: 1907, 3175: 3593, 3179: 685, 3180: 1200, 3181: 1199}
CASES_SHA256={3164: 'c22957a514c1e89921f695c106874a8cbd440e03cafb66e0163cf827cd2be4a0', 3169: 'da73728edcc4d824edc3ba3bdd0f4b4904c7a1397f9aac47a8eaa307df9bca17', 3170: 'ad985ecc1b39ac2693d84ec85bcf41437b8c5da073b40d2ca32d041d7b9e2b39', 3175: '072f7261f10dc8531e89a398c5c03c3cf2c394ac76e8aa5b3b74eff67c9acd3f', 3179: 'dab1fe82a3ba8b07d353f144f80dcb15233b356067e3f95252a6234097f0adb9', 3180: 'bd30749b68758782068a5c63a079b75938aeffcfa181ec856cf9b9db183df2eb', 3181: 'ab2040934f9f02bb5b06e4b45bb4189e22120a492a944ff6edb71f9fd3892c78'}
SEED_BASE=202610271001
MOD=1000000007
COMMON_CONTRACT=dict(exposure='Exposed deterministic development only, not fresh holdout or qualification.',interface='Official single-call positional parameters only; actual candidate exports/helpers unknown.',effects='Chosen strict typed-input preservation, no mutable return-input alias, IO or cross-call/global state; not claimed as official statement requirements.',numeric='Exact integer values, bool/float excluded; 3170 ASCII string return. Maximum3164 count1e10 and other outputs safely below2^53; candidate arithmetic not inspected.',limits='Unchanged q.MAX_FILE/MAX_PACKET/batches/LIMITS; expected values host-only.',native_gaps='No candidate execution, timing, resource, effect or complexity pass; no stateful/native binding inferred.')
CONTRACTS={3164:dict(domain='Both integer arrays length1..100000, values1..1000000;k1..1000.',result='Count all index pairs with nums1[i] divisible by nums2[j]*k; repeated values retain multiplicity.',reference='All cross-product pairs, bounded to20000 pair checks.',complexity='Candidate divisor/multiple enumeration O(n sqrt(V)+m) or O(V log(V)+n+m) with bounded storage; native caps remain unmeasured.'),3169:dict(domain='days1..1e9;1..100000 inclusive meeting intervals1<=start<=end<=days, overlaps/duplicates allowed.',result='Number of integer days uncovered by any interval.',reference='Explicit occupied-day set for days<=2000.',complexity='Candidate O(m log m) sort-and-union or justified equivalent; exact day count<=1e9.'),3170:dict(domain='ASCII lowercase/stars, length1..100000; every prefix permits all its stars to remove an earlier remaining letter.',result='Lexicographically least final string among leftmost-star operations removing any tied minimum earlier letter.',reference='Memoized enumeration of every eligible tied smallest deletion, length<=14.',complexity='Candidate O(26*n) or O(n log n), bounded linear storage; not recursive over100000 input positions.'),3175:dict(domain='Distinct skills length2..100000, values1..1e6;k1..1e9.',result='Original index of first player to win k consecutive front-of-queue games, loser moves to tail.',reference='Literal deque simulation for n<=12,k<=50.',complexity='Candidate O(n) or O(n log n), not O(k) for k1e9; original indices preserved.'),3179:dict(domain='n,k each1..1000.',result='Last element after k simultaneous inclusive-prefix updates of n initial ones, modulo1e9+7.',reference='Literal fresh rows for n,k<=40; exact C(n+k-1,k) modulo M for larger fixtures.',complexity='Candidate O(n*k) with O(n) or justified bounded equivalent; safe modular arithmetic must be separately inspected.'),3180:dict(domain='1..2000 reward values, each1..2000.',result='Maximum reachable total starting0, each selected unused index must have value strictly greater than current total.',reference='All used-index-mask operation states, length<=12.',complexity='Candidate bounded pseudopolynomial in maximum value<=2000, or bitset equivalent; result<2*maxreward.'),3181:dict(domain='1..50000 reward values, each1..50000.',result='Same strict unused-index operation semantics as3180, separate larger domain.',reference='All used-index-mask operation states, length<=12; shared semantics is not independent novelty.',complexity='Candidate ordered reachable-total bitset or justified scalable equivalent; naive n*V nested loops may exceed unchanged native caps. Result<=99999.')}
OMITTED_MAXIMUM_SHAPES={3164:'Arbitrary two100000-element arrays of maximum-width values exceed MAX_PACKET1100000. Full counts with compact values and maximum numeric values at shorter lengths retained; arbitrary full cross-products not exhausted.',3169:'100000 intervals of10-digit endpoints exceed MAX_PACKET1100000. Full interval count compact duplicates and high numeric endpoints at smaller counts retained; arbitrary full unions not exhausted.',3170:'All valid small strings over ab*, seeded short strings, and selected100000-character analytic families only; full alphabet/shape domain not exhausted.',3175:'Complete permutations through6 players with selected k, seeded small queues and selected100000-player/k1e9 analytic families. Arbitrary maximum skill orders omitted.',3179:'Small grid of scalars and selected exact binomial maximum/boundary cases; not all1000000 scalar pairs.',3180:'Complete small sequences and selected maximum count/value certificates; arbitrary2000-index states not enumerated.',3181:'Complete small sequences and selected50000 count/value certificates; arbitrary full state spaces omitted, no native bitset cost measured.'}

def validate(pid,args):
 if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):raise ValueError('unsupported identity or ordered args')
 if pid==3164:
  a,b,k=args;valid=ints(a,1,1000000,1,100000) and ints(b,1,1000000,1,100000) and integer(k,1,1000)
 elif pid==3169:
  days,meetings=args;valid=integer(days,1,10**9) and type(meetings) is list and 1<=len(meetings)<=100000 and all(type(x) is list and len(x)==2 and integer(x[0],1,days) and integer(x[1],x[0],days) for x in meetings)
 elif pid==3170:
  s=args[0];valid=type(s) is str and 1<=len(s)<=100000 and all(c in 'abcdefghijklmnopqrstuvwxyz*' for c in s)
  if valid:
   count=0
   for c in s:
    count+=-1 if c=='*' else 1
    if count<0:valid=False;break
 elif pid==3175:
  a,k=args;valid=ints(a,1,1000000,2,100000) and len(set(a))==len(a) and integer(k,1,10**9)
 elif pid==3179:valid=all(integer(x,1,1000) for x in args)
 else:valid=ints(args[0],1,2000 if pid==3180 else 50000,1,2000 if pid==3180 else 50000)
 if not valid:raise ValueError('outside complete pinned official domain')

def expected(pid,args):
 validate(pid,args)
 if pid==3164:
  a,b,k=args
  if len(a)*len(b)>20000:raise ValueError('all index-pair reference budget')
  return sum(x%(y*k)==0 for x in a for y in b)
 if pid==3169:
  days,meetings=args
  if days>2000:raise ValueError('literal occupied-day reference budget')
  busy=set()
  for a,b in meetings:busy.update(range(a,b+1))
  return days-len(busy)
 if pid==3170:
  s=args[0]
  if len(s)>14:raise ValueError('all tie-choice reference budget')
  @lru_cache(None)
  def visit(t):
   star=t.find('*')
   if star<0:return t
   least=min(t[:star]);return min(visit(t[:i]+t[i+1:star]+t[star+1:]) for i in range(star) if t[i]==least)
  return visit(s)
 if pid==3175:
  a,k=args
  if len(a)>12 or k>50:raise ValueError('literal queue reference budget')
  queue=deque(range(len(a)));last=None;wins=0
  while True:
   i=queue.popleft();j=queue.popleft();winner,loser=(i,j) if a[i]>a[j] else (j,i)
   wins=wins+1 if winner==last else 1;last=winner
   if wins==k:return winner
   queue.appendleft(winner);queue.append(loser)
 if pid==3179:
  n,k=args
  if max(n,k)>40:raise ValueError('literal simultaneous-row reference budget')
  row=[1]*n
  for _ in range(k):row=[sum(row[:i+1])%MOD for i in range(n)]
  return row[-1]
 a=args[0]
 if len(a)>12:raise ValueError('all unused-index state reference budget')
 @lru_cache(None)
 def visit(mask,total):
  return max([total]+[visit(mask|(1<<i),total+x) for i,x in enumerate(a) if not mask>>i&1 and x>total])
 return visit(0,0)

def public_examples(pid,raw):
 if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw)!=STATEMENT_SHA256[pid]:raise ValueError('exact pinned official statement required')
 cases=[]
 for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)',raw.decode(),re.S):
  call=ast.parse('f('+match[1].strip()+')',mode='eval').body
  if not isinstance(call,ast.Call) or call.args or tuple(x.arg for x in call.keywords)!=PARAMETERS[pid]:raise ValueError('ordered public parameters differ')
  args=[ast.literal_eval(x.value) for x in call.keywords];answer=json.loads(match[2]);assert q.exact(expected(pid,args),answer)
  cases.append(dict(args=args,expected=answer,compare='return'))
 if len(cases)!=EXAMPLE_COUNT[pid]:raise ValueError('complete public examples required')
 return cases

def _generate_cases(pid,statement):
 cases=[];cats=[];seen={};rng=random.Random(SEED_BASE+pid);sentinel=object()
 def add(args,category,answer=sentinel):
  validate(pid,args);answer=expected(pid,args) if answer is sentinel else answer
  if pid==3170:
   if type(answer) is not str or any(c not in 'abcdefghijklmnopqrstuvwxyz' for c in answer):raise ValueError('invalid string expectation')
  elif not integer(answer,0,{3164:10**10,3169:10**9,3175:99999,3179:MOD-1,3180:3999,3181:99999}[pid]):raise ValueError('invalid integer expectation')
  key=q.encoded(args)
  if key in seen:assert q.exact(seen[key],answer);return
  seen[key]=answer;cases.append(dict(args=args,expected=answer,compare='return'));cats.append(category)
 for c in public_examples(pid,statement):add(c['args'],'pinned_public_example',c['expected'])
 if pid==3164:
  arrays=[list(a) for n in range(1,4) for a in product((1,2,4),repeat=n)]
  for a in arrays:
   for b in arrays:
    for k in (1,2,3):add([a,b,k],'exhaustive_small_index_pairs')
  for _ in range(100):add([[rng.choice((1,2,3,6,999999,1000000)) for _ in range(rng.randrange(1,21))],[rng.choice((1,2,3,6,999999,1000000)) for _ in range(rng.randrange(1,21))],rng.choice((1,2,3,999,1000))],'seeded_divisibility_numeric_edges')
  for a,b,k,answer in [([1]*100000,[1]*100000,1,10**10),([2]*100000,[1]*100000,2,10**10),([1]*100000,[1]*100000,1000,0),([1000000]*50000,[1000]*50000,1000,2500000000),([999999]*30000,[1000000]*30000,1000,0)]:add([a,b,k],'analytic_large_repeated_divisibility',answer)
 elif pid==3169:
  for days in range(1,7):
   intervals=[(a,b) for a in range(1,days+1) for b in range(a,days+1)]
   for count in (1,2):
    for rows in combinations_with_replacement(intervals,count):add([days,[list(x) for x in rows]],'exhaustive_small_inclusive_unions')
  for _ in range(120):
   days=rng.randrange(1,101);rows=[]
   for _ in range(rng.randrange(1,15)):
    a=rng.randrange(1,days+1);rows.append([a,rng.randrange(a,days+1)])
   rng.shuffle(rows);add([days,rows],'seeded_overlapping_unsorted_meetings')
  add([10**9,[[1,1]]*100000],'analytic_maximum_count_duplicate_day',10**9-1)
  add([10**9,[[1,10**9]]*40000],'analytic_large_full_span_duplicates',0)
  add([10**9,[[10**9,10**9]]*30000],'analytic_large_maximum_endpoint_duplicates',10**9-1)
  add([10**9,[[i,i] for i in range(1,50001)]],'analytic_distinct_singletons',10**9-50000)
  add([10**9,[[1,499999999],[500000001,10**9]]],'analytic_one_internal_gap',1)
  add([10**9,[[1,500000000],[500000000,10**9]]],'analytic_shared_inclusive_endpoint',0)
 elif pid==3170:
  for n in range(1,8):
   for chars in product('ab*',repeat=n):
    s=''.join(chars);balance=0;valid=True
    for c in s:
     balance+=-1 if c=='*' else 1
     if balance<0:valid=False;break
    if valid:add([s],'exhaustive_small_valid_star_strings')
  for _ in range(100):
   chars=[];balance=0
   for _ in range(rng.randrange(8,15)):
    c=rng.choice('abcz*' if balance else 'abcz');chars.append(c);balance+=-1 if c=='*' else 1
   add([''.join(chars)],'seeded_tied_deletion_choices')
  for s,answer in [('z'*100000,'z'*100000),('a'*50000+'*'*50000,''),('a*'*50000,''),('a'*75000+'*'*25000,'a'*50000),('ba'*25000+'*'*50000,''),('abcdefghijklmnopqrstuvwxyz'*3846+'abcd','abcdefghijklmnopqrstuvwxyz'*3846+'abcd')]:add([s],'analytic_maximum_string_shape',answer)
 elif pid==3175:
  for n in range(2,7):
   for a in permutations(range(1,n+1)):
    for k in (1,2,n,n+1):add([list(a),k],'exhaustive_small_skill_orders')
  for _ in range(100):add([rng.sample(range(1,1000001),rng.randrange(2,13)),rng.randrange(1,51)],'seeded_literal_queue_games')
  for a,k,answer in [(list(range(1,100001)),10**9,99999),(list(range(100000,0,-1)),10**9,0),(list(range(1,100001)),1,1),([1000000]+list(range(1,100000)),1,0),(list(range(1,50001))+[1000000]+list(range(50001,100000)),10**9,50000)]:add([a,k],'analytic_maximum_players_and_streak',answer)
 elif pid==3179:
  for n in range(1,26):
   for k in range(1,26):add([n,k],'exhaustive_small_simultaneous_updates')
  for _ in range(80):add([rng.randrange(1,41),rng.randrange(1,41)],'seeded_literal_update_rows')
  for n,k in [(1,1000),(1000,1),(1000,1000),(999,1000),(1000,999),(500,1000),(1000,500),(17,997),(997,17)]:add([n,k],'analytic_binomial_coefficient',comb(n+k-1,k)%MOD)
 else:
  for n in range(1,7):
   for a in product((1,2,4),repeat=n):add([list(a)],'exhaustive_small_unused_index_states')
  for _ in range(100):add([[rng.randrange(1,31) for _ in range(rng.randrange(1,13))]],'seeded_reward_operation_states')
  top=2000 if pid==3180 else 50000;count=top
  for a,answer in [([1]*count,1),([top]*count,top),([top-1]*(count//2)+[top]*(count-count//2),2*top-1),(list(range(1,top+1)),2*top-1),([1]*(count-1)+[top],top+1)]:add([a],'analytic_maximum_reward_count_value',answer)
  powers=[1<<i for i in range(top.bit_length()) if 1<<i<=top];add([powers],'analytic_superincreasing_powers',sum(powers))
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
