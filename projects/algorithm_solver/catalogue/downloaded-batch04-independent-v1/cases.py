"""New bounded cases and official examples; delivered tests are not oracle inputs."""
import ast
from collections import Counter
import html
from itertools import combinations, permutations, product
import json
from pathlib import Path
import random
import re
import string

import oracles as o

IDS = o.IDS


def integer(x, low, high):
    return type(x) is int and low <= x <= high


def array(x, low, high, minimum=1, maximum=100000):
    return (type(x) is list and minimum <= len(x) <= maximum
            and all(integer(v, low, high) for v in x))


def matrix(x, low, high, rows=200, cols=200):
    return (type(x) is list and 1 <= len(x) <= rows and type(x[0]) is list
            and 1 <= len(x[0]) <= cols and all(type(r) is list and len(r) == len(x[0])
            and all(integer(v, low, high) for v in r) for r in x))


def letters(x, alphabet, minimum=1, maximum=100000):
    return type(x) is str and minimum <= len(x) <= maximum and all(c in alphabet for c in x)


def validate_generated(pid, args):
    """Check domain facts for generated cases, without pretending to prove all preconditions."""
    arity = {402:2,408:2,410:2,418:3,424:2,433:3,438:2,440:2,454:4,
             458:3,464:2,474:3,475:2,494:2,495:2,502:4}
    assert type(args) is list and len(args) == arity.get(pid,1), ('arity',pid)
    x = args[0]; good = False
    if pid == 402:
        good = letters(x,string.digits,1,100000) and (len(x)==1 or x[0]!='0') and integer(args[1],1,len(x))
    elif pid == 403:
        good = array(x,0,2**31-1,2,2000) and x[0]==0 and all(a<b for a,b in zip(x,x[1:]))
    elif pid == 406:
        good = type(x) is list and 1 <= len(x) <= 2000 and all(type(p) is list and len(p)==2 and integer(p[0],0,10**6) and integer(p[1],0,len(x)-1) for p in x)
    elif pid == 408:
        good = letters(x,string.ascii_lowercase,1,20) and letters(args[1],string.ascii_lowercase+string.digits,1,20)
    elif pid == 410:
        good = array(x,0,10**6,1,1000) and integer(args[1],1,min(50,len(x)))
    elif pid == 413: good = array(x,-1000,1000,1,5000)
    elif pid == 416: good = array(x,1,100,1,200)
    elif pid == 417: good = matrix(x,0,100000)
    elif pid == 418:
        good = type(x) is list and 1 <= len(x) <= 100 and all(letters(w,string.ascii_lowercase,1,10) for w in x) and integer(args[1],1,20000) and integer(args[2],1,20000)
    elif pid == 419:
        good = type(x) is list and 1 <= len(x) <= 200 and 1 <= len(x[0]) <= 200 and all(type(r) is list and len(r)==len(x[0]) and all(c in '.X' for c in r) for r in x)
        good = good and all(len({r for r,c in group}) == 1 or len({c for r,c in group}) == 1 for group in o.components(x))
    elif pid == 421: good = array(x,0,2**31-1,1,200000)
    elif pid == 423: good = letters(x,'egfihonsrutwvxz',1,100000)
    elif pid == 424: good = letters(x,string.ascii_uppercase,1,100000) and integer(args[1],0,len(x))
    elif pid == 433:
        good = letters(x,'ACGT',8,8) and letters(args[1],'ACGT',8,8) and type(args[2]) is list and len(args[2]) <= 10 and all(letters(w,'ACGT',8,8) for w in args[2])
    elif pid in (435,436,452):
        low,high,maximum = (-50000,50000,100000) if pid==435 else (-10**6,10**6,20000) if pid==436 else (-2**31,2**31-1,100000)
        good = type(x) is list and 1 <= len(x) <= maximum and all(type(p) is list and len(p)==2 and all(integer(v,low,high) for v in p) and (p[0] <= p[1] if pid==436 else p[0] < p[1]) for p in x)
        if pid==436: good = good and len({p[0] for p in x}) == len(x)
    elif pid == 438: good = all(letters(s,string.ascii_lowercase,1,30000) for s in args)
    elif pid == 440: good = integer(x,1,10**9) and integer(args[1],1,x)
    elif pid == 442: good = array(x,1,len(x),1,100000) and max(Counter(x).values()) <= 2
    elif pid == 443: good = type(x) is list and 1 <= len(x) <= 2000 and all(letters(c,string.printable[:-6]+' ',1,1) for c in x)
    elif pid == 446: good = array(x,-2**31,2**31-1,1,1000)
    elif pid == 447:
        good = type(x) is list and 1 <= len(x) <= 500 and all(array(p,-10000,10000,2,2) for p in x) and len(set(map(tuple,x))) == len(x)
    elif pid == 451: good = letters(x,string.ascii_letters+string.digits,1,500000)
    elif pid == 453: good = array(x,-10**9,10**9,1,100000) and 0 <= sum(x)-len(x)*min(x) < 2**31
    elif pid == 454: good = all(array(a,-2**28,2**28,1,200) and len(a)==len(x) for a in args)
    elif pid == 456: good = array(x,-10**9,10**9,1,200000)
    elif pid == 457: good = array(x,-1000,1000,1,5000) and all(x)
    elif pid == 458: good = integer(x,1,1000) and integer(args[1],1,100) and integer(args[2],args[1],100)
    elif pid == 462: good = array(x,-10**9,10**9,1,100000)
    elif pid == 464: good = integer(x,1,20) and integer(args[1],0,300)
    elif pid == 467: good = letters(x,string.ascii_lowercase,1,100000)
    elif pid == 468: good = letters(x,string.ascii_letters+string.digits+'.:',1,1000)
    elif pid == 473: good = array(x,1,10**8,1,15)
    elif pid == 474:
        good = type(x) is list and 1 <= len(x) <= 600 and all(letters(w,'01',1,100) for w in x) and integer(args[1],1,100) and integer(args[2],1,100)
    elif pid == 475: good = all(array(a,1,10**9,1,30000) for a in args)
    elif pid == 477: good = array(x,0,10**9,1,10000)
    elif pid == 481: good = integer(x,1,100000)
    elif pid == 486: good = array(x,0,10**7,1,20)
    elif pid == 491: good = array(x,-100,100,1,15)
    elif pid == 493: good = array(x,-2**31,2**31-1,1,50000)
    elif pid == 494: good = array(x,0,1000,1,20) and sum(x) <= 1000 and integer(args[1],-1000,1000)
    elif pid == 495: good = array(x,0,10**7,1,10000) and x == sorted(x) and integer(args[1],0,10**7)
    elif pid == 498: good = matrix(x,-100000,100000,10000,10000) and len(x)*len(x[0]) <= 10000
    elif pid == 502:
        good = integer(x,1,100000) and integer(args[1],0,10**9) and array(args[2],0,10000,1,100000) and array(args[3],0,10**9,1,100000) and len(args[2]) == len(args[3]) and args[1]+sum(args[2]) < 2**31
    elif pid == 503: good = array(x,-10**9,10**9,1,10000)
    assert good, ('generated case outside pinned or prepared domain',pid,args if len(str(args))<1000 else 'large')


