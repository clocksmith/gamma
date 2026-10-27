"""Queue06 subset01: source-blind public-spec references, not candidates.

Callers freshly authorize each statement body/hash access. Full-domain validators
are separate from bounded enumeration. Frozen analytic fixtures are explicit.
No source loading, candidate execution, admission, or engine is implemented here.
"""
from __future__ import annotations
import ast
from itertools import product
import json
import random
import re
from . import imported_qualification as q
from .imported_clean_domains import integer, ints, text

IDS = (2718,2730,2746,2750,2768,2769)
PARAMETERS = {2718:('n','queries'),2730:('s',),2746:('words',),2750:('nums',),2768:('m','n','coordinates'),2769:('num','t')}
STATEMENT_SHA256 = {
2718:'72b50ec3b159cafc49e4d41dc1d208844f633a81e9dc22bcc3b102f1ed79b4b1',
2730:'39bb80d5c3df39b4936f15652e26b5056d3f141098cf70bec96f570c5b2b4c1f',
2746:'c9d8b5836086aac0af02dd3ddefb34b3f102e69d0f61b4dc0d2175f5dc41c148',
2750:'df44cdee887473e477c3c23d027f34978936de9a42b0be1a8f74ac9600998f9b',
2768:'f49b980149ccd1dfada38e117923aea3c8b2888b173564cf3953ead0086834a9',
2769:'9db3593b06fb5c026256d172fde27fd354b40e2cb8986e8d96ae5a8574edf685'}
EXAMPLE_COUNT = {2718:2,2730:3,2746:3,2750:2,2768:2,2769:2}
CASE_COUNT = {2718: 733, 2730: 586, 2746: 405, 2750: 1065, 2768: 712, 2769: 2500}
CASES_SHA256 = {2718: '28dee149d2931e315d6c90e1392df0febdd8fc1c7b9af68017f10640ac801c89', 2730: '0d1585c1dc7c6f82029933e8818a8ac3a24606b86c2d04665ec3f960f7fa615d', 2746: '7c171d394b6fa1f5a7628d59285cdadb210208c3546c1c399f8bd94d3fa2628c', 2750: 'd983647994cc69df60bef76c5cd72546978460ac7286ba657f6d1cefb08d8481', 2768: '744bef7f694c5130fa2dca0088256cd76ff26b5dc640400b0727d49a51b709ca', 2769: 'b1590cf40c2474f48c2dcf1799971a09c24469b375b96b3eaad3ea194c018374'}
SEED_BASE = 202610271950
MOD = 1000000007
OMITTED_MAXIMUM_SHAPES = {
2718:'Dense reference is bounded to n<=12; maximum n and query count use stated analytic shapes. Arbitrary full matrices are not materialized. All legal individual input packets fit the current cap by size bound; runtime still unmeasured.',
2730:'Exhaustive binary strings through length8, full-alphabet seeded strings and selected length50 shapes; not all10^50 strings.',
2746:'Literal-string exhaustive reference stops at10words. Three maximum1000-word uniform shapes have exact length proofs; arbitrary maximum branching inputs are omitted.',
2750:'Cut-mask enumeration through14entries only; exhaustive binary inputs through9 and analytic length100000 forms do not exhaust the full domain.',
2768:'Direct block enumeration is bounded to dimensions<=20. Huge grid shapes use separately proved sparse geometry; arbitrary maximum coordinates are not enumerated.',
2769:'Every officially valid num,t pair is covered, but finite case agreement would still not qualify an unreviewed candidate.'}


def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):
        raise ValueError('unsupported identity or ordered argument shape')
    if pid==2718:
        n,queries=args
        valid=(integer(n,1,10000) and type(queries) is list and 1<=len(queries)<=50000
               and all(type(r) is list and len(r)==3 and integer(r[0],0,1) and integer(r[1],0,n-1) and integer(r[2],0,100000) for r in queries))
    elif pid==2730:
        valid=text(args[0],'0123456789',1,50)
    elif pid==2746:
        words=args[0];valid=type(words) is list and 1<=len(words)<=1000 and all(text(w,minimum=1,maximum=50) for w in words)
    elif pid==2750:
        valid=ints(args[0],0,1,1,100000)
    elif pid==2768:
        m,n,coords=args
        valid=(integer(m,2,100000) and integer(n,2,100000) and type(coords) is list and len(coords)<=10000
               and all(type(r) is list and len(r)==2 and integer(r[0],0,m-1) and integer(r[1],0,n-1) for r in coords)
               and len({tuple(r) for r in coords})==len(coords))
    else:
        valid=integer(args[0],1,50) and integer(args[1],1,50)
    if not valid:raise ValueError('outside complete pinned statement domain')


