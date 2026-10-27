"""Independent exposed-development queue03 oracles, no candidate loading.

Full statement validators are distinct from bounded reference work. Stateless
cases use the existing imported qualification packet/observer conventions.
No source interface is inferred here; adapter review remains a later gate.
"""
from functools import lru_cache
from itertools import product
import random
import string
import json
from math import prod

from . import imported_qualification as q

IDS = (2245, 2271, 2289, 2301, 2321, 2333, 2348)
PARAMETERS = {2245: ('grid',), 2271: ('tiles', 'carpetLen'), 2289: ('nums',),
              2301: ('s', 'sub', 'mappings'), 2321: ('nums1', 'nums2'),
              2333: ('nums1', 'nums2', 'k1', 'k2'), 2348: ('nums',)}
TITLES = {2245: 'Maximum Trailing Zeros in a Cornered Path',
          2271: 'Maximum White Tiles Covered by a Carpet',
          2289: 'Steps to Make Array Non-decreasing',
          2301: 'Match Substring After Replacement',
          2321: 'Maximum Score Of Spliced Array',
          2333: 'Minimum Sum of Squared Difference',
          2348: 'Number of Zero-Filled Subarrays'}
ALPHABET = frozenset(string.ascii_letters + string.digits)
SEED = 202610271835
DEFINITION_SHA256 = {
    2245: 'fb8b5ee887f7b04b9ab93bba28b40bcf56e2f8ba9d3a71bbfa7b9191a2ed9efd',
    2271: '3af215a73966a52712b2edfba3e275ebc872ba42499c0132fd43b24acc8e60c3',
    2289: '997616b966b67ae65b28e119b5c1d09df537c6049148a308f02eea4d818b288c',
    2301: 'effa976688678c569bc6c6f553dee75da67294280cec2f4f20db63edc3373a27',
    2321: 'bb7adb649e2e016a69d91569d306550987a63394154efd9f88e004296522f3f0',
    2333: '065f74e469b25ab5bf499d63170e03a8d6fbd92dcbbe4381590129f25438fd8a',
    2348: 'cabe0ff21c1e40098bba91e3d4a06962d6f0120cffb754524f4ec06358b57fe7',
}
SCOPE = {
    'evidence': 'exposed-development; finite evidence, not proof or fresh confirmation',
    'effects': 'Return-value oracle; public statements do not specify caller-input mutation. The eventual input-preserving observer envelope must be reported separately, not invented as a statement obligation.',
    'alias': 'All seven outputs are scalar; output/input alias edges are impossible. Input graph identity and repeated-call isolation require later observer review.',
    'numeric': 'Strict integer inputs excluding bool; all exact integer results at most 10^15, below 2^53; 2301 returns a strict boolean. ASCII-only strings; no Unicode extrapolation.',
    'complexity': 'Bounded brute references plus analytically justified size probes only. Candidate asymptotic/stack/memory review remains unresolved; no timing claim.',
    'interfaces': 'Ordered parameters derived from public specification; actual candidate exports, methods, wrappers, and source SHA256 unresolved.',
    'transport': 'Unchanged q.encoded/q.batches/MAX_FILE/MAX_PACKET/LIMITS. Simultaneous maximum decimal-width inputs exceeding these caps are omitted explicitly, not domain-excluded.',
}


def integer(x, lo, hi):
    return type(x) is int and lo <= x <= hi


