"""Deterministic independent batch05 cases; no delivered tests or sources read."""
import ast
import hashlib
import html
from itertools import combinations, permutations, product
import json
from pathlib import Path
import random
import re

import oracles as o

ASSIGNED_IDS = o.IDS
IDS = o.EXECUTABLE_IDS
SEED = 2026102805
MAX_HOST_PACKET_BYTES = 16 * 1024**2
MAX_EXPECTED_OUTPUT_BYTES = 16 * 1024**2


def packet(values, indices):
    """Existing value-observer packet; host expectations never enter it."""
    return {'entry':'solve','calls':[{'args':values[i]['args']} for i in indices]}


def projected_output_bytes(values, indices):
    """Host-only conservative successful-observation projection.

    The fixed value observers serialize these fields plus one newline per row
    and a terminal done record. Result type uses the longer supported spelling;
   128 extra bytes per row cover numerical formatting differences. Actual raw
    output remains subject to the unchanged sandbox output monitor.
    """
    total=len(encoded({'done':len(indices)}))+2
    for index,i in enumerate(indices):
        row=values[i];want=row['expected'];kind={list:'object',str:'string',bool:'boolean',int:'number',float:'number'}[type(want)]
        value={'i':index,'result':want,'result_type':kind,'args_before':row['args'],
               'args_after':row['args'],'alias_edges':[]}
        total+=len(encoded(value))+1+128
    return total