def expected(pid,args):
    """Independent finite reference with explicit computational domain bounds."""
    validate(pid,args)
    if pid==2718:
        n,queries=args
        if n>12:raise ValueError('dense reference budget; use justified analytic fixture')
        matrix=[[0]*n for _ in range(n)]
        for kind,index,value in queries:
            for j in range(n):
                if kind==0:matrix[index][j]=value
                else:matrix[j][index]=value
        return sum(map(sum,matrix))
    if pid==2730:
        s=args[0]
        return max(j-i for i in range(len(s)) for j in range(i+1,len(s)+1)
                   if sum(s[k]==s[k+1] for k in range(i,j-1))<=1)
    if pid==2746:
        words=args[0]
        if len(words)>10:raise ValueError('literal join enumeration budget')
        states={words[0]}
        def join(a,b):return a+b[1:] if a[-1]==b[0] else a+b
        for word in words[1:]:states={result for s in states for result in (join(s,word),join(word,s))}
        return min(map(len,states))
    if pid==2750:
        a=args[0];n=len(a)
        if n>14:raise ValueError('cut enumeration budget')
        ways=0
        for mask in range(1<<(n-1)):
            start=0;valid=True
            for end in range(1,n+1):
                if end==n or mask>>(end-1)&1:
                    if sum(a[start:end])!=1:valid=False;break
                    start=end
            ways+=valid
        return ways%MOD
    if pid==2768:
        m,n,coords=args
        if max(m,n)>20:raise ValueError('dense block enumeration budget')
        black=set(map(tuple,coords));answer=[0]*5
        for row in range(m-1):
            for col in range(n-1):answer[sum((row+dr,col+dc) in black for dr,dc in ((0,0),(0,1),(1,0),(1,1)))]+=1
        return answer
    num,t=args;reachable={0}
    for _ in range(t):reachable|={delta+dx-dnum for delta in reachable for dx in (-1,1) for dnum in (-1,1)}
    return num+max(reachable)


def valid_answer(pid,args,answer):
    if pid==2768:
        return ints(answer,0,(args[0]-1)*(args[1]-1),5,5) and sum(answer)==(args[0]-1)*(args[1]-1)
    bounds={2718:(0,args[0]**2*100000) if pid==2718 else (0,0),2730:(1,50),2746:(1,50000),2750:(0,MOD-1),2769:(1,150)}
    return integer(answer,*bounds[pid])