def ints(x, lo, hi, minimum=1, maximum=100000):
    return type(x) is list and minimum <= len(x) <= maximum and all(integer(v, lo, hi) for v in x)


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported identity or ordered argument shape')
    if pid == 2245:
        grid = args[0]
        ok = (type(grid) is list and 1 <= len(grid) <= 100000 and type(grid[0]) is list
              and 1 <= len(grid[0]) and len(grid) * len(grid[0]) <= 100000
              and all(ints(row, 1, 1000, len(grid[0]), len(grid[0])) for row in grid))
    elif pid == 2271:
        tiles, length = args
        ok = (type(tiles) is list and 1 <= len(tiles) <= 50000 and integer(length, 1, 10**9)
              and all(ints(t, 1, 10**9, 2, 2) and t[0] <= t[1] for t in tiles))
        if ok:
            ordered = sorted(tiles)
            ok = all(a[1] < b[0] for a, b in zip(ordered, ordered[1:]))
    elif pid in (2289, 2348):
        ok = ints(args[0], 1 if pid == 2289 else -10**9, 10**9)
    elif pid == 2301:
        s, sub, maps = args
        ok = (type(s) is str and type(sub) is str and 1 <= len(sub) <= len(s) <= 5000
              and set(s) <= ALPHABET and set(sub) <= ALPHABET and type(maps) is list and len(maps) <= 1000
              and all(type(p) is list and len(p) == 2 and all(type(c) is str and len(c) == 1 and c in ALPHABET for c in p)
                      and p[0] != p[1] for p in maps))
    else:
        a, b = args[:2]
        low, high = (1, 10000) if pid == 2321 else (0, 100000)
        ok = ints(a, low, high) and ints(b, low, high) and len(a) == len(b)
        if pid == 2333:
            ok = ok and all(integer(k, 0, 10**9) for k in args[2:])
    if not ok:
        raise ValueError('outside complete pinned public statement domain')


def _corner_products(grid):
    """Enumerate every corner and both endpoints, multiply actual path values."""
    best = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            for end_r in range(len(grid)):
                for end_c in range(len(grid[0])):
                    value = 1
                    for x in range(min(c, end_c), max(c, end_c) + 1):
                        value *= grid[r][x]
                    for y in range(min(r, end_r), max(r, end_r) + 1):
                        if y != r:
                            value *= grid[y][c]
                    zeros = 0
                    while value % 10 == 0:
                        zeros += 1
                        value //= 10
                    best = max(best, zeros)
    return best


def _decrement_allocations(a, b, budget):
    differences = [abs(x - y) for x, y in zip(a, b)]
    budget = min(budget, sum(differences))
    # Any <=k1+k2 gap-closing unit moves can be partitioned between arrays;
    # both signs and negative intermediate values are permitted by the spec.
    @lru_cache(None)
    def visit(i, remaining):
        if i == len(differences):
            return 0
        d = differences[i]
        return min((d - used)**2 + visit(i + 1, remaining - used)
                   for used in range(min(d, remaining) + 1))
    return visit(0, budget)


def expected(pid, args):
    validate(pid, args)
    if pid == 2245:
        if len(args[0]) > 7 or len(args[0][0]) > 7:
            raise ValueError('reference bound, not input-domain restriction')
        return _corner_products(args[0])
    if pid == 2271:
        tiles, length = args
        if max(r for _, r in tiles) - min(l for l, _ in tiles) > 200 or length > 200:
            raise ValueError('reference bound, not input-domain restriction')
        white = {x for l, r in tiles for x in range(l, r + 1)}
        return max(len(white.intersection(range(start, start + length)))
                   for start in range(min(white) - length, max(white) + 1))
    if pid == 2289:
        if len(args[0]) > 100:
            raise ValueError('reference bound, not input-domain restriction')
        current = args[0][:]
        count = 0
        while any(a > b for a, b in zip(current, current[1:])):
            current = [current[0]] + [current[i] for i in range(1, len(current)) if current[i - 1] <= current[i]]
            count += 1
        return count
    if pid == 2301:
        s, sub, maps = args
        if len(s) > 30 or len(sub) > 8:
            raise ValueError('reference bound, not input-domain restriction')
        choices = [{c} | {b for a, b in maps if a == c} for c in sub]
        if prod(map(len, choices)) > 100000:
            raise ValueError('reference expansion bound')
        return any(''.join(chars) in s for chars in product(*choices))
    if pid == 2321:
        a, b = args
        if len(a) > 30:
            raise ValueError('reference bound, not input-domain restriction')
        scores = [sum(a), sum(b)]
        for l in range(len(a)):
            for r in range(l + 1, len(a) + 1):
                scores.extend((sum(a[:l] + b[l:r] + a[r:]), sum(b[:l] + a[l:r] + b[r:])))
        return max(scores)
    if pid == 2333:
        a, b, k1, k2 = args
        if len(a) > 8 or sum(abs(x - y) for x, y in zip(a, b)) > 200:
            raise ValueError('reference bound, not input-domain restriction')
        return _decrement_allocations(a, b, k1 + k2)
    if len(args[0]) > 100:
        raise ValueError('reference bound, not input-domain restriction')
    values = args[0]
    return sum(all(x == 0 for x in values[l:r]) for l in range(len(values)) for r in range(l + 1, len(values) + 1))


