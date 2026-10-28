"""New deterministic cases; no delivered expected outputs are oracle inputs."""
from itertools import combinations, permutations, product
import ast
import html
import re
import json
from pathlib import Path
import random
import string
import oracles as o

ROOT=Path(__file__).resolve().parents[4]
BATCH=ROOT/'projects/algorithm_solver/catalogue/authored/downloaded-general68-v1'
ASSIGNMENT=json.loads((BATCH/'assignment.public-safe.json').read_text())
IDS=tuple(p['id'] for p in ASSIGNMENT['problems'])


def build(_statements=None):
    rng=random.Random(2026102801);data={i:[] for i in IDS};seen={i:set() for i in IDS}
    def add(pid,args,category='independent-seeded-small',want=None):
        key=json.dumps(args,separators=(',',':'))
        if key in seen[pid]:return
        seen[pid].add(key)
        data[pid].append({'args':args,'expected':o.expected(pid,args) if want is None else want,'category':category})
    if _statements is not None:
        for pid in IDS:
            for args,declared in official_examples(Path(_statements)/f'{pid}.json'):
                want=o.expected(pid,args)
                assert o.matches(pid,args,declared,want),('official-example-oracle-disagreement',pid,args,declared,want)
                add(pid,args,'official-example')
    # Complete bounded scalar domains and arithmetic edge neighborhoods.
    for n in list(range(-256,257))+[-2**31,2**31-1,1534236469,1463847412,1563847412,-1563847412,1000000000]:
        add(7,[n],'int32-reversal-and-overflow');add(9,[n],'signed-palindromes')
    for n in range(1,4000):add(13,[o.roman(n)],'complete-roman-domain')
    for n in range(1,46):add(70,[n],'complete-scalar-domain')
    for n in range(1,31):add(118,[n],'complete-scalar-domain')
    for n in range(34):add(119,[n],'complete-scalar-domain')
    for n in [1,26,27,52,53,676,677,702,703,2**31-1,*range(1,128)]:add(168,[n],'base26-boundaries')
    for n in [*range(201),3125,9999,10000]:add(172,[n],'factor-valuation')
    for n in range(201):add(204,[n],'trial-division-domain')
    for n in [1,2,3,10,100,500,1000,1690]:add(264,[n],'prime-factor-heap')
    for n in [*range(1,129),999,1000,9999,10000]:add(279,[n],'square-decomposition')
    for n in [*range(129),999999999,1000000000]:add(319,[n],'square-toggle-count')
    for n in range(-128,257):add(342,[n],'signed-integer-powers')
    for n in [4**k+d for k in range(16) for d in (-1,0,1) if -2**31<=4**k+d<2**31]:add(342,[n],'bit-neighborhoods')
    for n in range(2,59):add(343,[n],'complete-scalar-domain')
    for n in range(9):add(357,[n],'complete-scalar-domain')
    for x in range(1,9):
        for y in range(1,9):
            for target in range(1,18):add(365,[x,y,target],'complete-small-state-reachability')
    for n in [*range(1,129),*[(i*i)+d for i in (128,255,46340) for d in (-1,0,1)],2**31-1]:add(367,[n],'perfect-square-boundaries')
    for n in [*range(1,100),50000]:add(386,[n],'decimal-trie')
    for n in [*range(1,129),1000,5000]:add(390,[n],'explicit-elimination')
    for n in [*range(1,129),2**31-1]:add(397,[n],'shortest-integer-path')
    for byte in range(256):add(393,[[byte]],'every-leading-byte')
    for prefix in (0,127,128,191,192,193,223,224,239,240,247,248,255):
        for count in range(5):
            for suffix in (0,128,191,192,255):add(393,[[prefix]+[suffix]*count],'sequence-structure')
    for n in range(1,7):
        for bits in product((0,1),repeat=n):
            add(283,[list(bits)],'exhaustive-zero-placement')
    for _ in range(80):
        xs=[rng.randint(-9,9) for _ in range(rng.randint(1,8))]
        for pid in (189,198,213,215,229,238,274,275,300,324,334,344,349,350,368,376,396):
            if pid in (198,213):args=[[abs(v) for v in xs]]
            elif pid==189:args=[xs,rng.randint(0,100000)]
            elif pid==215:args=[xs,rng.randint(1,len(xs))]
            elif pid==238:args=[xs if len(xs)>=2 else xs+[0]]
            elif pid in (274,275):args=[[abs(v) for v in xs]];args[0].sort() if pid==275 else None
            elif pid==324:args=[rng.sample(range(30),len(xs))]
            elif pid==344:args=[[rng.choice(string.ascii_letters+' !') for _ in xs]]
            elif pid in (349,350):args=[[abs(v) for v in xs],[rng.randint(0,9) for _ in xs]]
            elif pid==368:args=[rng.sample(range(1,40),len(xs))]
            elif pid==376:args=[[v+10 for v in xs]]
            else:args=[xs]
            add(pid,args)
        ordered=sorted(rng.sample(range(-30,31),rng.randint(1,10)));k=rng.randrange(len(ordered))
        add(153,[ordered[k:]+ordered[:k]])
        peaks=[]
        for v in xs:
            if not peaks or peaks[-1]!=v:peaks.append(v)
        add(162,[peaks])
        sums={}
        for i,j in combinations(range(len(ordered)),2):sums.setdefault(ordered[i]+ordered[j],[]).append([i,j])
        unique=[s for s,pairs in sums.items() if len(pairs)==1]
        if unique:add(167,[ordered,rng.choice(unique)])
        add(179,[[abs(v) for v in xs[:6]]])
        add(209,[rng.randint(1,40),[abs(v)+1 for v in xs]])
        rows,cols=rng.randint(1,4),rng.randint(1,4)
        add(221,[[[rng.choice('01') for _ in range(cols)] for _ in range(rows)]])
        add(228,[sorted(set(xs))])
        matrix=[[r*10+c*2-20 for c in range(cols)] for r in range(rows)]
        add(240,[matrix,rng.randint(-20,30)])
        values=rng.sample(range(-100,101),rng.randint(2,5));singles=values[:2];paired=values[2:]
        arr=singles+paired+paired;rng.shuffle(arr);add(260,[arr])
        n=rng.randint(1,8);duplicate=rng.randint(1,n);arr=list(range(1,n+1))+[duplicate];rng.shuffle(arr);add(287,[arr])
        add(289,[[[rng.randrange(2) for _ in range(cols)] for _ in range(rows)]])
        s=''.join(rng.choices('01239',k=rng.randint(1,8)));guess=''.join(rng.choices('01239',k=len(s)));add(299,[s,guess])
        add(309,[[abs(v) for v in xs]])
        primes=sorted(rng.sample((2,3,5,7),rng.randint(1,4)));n=rng.randint(1,20)
        if o.smooth(n,primes)<=2**31-1:add(313,[n,primes])
        s=''.join(rng.choices('abc',k=rng.randint(1,9)));add(316,[s])
        words=[''.join(rng.choices('abcdef',k=rng.randint(1,6))) for _ in range(rng.randint(2,8))];add(318,[words])
        add(322,[sorted(rng.sample(range(1,15),rng.randint(1,5))),rng.randrange(41)])
        s=''.join(rng.choices(string.ascii_letters+' !?',k=rng.randint(1,30)));add(345,[s])
        add(371,[rng.randint(-1000,1000),rng.randint(-1000,1000)])
        exp=rng.randint(0,1000000);add(372,[rng.randint(1,2**31-1),[int(c) for c in str(exp)]])
        add(377,[rng.sample(range(1,8),rng.randint(1,5)),rng.randint(1,14)])
        n=rng.randint(1,4);matrix=[[r*10+c*2-30 for c in range(n)] for r in range(n)];add(378,[matrix,rng.randint(1,n*n)])
        s=''.join(rng.choices('abc',k=rng.randint(1,8)));t=''.join(rng.choices('abc',k=rng.randint(1,10)));add(383,[s,t])
        t=list(s+rng.choice('abc'));rng.shuffle(t);add(389,[s,''.join(t)])
        add(392,[s[:rng.randint(0,len(s))],t])
        add(393,[[rng.randrange(256) for _ in range(rng.randint(1,10))]])
        part=''.join(rng.choices('abc',k=rng.randint(1,3)));encoded=f'{rng.randint(1,4)}[a{rng.randint(1,4)}[{part}]]b';add(394,[encoded])
        add(395,[s,rng.randint(1,8)])
        words=[''.join(rng.choices(string.ascii_letters+string.digits,k=rng.randint(1,6))) for _ in range(rng.randint(1,6))]
        add(151,[' '*rng.randrange(4)+(' '*rng.randint(1,4)).join(words)+' '*rng.randrange(4)])
        # Arithmetic expression generation computes exact intermediate limits.
        left,right=rng.randint(-200,200),rng.choice([i for i in range(-20,21) if i]);op=rng.choice('+-*/');tokens=[str(left),str(right),op]
        add(150,[tokens])
    for pid in IDS:
        assert data[pid],pid
    return data


def official_examples(path):
    question=json.loads(path.read_text())['data']['question']
    body=re.sub(r'</?(?:p|pre|div|li|ul|ol|br)\b[^>]*>','\n',question['content'])
    body=html.unescape(re.sub(r'<[^>]*>','',body))
    examples=[]
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*\d+:|Constraints:|Follow up:|$)',body,re.S):
        node=ast.parse('f('+match[1].strip()+')',mode='eval').body
        assert isinstance(node,ast.Call) and not node.args and node.keywords
        args=[ast.literal_eval(k.value) for k in node.keywords]
        declared,_=json.JSONDecoder().raw_decode(match[2].strip())
        examples.append((args,declared))
    assert examples,question['questionFrontendId']
    return examples
