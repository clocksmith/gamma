"""Queue 07 subset 02 bounded source-blind references; not qualifications.

Full domain validators are distinct from reference work limits. Candidate bodies,
native interfaces, runtime acceptance and omitted maximum shapes remain separate.
"""
from collections import Counter
from functools import lru_cache
from heapq import heappop, heappush
from itertools import product
import ast
import json
import random
import re
import string
from . import imported_qualification as q
from .imported_clean_domains import integer, ints, text

IDS = (2896, 2939, 2949, 2962)
PARAMETERS = {2896: ('s1', 's2', 'x'), 2939: ('a', 'b', 'n'), 2949: ('s', 'k'), 2962: ('nums', 'k')}
TITLES = {2896: 'Apply Operations to Make Two Strings Equal', 2939: 'Maximum Xor Product', 2949: 'Count Beautiful Substrings II', 2962: 'Count Subarrays Where Max Element Appears at Least K Times'}
STATEMENT_SHA256 = {2896: '8ff72ca6839f4e44907d59dd205b6a72bff1b75d910bbd0a3736f55403222016', 2939: '2769ef7a03fb8dea9f8c05ab8fdef3be1a620980588b61474b95b3522b598891', 2949: '2701efcfe142d44ea13719acdb921073537a762596e060cc47c18f956177c826', 2962: '8b5a293cde5db678aaa00d45dfdc03d87e0116bd4d8e367dccdab82ed4b24ccd'}
EXAMPLE_COUNT = {2896: 2, 2939: 3, 2949: 3, 2962: 2}
CASE_COUNT = {2896: 1587, 2939: 1638, 2949: 2112, 2962: 7175}
CASES_SHA256 = {2896: '3bb4df5690279032d869b51d8c0f7c82ce28cacff8745af89ad5bc32356e79be', 2939: 'd3a4f798b95018887aa93927f083fbed43f7c5a76467bb529a7a598c9dbae935', 2949: '2f9281e6b10307a5d43b2d2f3da53f79b92955d2733e0f76b70c1b3c1f78f6c0', 2962: '17f12b331581af7adc0d196cae66d07dfe74e6208815d99233074b44885abeba'}
MOD = 1000000007
SEED = 202610272102


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported exact identity or ordered argument shape')
    if pid == 2896:
        a, b, x = args
        valid = text(a, '01', 1, 500) and text(b, '01', len(a), len(a)) and integer(x, 1, 500)
    elif pid == 2939:
        valid = all(integer(x, 0, (1 << 50)-1) for x in args[:2]) and integer(args[2], 0, 50)
    elif pid == 2949:
        valid = text(args[0], maximum=50000) and integer(args[1], 1, 1000)
    else:
        valid = ints(args[0], 1, 1000000, 1, 100000) and integer(args[1], 1, 100000)
    if not valid:
        raise ValueError('outside full pinned statement domain')


@lru_cache(maxsize=128)
def _flip_distances(n, cost):
    distances = [None]*(1 << n); distances[0] = 0; heap = [(0, 0)]
    moves = [((1 << i) | (1 << j), 1 if j == i+1 else cost)
             for i in range(n) for j in range(i+1, n)]
    while heap:
        distance, mask = heappop(heap)
        if distance != distances[mask]:
            continue
        for toggle, price in moves:
            nxt = mask ^ toggle; candidate = distance+price
            if distances[nxt] is None or candidate < distances[nxt]:
                distances[nxt] = candidate; heappush(heap, (candidate, nxt))
    return tuple(distances)