EXAMPLES = {
    2245: [([[[23,17,15,3,20],[8,1,20,27,11],[9,4,6,2,21],[40,9,1,10,6],[22,7,4,5,3]]], 3),
           ([[[4,3,2],[7,6,1],[8,8,8]]], 0)],
    2271: [([[[1,5],[10,11],[12,18],[20,25],[30,32]],10], 9), ([[[10,11],[1,1]],2], 2)],
    2289: [([[5,3,4,4,7,3,6,11,8,5,11]], 3), ([[4,5,7,7,13]], 0)],
    2301: [(['fool3e7bar','leet',[['e','3'],['t','7'],['t','8']]], True),
           (['fooleetbar','f00l',[['o','0']]], False),
           (['Fool33tbaR','leetd',[['e','3'],['t','7'],['t','8'],['d','b'],['p','b']]], True)],
    2321: [([[60,60,60],[10,90,10]], 210), ([[20,40,20,70,30],[50,20,50,40,20]], 220),
           ([[7,11,13],[1,1,1]],31)],
    2333: [([[1,2,3,4],[2,10,20,19],0,0],579), ([[1,4,10,12],[5,8,6,9],1,1],43)],
    2348: [([[1,3,0,0,2,0,0,4]],6), ([[0,0,0,2,0,0]],9), ([[2,10,2019]],0)],
}


