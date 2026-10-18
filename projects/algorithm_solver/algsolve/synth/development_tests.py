"""Explicit development-suite repair after input-contract violations were found.

Original imports and historical scores are unchanged. These source-bound
suites are rejected as qualification authorities and replaced with separately
identified, seeded oracle suites. This is development evidence, not benchmark
rescoring or protected evaluation. Oracles never enter candidate code.
"""
import random
from collections import Counter
from itertools import combinations, product

from . import mine

SOURCE_HASHES = {
    'lcd:268': 'd5509f7c446017f514ef94ca2295e1dc4e94c8279b9e49870b6efba2cd35ddcd',
    'lcd:684': '779cc552576d05dab8d510d4d8b23a09ace57a7c1026f0f0630278b4ba3192a0',
    'lcd:1101': '7ce4bd3cb4eed9b15e5a74de81c21b682c30d73a7a5f51a824661e041b9c6364',
    'lcd:1133': 'a529fa7422522078c8bd5d76ead57c82d89577687876113309ead5761b4f64f5',
    'lcd:252': '80a2881f3b5092413851bdc64ad775b6160ff8ce1456ed37a8d9c4d291a6b929',
}
SEED = 20261017


def missing_oracle(args):
    if len(args) != 1 or type(args[0]) is not list:
        raise ValueError('expected one integer array')
    nums = args[0]; n = len(nums)
    if not 1 <= n <= 10000:
        raise ValueError('array length outside 1..10000')
    if any(type(x) is not int or not 0 <= x <= n for x in nums):
        raise ValueError('value outside 0..len(nums)')
    if len(set(nums)) != n:
        raise ValueError('values must be distinct')
    # Independent of the target's arithmetic accumulation.
    return (set(range(n+1))-set(nums)).pop()


def connected(n, edges):
    adjacent = [[] for _ in range(n+1)]
    for u,v in edges:
        adjacent[u].append(v); adjacent[v].append(u)
    reached, pending = {1}, [1]
    while pending:
        for v in adjacent[pending.pop()]:
            if v not in reached:
                reached.add(v); pending.append(v)
    return len(reached) == n


def redundant_oracle(args):
    if len(args) != 1 or type(args[0]) is not list:
        raise ValueError('expected one edge array')
    edges = args[0]; n = len(edges)
    if not 3 <= n <= 1000:
        raise ValueError('edge/vertex count outside 3..1000')
    if any(type(e) is not list or len(e) != 2 or any(type(x) is not int for x in e)
           or not 1 <= e[0] < e[1] <= n for e in edges):
        raise ValueError('edge must satisfy 1 <= u < v <= len(edges)')
    if len({tuple(e) for e in edges}) != n or not connected(n, edges):
        raise ValueError('expected simple connected graph on n vertices with n edges')
    # Remove edges in reverse input order and check connectivity directly. With
    # n-1 edges, a connected remainder is a tree. No DSU or Kruskal is used.
    for i in range(n-1,-1,-1):
        if connected(n,edges[:i]+edges[i+1:]): return edges[i]
    raise ValueError('no removable edge')


def acquaintance_oracle(args):
    if len(args) != 2 or type(args[0]) is not list or type(args[1]) is not int:
        raise ValueError('expected logs and integer population')
    logs, n = args
    if not 2 <= n <= 100 or not 1 <= len(logs) <= 10000:
        raise ValueError('population/log count outside declared bounds')
    if any(type(e) is not list or len(e) != 3 or any(type(x) is not int for x in e)
           or not 0 <= e[0] <= 10**9 or not 0 <= e[1] < n or not 0 <= e[2] < n
           or e[1] == e[2] for e in logs):
        raise ValueError('timestamp/vertex outside contract or self edge')
    if len({e[0] for e in logs}) != len(logs) or len({tuple(e[1:]) for e in logs}) != len(logs):
        raise ValueError('timestamps and ordered pairs must be unique')
    adjacent = [set() for _ in range(n)]
    # Recompute reachable vertices, independently of the target's DSU counts.
    for time, a, b in sorted(logs):
        adjacent[a].add(b); adjacent[b].add(a)
        reached, todo = {0}, [0]
        while todo:
            for v in adjacent[todo.pop()] - reached:
                reached.add(v); todo.append(v)
        if len(reached) == n:
            return time
    return -1


def unique_maximum_oracle(args):
    if len(args) != 1 or type(args[0]) is not list or not 1 <= len(args[0]) <= 2000:
        raise ValueError('expected integer array of length 1..2000')
    if any(type(x) is not int or not 0 <= x <= 1000 for x in args[0]):
        raise ValueError('value outside 0..1000')
    return max((x for x, count in Counter(args[0]).items() if count == 1), default=-1)


