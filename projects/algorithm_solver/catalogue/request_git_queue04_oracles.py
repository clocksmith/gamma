"""Source-blind queue04 spec references, not candidate implementations or receipts.

Official definitions, full-domain validation, finite exhaustive references and
analytic resource probes are separate. Tree/stateful observer gaps stay closed.
Callers must freshly authorize before opening or hashing definition files.
"""
from __future__ import annotations

import ast
from collections import Counter
from functools import lru_cache
from itertools import combinations, permutations, product
import json
import random
import re

from . import imported_qualification as q
from .imported_clean_domains import integer, ints, text

QUEUE_IDS = (2355,2361,2371,2375,2378,2384,2393,2396,2408,2415,2424,2428,2431,
             2438,2443,2445,2449,2452,2459,2467,2471,2473,2476,2479,2498)
IDS = (2375,2384,2396,2428,2438,2443,2449,2452,2467,2498)
PARAMETERS = {2375: ('pattern',), 2384: ('num',), 2396: ('n',), 2428: ('grid',),
              2438: ('n','queries'), 2443: ('num',), 2449: ('nums','target'),
              2452: ('queries','dictionary'), 2467: ('edges','bob','amount'), 2498: ('stones',)}
STATEMENT_SHA256 = {
    2375: '4c9fcfe8b47ab7c36d06709689d6c13d92021245b8f695300bbd4a3d5e02ba0f',
    2384: 'eb89df8e4fd731e874f6be67851a7ee7207db30ca5125235817ff3cfde8cf06d',
    2396: 'b997eb4f1df1a93489459be23a2fd4b7fe750a48ee34857d56d0789fb94542bc',
    2428: 'ff99ab08a2e86899d75d5ab39a2a10170bb1e562cb9e27039e6b18e8fcafc5bd',
    2438: '2d4e4ded304b49033e186905278519240e2ea1488284ba2d9419c06ad4b4c240',
    2443: 'd8eab25db7a0f0795ad2d3452b1e830cd9aae933d70826048016b65f5447eeb0',
    2449: '366fb9c78833eb8ca5aca23ef820a76081584226e88034372d0149c06498e534',
    2452: 'c40aa5c1ebf482ada0dd5f981c879e6f8538de928515ce8c379241741f516c04',
    2467: 'f91e0b402ccc6546474acda43599f2adcf5a6a642d2ed902a815c2580c0c1905',
    2498: '2360be9c5315846910d89659eca90e9fb0928da196682a848c0957554abb6efd',
}
EXAMPLE_COUNT = {2375:2,2384:2,2396:2,2428:2,2438:2,2443:3,2449:3,2452:2,2467:2,2498:2}
CASE_COUNT = {2375: 512, 2384: 410, 2396: 516, 2428: 597, 2438: 290, 2443: 1033, 2449: 505, 2452: 405, 2467: 523, 2498: 291}
CASES_SHA256 = {2375: '9e506671242e0a7b573149d1f5c135b2f5ccd90e24450f471d52e1371049ea11', 2384: '5f349893cd8f27f23e2372341dee69a603082e08feb93eef0e4922884099ca68', 2396: 'd4db167b5722a11380669deb1ab8d6be4bfa4e4725a67716793bf2e78011c7a5', 2428: '017e774bba92182f86c760215d94b2ea2064c0906c0ef055bf615fcaa78b0472', 2438: '5d6b26f3ada9fce48af49f74406a52a4e339db41981741affc6d97365ac04eb7', 2443: '6a89f2fb5e45dcfb2e8af773b041b64690b2682741dc4f92ef6cf062c49d71ba', 2449: '6e4b27d8468127427743dd4642657c6e5b0666db42f07fcd7964a98711fc2fe6', 2452: '0f2ccfbfd27c06d2eefb178cb6fd0fc266dd27e30dcde30d10207459e7ef898b', 2467: 'c9e80467b8d6c4e2aca5c578d7b21fa8e3b646a7e03a84d7b9736ae8041e7314', 2498: 'a2a7ab8adb4fd57376d4dba25c8ddda9fc36f2dc4aae47690de449d3e79cfc1a'}
SEED_BASE = 202610271835
MOD = 10**9 + 7
BLOCKED = {
    2355:'Official page requires premium; stopped.',
    2361:'Official page requires premium; stopped.',
    2371:'Official page requires premium; stopped.',
    2378:'Official page inaccessible through web tool; stopped.',
    2393:'Official page requires premium; stopped.',
    2408:'Definition pinned; stateful SQL observer and rowId/columnId domain clarification required. Current public API ins/rmv/sel/exp must not be silently replaced with an older API.',
    2415:'Definition pinned; tree mutation/identity observer required for reversed node values and returned original root.',
    2424:'Definition pinned; persistent constructor/upload/longest observer required, distinct uploads and call-count obligations unmeasured.',
    2431:'Official page inaccessible through web tool; stopped.',
    2445:'Official page inaccessible through web tool; stopped.',
    2459:'Official page inaccessible through web tool; stopped.',
    2471:'Definition pinned; node-tree input observer and full valid tree transport required.',
    2473:'Official page requires premium; stopped.',
    2476:'Definition pinned; BST node input observer and duplicate-value convention require explicit review.',
    2479:'Official page inaccessible through web tool; stopped.',
}
OMITTED_MAXIMUM_SHAPES = {
    2375:'All 510 valid patterns covered by independently enumerated permutations; no broader program proof.',
    2384:'Maximum string length and digit extremes tested analytically; arbitrary huge multiset permutations not enumerated.',
    2396:'Small bases explicitly converted; large values use separate n-2 base witnesses. Finite probes do not prove candidate universality.',
    2428:'Maximum 150 by 150 grids included; arbitrary maximum grids not exhaustively enumerated.',
    2438:'Maximum n and query count tested in separate analytic shapes; arbitrary maximum query lists not enumerated.',
    2443:'Reference searches all possible nonnegative summands through num; tests do not exhaust the scalar domain.',
    2449:'Maximum array length with small values and maximum numeric spans with 1000 elements tested separately; simultaneous large decimal arrays exceed packet cap.',
    2452:'Maximum counts and word lengths included; arbitrary 100 by 100 word populations not enumerated.',
    2467:'A 100000-node explicit tree exceeds unchanged packet cap. Largest retained tree has 50000 nodes, with chain and star topologies; full validator still admits n100000.',
    2498:'Maximum count and endpoint tested in a fitting array; arbitrary full-length tours not enumerated.',
}


