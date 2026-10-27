"""Five source-blind public-definition oracles; no candidate access/execution."""
from collections import deque
from functools import lru_cache
import ast
import heapq
from itertools import product
import json
from math import comb, gcd, prod
import random
import re
from . import imported_qualification as q

IDS=(2585,2654,2662,2698,2712)
PARAMETERS={2585:('target','types'),2654:('nums',),2662:('start','target','specialRoads'),2698:('n',),2712:('s',)}
TITLES={2585:'Number of Ways to Earn Points',2654:'Minimum Number of Operations to Make All Array Elements Equal to 1',2662:'Minimum Cost of a Path With Special Roads',2698:'Find the Punishment Number of an Integer',2712:'Minimum Cost to Make All Characters Equal'}
SLUGS={2585:'number-of-ways-to-earn-points',2654:'minimum-number-of-operations-to-make-all-array-elements-equal-to-1',2662:'minimum-cost-of-a-path-with-special-roads',2698:'find-the-punishment-number-of-an-integer',2712:'minimum-cost-to-make-all-characters-equal'}
STATEMENT_SHA256={2585:'fe38a80f98e3d88be276a1b454794ad0fb1d7fa507617273f2fabaa6069f072d',2654:'20e800d553bf1e250a7aaf843537f3b930b5e7a29a2ad3cefaef5294b47c35db',2662:'8aaccd625a57eea8e05784bcb49681e43029f43288f94b8eb3cb8ade2ac4e194',2698:'81405fc39dd74099a078a8ede3f641ea18277953d54eee2f6cdd2b4dfbd49af1',2712:'c925ccad696554dfecd81e2595db657f683a783ce8188f50487f3bfb36184c70'}
EXAMPLE_COUNT={2585:3,2654:2,2662:3,2698:2,2712:2}
MOD=1000000007
CONTRACTS={
2585:dict(domain='target1..1000;1..50 ordered types [count,marks], both1..50; repeated type rows allowed and distinct types remain distinct.',result='Count bounded per-type quantity vectors whose score equals target, modulo1000000007; no within-type binomial multiplicity.',reference='Enumerate the Cartesian product of feasible per-type quantities when it has at most200000 vectors.',complexity='Candidate target O(type_count*target*max_count) or better with bounded storage; modulo arithmetic must be safe.'),
2654:dict(domain='2..50 positive exact integer values1..1000000.',result='Minimum adjacent-gcd replacement operations to make all entries1, or-1 when impossible.',reference='Breadth-first search of actual array states for length<=5 and values<=30; either endpoint of each adjacent pair can be replaced.',complexity='Candidate O(n^2 log(max_value)) or justified bounded equivalent; full-domain BFS is not an assumed candidate method.'),
2662:dict(domain='start/target coordinate pairs1..100000 with start<=target componentwise;1..200 directed roads, endpoints inside rectangle and costs1..100000; duplicates/self-roads allowed.',result='Exact minimum travel cost, with Manhattan walking and optional repeatable directed roads.',reference='Dijkstra on every integer grid point inside the start-target rectangle, area<=225, walking unit grid edges and using the literal directed roads.',complexity='Candidate polynomial in road count (e.g O(k^2 log k)), not full numeric-coordinate area; no timing claim.'),
2698:dict(domain='Exact integer n1..1000.',result='Sum i^2 for1<=i<=n when some contiguous decimal cut partition of i^2 has integer-piece sum i; zero-valued pieces permitted.',reference='Enumerate every cut mask of every square through1000^2; at most64 masks per square. Complete scalar domain.',complexity='Candidate bounded digit-partition enumeration or justified equivalent; finite full scalar-domain evidence is not source qualification.'),
2712:dict(domain='ASCII binary string length1..100000.',result='Minimum cost to make all bits equal using prefix/suffix inversions, each charged its length.',reference='For length<=10, multi-source Dijkstra over all binary strings, with every prefix/suffix inversion as a weighted edge.',complexity='Candidate O(n) time or comparably bounded full-length method; maximum answer2500000000 exceeds signed32bit.'),
}
COMMON_CONTRACT=dict(exposure='Exposed development, never fresh holdout confirmation.',interface='Ordered positional single-call values from official examples; actual candidate name/export/adapter is unknown.',effects='Conservative service envelope: unchanged typed inputs and identities, no mutable return/input aliases, no cross-call state or external IO. This is not an assertion that official challenge mutation is forbidden.',numeric='Exact integer results, bool rejected as integer input. Score counts require modulo; all output bounds fit exact JavaScript Number when computed correctly. No coercion or 32-bit narrowing.',helpers='All candidate helpers and dependencies remain uninspected and must be charged later.',expected_values='Host only; q.packet and q.batches unchanged.',limits='Unchanged q.MAX_FILE, q.MAX_PACKET and q.LIMITS.')
OMITTED_MAXIMUM_SHAPES={2585:'Maximum target, type count and count/mark values covered by independent bounded-composition identities. Arbitrary50-type Cartesian products are not enumerated.',2654:'Full length50 and value1000000 appear in analytic GCD-invariant and first-one families; BFS is bounded to5entries<=30, not every maximal array.',2662:'Maximum coordinates and200roads covered by geometric families. Arbitrary maximum200-road geometry is not expanded into its enormous coordinate grid.',2698:'Every normative n1..1000 is included; this still does not qualify an unseen source.',2712:'All binary strings through length8 plus selected9/10-bit strings and analytic length100000 forms; not every maximal string is enumerated.'}

