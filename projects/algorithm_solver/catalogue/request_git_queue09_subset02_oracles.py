"""Independent public-spec references; source-blind exposed development only."""
from __future__ import annotations
from itertools import combinations, product
from math import comb
import ast
import json
import random
import re
from . import imported_qualification as q
IDS = (3112, 3116, 3122, 3129, 3133, 3138)
TITLES = {3112: 'Minimum Time to Visit Disappearing Nodes', 3116: 'Kth Smallest Amount With Single Denomination Combination', 3122: 'Minimum Number of Operations to Satisfy Conditions', 3129: 'Find All Possible Stable Binary Arrays I', 3133: 'Minimum Array End', 3138: 'Minimum Length of Anagram Concatenation'}
SLUGS = {3112: 'minimum-time-to-visit-disappearing-nodes', 3116: 'kth-smallest-amount-with-single-denomination-combination', 3122: 'minimum-number-of-operations-to-satisfy-conditions', 3129: 'find-all-possible-stable-binary-arrays-i', 3133: 'minimum-array-end', 3138: 'minimum-length-of-anagram-concatenation'}
STATEMENT_SHA256 = {3112: 'c5e8497c75ef1a074fad854ffd3a03b9543bc9b7b4c314e8d1922e7ae21af578', 3116: '4542181962be4d78c688789eb6b65f4ed5f9e4188cb3ce9d5fd5e7fec225d413', 3122: '93a254d29964fbf5803ec40cd35efededfb9c859f50b92bc985caf745d68ee01', 3129: 'b84f8cc01ab2f12971b16a894f28dd86d904577be7094b8f8565c5615640c06b', 3133: 'ee83c48c1941e216ddff140380214a5debe6715479f534126b94f7724c4f141a', 3138: '5f4a7440da9b08fe20c771df533e2d7bfba4ca962514b4879f6f12ea73ad28b7'}
PARAMETERS={3112:('n','edges','disappear'),3116:('coins','k'),3122:('grid',),3129:('zero','one','limit'),3133:('n','x'),3138:('s',)}
EXAMPLE_COUNT={3112:3,3116:2,3122:3,3129:3,3133:2,3138:3}
SEED_BASE=202610272111
CONTRACTS={
3112:dict(domain='n1..50000;0..100000 undirected [u,v,length] edges with endpoints0..n-1, length1..100000; n deadlines1..100000. Multiple edges and self-loops allowed; no statement exclusion.',result='Fresh exact-int array, each shortest arrival strictly before disappearance or-1; root0 reaches at0.',reference='Enumerate every simple path, checking all arrival deadlines; collapse parallel edges to shortest positive length. n<=7,<=20edges.',complexity='Reference factorial small-n path enumeration; candidate target O((n+m)log(n+m)) time/O(n+m) space, heap costs counted.'),
3116:dict(domain='1..15 pairwise-distinct exact coin values1..25; k1..2000000000.',result='kth distinct positive integer divisible by at least one coin, <=50000000000.',reference='Scan positive amounts and divisibility, k<=200; maximum cases analytic singleton, divisibility-redundant or containing1.',complexity='Reference O(k*mincoin*coin_count) time/O(1) auxiliary; candidate target O(2^c*log(k*mincoin)) with exact LCM/count arithmetic, or justified equivalent.'),
3122:dict(domain='Rectangular1..1000rows and1..1000columns of exact integers0..9; changes may use any nonnegative number.',result='Minimum changed cells to constant columns and unequal adjacent columns; exact0..rows*cols.',reference='Enumerate all adjacent-distinct column choices from0..11; <=6rows,<=4cols. Two fresh symbols represent arbitrary outside-input values; any such symbol may be replaced by a digit avoiding its two neighbors without increasing cost.',complexity='Reference O(12^cols*rows*cols) time/O(cols) auxiliary; candidate O(rows*cols+100*cols) time and O(10*cols) or better.'),
3129:dict(domain='Exact zero,one,limit each1..200; body uses num_zeros/num_ones prose aliases but official positional examples zero,one,limit.',result='Number of binary words with given counts and run lengths<=limit, modulo1000000007.',reference='Enumerate all zero-position subsets for total<=16; analytic large cases independently count bounded positive run compositions and alternating run counts.',complexity='Small reference O(C(z+o,z)*(z+o)); large composition O((z+o)^2) combinatorial terms; candidate polynomial DP, exact modulo/no32bit overflow.'),
3133:dict(domain='Exact n,x each1..100000000.',result='Minimum final element of strictly increasing positive n-list with bitwiseANDx; exact integer, potentially above32bit but <=6710886399999999<2^53.',reference='Scan integer supersets of x until nth for n<=40,x<=127. Including firstx ensures whole ANDx. Analytic powers and low-bit masks at maximum n/x.',complexity='Bounded scan O(n*2^popcount(x)); candidate target O(logn+logx) bit placement or exact rank method, avoiding32bit truncation.'),
3138:dict(domain='1..100000 lowercase ASCII English letters. t may equal s, so every such string valid.',result='Minimum block size dividing length for which all blocks are anagrams; exact1..len(s).',reference='Try every block width dividing length and compare literally sorted blocks; len<=80.',complexity='Reference O(n*divisors(n)*logn) plus length-divisibility scan; candidate O(n*divisors(n)+n) or equivalent, helper costs explicit.')}
COMMON_CONTRACT=dict(exposure='Exposed development, not heldout or qualification.',interface='Ordered plain values from official examples; actual candidate exports unknown.',effects='Conservative service envelope: unchanged input values/identities, no mutable return/input alias, persistent mutable state or external I/O; not attributed to public mutation permissions.',numeric='Strict exact integers, no Boolean-as-int. Scalar3133 result below2^53 yet may require>32bits. 3116 result<=5e10;3129 residue0..1e9+6.',expected_values='Host-side only, never q.packet.',limits='Exact immutable q support, unchanged caps and q.batches.',candidate_execution=False)
OMITTED_MAXIMUM_SHAPES={3112:'Full n50000/m100000/deadline100000 combined with wide endpoints exceeds packet. Full n/m low-label repeated-edge and full-n chain retained; arbitrary maximum graphs omitted.',3116:'Entire scalar/list maximum domain transports; arbitrary max-k multi-denomination sets without analytic family are not enumerated by reference.',3122:'Even minimum-valued1000x1000 grid exceeds packet cap.500x1000 plus1000x500 retain each maximum dimension, not simultaneous million cells; no cap change.',3129:'All three maxima together included via run-composition count; not all200^3 combinations enumerated.',3133:'Full scalar domain transports; analytic maximal shapes retained, not all1e16 pairs.',3138:'Maximum length transports; only structured analytically justified maximum strings, not all strings.'}