def _generate_cases(pid):
    cases, categories = [], []
    rng = random.Random(SEED + pid)
    sentinel = object()
    def add(args, category, answer=sentinel):
        validate(pid, args)
        cases.append({'args': args, 'expected': expected(pid, args) if answer is sentinel else answer, 'compare': 'return'})
        categories.append(category)
    for args, answer in EXAMPLES[pid]:
        if expected(pid, args) != answer:
            raise AssertionError('independent reference disagrees with pinned public example')
        add(args, 'pinned_public_example', answer)
    if pid == 2245:
        for values in product((1,2,5,10,1000), repeat=4):
            add([[list(values[:2]), list(values[2:])]], 'exhaustive_2_by_2_path_products')
        for _ in range(80):
            m, n = rng.randrange(1,6), rng.randrange(1,6)
            add([[[rng.choice((1,2,4,5,25,40,125,128,1000)) for _ in range(n)] for _ in range(m)]], 'seeded_corner_products')
        add([[[1000]*100000]], 'analytic_maximum_horizontal_path', 300000)
        add([[[10] for _ in range(100000)]], 'analytic_maximum_vertical_path', 100000)
        add([[[10]*250 for _ in range(400)]], 'analytic_maximum_area_rectangle', 649)
    elif pid == 2271:
        for mask in range(1, 256):
            tiles = [[i+1,i+1] for i in range(8) if mask >> i & 1]
            rng.shuffle(tiles)
            for length in (1,2,5,10):
                add([tiles,length], 'exhaustive_eight_position_white_sets')
        for _ in range(80):
            points = sorted(rng.sample(range(1,80), 12))
            tiles = [points[i:i+2] for i in range(0,12,2)]
            rng.shuffle(tiles)
            add([tiles,rng.randrange(1,81)], 'seeded_disjoint_interval_lengths')
        add([[[1,10**9]],10**9], 'analytic_full_coordinate_interval',10**9)
        add([[[2*i+1,2*i+1] for i in range(50000)],10**9], 'analytic_maximum_tile_count',50000)
        add([[[1,2],[10**9-1,10**9]],3], 'analytic_extreme_gap',2)
    elif pid in (2289,2348):
        alphabet = (1,2,3) if pid == 2289 else (-1,0,1)
        for n in range(1,7):
            for values in product(alphabet,repeat=n):
                add([list(values)], 'exhaustive_ternary_arrays_up_to_six')
        for _ in range(80):
            add([[rng.choice(alphabet + ((10**9,) if pid == 2289 else (-10**9,10**9))) for _ in range(rng.randrange(7,35))]], 'seeded_numeric_boundaries')
        if pid == 2289:
            add([[100000]+list(range(1,100000))], 'analytic_one_removal_per_round',99999)
            add([list(range(100000,0,-1))], 'analytic_simultaneous_decreasing_removal',1)
            add([[1]*100000], 'analytic_maximum_equal_array',0)
        else:
            add([[0]*100000], 'analytic_maximum_zero_run',100000*100001//2)
            add([[-1]*100000], 'analytic_maximum_nonzero_array',0)
            add([[0,1]*50000], 'analytic_separated_zero_runs',50000)
    elif pid == 2301:
        mapsets = ([], [['a','b']], [['b','a']], [['a','b'],['b','a']], [['a','b'],['b','0']], [['a','b'],['a','b']])
        for n in range(1,5):
            for chars in product('ab',repeat=n):
                for m in range(1,min(n,3)+1):
                    for sub in product('ab',repeat=m):
                        for maps in mapsets:
                            add([''.join(chars),''.join(sub),maps], 'exhaustive_binary_strings_directional_and_duplicate_maps')
        add(['0','a',[['a','b'],['b','0']]], 'no_transitive_replacement',False)
        add(['A','a',[]], 'case_sensitive_ascii',False)
        add(['a'*5000,'a'*5000,[]], 'analytic_maximum_identical_strings',True)
        add(['a'*4999+'b','a'*2500+'b',[]], 'analytic_late_match',True)
        add(['a'*5000,'a'*2499+'b',[['b','0']]*1000], 'analytic_maximum_mappings_late_failure',False)
    elif pid == 2321:
        for n in range(1,5):
            for values in product((1,4),repeat=2*n):
                add([list(values[:n]),list(values[n:])], 'exhaustive_binary_array_pairs')
        for _ in range(100):
            n=rng.randrange(1,15)
            add([[rng.randrange(1,10001) for _ in range(n)] for _ in range(2)], 'seeded_all_splice_intervals')
        add([[1]*100000,[10000]*100000], 'analytic_maximum_score_upper_bound',10**9)
        add([[1]*100000,[1]*100000], 'analytic_maximum_equal_arrays',100000)
    else:
        for n in range(1,4):
            for differences in product(range(4),repeat=n):
                for k1,k2 in product(range(3),repeat=2):
                    add([[0]*n,list(differences),k1,k2], 'exhaustive_small_gap_allocations')
        for _ in range(80):
            n=rng.randrange(1,7)
            add([[rng.randrange(11) for _ in range(n)],[rng.randrange(11) for _ in range(n)],rng.randrange(20),rng.randrange(20)], 'seeded_budget_allocations')
        add([[0]*100000,[100000]*100000,0,0], 'analytic_maximum_exact_integer_sum',10**15)
        add([[0]*100000,[100000]*100000,10**9,10**9], 'analytic_uniform_balanced_reductions',100000*80000**2)
        add([[0]*100000,[1]*100000,10**9,10**9], 'analytic_excess_budget_at_most_not_exactly',0)
    return cases,categories


def build_cases(pid, statement):
    if pid not in IDS:
        raise ValueError('no source-blind reference frozen for this identity')
    if type(statement) is not bytes or q.sha(statement) != DEFINITION_SHA256[pid]:
        raise ValueError('exact freshly gated definition bytes required')
    definition = json.loads(statement)
    if definition['problem_id'] != pid or f'{pid}. {TITLES[pid]}' not in str(definition['web_result']):
        raise ValueError('numeric/title definition identity mismatch')
    cases,categories = _generate_cases(pid)
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('unchanged case file cap exceeded')
    for _,batch in q.batches(cases):
        for language in ('python','javascript'):
            records = [{'i':i,'result':c['expected'],'result_type':q.expected_type(c['expected'],language),
                        'args_before':c['args'],'args_after':c['args'],'alias_edges':[]} for i,c in enumerate(batch)]
            projected = sum(len(q.encoded(r)) for r in records) + len(q.encoded({'done':len(batch)})) + (language == 'python')
            if projected > q.LIMITS['max_output_bytes']:
                raise ValueError('unchanged observation cap exceeded')
    return cases,categories