def integer(x,a,b):return type(x) is int and a<=x<=b
def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):raise ValueError('unsupported identity or ordered argument shape')
    if pid==2585:
        target,types=args
        ok=integer(target,1,1000) and type(types) is list and 1<=len(types)<=50 and all(type(r) is list and len(r)==2 and integer(r[0],1,50) and integer(r[1],1,50) for r in types)
    elif pid==2654:
        a=args[0];ok=type(a) is list and 2<=len(a)<=50 and all(integer(x,1,1000000) for x in a)
    elif pid==2662:
        start,target,roads=args
        ok=all(type(p) is list and len(p)==2 and all(integer(x,1,100000) for x in p) for p in (start,target))
        if ok:ok=start[0]<=target[0] and start[1]<=target[1] and type(roads) is list and 1<=len(roads)<=200 and all(type(r) is list and len(r)==5 and all(integer(r[i],start[i%2],target[i%2]) for i in range(4)) and integer(r[4],1,100000) for r in roads)
    elif pid==2698:ok=integer(args[0],1,1000)
    else:ok=type(args[0]) is str and 1<=len(args[0])<=100000 and set(args[0])<=set('01')
    if not ok:raise ValueError('outside pinned full statement domain')

def _gcd_bfs(nums):
    initial=tuple(nums);goal=(1,)*len(nums);queue=deque([(initial,0)]);seen={initial}
    while queue:
        state,distance=queue.popleft()
        if state==goal:return distance
        for i in range(len(state)-1):
            value=gcd(state[i],state[i+1])
            for index in (i,i+1):
                nxt=state[:index]+(value,)+state[index+1:]
                if nxt not in seen:seen.add(nxt);queue.append((nxt,distance+1))
    return -1

def _grid_roads(start,target,roads):
    outgoing={}
    for x,y,u,v,cost in roads:outgoing.setdefault((x,y),[]).append((u,v,cost))
    origin=tuple(start);goal=tuple(target);distance={origin:0};heap=[(0,*origin)]
    while heap:
        cost,x,y=heapq.heappop(heap)
        if distance[x,y]!=cost:continue
        if (x,y)==goal:return cost
        edges=outgoing.get((x,y),[])+[(x+1,y,1),(x-1,y,1),(x,y+1,1),(x,y-1,1)]
        for u,v,price in edges:
            if not(start[0]<=u<=target[0] and start[1]<=v<=target[1]):continue
            nxt=cost+price
            if nxt<distance.get((u,v),10**12):distance[u,v]=nxt;heapq.heappush(heap,(nxt,u,v))
    raise AssertionError('walking route must exist')

@lru_cache(maxsize=1)
def punishment_prefixes():
    sums=[0]
    for value in range(1,1001):
        digits=str(value*value);qualifies=False
        for mask in range(1<<(len(digits)-1)):
            subtotal=0;start=0
            for end in range(1,len(digits)+1):
                if end==len(digits) or mask>>(end-1)&1:subtotal+=int(digits[start:end]);start=end
            if subtotal==value:qualifies=True;break
        sums.append(sums[-1]+(value*value if qualifies else 0))
    return tuple(sums)