def expected(pid, args):
    validate(pid, args)
    if pid == 2896 and len(args[0]) <= 12:
        a, b, x = args; mask = sum((u != v) << i for i, (u, v) in enumerate(zip(a, b)))
        result = _flip_distances(len(a), x)[mask]
        return -1 if result is None else result
    if pid == 2939 and args[2] <= 10:
        a, b, n = args
        return max((a ^ x)*(b ^ x) for x in range(1 << n)) % MOD
    if pid == 2949 and len(args[0]) <= 80:
        s, k = args; answer = 0
        for left in range(len(s)):
            vowels = consonants = 0
            for right in range(left, len(s)):
                if s[right] in 'aeiou': vowels += 1
                else: consonants += 1
                answer += vowels == consonants and vowels*consonants % k == 0
        return answer
    if pid == 2962 and len(args[0]) <= 60:
        nums, k = args; maximum = max(nums); answer = 0
        for left in range(len(nums)):
            count = 0
            for right in range(left, len(nums)):
                count += nums[right] == maximum; answer += count >= k
        return answer
    raise ValueError('bounded independent reference budget exceeded')


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned statement bytes required')
    body = re.sub(r'^L\d+: ?', '', raw.decode(), flags=re.M)
    if f'{pid}. {TITLES[pid]}' not in body:
        raise ValueError('numeric identity/title mismatch')
    examples = []
    for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)', body, re.S):
        call = ast.parse('f('+match[1].strip()+')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(x.arg for x in call.keywords) != PARAMETERS[pid]:
            raise ValueError('ordered example parameters mismatch')
        args = [ast.literal_eval(x.value) for x in call.keywords]; answer = json.loads(match[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('reference disagrees with public example')
        examples.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(examples) != EXAMPLE_COUNT[pid]:
        raise ValueError('complete pinned public examples required')
    return examples


def _generate_cases(pid, raw):
    cases = []; categories = []; seen = {}; rng = random.Random(SEED+pid); absent = object()
    def add(args, category, answer=absent):
        validate(pid, args); result = expected(pid, args) if answer is absent else answer; key = q.encoded(args)
        if key in seen:
            i = seen[key]
            if not q.exact(cases[i]['expected'], result): raise ValueError('conflicting duplicate expectation')
            if category not in categories[i].split('|'): categories[i] += '|'+category
            return
        seen[key] = len(cases); cases.append({'args': args, 'expected': result, 'compare': 'return'}); categories.append(category)
    for case in public_examples(pid, raw): add(case['args'], 'pinned-public-example', case['expected'])
    if pid == 2896:
        for n in range(1, 9):
            for bits in product('01', repeat=n):
                for x in (1, 2, 5): add(['0'*n, ''.join(bits), x], 'exhaustive-mismatch-state-graph')
        for _ in range(50):
            n = rng.randrange(1, 11)
            add([''.join(rng.choices('01', k=n)), ''.join(rng.choices('01', k=n)), rng.choice((1,2,5,499,500))], 'seeded-nonzero-original-strings')
        for x in (1, 500):
            for word, answer in [('0'*500, 0), ('1'+'0'*499, -1), ('1'*500, 250), ('1'+'0'*498+'1', min(x,499)), ('10'*250, 125*min(x,2))]:
                add(['0'*500, word, x], 'analytic-maximum-length-parity-and-pairing', answer)
    elif pid == 2939:
        for a in range(16):
            for b in range(16):
                for n in range(6): add([a,b,n], 'exhaustive-small-x-product-before-modulo')
        for _ in range(80): add([rng.randrange(1 << 50), rng.randrange(1 << 50), rng.randrange(11)], 'seeded-full-input-numeric-bounded-exhaustion')
        for n in (0,31,32,49,50):
            mask = (1 << n)-1
            for a in (0,1,(1 << 49), (1 << 50)-1): add([a,a,n], 'analytic-equal-operands-full-bit-width', (a | mask)**2 % MOD)
        for a,b in [(0,(1 << 50)-1),((1 << 49)-1,1 << 49),((1 << 50)-1,0)]:
            add([a,b,50], 'analytic-complementary-fixed-sum-optimum', ((1 << 49)*((1 << 49)-1)) % MOD)
        add([(1 << 50)-1,(1 << 50)-2,0], 'analytic-fixed-product-near-100-bits', (((1 << 50)-1)*((1 << 50)-2)) % MOD)
    elif pid == 2949:
        for n in range(1,8):
            for chars in product('ab',repeat=n):
                for k in range(1,9): add([''.join(chars),k], 'exhaustive-vowel-consonant-intervals')
        for _ in range(60): add([''.join(rng.choices(string.ascii_lowercase,k=rng.randrange(1,81))),rng.randrange(1,1001)], 'seeded-full-alphabet-divisibility')
        for word in ('a'*50000,'b'*50000,'ab'*25000):
            for k in (1,2,4,6,997,1000):
                answer = sum(50000-2*t+1 for t in range(1,25001) if t*t%k==0) if word[0]!=word[1] else 0
                add([word,k], 'analytic-maximum-length-uniform-and-alternating', answer)
    else:
        for n in range(1,7):
            for values in product((1,2,3),repeat=n):
                for k in range(1,n+2): add([list(values),k], 'exhaustive-global-maximum-subarray-count')
        for _ in range(60):
            n=rng.randrange(1,61);add([[rng.randrange(1,1000001) for _ in range(n)],rng.randrange(1,100001)], 'seeded-full-numeric-and-k-domain')
        n=100000
        for k in (1,n): add([[1000000]*n,k], 'analytic-maximum-length-uniform', (n-k+1)*(n-k+2)//2)
        for pos in (0,n//2,n-1):
            a=[1]*n;a[pos]=1000000
            add([a,1], 'analytic-maximum-length-single-global-maximum', (pos+1)*(n-pos))
            if pos==n//2:add([a,2], 'analytic-insufficient-maximum-occurrences', 0)
        add([[1,1000000]*(n//2),n], 'analytic-maximum-length-k-too-large', 0)
    return cases, categories


def expected_observation_bytes(batch, language):
    if language not in ('javascript','python'): raise ValueError('unsupported language')
    return sum(len(q.encoded({'i':i,'result':c['expected'],'result_type':q.expected_type(c['expected'],language),'args_before':c['args'],'args_after':c['args'],'alias_edges':[]})) for i,c in enumerate(batch))+len(q.encoded({'done':len(batch)}))+(language=='python')


def build_cases(pid, raw):
    cases,categories=_generate_cases(pid,raw)
    if len(cases)!=CASE_COUNT.get(pid) or q.sha(q.encoded(cases))!=CASES_SHA256.get(pid): raise ValueError('frozen case identity mismatch')
    if len(q.encoded(cases))>q.MAX_FILE: raise ValueError('case file cap exceeded')
    for _,batch in q.batches(cases):
        if any(expected_observation_bytes(batch,lang)>q.LIMITS['max_output_bytes'] for lang in ('javascript','python')): raise ValueError('output cap exceeded')
    return cases,categories