def official_examples(path):
    q = json.loads(Path(path).read_bytes())['data']['question']
    if not q['content']: return []
    body = re.sub(r'</?(?:p|pre|div|li|ul|ol|br)\b[^>]*>','\n',q['content'])
    body = html.unescape(re.sub(r'<[^>]*>','',body)); result = []
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*\d+:|Constraints:|Follow up:|$)',body,re.S):
        node = ast.parse('f('+match[1].strip()+')',mode='eval').body
        assert isinstance(node,ast.Call) and not node.args and node.keywords
        args = [ast.literal_eval(k.value) for k in node.keywords]
        declared,_ = json.JSONDecoder().raw_decode(match[2].strip())
        result.append((args,declared))
    assert result, q['questionFrontendId']
    return result


def build(statements=None):
    rng = random.Random(2026102804); data = {pid:[] for pid in IDS}; seen = {pid:set() for pid in IDS}; unset = object()
    def add(pid,args,category='independent-seeded-small',want=unset,isolate=False):
        validate_generated(pid,args)
        key = json.dumps(args,sort_keys=True,separators=(',',':'))
        if key in seen[pid]: return
        seen[pid].add(key)
        value = o.expected(pid,args) if want is unset else want
        if pid in (446,453,462,477,502): assert type(value) is int and -(2**31) <= value < 2**31
        data[pid].append({'args':args,'expected':value,'category':category,'isolate':isolate})
    if statements is not None:
        for pid in IDS:
            for args,declared in official_examples(Path(statements)/f'{pid}.json'):
                want = o.expected(pid,args)
                assert (declared == len(want) if pid==443 else o.matches(pid,args,declared,want)), ('official example disagreement',pid,args,declared,want)
                add(pid,args,'official-example-functional-adapter' if pid==443 else 'official-example')
    for length in range(1,7):
        for digits in product('012',repeat=length):
            if length > 1 and digits[0]=='0': continue
            text = ''.join(digits)
            for k in {1,length,max(1,length//2)}: add(402,[text,k],'exhaustive-small-digit-deletions')
    for count in range(2,8):
        for chosen in combinations(range(1,11),count-1): add(403,[[0,*chosen]],'exhaustive-small-stone-positions')
    for n in range(1,6):
        for values in product((-1,0,1),repeat=n):
            xs = list(values)
            for pid in (413,446,456,493,503): add(pid,[xs],'exhaustive-small-sign-and-order')
    for bits in product('.X',repeat=9):
        board = [list(bits[r*3:r*3+3]) for r in range(3)]
        if all(len({r for r,c in group}) == 1 or len({c for r,c in group}) == 1 for group in o.components(board)):
            add(419,[board],'exhaustive-valid-three-by-three-ships')
    for n in range(1,6):
        for values in product((-2,-1,1,2),repeat=n): add(457,[list(values)],'exhaustive-small-circular-graphs')
    for n in range(1,129): add(481,[n],'fixed-point-run-description')
    for buckets in range(1,101):
        for die,test in ((1,1),(1,2),(15,15),(15,30),(25,100)):
            add(458,[buckets,die,test],'exact-information-capacity-boundaries')
    for n in range(1,8):
        for desired in range(0,min(30,n*(n+1)//2+3)):
            add(464,[n,desired],'complete-small-game-states')
    addresses = ['172.16.254.1','172.16.254.01','256.256.256.256','0.0.0.0','255.255.255.255',
                 '1.1.1','1.1.1.1.','1..1.1','1e1.1.1.1','2001:0db8:85a3:0000:0000:8a2e:0370:7334',
                 '2001:db8:85a3::8a2e:370:7334','0:0:0:0:0:0:0:0','FFFF:ffff:0:0:0:0:0:1','1:2:3:4:5:6:7:gggg']
    for s in addresses: add(468,[s],'address-grammar-boundaries')
    add(433,['AACCGGTT','AACCGGTT',[]],'zero-mutation-does-not-require-bank-entry')
    for _ in range(80):
        size = rng.randint(1,8); values = [rng.randint(-5,5) for _ in range(size)]
        heights = [rng.randint(0,10) for _ in range(size)]
        queue = [[h,sum(v >= h for v in heights[:i])] for i,h in enumerate(heights)]
        shuffled = [p[:] for p in queue]; rng.shuffle(shuffled); add(406,[shuffled],'constructed-valid-queue')
        word = ''.join(rng.choices('abc',k=rng.randint(1,12))); abbr = ''.join(rng.choices('abc01239',k=rng.randint(1,12)))
        add(408,[word,abbr],'prepared-word-abbreviation-case')
        add(408,[word,str(len(word))],'prepared-whole-word-abbreviation')
        add(410,[[abs(v) for v in values],rng.randint(1,size)])
        add(416,[[abs(v)+1 for v in values]])
        rows,cols = rng.randint(1,5),rng.randint(1,5)
        add(417,[[[rng.randrange(6) for _ in range(cols)] for _ in range(rows)]])
        sentence = [''.join(rng.choices('ab',k=rng.randint(1,6))) for _ in range(rng.randint(1,4))]
        add(418,[sentence,rng.randint(1,8),rng.randint(1,20)],'prepared-screen-layout-case')
        add(421,[[abs(v) for v in values]])
        chosen = [rng.randrange(10) for _ in range(rng.randint(1,8))]
        s = list(''.join(o.DIGITS[d] for d in chosen)); rng.shuffle(s); add(423,[''.join(s)],'spelled-digit-multiset-model')
        s = ''.join(rng.choices('ABCD',k=rng.randint(1,15))); add(424,[s,rng.randint(0,len(s))])
        gene = lambda: ''.join(rng.choices('ACGT',k=8))
        start = gene(); bank = [start]
        for _step in range(rng.randint(0,9)):
            last = list(bank[-1]); last[rng.randrange(8)] = rng.choice('ACGT'); bank.append(''.join(last))
        end = rng.choice(bank) if rng.randrange(2) else gene(); bank = list(dict.fromkeys(bank[1:])); add(433,[start,end,bank])
        intervals = [[v,v+rng.randint(1,6)] for v in values]; add(435,[intervals]); add(452,[intervals])
        starts = rng.sample(range(-20,21),size); add(436,[[[v,v+rng.randrange(6)] for v in starts]])
        s = ''.join(rng.choices('abc',k=rng.randint(1,15))); pattern = ''.join(rng.choices('abc',k=rng.randint(1,8))); add(438,[s,pattern])
        n = rng.randint(1,1000); add(440,[n,rng.randint(1,n)])
        pool = list(range(1,size+1))*2; rng.shuffle(pool); add(442,[pool[:size]])
        chars = [rng.choice('abA19!?') for _ in range(rng.randint(1,30))]; add(443,[chars])
        points = rng.sample([(r,c) for r in range(-3,4) for c in range(-3,4)],size); add(447,[[list(p) for p in points]])
        s = ''.join(rng.choices('abAB01',k=rng.randint(1,30))); add(451,[s])
        add(453,[values]); add(462,[values])
        add(454,[[rng.randint(-5,5) for _ in range(min(size,5))] for _ in range(4)])
        add(467,[''.join(rng.choices('abxyz',k=rng.randint(1,15)))])
        add(468,[''.join(rng.choices('0129abcdefG.:',k=rng.randint(1,39)))])
        add(473,[[abs(v)+1 for v in values]])
        strings = [''.join(rng.choices('01',k=rng.randint(1,6))) for _ in range(size)]; add(474,[strings,rng.randint(1,8),rng.randint(1,8)])
        add(475,[[abs(v)+1 for v in values],[rng.randint(1,30) for _ in range(rng.randint(1,8))]])
        add(477,[[abs(v) for v in values]]); add(486,[[abs(v) for v in values]])
        add(491,[values]); add(494,[[abs(v) for v in values],rng.randint(-30,30)])
        add(495,[sorted(abs(v) for v in values),rng.randint(0,8)])
        add(498,[[[rng.randint(-10,10) for _ in range(cols)] for _ in range(rows)]])
        add(502,[rng.randint(1,size+2),rng.randrange(6),[rng.randrange(8) for _ in range(size)],[rng.randrange(12) for _ in range(size)]])
    # Large legal witnesses use independently derived results, never the supplied functions.
    add(402,['9'*100000,50000],'maximum-length-identical-digits',want='9'*50000,isolate=True)
    add(403,[list(range(2000))],'maximum-consecutive-stones',want=True,isolate=True)
    add(403,[[0,2**31-1]],'maximum-position-unreachable',want=False)
    add(410,[[10**6]*1000,50],'maximum-size-uniform-partition',want=20*10**6,isolate=True)
    add(413,[[0]*5000],'maximum-uniform-arithmetic-array',want=(4999*4998)//2,isolate=True)
    add(416,[[100]*200],'maximum-even-uniform-sum',want=True,isolate=True)
    add(417,[[[7]*200 for _ in range(200)]],'maximum-flat-ocean-grid',want=[[r,c] for r in range(200) for c in range(200)],isolate=True)
    add(418,[['a'],20000,20000],'prepared-maximum-screen-resource-witness',want=200000000,isolate=True)
    add(421,[[0,2**31-1]],'maximum-xor-value',want=2**31-1)
    add(423,['zero'*25000],'maximum-valid-spelled-input',want='0'*25000,isolate=True)
    add(424,['A'*100000,0],'maximum-constant-replacement-window',want=100000,isolate=True)
    add(435,[[[-50000+i,-50000+i+1] for i in range(100000)]],'maximum-touching-disjoint-intervals',want=0,isolate=True)
    add(440,[10**9,1],'maximum-trie-first-key',want=1)
    add(440,[10**9,10**9],'maximum-trie-final-key',want=999999999)
    add(442,[list(range(1,100001))],'maximum-no-duplicates',want=[],isolate=True)
    add(443,[['a']*2000],'maximum-compression-run')
    cantor = [sum(((i >> k)&1)*3**k for k in range(10)) for i in range(1000)]
    add(446,[cantor],'maximum-unique-ternary-progression-free-set',want=0,isolate=True)
    add(447,[[[i,0] for i in range(500)]],'maximum-collinear-points',want=2*sum(min(i,499-i) for i in range(500)),isolate=True)
    add(451,['A'*500000],'maximum-single-frequency-block',want='A'*500000,isolate=True)
    add(452,[[[-2**31,2**31-1]]],'extreme-balloon-endpoints',want=1)
    add(453,[[-10**9,10**9]],'large-exact-integer-moves',want=2*10**9)
    add(454,[[0]*200 for _ in range(4)],'maximum-four-array-multiplicity',want=200**4,isolate=True)
    add(456,[list(range(200000))],'maximum-increasing-no-pattern',want=False,isolate=True)
    add(457,[[1]*4999+[-1]],'maximum-long-direction-path-no-cycle',want=False,isolate=True)
    add(458,[1000,100,100],'maximum-buckets-binary-information-capacity')
    add(462,[[10**9]*100000],'maximum-identical-median-input',want=0,isolate=True)
    add(464,[20,0],'maximum-choices-zero-target',want=True)
    add(464,[20,300],'unreachable-total',want=False)
    wrap = ('abcdefghijklmnopqrstuvwxyz'*3847)[:100000]
    add(467,[wrap],'maximum-contiguous-wraparound-string',want=26*100000-325,isolate=True)
    add(473,[[10**8]*12],'large-square-equal-sticks',want=True,isolate=True)
    add(474,[['0']*600,100,100],'maximum-single-symbol-knapsack',want=100,isolate=True)
    add(475,[[10**9]*30000,[1]*30000],'maximum-house-heater-distance',want=10**9-1,isolate=True)
    add(477,[[10**9]*10000],'maximum-equal-hamming-values',want=0,isolate=True)
    add(481,[100000],'maximum-fixed-point-prefix',isolate=True)
    add(486,[[10**7]*20],'maximum-even-equal-game',want=True,isolate=True)
    add(491,[[0]*15],'maximum-identical-subsequence-multiplicity',want=[(0,)*n for n in range(2,16)],isolate=True)
    add(493,[[2**31-1,-2**31]],'signed-double-width-pair',want=1)
    add(493,[[0]*50000],'maximum-equal-zero-reverse-pairs',want=0,isolate=True)
    add(494,[[0]*20,0],'maximum-zero-sign-multiplicity',want=2**20,isolate=True)
    add(495,[[0]*10000,10**7],'maximum-overlapping-poison-intervals',want=10**7,isolate=True)
    add(498,[[list(range(10000))]],'maximum-single-row-diagonal-readback',want=list(range(10000)),isolate=True)
    add(502,[100000,0,[1]*100000,[0]*100000],'maximum-affordable-project-resource-witness',want=100000,isolate=True)
    add(503,[[10**9]*10000],'maximum-equal-circular-elements',want=[-1]*10000,isolate=True)
    assert all(data.values()) and set(data)==set(IDS)
    return data