@lru_cache(maxsize=10)
def inversion_distances(n):
    if not integer(n,1,10):raise ValueError('bounded weighted-state reference budget')
    allbits=(1<<n)-1;dist=[10**9]*(1<<n);dist[0]=dist[allbits]=0;heap=[(0,0),(0,allbits)]
    operations=[((1<<width)-1,width) for width in range(1,n+1)]
    operations += [(allbits^((1<<(n-width))-1),width) for width in range(1,n+1)]
    while heap:
        cost,state=heapq.heappop(heap)
        if cost!=dist[state]:continue
        for mask,price in operations:
            nxt=state^mask
            if cost+price<dist[nxt]:dist[nxt]=cost+price;heapq.heappush(heap,(cost+price,nxt))
    return tuple(dist)

def expected(pid,args):
    validate(pid,args)
    if pid==2585:
        target,types=args;choices=[range(min(count,target//marks)+1) for count,marks in types]
        if prod(map(len,choices))>200000:raise ValueError('bounded quantity enumeration budget')
        return sum(sum(amount*marks for amount,(_,marks) in zip(values,types))==target for values in product(*choices))%MOD
    if pid==2654:
        if len(args[0])>5 or max(args[0])>30:raise ValueError('bounded actual-state BFS budget')
        return _gcd_bfs(args[0])
    if pid==2662:
        if (args[1][0]-args[0][0]+1)*(args[1][1]-args[0][1]+1)>225:raise ValueError('bounded explicit-coordinate reference budget')
        return _grid_roads(*args)
    if pid==2698:return punishment_prefixes()[args[0]]
    if len(args[0])>10:raise ValueError('bounded weighted-state reference budget')
    return inversion_distances(len(args[0]))[int(args[0],2)]

def public_examples(pid,raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw)!=STATEMENT_SHA256[pid]:raise ValueError('exact pinned official definition bytes required')
    text=json.loads(raw)
    if type(text) is not str or f'{pid}. {TITLES[pid]}' not in text or f'https://leetcode.com/problems/{SLUGS[pid]}/description/' not in text:raise ValueError('numeric/title/slug identity mismatch')
    text=re.sub(r'(?m)^L\d+: ?','',text);cases=[]
    for item in re.finditer(r'Input:\s*([^\n]+)\n\s*Output:\s*([^\n]+)',text):
        call=ast.parse('f('+item[1].strip()+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or tuple(k.arg for k in call.keywords)!=PARAMETERS[pid]:raise ValueError('ordered official parameters differ')
        args=[ast.literal_eval(k.value) for k in call.keywords];answer=json.loads(item[2])
        if not q.exact(expected(pid,args),answer):raise ValueError('public example reference disagreement')
        cases.append(dict(args=args,expected=answer,compare='return'))
    if len(cases)!=EXAMPLE_COUNT[pid]:raise ValueError('complete pinned public examples required')
    return cases

def bounded_compositions(total,variables,cap):
    return sum((-1)**j*comb(variables,j)*comb(total-j*(cap+1)+variables-1,variables-1) for j in range(min(variables,total//(cap+1))+1))%MOD

def _generate_cases(pid,raw):
    cases=[];categories=[];seen={};rng=random.Random(202610272001+pid);sentinel=object()
    def add(args,category,answer=sentinel):
        validate(pid,args);answer=expected(pid,args) if answer is sentinel else answer;key=q.encoded(args)
        if key in seen:
            assert q.exact(seen[key],answer);return
        assert type(answer) is int
        seen[key]=answer;cases.append(dict(args=args,expected=answer,compare='return'));categories.append(category)
    for c in public_examples(pid,raw):add(c['args'],'pinned_public_example',c['expected'])
    if pid==2585:
        for n in range(1,4):
            for types in product(list(product((1,2),(1,2,3))),repeat=n):
                for target in range(1,9):add([target,[list(t) for t in types]],'exhaustive_bounded_quantity_vectors')
        for _ in range(80):add([rng.randint(1,30),[[rng.randint(1,4),rng.randint(1,6)] for _ in range(rng.randint(1,6))]],'seeded_quantity_vectors_and_repeated_types')
        for target,count,marks in [(1000,50,1),(1000,50,50),(999,50,2),(25,1,1),(1000,1,1),(1,50,1)]:
            answer=bounded_compositions(target//marks,50,count) if target%marks==0 else 0
            add([target,[[count,marks] for _ in range(50)]],'analytic_maximum_bounded_compositions',answer)
    elif pid==2654:
        for n in range(2,6):
            for nums in product((1,2,3),repeat=n):add([list(nums)],'exhaustive_actual_gcd_state_graphs')
        for _ in range(80):add([[rng.choice((1,2,3,4,6,10,15,30)) for _ in range(rng.randint(2,5))]],'seeded_actual_gcd_states')
        for nums,answer in [([1]*50,0),([1000000]*50,-1),([1]+[1000000]*49,49),([6,10,15]+[30]*47,51),([2]*49+[3],50),([1000000]*49+[999999],50)]:add([nums],'analytic_maximum_first_one_and_gcd_invariant',answer)
    elif pid==2662:
        points=list(product((1,2),repeat=2));roads=[[*a,*b,c] for a in points for b in points for c in (1,2,3)]
        for road in roads:add([[1,1],[2,2],[road]],'exhaustive_single_directed_roads')
        for pair in product(roads,repeat=2):add([[1,1],[2,2],[list(r) for r in pair]],'exhaustive_two_directed_roads_including_duplicates')
        for _ in range(80):
            start=[rng.randint(1,3),rng.randint(1,3)];target=[start[0]+rng.randint(0,6),start[1]+rng.randint(0,6)]
            rs=[[rng.randint(start[0],target[0]),rng.randint(start[1],target[1]),rng.randint(start[0],target[0]),rng.randint(start[1],target[1]),rng.choice((1,2,7,100000))] for _ in range(rng.randint(1,8))]
            add([start,target,rs],'seeded_explicit_grid_shortest_paths')
        add([[1,1],[100000,100000],[[1,1,1,1,100000]]*200],'analytic_maximum_self_roads_ignored',199998)
        add([[1,1],[100000,100000],[[1,1,100000,100000,1]]*200],'analytic_maximum_duplicate_direct_road',1)
        add([[1,1],[100000,100000],[[100000,100000,1,1,1]]*200],'analytic_maximum_reverse_road_is_not_forward',199998)
        points=[1+99999*i//200 for i in range(201)]
        add([[1,1],[100000,1],[[a,1,b,1,1] for a,b in zip(points,points[1:])]],'analytic_maximum_monotone_road_chain',200)
        add([[100000,100000],[100000,100000],[[100000]*5]*200],'analytic_maximum_equal_start_target',0)
    elif pid==2698:
        for n in range(1,1001):add([n],'exhaustive_complete_scalar_domain_cut_masks')
    else:
        for n in range(1,9):
            for bits in product('01',repeat=n):add([''.join(bits)],'exhaustive_weighted_binary_state_graphs')
        for _ in range(80):add([''.join(rng.choice('01') for _ in range(rng.randint(9,10)))],'seeded_weighted_state_graphs')
        for s,answer in [('0'*100000,0),('1'*100000,0),('01'*50000,2500000000),('01'*49999+'0',2499950000),('0'*50000+'1'*50000,50000),('1'+'0'*99998+'1',2)]:add([s],'analytic_maximum_independent_boundary_costs',answer)
    return cases,categories

def expected_observation_bytes(batch,language):
    if language not in ('javascript','python'):raise ValueError('unsupported observer language')
    return sum(len(q.encoded(dict(i=i,result=c['expected'],result_type=q.expected_type(c['expected'],language),args_before=c['args'],args_after=c['args'],alias_edges=[]))) for i,c in enumerate(batch))+len(q.encoded(dict(done=len(batch))))+(language=='python')

def build_cases(pid,raw):
    cases,categories=_generate_cases(pid,raw)
    if len(q.encoded(cases))>q.MAX_FILE:raise ValueError('case artifact exceeds unchanged reader cap')
    for _,batch in q.batches(cases):
        if any(expected_observation_bytes(batch,l)>q.LIMITS['max_output_bytes'] for l in ('javascript','python')):raise ValueError('projected output exceeds unchanged observer cap')
    return cases,categories
