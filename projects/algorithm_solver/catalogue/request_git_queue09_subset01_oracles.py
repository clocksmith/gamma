"""Source-blind public-definition references, not candidate qualification."""
from __future__ import annotations
import ast
from itertools import combinations, product
import json
import random
import re
from . import imported_qualification as q

IDS = (3107, 3111, 3115, 3121)
PARAMETERS = {3107: ('nums', 'k'), 3111: ('points', 'w'), 3115: ('nums',), 3121: ('word',)}
TITLES = {3107: 'Minimum Operations to Make Median of Array Equal to K', 3111: 'Minimum Rectangles to Cover Points', 3115: 'Maximum Prime Difference', 3121: 'Count the Number of Special Characters II'}
SLUGS = {3107: 'minimum-operations-to-make-median-of-array-equal-to-k', 3111: 'minimum-rectangles-to-cover-points', 3115: 'maximum-prime-difference', 3121: 'count-the-number-of-special-characters-ii'}
STATEMENT_SHA256 = {3107: '5aaa0bb5ed1b84dfac4d96c232ea38285dc8deba69a2b1fbfb0334aea67f5332', 3111: 'd76f9cc677245a83064ebd6c833221abaf5d38c4122a84b3eb80ffe411129a9c', 3115: '7d72f626f1a61452b64c6f7955514fc7a1345a8c5507c2c8222e0983b97f21fa', 3121: 'bc395000ede49402b53bca7c70301f111455f9f564f9be178c2c10eb194309af'}
EXAMPLE_COUNT = {3107: 3, 3111: 3, 3115: 2, 3121: 3}
SEED_BASE = 202610272104
CONTRACTS = {
3107: dict(domain='1..200000 exact integers nums[i] in1..1e9; exact k in1..1e9. Even length uses upper median.', result='Exact minimum unit increment/decrement count, integer0..100001*(1e9-1).', reference='Enumerate one equal-k index and choose floor(n/2) other lower-side indices; clamp others above k. Minimum assignment cost; n<=10.', complexity='Reference O(n^2*C(n-1,floor(n/2))) time and O(n) auxiliary; candidate target O(n log n) or better, with all sort effects reviewed.'),
3111: dict(domain='1..100000 distinct coordinate pairs [x,y], exact x/y/w in0..1e9.', result='Exact minimum number of closed width<=w rectangles rooted at y0, integer1..n.', reference='Width-w intervals anchored at every input x define covered masks; subset-cover dynamic programming minimizes count, <=12 points.', complexity='Reference O(n*2^n+n^2) time/O(2^n+n) space; candidate target O(n log n) time/O(n) or better.'),
3115: dict(domain='1..300000 exact integers1..100 with at least one prime.', result='Maximum absolute difference of prime positions, including same position; integer0..n-1.', reference='Trial division and enumerate every pair of prime indices, <=60 values.', complexity='Reference O(n^2+n*sqrt(100)) time/O(n) space; candidate target O(n) time with bounded prime test.'),
3121: dict(domain='1..200000 ASCII English lowercase/uppercase letters.', result='Number of letters present both cases with every lowercase occurrence before first uppercase; integer0..26.', reference='For each letter gather every index and explicitly test all lower/upper position pairs; <=300 chars.', complexity='Reference O(26*n+n^2) time/O(n) space; candidate target O(n+26) time/O(26) state or justified equivalent.')}
COMMON_CONTRACT = dict(exposure='Exposed deterministic development, not fresh holdout or qualification.', interface='Ordered single-call values from official examples; actual candidate exports remain unknown.', effects='Conservative service envelope distinct from public mutation permission: inputs retain values/identities; no mutable result/input alias, external I/O or persistent mutable state.', numeric='Exact integers with Boolean excluded from integer inputs; 3107 may exceed32-bit but stays below2^53.', expected_values='Host-side only, absent from q.packet.', limits='Unchanged q.MAX_FILE/MAX_PACKET=1100000/LIMITS, q.batches; frozen helper must be bound explicitly.', candidate_execution=False)
OMITTED_MAXIMUM_SHAPES = {3107: 'Full200000 entries at1e9 exceeds packet cap; full low-value length with k1e9 included and90000 all1e9. Arbitrary maximum arrays not exhaustive.', 3111: '100000 large-coordinate pairs exceed packet; full distinct small-coordinate grid included and value1e9 separately. No arbitrary maximum geometry enumeration.', 3115: '300000 values100 with required prime exceeds packet; full low-value count and a separate maximum-value boundary are included.', 3121: 'Full length200000 fits packet; only analytic structured strings, not exhaustive arbitrary maximum strings.'}

