"""Source-blind public-definition references, not source or runtime qualification."""
from __future__ import annotations
from itertools import combinations, product
import ast
import json
import random
import re
from . import imported_qualification as q
IDS = (3143, 3148, 3152, 3153, 3160, 3163)
TITLES = {3143: 'Maximum Points Inside the Square', 3148: 'Maximum Difference Score in a Grid', 3152: 'Special Array II', 3153: 'Sum of Digit Differences of All Pairs', 3160: 'Find the Number of Distinct Colors Among the Balls', 3163: 'String Compression III'}
SLUGS = {3143: 'maximum-points-inside-the-square', 3148: 'maximum-difference-score-in-a-grid', 3152: 'special-array-ii', 3153: 'sum-of-digit-differences-of-all-pairs', 3160: 'find-the-number-of-distinct-colors-among-the-balls', 3163: 'string-compression-iii'}
STATEMENT_SHA256 = {3143: 'e2bd88ecddc6949014ae3297210e9ba88b2c93ba460425b6e87184d30b072623', 3148: 'd0c541f25c000196256eaec774f9b559cbb5f7bd9904cdf68c750270a3712520', 3152: '1dfea2d5ed7f3ccbd4b622f06682d97bb37a438e0fc9bcf120d2e29a3292a093', 3153: '697016ef6605a0e59a22c499996a5a7f252860bda7c443ce286d7bc0ec9f6332', 3160: 'c210148a5712328369766d89a3b6f9667c3726e8f9dbed0e318c8b8288417193', 3163: '02058c26087a3621778e81f22469de195fbb6eda4140dcd80433da5e8a27ea9c'}
PARAMETERS={3143:('points','s'),3148:('grid',),3152:('nums','queries'),3153:('nums',),3160:('limit','queries'),3163:('word',)}
EXAMPLE_COUNT={3143:3,3148:2,3152:2,3153:2,3160:2,3163:2}
SEED_BASE=202610272115
CONTRACTS={
3143:dict(domain='1..100000 distinct integer-coordinate pairs in[-1e9,1e9]^2; same-length lowercase ASCII tags. Axis-aligned square centered at origin, closed boundaries, side length may0.',result='Maximum contained points with all tags distinct, exact0..26.',reference='Enumerate every max-absolute-coordinate radius and0, rescan all points and check tag uniqueness; <=40points.',complexity='Reference O(n^2) time/O(n) space; candidate O(n logn) or O(n+26) with bounded tag minima, no source assumptions.'),
3148:dict(domain='Rectangular exact-int grid,2..1000 rows/columns,4..100000totalcells,values1..100000.',result='Maximum nonempty monotone right/down path score; integer-99999..99999, may negative.',reference='Enumerate every distinct start/end coordinate pair with end weakly southeast; path score telescopes to endvalue-startvalue; <=64cells.',complexity='Reference O((rows*cols)^2) time/O(1) auxiliary; candidate O(rows*cols) time/O(rows*cols) or better.'),
3152:dict(domain='1..100000 exact nums values1..100000;1..100000 [from,to] queries with0<=from<=to<len(nums).',result='Fresh list of strict Boolean values for all adjacent pairs in each closed interval having different parity. Singleton interval true.',reference='Literal adjacent scans per query, <=80numbers/100queries.',complexity='Reference O(n*q) time/O(q) output; candidate O(n+q) time/O(n+q) space.'),
3153:dict(domain='2..100000 exact integers1<=value<1e9, all with identical decimal width.',result='Exact sum of positionwise unequal digits over unordered index pairs; nonnegative and <=9*C(100000,2), may exceed32bit but below2^53.',reference='Enumerate every unordered index pair and zip their decimal strings; <=60values.',complexity='Reference O(n^2*digits) time/O(n*digits) strings; candidate O(n*digits) time/O(10*digits) state or equivalent.'),
3160:dict(domain='Exact limit1..1e9;1..100000 [ball,color] queries with ball0..limit and color1..1e9. Initially all limit+1 balls uncolored.',result='Fresh exact-int list of distinct currently assigned colors after every query; uncolored excluded, duplicates replace not add.',reference='Fresh sparse ball map; recompute set of current values after every assignment; <=100queries, full limit allowed.',complexity='Reference O(q^2) time/O(q) space/output; candidate expected O(q) time/O(min(q,limit+1)) state plus output, never require O(limit).'),
3163:dict(domain='1..200000 lowercase ASCII English letters.',result='Exact compressed string from repeatedly removing maximal samechar prefix of length<=9; result length<=400000.',reference='Literally slice remaining prefix and append length+char; <=400chars.',complexity='Reference O(n^2) slicing time/O(n) space; candidate O(n+output) time/storage or justified immutable-string behavior.')}
COMMON_CONTRACT=dict(exposure='Deterministic exposed development, not heldout/full-domain or runtime qualification.',interface='Ordered single-call plain values from official examples; exports not yet inspected.',effects='Conservative service envelope: input values/identities unchanged; no mutable result/input alias or persistent mutable state or external I/O, independent of public mutation permission.',numeric='Strict exact integers and Boolean query results; no Boolean-as-int inputs or32-bit narrowing of3153 totals.',unicode='All text ASCII English as declared, not generalized Unicode.',limits='Unchanged q schema,MAX_PACKET1100000,MAX_FILE,LIMITS and q.batches with exact helper pin.',expected_values='Host-side only, absent from packet.',candidate_execution=False)
OMITTED_MAXIMUM_SHAPES={3143:'100000 pairs with wide1e9 coordinates plus tags exceed packet; fullcount low-coordinate distinct grid and isolated numeric extremes retained. No arbitrary maximum geometry enumeration.',3148:'All official maximum product/value combinations transport belowcap, each dimension1000 separately since product100000; arbitrary maximum grids not exhaustively enumerated.',3152:'Fullcount nums plus100000 wide-index queries exceed cap; fullcount small-index repeated queries and full numeric/index boundaries separately retained.',3153:'Full100000 nine-digit values fitpacket; structured two-value and balanced9digit families included, arbitrary maximum arrays not exhaustive.',3160:'100000 simultaneous maximum ball/color pairs exceedcap; fullcount low-numeric/repeatedcolor streams and isolated maxlabel/maxcolor retained.',3163:'Full200000 length and output400000 fitpacket/outputcap; structured runs/alternations only, not all maximum strings.'}
ANALYTIC_JUSTIFICATIONS={3143:'Lowgrid alltag a contains origin uniquely untilradius1; result1. A unique-tag inner group followed by at leastone repeated-tag boundary admits innercount only. Wide-boundary probes verify tiedradius groups cannot partially enter.',3148:'Allsame=>0; row-major increasing1..100000 gives99999 from firsttolast; row+col strictlydecreasing gives best-1, requiringnonempty path.',3152:'Alternating parity makes every interval true; uniform parity makes only singleton intervals true; repeated small-index queries at fullcounts independent exactpattern.',3153:'Two values differing in d positions contribute d*group1*group2. Nine groups111111111 through999999999 allpairs between groups differ in9positions; answer9*(C(N,2)-sum C(group,2)).',3160:'Repeated sameball alwaysonecolor; increasingball/color assignments make distinctcounts1..q; sharedcolor on distinctballs alwaysone; reassignments collapse/remove exactcolors.',3163:'Uniform nrun emits floor(n/9)copies9c plus remainder ifnonzero; alternating emits1c each; each maximal run independently splits into9chunks.'}