def _int(x,lo,hi):return type(x) is int and lo<=x<=hi

def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):raise ValueError('unsupported identity or argument shape')
    if pid==3112:
        n,e,d=args
        valid=_int(n,1,50000) and type(e) is list and len(e)<=100000 and all(type(row) is list and len(row)==3 and _int(row[0],0,n-1) and _int(row[1],0,n-1) and _int(row[2],1,100000) for row in e) and type(d) is list and len(d)==n and all(_int(x,1,100000) for x in d)
    elif pid==3116:
        c,k=args;valid=type(c) is list and 1<=len(c)<=15 and all(_int(x,1,25) for x in c) and len(set(c))==len(c) and _int(k,1,2*10**9)
    elif pid==3122:
        g=args[0];valid=type(g) is list and 1<=len(g)<=1000 and type(g[0]) is list and 1<=len(g[0])<=1000 and all(type(row) is list and len(row)==len(g[0]) and all(_int(v,0,9) for v in row) for row in g)
    elif pid==3129:valid=all(_int(x,1,200) for x in args)
    elif pid==3133:valid=all(_int(x,1,10**8) for x in args)
    else:valid=type(args[0]) is str and 1<=len(args[0])<=100000 and all('a'<=x<='z' for x in args[0])
    if not valid:raise ValueError('outside full public domain')

def _paths(n,edges,disappear):
    adj=[{} for _ in range(n)]
    for u,v,w in edges:
        if u!=v:
            adj[u][v]=min(adj[u].get(v,w),w);adj[v][u]=min(adj[v].get(u,w),w)
    answer=[None]*n
    def visit(u,t,seen):
        answer[u]=t if answer[u] is None else min(answer[u],t)
        for v,w in adj[u].items():
            if v not in seen and t+w<disappear[v]:visit(v,t+w,seen|{v})
    visit(0,0,{0});return [-1 if v is None else v for v in answer]

def _columns(g):
    rows,cols=len(g),len(g[0]);costs=[[sum(row[j]!=v for row in g) for v in range(12)] for j in range(cols)]
    return min(sum(costs[j][v] for j,v in enumerate(values)) for values in product(range(12),repeat=cols) if all(values[j]!=values[j-1] for j in range(1,cols)))

def _stable_literal(z,o,limit):
    answer=0
    for positions in combinations(range(z+o),z):
        word=[1]*(z+o)
        for i in positions:word[i]=0
        longest=run=1
        for i in range(1,len(word)):
            run=run+1 if word[i]==word[i-1] else 1;longest=max(longest,run)
        answer+=longest<=limit
    return answer%1000000007