def _int(x, low, high):
    return type(x) is int and low <= x <= high

def _prime(x):
    return x >= 2 and all(x % d for d in range(2, int(x**0.5)+1))

def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported identity or ordered argument shape')
    if pid == 3107:
        nums, k = args
        valid = type(nums) is list and 1 <= len(nums) <= 200000 and all(_int(x,1,10**9) for x in nums) and _int(k,1,10**9)
    elif pid == 3111:
        pts,w = args
        valid = type(pts) is list and 1 <= len(pts) <= 100000 and _int(w,0,10**9) and all(type(p) is list and len(p)==2 and all(_int(x,0,10**9) for x in p) for p in pts)
        if valid:
            valid = len({tuple(p) for p in pts}) == len(pts)
    elif pid == 3115:
        nums = args[0]
        valid = type(nums) is list and 1 <= len(nums) <= 300000 and all(_int(x,1,100) for x in nums) and any(_prime(x) for x in nums)
    else:
        word = args[0]
        valid = type(word) is str and 1 <= len(word) <= 200000 and all('a'<=c<='z' or 'A'<=c<='Z' for c in word)
    if not valid:
        raise ValueError('outside full pinned public domain')

def expected(pid, args):
    validate(pid,args)
    if pid == 3107:
        nums,k=args;n=len(nums)
        if n>10: raise ValueError('reference budget exceeded')
        best = 10**20
        for eq in range(n):
            others = [i for i in range(n) if i!=eq]
            for lower in combinations(others,n//2):
                lower=set(lower)
                cost=abs(nums[eq]-k)+sum(max(0,nums[i]-k) if i in lower else max(0,k-nums[i]) for i in others)
                best=min(best,cost)
        return best
    if pid == 3111:
        pts,w=args;n=len(pts)
        if n>12: raise ValueError('reference budget exceeded')
        covers={sum(1<<i for i,p in enumerate(pts) if left<=p[0]<=left+w) for left,_ in pts}
        dp=[n+1]*(1<<n);dp[0]=0
        for mask in range(1<<n):
            for cover in covers:
                dp[mask|cover]=min(dp[mask|cover],dp[mask]+1)
        return dp[-1]
    if pid == 3115:
        nums=args[0]
        if len(nums)>60: raise ValueError('reference budget exceeded')
        indices=[i for i,x in enumerate(nums) if _prime(x)]
        return max(abs(i-j) for i in indices for j in indices)
    word=args[0]
    if len(word)>300: raise ValueError('reference budget exceeded')
    answer=0
    for c in 'abcdefghijklmnopqrstuvwxyz':
        lower=[i for i,x in enumerate(word) if x==c]
        upper=[i for i,x in enumerate(word) if x==c.upper()]
        answer+=bool(lower and upper and all(i<j for i in lower for j in upper))
    return answer

def public_examples(pid, raw):
    if pid not in IDS or type(raw) is not bytes or q.sha(raw)!=STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned statement required')
    statement=re.sub(r'(?m)^L\d+: ?', '', json.loads(raw))
    if f'{pid}. {TITLES[pid]}' not in statement or f'https://leetcode.com/problems/{SLUGS[pid]}/description/' not in statement:
        raise ValueError('official numeric/title/slug mismatch')
    cases=[]
    for found in re.finditer(r'Input:\s*([^\n]+)\n\s*Output:\s*([^\n]+)',statement):
        call=ast.parse('f('+found[1]+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or tuple(k.arg for k in call.keywords)!=PARAMETERS[pid]:
            raise ValueError('official argument order differs')
        args=[ast.literal_eval(k.value) for k in call.keywords];answer=json.loads(found[2])
        if not q.exact(expected(pid,args),answer): raise ValueError('official example differs')
        cases.append(dict(args=args,expected=answer,compare='return'))
    if len(cases)!=EXAMPLE_COUNT[pid]: raise ValueError('incomplete examples')
    return cases

def _generate_cases(pid,raw):
    cases=public_examples(pid,raw);cats=['pinned_public_example']*len(cases);rng=random.Random(SEED_BASE+pid);unset=object()
    def add(args,category,answer=unset):
        validate(pid,args);cases.append(dict(args=args,expected=expected(pid,args) if answer is unset else answer,compare='return'));cats.append(category)
    if pid==3107:
        for n in range(1,6):
            for a in product((1,2,4),repeat=n):
                for k in (1,2,3,4): add([list(a),k],'exhaustive_index_partition')
        for _ in range(80):
            add([[rng.choice((1,2,7,10**9-1,10**9)) for _ in range(rng.randint(6,10))],rng.choice((1,5,10**9))],'seeded_extremes_upper_median')
        for a,k,result in [([1]*200000,10**9,100000*(10**9-1)),([1]*200000,1,0),([10**9]*90000,1,45001*(10**9-1)),([1]*100000+[2]*100000,1,1),([2]*100000+[1]*100000,2,0)]:
            add([a,k],'analytic_maximum_length_or_value',result)
    elif pid==3111:
        universe=list(product(range(3),range(2)))
        for bits in range(1,1<<len(universe)):
            pts=[list(p) for i,p in enumerate(universe) if bits>>i&1]
            for w in range(3):add([pts,w],'exhaustive_interval_set_cover')
        for _ in range(80):
            pts=[list(p) for p in rng.sample(list(product(range(8),range(3))),rng.randint(1,12))]
            add([pts,rng.randint(0,8)],'seeded_duplicate_x_order_and_height')
        for w,result in [(0,1000),(17,56),(999,1)]:
            add([[[i//100,i%100] for i in range(100000)],w],'analytic_maximum_count_grid',result)
        for pts,w,result in [([[0,10**9],[10**9,0]],10**9,1),([[0,0],[10**9,10**9]],10**9-1,2),([[10**9,i] for i in range(12)],0,1)]:
            add([pts,w],'analytic_numeric_boundaries',result)
    elif pid==3115:
        for n in range(1,7):
            for a in product((1,2,4),repeat=n):
                if 2 in a:add([list(a)],'exhaustive_prime_index_pairs')
        for _ in range(80):
            a=[rng.randint(1,100) for _ in range(rng.randint(7,60))];a[rng.randrange(len(a))]=97
            add([a],'seeded_prime_square_and_endpoint_gaps')
        for a,result in [([2]+[1]*299998+[97],299999),([1]*150000+[2]+[1]*149999,0),([2]*300000,299999),([100]*60+[97],0)]:
            add([a],'analytic_maximum_length_or_value',result)
    else:
        for n in range(1,7):
            for chars in product('aAbB',repeat=n):add([''.join(chars)],'exhaustive_case_order_pairs')
        for _ in range(80):
            add([''.join(rng.choice('aAbBcCzZ') for _ in range(rng.randint(7,80)))],'seeded_mixed_case_invalidations')
        for word,result in [('a'*100000+'A'*100000,1),('A'*100000+'a'*100000,0),('aA'*100000,0),('abcdefghijklmnopqrstuvwxyz'*3846+'ABCDEFGHIJKLMNOPQRSTUVWXYZ'*3846+'a'*8,25),('z'*200000,0)]:
            assert len(word)==200000
            add([word],'analytic_maximum_length_case_patterns',result)
    seen={};unique=[];categories=[]
    for c,cat in zip(cases,cats):
        key=q.encoded(c['args'])
        if key in seen:
            if not q.exact(seen[key],c['expected']):raise ValueError('duplicate expectation mismatch')
        else:seen[key]=c['expected'];unique.append(c);categories.append(cat)
    return unique,categories

def expected_observation_bytes(batch,language):
    if language not in ('javascript','python'): raise ValueError('unknown observer language')
    records=[dict(i=i,result=c['expected'],result_type=q.expected_type(c['expected'],language),args_before=c['args'],args_after=c['args'],alias_edges=[]) for i,c in enumerate(batch)]
    return sum(len(q.encoded(r)) for r in records)+len(q.encoded(dict(done=len(batch))))+(language=='python')

def build_cases(pid,raw):
    cases,cats=_generate_cases(pid,raw)
    if len(q.encoded(cases))>q.MAX_FILE:raise ValueError('unchanged case-file cap exceeded')
    for _,batch in q.batches(cases):
        if max(expected_observation_bytes(batch,lang) for lang in ('javascript','python'))>q.LIMITS['max_output_bytes']:
            raise ValueError('unchanged observer output cap exceeded')
    return cases,cats