def _int(x,lo,hi):return type(x) is int and lo<=x<=hi

def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):raise ValueError('unsupported identity or argument shape')
    if pid==3143:
        p,s=args;valid=type(p) is list and 1<=len(p)<=100000 and all(type(x) is list and len(x)==2 and all(_int(v,-10**9,10**9) for v in x) for x in p) and type(s) is str and len(s)==len(p) and all('a'<=x<='z' for x in s)
        if valid:valid=len({tuple(x) for x in p})==len(p)
    elif pid==3148:
        g=args[0];valid=type(g) is list and 2<=len(g)<=1000 and type(g[0]) is list and 2<=len(g[0])<=1000 and len(g)*len(g[0])<=100000 and all(type(row) is list and len(row)==len(g[0]) and all(_int(v,1,100000) for v in row) for row in g)
    elif pid==3152:
        a,queries=args;valid=type(a) is list and 1<=len(a)<=100000 and all(_int(v,1,100000) for v in a) and type(queries) is list and 1<=len(queries)<=100000 and all(type(row) is list and len(row)==2 and _int(row[0],0,len(a)-1) and _int(row[1],row[0],len(a)-1) for row in queries)
    elif pid==3153:
        a=args[0];valid=type(a) is list and 2<=len(a)<=100000 and all(_int(v,1,10**9-1) for v in a)
        if valid:valid=len({len(str(v)) for v in a})==1
    elif pid==3160:
        limit,queries=args;valid=_int(limit,1,10**9) and type(queries) is list and 1<=len(queries)<=100000 and all(type(row) is list and len(row)==2 and _int(row[0],0,limit) and _int(row[1],1,10**9) for row in queries)
    else:valid=type(args[0]) is str and 1<=len(args[0])<=200000 and all('a'<=c<='z' for c in args[0])
    if not valid:raise ValueError('outside full public domain')