def _tree(n, edges):
    if type(edges) is not list or len(edges) != n - 1:
        return False
    parent = list(range(n))
    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for edge in edges:
        if not ints(edge, 0, n - 1, 2, 2) or edge[0] == edge[1]:
            return False
        a,b = map(root,edge)
        if a == b:
            return False
        parent[a] = b
    return True


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered argument shape')
    if pid == 2375:
        valid = text(args[0], 'ID', 1, 8)
    elif pid == 2384:
        valid = text(args[0], '0123456789', 1, 100000)
    elif pid == 2396:
        valid = integer(args[0],4,100000)
    elif pid == 2428:
        a = args[0]
        valid = (type(a) is list and 3 <= len(a) <= 150 and type(a[0]) is list
                 and 3 <= len(a[0]) <= 150 and all(ints(r,0,10**6,len(a[0]),len(a[0])) for r in a))
    elif pid == 2438:
        n,queries = args
        valid = (integer(n,1,10**9) and type(queries) is list and 1 <= len(queries) <= 100000
                 and all(ints(row,0,n.bit_count()-1,2,2) and row[0] <= row[1] for row in queries))
    elif pid == 2443:
        valid = integer(args[0],0,100000)
    elif pid == 2449:
        a,b = args
        valid = (ints(a,1,10**6,1,100000) and ints(b,1,10**6,len(a),len(a))
                 and sum(a) == sum(b) and sum(x%2 for x in a) == sum(x%2 for x in b))
    elif pid == 2452:
        a,b = args
        valid = (type(a) is list and type(b) is list and 1 <= len(a) <= 100 and 1 <= len(b) <= 100
                 and text(a[0],maximum=100) and all(text(w,minimum=len(a[0]),maximum=len(a[0])) for w in a+b))
    elif pid == 2467:
        edges,bob,amount = args
        valid = (ints(amount,-10000,10000,2,100000) and all(v%2 == 0 for v in amount)
                 and integer(bob,1,len(amount)-1) and _tree(len(amount),edges))
    else:
        a = args[0]
        valid = ints(a,0,10**9,2,100000) and a[0] == 0 and all(x < y for x,y in zip(a,a[1:]))
    if not valid:
        raise ValueError('outside pinned full statement domain')


