"""Explicit development-suite repair after input-contract violations were found.

Original imports and historical scores are unchanged. These two source-bound
suites are rejected as qualification authorities and replaced with separately
identified, seeded oracle suites. This is development evidence, not benchmark
rescoring or protected evaluation. Oracles never enter candidate code.
"""
import random

from . import mine

SOURCE_HASHES = {
    'lcd:268': 'd5509f7c446017f514ef94ca2295e1dc4e94c8279b9e49870b6efba2cd35ddcd',
    'lcd:684': '779cc552576d05dab8d510d4d8b23a09ace57a7c1026f0f0630278b4ba3192a0',
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
    else:
        raise ValueError('No oracle suite for this problem')
    return cases


def select(uid, imported):
    source = mine.digest(imported)
    if uid not in SOURCE_HASHES:
        return imported, {'kind':'imported_independent_tests','sha256':source}
    if source != SOURCE_HASHES[uid]:
        raise ValueError('Development import changed; review its contract before applying repair')
    oracle = missing_oracle if uid == 'lcd:268' else redundant_oracle
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