def expected(pid,args):
    validate(pid,args)
    if pid==3143:
        points,s=args
        if len(points)>40:raise ValueError('reference budget exceeded')
        best=0
        for radius in {0}|{max(abs(x),abs(y)) for x,y in points}:
            tags=[s[i] for i,(x,y) in enumerate(points) if abs(x)<=radius and abs(y)<=radius]
            if len(tags)==len(set(tags)):best=max(best,len(tags))
        return best
    if pid==3148:
        g=args[0];m,n=len(g),len(g[0])
        if m*n>64:raise ValueError('reference budget exceeded')
        return max(g[b][c]-g[i][j] for i in range(m) for j in range(n) for b in range(i,m) for c in range(j,n) if (i,j)!=(b,c))
    if pid==3152:
        a,queries=args
        if len(a)>80 or len(queries)>100:raise ValueError('reference budget exceeded')
        return [all(a[i]%2!=a[i+1]%2 for i in range(lo,hi)) for lo,hi in queries]
    if pid==3153:
        a=args[0]
        if len(a)>60:raise ValueError('reference budget exceeded')
        text=[str(v) for v in a];return sum(sum(x!=y for x,y in zip(text[i],text[j])) for i,j in combinations(range(len(a)),2))
    if pid==3160:
        limit,queries=args
        if len(queries)>100:raise ValueError('reference budget exceeded')
        balls={};out=[]
        for ball,color in queries:balls[ball]=color;out.append(len(set(balls.values())))
        return out
    word=args[0]
    if len(word)>400:raise ValueError('reference budget exceeded')
    out=''
    while word:
        n=1
        while n<min(9,len(word)) and word[n]==word[0]:n+=1
        out+=str(n)+word[0];word=word[n:]
    return out

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
    if len(cases)!=EXAMPLE_COUNT[pid]:raise ValueError('incomplete examples')
    return cases