@lru_cache(maxsize=8)
def _permutation_patterns(n):
    # Any n+1 distinct positive digits can be order-preservingly relabeled to
    # 1..n+1, preserving comparisons and weakly decreasing every digit.
    result = {}
    for digits in permutations('123456789'[:n+1]):
        pattern = ''.join('I' if a < b else 'D' for a,b in zip(digits,digits[1:]))
        result.setdefault(pattern,''.join(digits))
    return result


def _palindromes(num):
    # Enumerate every distinct nonempty sequence drawn without replacement,
    # rather than using the candidate-style greedy digit-pair construction.
    counts = Counter(num); best = ''
    def walk(s):
        nonlocal best
        if s and s == s[::-1] and (len(s),s) > (len(best),best):
            best = s
        for digit in counts:
            if counts[digit] and (s or digit != '0'):
                counts[digit] -= 1
                walk(s+digit)
                counts[digit] += 1
    walk('')
    return best or '0'


def _bases(n):
    for base in range(2,n-1):
        value = n; digits = []
        while value:
            value,remainder = divmod(value,base); digits.append(remainder)
        if digits != digits[::-1]:
            return False
    return True


@lru_cache(maxsize=1)
def _minimum_coin_decompositions():
    # Unbounded coin DP explores every possible final power, independent of
    # set-bit extraction and prefix-exponent product implementations.
    out = [()]
    for total in range(1,256):
        options = [tuple(sorted(out[total-c]+(c,))) for c in (1,2,4,8,16,32,64,128) if c <= total]
        out.append(min(options,key=lambda x:(len(x),x)))
    return tuple(out)


def _reverse_sum(n):
    for x in range(n+1):
        remainder = x; reversed_value = 0
        while remainder:
            remainder,digit = divmod(remainder,10)
            reversed_value = reversed_value*10+digit
        if x+reversed_value == n:
            return True
    return False