def public_examples(pid,raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw)!=STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned definition bytes required')
    cases=[]
    for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)',raw.decode(),re.S):
        call=ast.parse('f('+match[1].strip()+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or tuple(x.arg for x in call.keywords)!=PARAMETERS[pid]:
            raise ValueError('public ordered parameters differ')
        args=[ast.literal_eval(x.value) for x in call.keywords];answer=json.loads(match[2])
        if not q.exact(expected(pid,args),answer):raise ValueError('public example disagrees with independent reference')
        cases.append({'args':args,'expected':answer,'compare':'return'})
    if len(cases)!=EXAMPLE_COUNT[pid]:raise ValueError('complete public examples required')
    return cases


def _generate_cases(pid,statement):
    cases=[];categories=[];seen={};rng=random.Random(SEED_BASE+pid);sentinel=object()
    def add(args,category,answer=sentinel):
        validate(pid,args);answer=expected(pid,args) if answer is sentinel else answer
        if not valid_answer(pid,args,answer):raise ValueError('invalid exact expected result')
        key=q.encoded(args)
        if key in seen:
            if not q.exact(seen[key],answer):raise ValueError('inconsistent duplicate input')
            return
        seen[key]=answer;cases.append({'args':args,'expected':answer,'compare':'return'});categories.append(category)
    for case in public_examples(pid,statement):add(case['args'],'pinned_public_example',case['expected'])
    if pid==2718:
        for n in (1,2):
            options=[[kind,index,value] for kind in range(2) for index in range(n) for value in (0,1)]
            for count in range(1,4):
                for queries in product(options,repeat=count):add([n,[list(r) for r in queries]],'exhaustive_small_dense_overwrites')
        for _ in range(60):
            n=rng.randrange(1,9);add([n,[[rng.randrange(2),rng.randrange(n),rng.choice((0,1,99999,100000))] for _ in range(rng.randrange(1,31))]],'seeded_dense_order_and_numeric')
        add([10000,[[0,i,100000] for i in range(10000)]],'analytic_maximum_full_row_fill',10**13)
        add([10000,[[1,i,100000] for i in range(10000)]+[[0,0,0]]],'analytic_maximum_column_fill_then_clear_row',9999000000000)
        add([10000,[[0,9999,100000] for _ in range(50000)]],'analytic_maximum_queries_same_row',10**9)
        add([2,[[i%2,(i//2)%2,(i*7919)%100001] for i in range(50000)]],'maximum_query_count_dense_simulation')
    elif pid==2730:
        for n in range(1,9):
            for chars in product('01',repeat=n):add([''.join(chars)],'exhaustive_binary_substring_enumeration')
        for _ in range(70):add([''.join(rng.choices('0123456789',k=rng.randrange(1,51)))],'seeded_full_digit_alphabet')
        for s in ('0'*50,'01'*25,'0123456789'*5,'0'*24+'11'+'0'*24):add([s],'maximum_length_substring_enumeration')
    elif pid==2746:
        for n in range(1,5):
            for words in product(('a','b','ab','ba'),repeat=n):add([list(words)],'exhaustive_literal_join_choices')
        for _ in range(60):add([[''.join(rng.choices('abc',k=rng.randrange(1,5))) for _ in range(rng.randrange(1,9))]],'seeded_literal_join_strings')
        add([['a']*1000],'analytic_maximum_all_single_same',1)
        add([['a'*50]*1000],'analytic_maximum_all_equal_fifty_chars',49001)
        add([['ab'*25]*1000],'analytic_maximum_no_boundary_match',50000)
    elif pid==2750:
        for n in range(1,10):
            for values in product((0,1),repeat=n):add([list(values)],'exhaustive_cut_mask_partitions')
        for _ in range(40):add([[rng.randrange(2) for _ in range(rng.randrange(10,15))]],'seeded_cut_mask_partitions')
        add([[0]*100000],'analytic_maximum_no_one',0)
        add([[1]*100000],'analytic_maximum_every_cell_one',1)
        add([[0]*50000+[1]+[0]*49999],'analytic_maximum_single_one',1)
        add([[1,0]*50000],'analytic_independent_two_cut_choices_per_gap',pow(2,49999,MOD))
    elif pid==2768:
        for m,n in ((2,2),(2,3),(3,2),(3,3)):
            positions=list(product(range(m),range(n)))
            for mask in range(1<<len(positions)):add([m,n,[list(v) for i,v in enumerate(positions) if mask>>i&1]],'exhaustive_small_grid_colorings')
        for _ in range(50):
            m,n=rng.randrange(2,10),rng.randrange(2,10);positions=list(product(range(m),range(n)));rng.shuffle(positions);add([m,n,[list(v) for v in positions[:rng.randrange(len(positions)+1)]]],'seeded_dense_rectangle_blocks')
        total=99999**2
        add([100000,100000,[]],'analytic_maximum_all_white',[total,0,0,0,0])
        add([100000,100000,[[0,0],[0,99999],[99999,0],[99999,99999]]],'analytic_maximum_four_corners',[total-4,4,0,0,0])
        add([100000,100000,[[50000,50000]]],'analytic_maximum_single_interior',[total-4,4,0,0,0])
        add([100000,100000,[[0,2*i] for i in range(10000)]],'analytic_maximum_coordinate_count_isolated_edge',[total-19999,19999,0,0,0])
        add([100000,100000,[[i,j] for i in range(100) for j in range(100)]],'analytic_maximum_coordinate_count_solid_corner_square',[total-10000,1,198,0,9801])
    else:
        for num in range(1,51):
            for t in range(1,51):add([num,t],'exhaustive_official_domain_operation_reachability')
    return cases,categories


def expected_observation_bytes(batch,language):
    if language not in ('javascript','python'):raise ValueError('unsupported language')
    return sum(len(q.encoded({'i':i,'result':c['expected'],'result_type':q.expected_type(c['expected'],language),'args_before':c['args'],'args_after':c['args'],'alias_edges':[]})) for i,c in enumerate(batch))+len(q.encoded({'done':len(batch)}))+(language=='python')


def build_cases(pid,statement):
    cases,categories=_generate_cases(pid,statement)
    if len(cases)!=CASE_COUNT.get(pid) or q.sha(q.encoded(cases))!=CASES_SHA256.get(pid):raise ValueError('frozen case population drift')
    if len(q.encoded(cases))>q.MAX_FILE:raise ValueError('case file exceeds unchanged cap')
    for _,batch in q.batches(cases):
        if any(expected_observation_bytes(batch,lang)>q.LIMITS['max_output_bytes'] for lang in ('javascript','python')):raise ValueError('expected observations exceed unchanged cap')
    return cases,categories