def _generate_cases(pid,raw):
    cases=public_examples(pid,raw);cats=['pinned_public_example']*len(cases);rng=random.Random(SEED_BASE+pid);unset=object()
    def add(a,cat,v=unset):
        validate(pid,a);cases.append(dict(args=a,expected=expected(pid,a) if v is unset else v,compare='return'));cats.append(cat)
    if pid==3143:
        universe=[[-1,-1],[0,0],[1,0],[2,-2]]
        for size in range(1,5):
            for indices in combinations(range(4),size):
                p=[universe[i] for i in indices]
                for tags in product('ab',repeat=size):add([p,''.join(tags)],'exhaustive_square_ties_origin_tags')
        for _ in range(80):
            p=[list(x) for x in rng.sample(list(product(range(-5,6),repeat=2)),rng.randint(1,40))];s=''.join(rng.choice('abcde') for _ in p)
            add([p,s],'seeded_signed_coordinates_repeated_tags')
        add([[[i//100,i%100] for i in range(100000)],'a'*100000],'analytic_maximum_count_origin',1)
        add([[[i,0] for i in range(26)]+[[i//100+100,i%100] for i in range(99974)],'abcdefghijklmnopqrstuvwxyz'+'a'*99974],'analytic_maximum_unique_inner_tags',26)
        add([[[-10**9,10**9],[10**9,-10**9]],'aa'],'analytic_wide_tied_radius',0)
        add([[[0,0],[10**9,10**9]],'ab'],'analytic_wide_unique_radius',2)
    elif pid==3148:
        for m,n in ((2,2),(2,3),(3,2)):
            for a in product((1,2),repeat=m*n):add([[list(a[j*n:(j+1)*n]) for j in range(m)]],'exhaustive_nondecreasing_endpoint_order')
        for _ in range(80):
            m,n=rng.randint(2,8),rng.randint(2,8);add([[[rng.choice((1,2,100000)) for _ in range(n)] for _ in range(m)]],'seeded_negative_and_extreme_scores')
        for m,n in ((100,1000),(1000,100)):
            add([[[100000]*n for _ in range(m)]],'analytic_maximum_product_value_constant',0)
            add([[[i*n+j+1 for j in range(n)] for i in range(m)]],'analytic_maximum_product_increasing',99999)
            add([[[2000-i-j for j in range(n)] for i in range(m)]],'analytic_maximum_product_decreasing',-1)
    elif pid==3152:
        for n in range(1,8):
            for a in product((1,2),repeat=n):add([list(a),[[i,j] for i in range(n) for j in range(i,n)]],'exhaustive_parity_all_intervals')
        for _ in range(80):
            a=[rng.randint(1,100000) for _ in range(rng.randint(8,80))];queries=[]
            for _ in range(rng.randint(1,100)):
                i,j=sorted((rng.randrange(len(a)),rng.randrange(len(a))));queries.append([i,j])
            add([a,queries],'seeded_mixed_parity_queries')
        add([[1,2]*50000,[[0,1] for _ in range(100000)]],'analytic_maximum_both_counts',[True]*100000)
        add([[100000]*100000,[[0,0],[0,99999],[99999,99999]]],'analytic_maximum_numeric_and_index',[True,False,True])
        add([[1]*100000,[[0,1] for _ in range(100000)]],'analytic_maximum_false_stream',[False]*100000)
    elif pid==3153:
        for n in range(2,7):
            for a in product((10,11,20),repeat=n):add([list(a)],'exhaustive_pairwise_decimal_positions')
        for _ in range(80):
            width=rng.randint(1,9);a=[rng.randint(10**(width-1),10**width-1) for _ in range(rng.randint(7,60))];add([a],'seeded_equal_width_digit_pairs')
        add([[111111111]*50000+[999999999]*50000],'analytic_maximum_two_group_difference',9*50000*50000)
        add([[999999999]*100000],'analytic_maximum_uniform_value',0)
        groups=[11112]+[11111]*8;a=[int(str(i+1)*9) for i,c in enumerate(groups) for _ in range(c)]
        add([a],'analytic_maximum_balanced_nine_digits',9*(100000*99999//2-sum(c*(c-1)//2 for c in groups)))
    elif pid==3160:
        for limit in (1,2):
            ops=list(product(range(limit+1),(1,2)))
            for length in range(1,5 if limit==1 else 4):
                for seq in product(ops,repeat=length):add([limit,[list(x) for x in seq]],'exhaustive_sparse_repaint_traces')
        for _ in range(80):
            limit=rng.choice((1,5,10**9));seq=[[rng.choice((0,limit,limit//2)),rng.choice((1,2,10**9))] for _ in range(rng.randint(5,100))];add([limit,seq],'seeded_full_numeric_sparse_traces')
        add([10**9,[[0,1] for _ in range(100000)]],'analytic_maximum_repeated_ball',[1]*100000)
        add([10**9,[[i,1] for i in range(100000)]],'analytic_maximum_shared_color',[1]*100000)
        add([10**9,[[i,i+1] for i in range(50000)]],'analytic_large_all_distinct',list(range(1,50001)))
        add([10**9,[[10**9,10**9],[0,10**9],[10**9,1],[0,1]]],'analytic_maximum_color_replacement',[1,1,2,1])
    else:
        for n in range(1,10):
            for a in product('ab',repeat=n):add([''.join(a)],'exhaustive_literal_prefix_removal')
        for run in range(1,31):
            for extra in (1,8,9,10):add(['a'*run+'b'*extra+'a'*run],'boundary_nine_chunk_residual')
        for _ in range(80):add([''.join(rng.choice('abcd') for _ in range(rng.randint(10,400)))],'seeded_run_boundaries')
        for word,answer in [('a'*200000,'9a'*(200000//9)+'2a'),('ab'*100000,'1a1b'*100000),('a'*99999+'b'*100001,'9a'*11111+'9b'*11111+'2b'),('z'*199999+'a','9z'*22222+'1z1a')]:add([word],'analytic_maximum_input_output',answer)
    seen={};out=[];categories=[]
    for c,cat in zip(cases,cats):
        key=q.encoded(c['args'])
        if key in seen:
            if not q.exact(seen[key],c['expected']):raise ValueError('duplicate expectation mismatch')
        else:seen[key]=c['expected'];out.append(c);categories.append(cat)
    return out,categories

def maximum_omitted_inputs():
    return {3143:[[[10**9-i,10**9] for i in range(100000)],'a'*100000],3152:[[100000]*100000,[[0,99999] for _ in range(100000)]],3160:[10**9,[[10**9,10**9] for _ in range(100000)]]}

def expected_observation_bytes(batch,language):
    if language not in ('javascript','python'):raise ValueError('unknown language')
    return sum(len(q.encoded(dict(i=i,result=c['expected'],result_type=q.expected_type(c['expected'],language),args_before=c['args'],args_after=c['args'],alias_edges=[]))) for i,c in enumerate(batch))+len(q.encoded(dict(done=len(batch))))+(language=='python')

def build_cases(pid,raw):
    cases,cats=_generate_cases(pid,raw)
    if len(q.encoded(cases))>q.MAX_FILE:raise ValueError('unchanged artifact cap exceeded')
    for _,b in q.batches(cases):
        if max(expected_observation_bytes(b,l) for l in ('javascript','python'))>q.LIMITS['max_output_bytes']:raise ValueError('unchanged output cap exceeded')
    return cases,cats