def batch_plan(values):
    """Prospective bounded host packets and first-call carryover repetition.

    Ordinary groups have at most32 distinct calls followed by their first call.
    A large boundary normally repeats itself. If duplicate input exceeds the
    explicit16MiB host packet budget or projected observations exceed the
    existing16MiB output bound, a small existing case brackets the boundary in
    the same interpreter. Child RLIMIT_FSIZE remains unchanged and is not
    mislabeled as a host input cap. Oversized single cases fail closed.
    """
    if not values:raise ValueError('nonempty fixed-problem case list required')
    probe=min(range(len(values)),key=lambda i:len(encoded(values[i]['args']))+projected_output_bytes(values,[i]))
    groups=[];current=[];size=0
    def append(indices):
        if len(encoded(packet(values,indices)))>MAX_HOST_PACKET_BYTES:
            raise ValueError('prospective host packet budget exceeded; no execution permitted')
        if projected_output_bytes(values,indices)>MAX_EXPECTED_OUTPUT_BYTES:
            raise ValueError('existing output bound exceeded by planned successful observations')
        groups.append(indices)
    def flush():
        nonlocal current,size
        if current:append(current+[current[0]])
        current=[];size=0
    for i,row in enumerate(values):
        length=len(encoded(row['args']))
        if row.get('isolate'):
            flush();indices=[i,i]
            if (len(encoded(packet(values,indices)))>MAX_HOST_PACKET_BYTES or
                    projected_output_bytes(values,indices)>MAX_EXPECTED_OUTPUT_BYTES):indices=[probe,i,probe]
            append(indices);continue
        if current and (len(current)>=32 or size+length>256*1024):flush()
        current.append(i);size+=length
    flush();return groups


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def official_examples(path, read_raw=None):
    raw=Path(path).read_bytes() if read_raw is None else read_raw(Path(path))
    question=json.loads(raw)['data']['question']
    body=re.sub(r'</?(?:p|pre|div|li|ul|ol|br)\b[^>]*>','\n',question['content'])
    body=html.unescape(re.sub(r'<[^>]*>','',body));examples=[]
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*\d+:|Constraints:|Follow up:|$)',body,re.S):
        call=ast.parse('f('+match[1].strip()+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or not call.keywords:raise ValueError('ordered official example syntax')
        args=[ast.literal_eval(k.value) for k in call.keywords]
        declared,_=json.JSONDecoder().raw_decode(match[2].strip());examples.append((args,declared))
    if not examples:raise ValueError('official public examples missing')
    return examples


def validate_definitions(directory, read_raw=None, selected_ids=IDS):
    contract=json.loads(Path(__file__).with_name('contracts.json').read_text())
    rows={r['id']:r for r in contract['problems']}
    for pid in selected_ids:
        pin=rows[pid]['definition'];path=Path(directory)/f'{pid}.json'
        raw=path.read_bytes() if read_raw is None else read_raw(path)
        question=json.loads(raw)['data']['question']
        if (hashlib.sha256(raw).hexdigest()!=pin['snapshot_sha256'] or
                hashlib.sha256((question.get('content') or '').encode()).hexdigest()!=pin['content_sha256'] or
                question.get('questionFrontendId')!=str(pid) or question.get('titleSlug')!=pin['slug'] or
                not question.get('content') or question.get('isPaidOnly') is not False):
            raise ValueError('exact public definition identity changed')


def compositions(n):
    if not n:yield [];return
    for first in range(1,n+1):
        for tail in compositions(n-first):yield [first]+tail


def build(statements=None, read_raw=None, selected_ids=IDS):
    if not selected_ids or len(set(selected_ids))!=len(selected_ids) or any(type(pid) is not int or pid not in IDS for pid in selected_ids):raise ValueError('invalid reference subset')
    rng=random.Random(SEED);data={pid:[] for pid in IDS};seen={pid:set() for pid in IDS};absent=object()
    def add(pid,args,category='independent-seeded-small',want=absent,isolate=False):
        o.validate_generated(pid,args);key=encoded(args)
        if key in seen[pid]:return
        result=o.expected(pid,args) if want is absent else want
        if pid==673 and not 1<=result<2**31:raise ValueError('LIS count exceeds guaranteed domain')
        seen[pid].add(key);row={'args':args,'expected':result,'category':category}
        if isolate:row['isolate']=True
        data[pid].append(row)
    if statements is not None:
        validate_definitions(statements, read_raw, selected_ids)
        for pid in selected_ids:
            for args,declared in official_examples(Path(statements)/f'{pid}.json', read_raw):
                expected=o.expected(pid,args)
                if not o.matches(pid,args,declared,expected):raise ValueError(f'official example reference disagreement: {pid}')
                add(pid,args,'official-example')
    for n in range(1,6):
        for nums in product((2,3,4),repeat=n):add(553,[list(nums)],'exhaustive-division-parenthesizations')
    for width in range(1,7):
        rows=list(compositions(width))
        for a in rows:
            add(554,[[a]],'exhaustive-small-row-compositions')
            for b in rows[:16]:add(554,[[a,b]],'bounded-composition-crossings')
    for n in [*range(1,401),12,21,120,201,115,1999999999,2147483476,2147483647,1000000000]:add(556,[n],'digit-multiset-and-int32-boundaries')
    for n in range(1,7):
        for nums in product((-1,0,1),repeat=n):
            for k in (-2,0,2):add(560,[list(nums),k],'exhaustive-small-contiguous-intervals')
    for n in range(1,7):
        for p in permutations(range(n)):add(565,[list(p)],'exhaustive-small-permutation-orbits')
    for a in ('a','ab','aa','aba','abc','aaaa'):
        for n in range(1,7):
            for b in product('ab',repeat=n):add(567,[a,''.join(b)],'exhaustive-small-literal-windows')
    for m in range(1,5):
        for n in range(1,5):
            for moves in range(6):
                for r in range(m):
                    for c in range(n):add(576,[m,n,moves,r,c],'exhaustive-small-counted-paths')
    for n in range(1,7):
        for nums in product((0,1,2),repeat=n):
            add(581,[list(nums)],'exhaustive-sorted-intervals');add(665,[list(nums)],'exhaustive-single-index-repair')
    words=[''.join(p) for n in range(1,5) for p in product('ab',repeat=n)]
    for a in words:
        for b in words:add(583,[a,b],'exhaustive-small-deletion-intersection')
    for a in range(-10,11):
        for b in range(1,11):
            if a and o.math.gcd(a,b)==1:add(592,[f'{a}/{b}'],'irreducible-single-fraction')
    for points in combinations(list(product(range(-1,2),repeat=2)),4):add(593,[list(p) for p in points],'exhaustive-small-square-configurations')
    for m in range(1,5):
        for n in range(1,5):
            choices=[[a,b] for a in range(1,m+1) for b in range(1,n+1)]
            add(598,[m,n,[]],'empty-operations')
            for a in choices:
                add(598,[m,n,[a]],'small-explicit-matrix')
                for b in choices[:6]:add(598,[m,n,[a,b]],'small-explicit-matrix')
    for n in range(1,8):
        for nums in product((0,1,2),repeat=n):add(611,[list(nums)],'exhaustive-triangle-triples')
    for n in range(1,9):
        for a in range(n+1):
            for gap in range(4):add(621,[['A']*a+['B']*(n-a),gap],'exhaustive-two-label-scheduling-states')
    for c in range(1001):add(633,[c],'complete-small-square-sum-domain')
    for c in (2**31-1,2147395600,2147395601,1000000000):add(633,[c],'full-int32-square-neighborhoods')
    for n in range(1,101):add(650,[n],'complete-small-copy-paste-reachability')
    for n in range(1,7):
        for nums in product((1,2,3),repeat=n):add(659,[sorted(nums)],'exhaustive-small-consecutive-multiset-covers')
    for m in range(1,11):
        for n in range(1,11):
            for k in range(1,m*n+1):add(668,[m,n,k],'complete-small-multiplication-tables')
    for n in range(1001):add(670,[n],'every-small-single-swap')
    for n in range(1,15):
        for presses in range(10):add(672,[n,presses],'all-button-parity-combinations')
    for n in range(1,7):
        for nums in product((1,2,3),repeat=n):add(673,[list(nums)],'exhaustive-index-subsequences')
    for n in range(1,8):
        for s in product('()*',repeat=n):add(678,[''.join(s)],'exhaustive-wildcard-balance-reachability')
    for n in range(1,8):
        for s in product('RD',repeat=n):add(649,[''.join(s)],'exhaustive-optimal-opponent-ban-trees')
    for n in range(1,8):
        for s in product('ab',repeat=n):add(680,[''.join(s)],'exhaustive-literal-palindrome-deletions')
    for n in range(1,7):
        for steps in range(5):
            for r in range(n):
                for c in range(n):add(688,[n,steps,r,c],'complete-small-integer-surviving-path-counts')
    for rows in range(1,4):
        for cols in range(1,4):
            for bits in product((0,1),repeat=rows*cols):add(695,[[list(bits[r*cols:(r+1)*cols]) for r in range(rows)]],'exhaustive-small-land-components')
    for _ in range(64):
        n=rng.randint(1,8);nums=[rng.randint(-8,8) for _ in range(n)]
        add(553,[[rng.randint(2,1000) for _ in range(rng.randint(1,10))]])
        add(560,[nums,rng.randint(-10,10)]);add(581,[nums]);add(665,[nums]);add(673,[nums])
        add(611,[[abs(x) for x in nums]])
        a=''.join(rng.choices('abc',k=n));b=''.join(rng.choices('abc',k=rng.randint(1,10)))
        add(567,[a,b]);add(583,[a,b]);add(647,[a]);add(680,[b]);add(686,[a,b])
        add(624,[[sorted(rng.randint(-20,20) for _ in range(rng.randint(1,6))) for _ in range(rng.randint(2,5))]])
        add(621,[[rng.choice('ABC') for _ in range(n)],rng.randint(0,4)])
        fractions=[]
        for i in range(rng.randint(1,10)):
            numerator,denominator=rng.randint(1,10),rng.randint(1,10)
            divisor=o.math.gcd(numerator,denominator);numerator//=divisor;denominator//=divisor
            fractions.append(('' if i==0 else rng.choice('+-'))+f'{numerator}/{denominator}')
        add(592,[''.join(fractions)])
        add(593,[[rng.randint(-10000,10000),rng.randint(-10000,10000)] for _ in range(4)])
        paths=[]
        for directory in range(rng.randint(1,5)):
            files=[f'{i}.txt({rng.choice(("abc","efg","different"))})' for i in range(rng.randint(1,5))]
            paths.append('root/'+str(directory)+' '+' '.join(files))
        add(609,[paths])
        # Each interval is an independent call; nested and recursive cases below.
        functions=rng.randint(1,5);logs=[];clock=0
        for _ in range(rng.randint(1,6)):
            ident=rng.randrange(functions);length=rng.randint(1,8)
            logs.extend([f'{ident}:start:{clock}',f'{ident}:end:{clock+length-1}']);clock+=length
        add(636,[functions,logs])
        dimensions=rng.randint(1,4);price=[rng.randint(0,10) for _ in range(dimensions)];needs=[rng.randint(0,4) for _ in price]
        offers=[]
        for _ in range(rng.randint(1,5)):
            quantities=[rng.randint(0,5) for _ in price]
            if not any(quantities):quantities[0]=1
            offers.append(quantities+[rng.randint(0,30)])
        add(638,[price,offers,needs])
        a,c=rng.randint(0,10),rng.randint(0,10);value=rng.randint(-5,5);b=rng.randint(-10,10);d=b+(a-c)*value
        add(640,[f'{a}x{b:+d}={c}x{d:+d}'])
        pairs=[]
        for _ in range(n):
            lo=rng.randint(-10,9);pairs.append([lo,rng.randint(lo+1,10)])
        add(646,[pairs])
        roots=[''.join(rng.choices('abc',k=rng.randint(1,4))) for _ in range(rng.randint(1,8))]
        sentence=' '.join(''.join(rng.choices('abc',k=rng.randint(1,8))) for _ in range(n))
        add(648,[roots,sentence])
        ordered=sorted(nums);add(658,[ordered,rng.randint(1,n),rng.randint(-10,10)])
        add(670,[rng.randint(0,10**8)])
        distinct=[rng.choice(('a','ab','abc','b','ba','c')) for _ in range(n)]
        add(692,[distinct,rng.randint(1,len(set(distinct)))])
        n=rng.randint(3,10);tree={tuple(sorted((i,rng.randrange(1,i)))) for i in range(2,n+1)}
        missing=[e for e in combinations(range(1,n+1),2) if e not in tree]
        edges=[list(e) for e in sorted(tree)]+[list(rng.choice(missing))];rng.shuffle(edges);add(684,[edges])
        nums=[rng.randint(1,9) for _ in range(rng.randint(1,10))]
        if max(o.Counter(nums).values())<=4:add(698,[nums,rng.randint(1,len(nums))])
    # Derived full-domain witnesses are separate from bounded enumeration.
    add(553,[[1000]*10],'maximum-operand-count-and-value')
    for nums,answer in [([0]*20000,20000*20001//2),([1000]*20000,0)]:add(560,[nums,0],'analytic-maximum-length',answer,True)
    add(565,[list(range(100000))],'analytic-maximum-fixed-points',1,True)
    add(565,[list(range(1,100000))+[0]],'analytic-maximum-single-cycle',100000,True)
    add(567,['a'*10000,'a'*10000],'analytic-maximum-equal-strings',True,True)
    add(567,['b','a'*10000],'analytic-maximum-disjoint-alphabet',False,True)
    add(576,[50,50,50,0,0],'full-grid-and-move-bounds',isolate=True)
    add(581,[list(range(10000))],'analytic-maximum-sorted',0,True)
    add(581,[list(range(10000,0,-1))],'analytic-maximum-reversed',10000,True)
    add(583,['a'*500,'b'*500],'analytic-maximum-disjoint-strings',1000,True)
    add(583,['a'*500,'a'*500],'analytic-maximum-equal-strings',0,True)
    add(554,[[[2**31-1]]*10000],'analytic-maximum-rows-no-internal-edge',10000,True)
    add(593,[[-10000,-10000],[-10000,10000],[10000,-10000],[10000,10000]],'maximum-coordinate-square')
    add(598,[40000,40000,[]],'analytic-maximum-area-empty-operations',1600000000,True)
    add(598,[40000,40000,[[40000,40000]]*10000],'analytic-maximum-operations-uniform-increment',1600000000,True)
    add(611,[[1000]*1000],'analytic-maximum-equal-triangles',1000*999*998//6,True)
    add(609,[[f'r{i} f(x)' for i in range(20000)]],'maximum-directory-count-one-content-group',isolate=True)
    add(621,[['A']*10000,100],'analytic-single-label-cooling',9999*101+1,True)
    add(624,[[[i] for i in range(-10000,10001)]],'analytic-many-singleton-arrays',20000,True)
    add(624,[[[-10000]*500]+[[10000]*500 for _ in range(199)]],'analytic-maximum-total-array-elements',20000,True)
    add(636,[1,['0:start:0','0:end:1000000000']],'analytic-full-timestamp-span',[1000000001],True)
    add(636,[1,['0:start:0','0:start:2','0:end:5','0:start:6','0:end:6','0:end:7']],'recursive-exclusive-intervals')
    add(638,[[10]*6,[[1]*6+[0]],[0]*6],'analytic-zero-needs',0,True)
    add(638,[[10]*6,[[50]*6+[0]]*100,[10]*6],'analytic-maximum-quantity-state-domain-unusable-offers',600,True)
    add(640,['2x'+'+x'*249+'='+'x'+'+x'*249],'analytic-maximum-equation-length','x=0',True)
    add(646,[[[i,i+1] for i in range(-1000,1000,2)]],'analytic-maximum-disjoint-chain',1000,True)
    add(647,['a'*1000],'analytic-maximum-uniform-palindromes',500500,True)
    add(648,[['a'], ' '.join(['a'*999]*1000)],'analytic-maximum-word-count-and-length',' '.join(['a']*1000),True)
    add(649,['R'*10000],'analytic-single-party', 'Radiant',True)
    add(649,['D'*10000],'analytic-single-party', 'Dire',True)
    add(649,['RD'*5000],'analytic-maximum-alternating-first-party-dominance','Radiant',True)
    add(649,['DR'*5000],'analytic-maximum-alternating-first-party-dominance','Dire',True)
    add(650,[1000],'full-scalar-bound',isolate=True)
    add(658,[[-10000]*10000,10000,10000],'analytic-entire-array-required',[-10000]*10000,True)
    add(659,[[1]*3333+[2]*3333+[3]*3333+[4]],'analytic-complete-triplet-multiplicity-and-one-extension',True,True)
    add(659,[[1]*10000],'analytic-no-three-consecutive-values',False,True)
    add(665,[list(range(10000))],'maximum-sorted-input',isolate=True)
    add(668,[30000,30000,1],'analytic-table-minimum',1,True)
    add(668,[30000,30000,900000000],'analytic-table-maximum',900000000,True)
    add(670,[100000000],'full-scalar-bound')
    add(672,[1000,1000],'full-bulb-and-press-bounds',isolate=True)
    add(673,[[1]*2000],'analytic-maximum-equal-lis-count',2000,True)
    add(673,[list(range(2000))],'analytic-maximum-strictly-increasing',1,True)
    add(678,['*'*100],'full-wildcard-length-bound',isolate=True)
    add(680,['a'*100000],'analytic-maximum-palindrome',True,True)
    add(684,[[[i,i+1] for i in range(1,1000)]+[[1,1000]]],'maximum-single-cycle-last-edge',[1,1000],True)
    add(686,['a','a'*10000],'analytic-maximum-repeat-count',10000,True)
    add(686,['a'*9999+'b','b'+'a'*9999],'analytic-maximum-equal-length-boundary-crossing',2,True)
    add(688,[25,100,12,12],'full-board-and-move-bounds',isolate=True)
    add(692,[['abcdefghij']*500,1],'analytic-maximum-duplicate-word-count',['abcdefghij'],True)
    words=['aaaaaaa'+''.join(chr(97+(i//26**k)%26) for k in (2,1,0)) for i in range(500)]
    add(692,[words,500],'analytic-maximum-distinct-word-count',sorted(words),True)
    add(695,[[[1]*50 for _ in range(50)]],'analytic-maximum-land-component',2500,True)
    add(695,[[[0]*50 for _ in range(50)]],'analytic-maximum-water-grid',0,True)
    add(698,[list(range(1,17)),8],'analytic-complementary-pairs',True,True)
    add(698,[[10000]*4+[9999]*4+[9998]*4+[9997]*4,4],'analytic-four-equal-column-groups',True,True)
    if set(data)!=set(IDS) or any(not rows for rows in data.values()):raise ValueError('incomplete public subset')
    return {pid:data[pid] for pid in selected_ids}