def _assignments(a,b):
    costs = []
    for target in set(permutations(b)):
        if all((x-y)%2 == 0 for x,y in zip(a,target)):
            costs.append(sum(max(0,y-x)//2 for x,y in zip(a,target)))
    return min(costs)


def _edits(queries,dictionary):
    result = []
    for word in queries:
        for other in dictionary:
            # Exhaust every possible set of at most two edited positions.
            if any(all(word[i] == other[i] for i in range(len(word)) if i not in edited)
                   for count in range(3) for edited in combinations(range(len(word)),count)):
                result.append(word); break
    return result


def _game(edges,bob,amount):
    adjacency = [[] for _ in amount]
    for a,b in edges:
        adjacency[a].append(b); adjacency[b].append(a)
    paths = []; stack = [(0,-1,[0])]; bob_path = None
    while stack:
        node,parent,path = stack.pop()
        if node == bob:
            bob_path = path[::-1]
        children = [x for x in adjacency[node] if x != parent]
        if not children:
            paths.append(path)
        for child in children:
            stack.append((child,node,path+[child]))
    best = None
    for alice in paths:
        opened = set(); income = 0
        for time in range(max(len(alice),len(bob_path))):
            a = alice[time] if time < len(alice) else None
            b = bob_path[time] if time < len(bob_path) else None
            if a is not None and a not in opened:
                income += amount[a]//2 if a == b else amount[a]
            opened.update(x for x in (a,b) if x is not None)
        best = income if best is None else max(best,income)
    return best


def _tours(stones):
    # All subsets and all visit orders: the final stone may appear anywhere
    # in the tour, but must appear. This does not assume monotone outbound legs.
    best = stones[-1]
    for count in range(len(stones)-1):
        for subset in combinations(range(1,len(stones)-1),count):
            for order in permutations(subset+(len(stones)-1,)):
                indices = (0,)+order+(0,)
                best = min(best,max(abs(stones[a]-stones[b]) for a,b in zip(indices,indices[1:])))
    return best


def expected(pid,args):
    validate(pid,args)
    bounded = {2375:lambda:True,2384:lambda:len(args[0])<=9,2396:lambda:args[0]<=512,
               2428:lambda:len(args[0])*len(args[0][0])<=100,
               2438:lambda:args[0]<=255 and len(args[1])<=64,2443:lambda:True,
               2449:lambda:len(args[0])<=8,2452:lambda:len(args[0])<=10 and len(args[1])<=10 and len(args[0][0])<=12,
               2467:lambda:len(args[2])<=12,2498:lambda:len(args[0])<=8}[pid]()
    if not bounded:
        raise ValueError('bounded independent reference budget exceeded')
    if pid == 2375:
        return _permutation_patterns(len(args[0]))[args[0]]
    if pid == 2384:
        return _palindromes(args[0])
    if pid == 2396:
        return _bases(args[0])
    if pid == 2428:
        a = args[0]
        return max(sum(a[r+dr][c+dc] for dr,dc in ((0,0),(0,1),(0,2),(1,1),(2,0),(2,1),(2,2)))
                   for r in range(len(a)-2) for c in range(len(a[0])-2))
    if pid == 2438:
        powers = _minimum_coin_decompositions()[args[0]]; answer = []
        for left,right in args[1]:
            value = 1
            for item in powers[left:right+1]:
                value = value*item%MOD
            answer.append(value)
        return answer
    if pid == 2443:
        return _reverse_sum(args[0])
    if pid == 2449:
        return _assignments(*args)
    if pid == 2452:
        return _edits(*args)
    if pid == 2467:
        return _game(*args)
    return _tours(args[0])


def public_examples(pid,raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned statement bytes required')
    cases = []
    for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)',raw.decode(),re.S):
        call = ast.parse('f('+match[1].strip()+')',mode='eval').body
        if not isinstance(call,ast.Call) or call.args or tuple(x.arg for x in call.keywords) != PARAMETERS[pid]:
            raise ValueError('pinned ordered example parameters differ')
        args = [ast.literal_eval(x.value) for x in call.keywords]; answer = json.loads(match[2])
        if not q.exact(expected(pid,args),answer):
            raise ValueError('independent reference disagrees with public example')
        cases.append({'args':args,'expected':answer,'compare':'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('complete pinned public examples required')
    return cases


def _generate_cases(pid,statement):
    cases = public_examples(pid,statement); categories = ['pinned_public_example']*len(cases)
    rng = random.Random(SEED_BASE+pid); sentinel = object()
    def add(args,category,answer=sentinel):
        validate(pid,args)
        cases.append({'args':args,'expected':expected(pid,args) if answer is sentinel else answer,'compare':'return'})
        categories.append(category)
    if pid == 2375:
        for length in range(1,9):
            for pattern in product('ID',repeat=length):
                add([''.join(pattern)],'exhaustive_all_valid_patterns_permutation_reference')
    elif pid == 2384:
        for length in range(1,6):
            for digits in product('019',repeat=length):
                add([''.join(digits)],'exhaustive_short_multiset_sequence_search')
        for _ in range(40):
            add([''.join(rng.choices('0123456789',k=rng.randrange(1,8)))],'seeded_multiset_sequence_search')
        for s,answer in [('0'*100000,'0'),('9'*100000,'9'*100000),('0'*99999+'9','9'),
                         ('1'*50000+'0'*50000,'1'*25000+'0'*50000+'1'*25000),('0123456789'*10000,''.join(str(i)*5000 for i in range(9,-1,-1))+''.join(str(i)*5000 for i in range(10)))]:
            add([s],'analytic_maximum_digit_populations',answer)
    elif pid == 2396:
        for n in range(4,513):
            add([n],'exhaustive_small_explicit_base_conversions')
        for n in (513,999,1024,99999,100000):
            add([n],'analytic_base_n_minus_two_is_digits_one_two',False)
    elif pid == 2428:
        for values in product((0,1),repeat=9):
            add([[list(values[0:3]),list(values[3:6]),list(values[6:9])]],'exhaustive_binary_three_by_three')
        for _ in range(80):
            rows,cols = rng.randrange(3,8),rng.randrange(3,8)
            add([[[rng.choice((0,1,999999,1000000)) for _ in range(cols)] for _ in range(rows)]],'seeded_rectangular_numeric_hourglasses')
        for value in (0,1000000):
            add([[[value]*150 for _ in range(150)]],'analytic_maximum_uniform_matrix',value*7)
        a = [[0]*150 for _ in range(150)]; a[149][149] = 1000000
        add([a],'analytic_maximum_corner_impulse',1000000)
    elif pid == 2438:
        for n in range(1,256):
            count = n.bit_count(); queries = [[a,b] for a in range(count) for b in range(a,count)]
            add([n,queries],'exhaustive_small_minimum_coin_decompositions_all_ranges')
        for exponent in range(30):
            add([2**exponent,[[0,0]]],'analytic_single_power',[2**exponent%MOD])
        add([2**29-1,[[0,28],[1,27],[28,28]]],'analytic_consecutive_power_exponents',[pow(2,406,MOD),pow(2,378,MOD),2**28])
        add([1,[[0,0] for _ in range(100000)]],'analytic_maximum_query_count',[1]*100000)
        # 10^9 = 2^29+2^28+2^27+2^25+2^24+2^23+2^20+2^19+2^17+2^15+2^14+2^11+2^9.
        add([10**9,[[0,12],[0,0],[12,12]]],'analytic_maximum_n_binary_expansion',[pow(2,261,MOD),512,2**29])
    elif pid == 2443:
        for n in range(1025):
            add([n],'exhaustive_small_scalar_summand_search')
        for n in (10000,10001,99990,99999,100000):
            add([n],'full_bound_summand_reference')
    elif pid == 2449:
        for length in range(1,4):
            arrays = list(product((1,2,3,4),repeat=length))
            for a in arrays:
                for b in arrays:
                    if sum(a)==sum(b) and sum(x%2 for x in a)==sum(x%2 for x in b):
                        add([list(a),list(b)],'exhaustive_short_feasible_assignment_permutations')
        for _ in range(60):
            n=rng.randrange(2,9); a=[rng.randrange(1,20) for _ in range(n)]; b=a.copy()
            for _ in range(5):
                i,j=rng.sample(range(n),2)
                if b[j]>2:
                    b[i]+=2;b[j]-=2
            rng.shuffle(b);add([a,b],'seeded_feasible_assignment_permutations')
        add([[2]*100000,[2]*100000],'analytic_maximum_length_identity',0)
        add([[2]*500+[1000000]*500,[500000]*500+[500002]*500],'analytic_large_integer_transfer_cost',124999500)
    elif pid == 2452:
        for length in range(1,5):
            words=[''.join(v) for v in product('ab',repeat=length)]
            for a in words:
                for b in words:
                    add([[a],[b]],'exhaustive_binary_words_edit_position_subsets')
        for _ in range(60):
            length=rng.randrange(1,10)
            add([[''.join(rng.choices('abcxyz',k=length)) for _ in range(rng.randrange(1,9))],
                 [''.join(rng.choices('abcxyz',k=length)) for _ in range(rng.randrange(1,9))]],'seeded_order_duplicates_edit_positions')
        add([['a'*100]*100,['b'*100]*100],'analytic_maximum_all_mismatch',[])
        add([['a'*100]*100,['a'*100]*100],'analytic_maximum_all_match',['a'*100]*100)
        add([['z'*98+'aa','z'*97+'aaa','z'*100]*33+['z'*98+'aa'],['z'*100]*100],
            'analytic_maximum_two_three_edit_boundary',(['z'*98+'aa','z'*100]*33)+['z'*98+'aa'])
    elif pid == 2467:
        for n in range(2,6):
            for parents in product(*(range(child) for child in range(1,n))):
                edges=[[p,child] for child,p in enumerate(parents,1)]
                amounts=list(product((-2,0,2),repeat=n)) if n<=3 else [tuple([-2]*n),tuple([2]*n),tuple(2*(-1)**i for i in range(n))]
                for bob in range(1,n):
                    for amount in amounts:
                        add([edges,bob,list(amount)],'exhaustive_small_recursive_trees_simulated_paths')
        for _ in range(60):
            n=rng.randrange(2,13); labels=list(range(n));rng.shuffle(labels)
            edges=[[labels[rng.randrange(i)],labels[i]] for i in range(1,n)];rng.shuffle(edges)
            add([edges,rng.randrange(1,n),[rng.choice((-10000,-2,0,2,10000)) for _ in range(n)]],'seeded_relabelled_tree_path_simulation')
        n=50000
        add([[[i-1,i] for i in range(1,n)],n-1,[10000]*n],'analytic_long_chain_equal_arrival_partition',250000000)
        add([[[0,i] for i in range(1,n)],n-1,[-10000]*n],'analytic_large_star_choose_bob_opened_leaf',-10000)
    else:
        for n in range(2,8):
            for tail in combinations(range(1,9),n-1):
                add([[0,*tail]],'exhaustive_small_stone_subsets_all_tours')
        for _ in range(40):
            n=rng.randrange(2,9)
            add([[0,*sorted(rng.sample(range(1,100),n-1))]],'seeded_all_tours')
        add([list(range(100000))],'analytic_maximum_count_equal_spacing',2)
        add([[0]+list(range(999900002,1000000001))],'analytic_maximum_count_endpoint_first_gap',999900003)
        add([[0,10**9]],'analytic_two_stone_maximum_endpoint',10**9)
    return cases,categories


def expected_observation_bytes(batch,language):
    if language not in ('javascript','python'):
        raise ValueError('unsupported observer language')
    size = sum(len(q.encoded({'i':i,'result':c['expected'],'result_type':q.expected_type(c['expected'],language),
                             'args_before':c['args'],'args_after':c['args'],'alias_edges':[]})) for i,c in enumerate(batch))
    return size+len(q.encoded({'done':len(batch)}))+(language=='python')


def build_cases(pid,statement):
    cases,categories = _generate_cases(pid,statement)
    if len(cases) != CASE_COUNT.get(pid) or q.sha(q.encoded(cases)) != CASES_SHA256.get(pid):
        raise ValueError('frozen case population or bytes changed')
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case file exceeds unchanged reader cap')
    for _,batch in q.batches(cases):
        if any(expected_observation_bytes(batch,language)>q.LIMITS['max_output_bytes'] for language in ('javascript','python')):
            raise ValueError('expected observations exceed unchanged output cap')
    return cases,categories