def _composition(total,runs,limit):
    if runs<1 or runs>total:return 0
    # Positive parts1..limit. Shift by1 then inclusion-exclusion on parts>=limit.
    return sum((-1)**j*comb(runs,j)*comb(total-j*limit-1,runs-1) for j in range(min(runs,(total-runs)//limit)+1))

def stable_run_count(z,o,limit):
    a=[0]+[_composition(z,r,limit) for r in range(1,z+1)]+[0]
    b=[0]+[_composition(o,r,limit) for r in range(1,o+1)]+[0]
    def at(v,i):return v[i] if i<len(v) else 0
    return sum(2*at(a,r)*at(b,r)+at(a,r+1)*at(b,r)+at(a,r)*at(b,r+1) for r in range(1,max(z,o)+1))%1000000007

def expected(pid,args):
    validate(pid,args)
    if pid==3112:
        if args[0]>7 or len(args[1])>20:raise ValueError('reference budget exceeded')
        return _paths(*args)
    if pid==3116:
        coins,k=args
        if k>200:raise ValueError('reference budget exceeded')
        amount=count=0
        while count<k:
            amount+=1;count+=any(amount%c==0 for c in coins)
        return amount
    if pid==3122:
        if len(args[0])>6 or len(args[0][0])>4:raise ValueError('reference budget exceeded')
        return _columns(args[0])
    if pid==3129:
        if args[0]+args[1]>16:raise ValueError('reference budget exceeded')
        return _stable_literal(*args)
    if pid==3133:
        n,x=args
        if n>40 or x>127:raise ValueError('reference budget exceeded')
        v=x;count=1
        while count<n:
            v+=1;count+=(v&x)==x
        return v
    s=args[0]
    if len(s)>80:raise ValueError('reference budget exceeded')
    for width in range(1,len(s)+1):
        if len(s)%width==0 and all(sorted(s[j:j+width])==sorted(s[:width]) for j in range(0,len(s),width)):return width

def public_examples(pid,raw):
    if pid not in IDS or type(raw) is not bytes or q.sha(raw)!=STATEMENT_SHA256[pid]:raise ValueError('exact pinned statement required')
    s=re.sub(r'(?m)^L\d+: ?', '', json.loads(raw))
    if f'{pid}. {TITLES[pid]}' not in s or f'https://leetcode.com/problems/{SLUGS[pid]}/description/' not in s:raise ValueError('identity mismatch')
    cases=[]
    for m in re.finditer(r'Input:\s*([^\n]+)\n\s*Output:\s*([^\n]+)',s):
        c=ast.parse('f('+m[1]+')',mode='eval').body
        if not isinstance(c,ast.Call) or c.args or tuple(k.arg for k in c.keywords)!=PARAMETERS[pid]:raise ValueError('official order differs')
        a=[ast.literal_eval(k.value) for k in c.keywords];v=json.loads(m[2])
        if not q.exact(expected(pid,a),v):raise ValueError('example disagrees')
        cases.append(dict(args=a,expected=v,compare='return'))
    if len(cases)!=EXAMPLE_COUNT[pid]:raise ValueError('incomplete public examples')
    return cases

def _generate_cases(pid,raw):
    cases=public_examples(pid,raw);cats=['pinned_public_example']*len(cases);rng=random.Random(SEED_BASE+pid);unset=object()
    def add(a,cat,v=unset):
        validate(pid,a);cases.append(dict(args=a,expected=expected(pid,a) if v is unset else v,compare='return'));cats.append(cat)
    if pid==3112:
        pairs=[(0,1),(0,2),(1,2)]
        for weights in product((0,1,2),repeat=3):
            edges=[[u,v,w] for (u,v),w in zip(pairs,weights) if w]
            for d in product((1,2,4),repeat=3):add([3,edges,list(d)],'exhaustive_weighted_graph_deadlines')
        for _ in range(80):
            n=rng.randint(1,7);edges=[[rng.randrange(n),rng.randrange(n),rng.randint(1,9)] for _ in range(rng.randint(0,20))]
            add([n,edges,[rng.randint(1,20) for _ in range(n)]],'seeded_self_loops_parallel_edges_deadlines')
        n=50000
        add([n,[],[100000]*n],'analytic_maximum_disconnected',[0]+[-1]*(n-1))
        add([n,[[0,1,1] for _ in range(100000)],[2]*n],'analytic_maximum_vertices_and_edges',[0,1]+[-1]*(n-2))
        add([n,[[i,i+1,1] for i in range(n-1)],[50000]*n],'analytic_maximum_chain',list(range(n)))
        add([2,[[0,1,100000]],[100000,100000]],'analytic_strict_maximum_deadline',[0,-1])
    elif pid==3116:
        for mask in range(1,64):
            coins=[i+1 for i in range(6) if mask>>i&1]
            for k in (1,2,3,7,20,50):add([coins,k],'exhaustive_coin_subsets_amount_scan')
        for _ in range(80):add([rng.sample(range(1,26),rng.randint(1,15)),rng.randint(1,200)],'seeded_nondividing_denominations')
        for c in (1,2,7,13,25):add([[c],2*10**9],'analytic_maximum_k_singleton',c*2*10**9)
        add([list(range(1,16)),2*10**9],'analytic_maximum_count_and_k_coin1',2*10**9)
        add([[5,10,15,20,25],2*10**9],'analytic_maximum_k_redundant_denominations',10**10)
        add([list(range(11,26)),200],'maximum_coin_count_value_scan')
    elif pid==3122:
        for rows,cols in ((1,1),(1,2),(1,3),(2,1),(2,2),(3,1)):
            for a in product((0,1),repeat=rows*cols):add([[list(a[j*cols:(j+1)*cols]) for j in range(rows)]],'exhaustive_binary_column_assignments')
        for _ in range(40):
            rows=rng.randint(1,6);cols=rng.randint(1,4)
            add([[[rng.randrange(10) for _ in range(cols)] for _ in range(rows)]],'seeded_all_digits_column_choices')
        for rows,cols in ((500,1000),(1000,500)):
            add([[[0]*cols for _ in range(rows)]],'analytic_largest_transport_uniform',rows*(cols//2))
            add([[[j%2 for j in range(cols)] for _ in range(rows)]],'analytic_largest_transport_alternating',0)
        add([[[i%10 for _ in range(1000)] for i in range(10)]],'analytic_all_digit_ties',9000)
    elif pid==3129:
        for z in range(1,9):
            for o in range(1,9):
                for limit in range(1,10):add([z,o,limit],'exhaustive_zero_position_subsets')
        for z,o,limit in [(200,200,1),(200,200,2),(200,200,3),(200,200,100),(200,200,199),(200,200,200),(200,1,1),(200,1,199),(200,1,200),(1,200,200),(199,200,1),(150,199,17)]:
            add([z,o,limit],'analytic_bounded_run_compositions',stable_run_count(z,o,limit))
    elif pid==3133:
        for n in range(1,17):
            for x in range(1,65):add([n,x],'exhaustive_integer_superset_scan')
        for _ in range(80):add([rng.randint(17,40),rng.randint(65,127)],'seeded_low_bit_gaps')
        for b in (1,2,5,10,20,26):add([10**8,(1<<b)-1],'analytic_maximum_n_lowbit_masks',10**8*(1<<b)-1)
        add([1,10**8],'analytic_maximum_x_singleton',10**8)
        for b in (1,4,20,26):
            x=1<<b;rank=10**8-1;v=(rank%(1<<b))+x+(rank//(1<<b))*(1<<(b+1));add([10**8,x],'analytic_maximum_n_single_fixed_bit',v)
    else:
        for n in range(1,9):
            for a in product('ab',repeat=n):add([''.join(a)],'exhaustive_sorted_blocks')
        for _ in range(80):add([''.join(rng.choice('abcd') for _ in range(rng.randint(9,80)))],'seeded_irregular_divisor_shapes')
        for s,v in [('a'*100000,1),('ab'*50000,2),('a'*99999+'b',100000),('abba'*25000,2),('abcde'*20000,5)]:add([s],'analytic_maximum_length',v)
    seen={};out=[];categories=[]
    for c,cat in zip(cases,cats):
        key=q.encoded(c['args'])
        if key in seen:
            if not q.exact(seen[key],c['expected']):raise ValueError('duplicate expectation mismatch')
        else:seen[key]=c['expected'];out.append(c);categories.append(cat)
    return out,categories

def expected_observation_bytes(batch,language):
    if language not in ('javascript','python'):raise ValueError('unknown observer language')
    return sum(len(q.encoded(dict(i=i,result=c['expected'],result_type=q.expected_type(c['expected'],language),args_before=c['args'],args_after=c['args'],alias_edges=[]))) for i,c in enumerate(batch))+len(q.encoded(dict(done=len(batch))))+(language=='python')

def build_cases(pid,raw):
    cases,cats=_generate_cases(pid,raw)
    if len(q.encoded(cases))>q.MAX_FILE:raise ValueError('case artifact cap exceeded')
    for _,b in q.batches(cases):
        if max(expected_observation_bytes(b,l) for l in ('javascript','python'))>q.LIMITS['max_output_bytes']:raise ValueError('observer output cap exceeded')
    return cases,cats