def meetings_oracle(args):
    if len(args) != 1 or type(args[0]) is not list or len(args[0]) > 10000:
        raise ValueError('expected at most 10000 intervals')
    if any(type(e) is not list or len(e) != 2 or any(type(x) is not int for x in e)
           or not 0 <= e[0] < e[1] <= 10**6 for e in args[0]):
        raise ValueError('interval must satisfy 0 <= start < end <= 1000000')
    # Sweep event occupancy rather than the target's reverse interval scan.
    events = [(start,1) for start,end in args[0]] + [(end,-1) for start,end in args[0]]
    active = 0
    for _, delta in sorted(events):
        active += delta
        if active > 1: return False
    return True


ORACLES = {'lcd:268': missing_oracle, 'lcd:684': redundant_oracle,
           'lcd:1101': acquaintance_oracle, 'lcd:1133': unique_maximum_oracle, 'lcd:252': meetings_oracle}


def generated(uid):
    rng = random.Random(SEED)
    cases = []
    if uid == 'lcd:268':
        settings = [(n, missing) for n in range(1,25) for missing in range(n+1)]
        settings += [(n, missing) for n in (33,100,1000,10000) for missing in (0,n//2,n)]
        for n, missing in settings:
            values = [v for v in range(n+1) if v != missing]
            rng.shuffle(values)
            cases.append({'args': [values], 'expected': missing_oracle([values]), 'compare': 'return'})
    elif uid == 'lcd:684':
        for n in list(range(3,31))*6 + [100, 1000]:
            edges = [[rng.randrange(1,v),v] for v in range(2,n+1)]
            present = {tuple(e) for e in edges}
            while True:
                u,v = sorted(rng.sample(range(1,n+1),2))
                if (u,v) not in present: break
            edges.append([u,v]); rng.shuffle(edges)
            cases.append({'args':[edges], 'expected':redundant_oracle([edges]), 'compare':'return'})
    elif uid == 'lcd:1101':
        for n in list(range(2,11))*12 + [100]:
            possible = list(combinations(range(n),2))
            selected = rng.sample(possible, rng.randrange(1,len(possible)+1))
            logs = [[t, *e] for t,e in enumerate(selected)]
            rng.shuffle(logs)
            cases.append({'args':[logs,n], 'expected':acquaintance_oracle([logs,n]), 'compare':'return'})
        for args in ([[[0,0,1]],2], [[[10**9,0,1]],2], [[[0,1,2]],3]):
            cases.append({'args':args,'expected':acquaintance_oracle(args),'compare':'return'})
    elif uid == 'lcd:1133':
        arrays = [list(xs) for size in range(1,6) for xs in product(range(3),repeat=size)]
        arrays += [[1000]*2000, list(range(1001))+list(range(999)), [0], [1000]]
        for nums in arrays:
            cases.append({'args':[nums],'expected':unique_maximum_oracle([nums]),'compare':'return'})
    elif uid == 'lcd:252':
        possible = [[a,b] for a in range(4) for b in range(a+1,5)]
        groups = [list(xs) for size in range(4) for xs in combinations(possible,size)]
        groups += [[[0,1],[0,1]], [[999999,1000000]], [[i,i+1] for i in range(10000)]]
        for intervals in groups:
            rng.shuffle(intervals)
            cases.append({'args':[intervals],'expected':meetings_oracle([intervals]),'compare':'return'})
    else:
        raise ValueError('No oracle suite for this problem')
    return cases


def select(uid, imported):
    source = mine.digest(imported)
    if uid not in SOURCE_HASHES:
        return imported, {'kind':'imported_independent_tests','sha256':source}
    if source != SOURCE_HASHES[uid]:
        raise ValueError('Development import changed; review its contract before applying repair')
    oracle = ORACLES[uid]
    rejected = []
    for i, test in enumerate(imported):
        try:
            answer = oracle(test['args'])
            if answer != test['expected']:
                raise ValueError('expected output disagrees with independent oracle')
        except (ValueError, KeyError, TypeError) as error:
            rejected.append({'index':i,'case_sha256':mine.digest(test),'reason':str(error)})
    if not rejected:
        raise ValueError('Repair requires reproduced source-suite defect')
    replacement = generated(uid)
    return replacement, {'kind':'seeded_independent_development_oracle', 'seed':SEED,
                         'original_suite_sha256':source,'original_count':len(imported),
                         'rejected_original_cases':rejected,'replacement_count':len(replacement),
                         'sha256':mine.digest(replacement),
                         'policy':'entire invalid import rejected as qualification suite; original files/results preserved; replacement is separate development evidence'}
