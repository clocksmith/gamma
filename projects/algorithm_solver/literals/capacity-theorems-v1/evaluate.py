#!/usr/bin/env python3
"""Check the pre-registered predictions by exhaustive enumeration. Python 3.8+, no solver.

    python3 -B evaluate.py --selftest     tests on corpora that are NOT in instances.json
    python3 -B evaluate.py                evaluate every frozen instance and the random family; write results.json

Everything is computed from the definitions in PREREGISTRATION.md:
  minimum entries and coverage by trying every dictionary, smallest first;
  the disjoint bound by trying every set of positions;
  ranks over the field of 1,000,000,007 elements with base 2.
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P, B = 1_000_000_007, 2


# ------------------------------------------------------------------ rules
def substrings(s):
    return {s[a:b] for a in range(len(s)) for b in range(a + 1, len(s) + 1)}


def eligible(programs, rule):
    whole = set(programs)
    every = set().union(*(substrings(s) for s in programs))
    if rule == 'U':
        return every - whole
    if rule == 'U+':                       # ablation: whole programs allowed
        return every
    if rule == 'W2':
        return {t for t in every if (len(t) == 1 or sum(t in s for s in programs) >= 2)} - whole
    raise ValueError(rule)


def tiles(s, words):
    reach = [False] * (len(s) + 1)
    reach[0] = True
    for i in range(len(s)):
        if reach[i]:
            for w in words:
                if s.startswith(w, i):
                    reach[i + len(w)] = True
    return reach[len(s)]


def minimum_and_curve(programs, tokens):
    """Smallest dictionary spelling every program, and the most programs spelled at each budget up to it."""
    tokens = sorted(tokens)
    curve, k = [0], 0
    while curve[-1] < len(programs):
        k += 1
        if k > len(tokens):
            return None, curve                      # the corpus cannot be spelled at all
        best = curve[-1]
        for words in itertools.combinations(tokens, k):
            got = sum(tiles(s, words) for s in programs)
            if got > best:
                best = got
                if best == len(programs):
                    break
        curve.append(best)
    return k, curve


# ------------------------------------------------------------------ linear algebra
def vector(word, chars):
    v, weight = [0] * len(chars), 1
    for c in word:
        v[chars[c]] = (v[chars[c]] + weight) % P
        weight = weight * B % P
    return v


def echelon(vectors):
    basis = []                                       # (pivot, row), each row reduced against the others
    for v in vectors:
        v = list(v)
        for pivot, row in basis:
            if v[pivot]:
                f = v[pivot]
                v = [(a - f * b) % P for a, b in zip(v, row)]
        pivot = next((j for j, x in enumerate(v) if x), None)
        if pivot is None:
            continue
        inv = pow(v[pivot], P - 2, P)
        v = [x * inv % P for x in v]
        basis = [(pj, [(a - row[pivot] * b) % P for a, b in zip(row, v)] if row[pivot] else row) for pj, row in basis]
        basis.append((pivot, v))
    return basis


def in_span(v, basis):
    v = list(v)
    for pivot, row in basis:
        if v[pivot]:
            f = v[pivot]
            v = [(a - f * b) % P for a, b in zip(v, row)]
    return not any(v)


def alphabet_index(programs):
    return {c: i for i, c in enumerate(sorted(set(''.join(programs))))}


def program_rank(programs):
    chars = alphabet_index(programs)
    return len(echelon([vector(s, chars) for s in programs]))


def every_program_cuttable(programs):
    chars = alphabet_index(programs)
    basis = echelon([vector(s, chars) for s in programs])
    return all(any(in_span(vector(s[:i], chars), basis) for i in range(1, len(s))) for s in programs)


def block_rank(programs):
    chars = alphabet_index(programs)
    blocks = []
    for s in programs:
        start = 0
        for i in range(len(s) - 1):
            if sum(s[i:i + 2] in t for t in programs) < 2:
                blocks.append(s[start:i + 1])
                start = i + 1
        blocks.append(s[start:])
    return len(echelon([vector(b, chars) for b in set(blocks)]))


# ------------------------------------------------------------------ cover sets
def cover_sets(programs, tokens):
    out = []
    for s in programs:
        for i in range(len(s)):
            out.append((s[i], frozenset(s[a:b] for a in range(i + 1) for b in range(i + 1, len(s) + 1) if s[a:b] in tokens)))
    return out


def forced_singletons(programs, tokens):
    return len({c for c, cover in cover_sets(programs, tokens) if cover == frozenset([c])})


def disjoint_bound(programs, tokens):
    sets = sorted({cover for _, cover in cover_sets(programs, tokens) if cover}, key=len)
    best = 0

    def grow(start, used, count):
        nonlocal best
        best = max(best, count)
        if count + len(sets) - start <= best:
            return
        for j in range(start, len(sets)):
            if used.isdisjoint(sets[j]):
                grow(j + 1, used | sets[j], count + 1)

    grow(0, frozenset(), 0)
    return best


# ------------------------------------------------------------------ one corpus
def measure(programs, with_curves=True):
    out = {'alphabetSize': len(set(''.join(programs)))}
    for rule, key in (('U', 'unrestricted'), ('W2', 'witnessThreshold2')):
        tokens = eligible(programs, rule)
        minimum, curve = minimum_and_curve(programs, tokens)
        row = {'forcedSingletons': forced_singletons(programs, tokens), 'disjointBound': disjoint_bound(programs, tokens),
               'minimumEntries': minimum, 'coverageByBudget': curve}
        if rule == 'U':
            row['programRank'] = program_rank(programs)
            row['everyProgramHasACuttablePrefix'] = every_program_cuttable(programs)
        else:
            row['blockRank'] = block_rank(programs)
        out[key] = row
    return out


def proved_claims(programs, m):
    """S1 to S6 of the pre-registration. Returns the names of the claims that fail."""
    u, w = m['unrestricted'], m['witnessThreshold2']
    failed = []
    if u['minimumEntries'] is not None and u['programRank'] > u['minimumEntries']:
        failed.append('S1')
    if w['minimumEntries'] is not None and w['blockRank'] > w['minimumEntries']:
        failed.append('S2')
    for row in (u, w):
        if row['minimumEntries'] is not None and not row['forcedSingletons'] <= row['disjointBound'] <= row['minimumEntries']:
            failed.append('S3')
    if all(len(s) > 1 for s in programs) and (w['minimumEntries'] is None or w['minimumEntries'] > m['alphabetSize']):
        failed.append('S4')
    if u['minimumEntries'] == u['programRank'] and not u['everyProgramHasACuttablePrefix']:
        failed.append('S5')
    for row in (u, w):
        if any(b < a for a, b in zip(row['coverageByBudget'], row['coverageByBudget'][1:])):
            failed.append('S6')
    for k, value in enumerate(w['coverageByBudget']):
        ceiling = u['coverageByBudget'][k] if k < len(u['coverageByBudget']) else len(programs)
        if value > ceiling:
            failed.append('S6')
    return sorted(set(failed))


def selftest():
    """Corpora that are not in instances.json and are not relabelled copies of one, with values worked out by hand."""
    cases = [
        (['aaa'], {'U': (1, [0, 1]), 'W2': (1, [0, 1])}),
        (['abab'], {'U': (1, [0, 1]), 'W2': (2, [0, 0, 1])}),
        (['ab', 'ba'], {'U': (2, [0, 0, 2]), 'W2': (2, [0, 0, 2])}),
        (['aaa', 'aab'], {'U': (2, [0, 1, 2]), 'W2': (2, [0, 1, 2])}),
    ]
    for programs, expected in cases:
        for rule, (minimum, curve) in expected.items():
            got = minimum_and_curve(programs, eligible(programs, rule))
            assert got == (minimum, curve), (programs, rule, got, (minimum, curve))
    assert program_rank(['ab', 'ba']) == 2 and program_rank(['ab', 'abab']) == 1
    assert block_rank(['aaa', 'aab']) == 2          # 'aa' is shared, so the blocks are aaa and aa, b
    assert forced_singletons(['pq', 'pr'], eligible(['pq', 'pr'], 'W2')) == 3
    assert disjoint_bound(['pq', 'pr'], eligible(['pq', 'pr'], 'W2')) == 3
    assert every_program_cuttable(['abab']) is True and every_program_cuttable(['abc']) is False
    assert minimum_and_curve(['pq', 'pr'], eligible(['pq', 'pr'], 'U+')) == (2, [0, 1, 2])
    print('selftest: ok (no frozen instance was read)')


def main():
    instances = json.load(open(os.path.join(HERE, 'instances.json')))
    predictions = json.load(open(os.path.join(HERE, 'predictions.json')))
    results = {'schema': 'capacity-theorems-results/v1', 'field': {'prime': P, 'base': B}, 'instances': {}, 'misses': [],
               'provedClaimFailures': [], 'ablation': {}, 'random': {}}
    for name, entry in instances['instances'].items():
        programs = entry['programs']
        observed = measure(programs)
        predicted = predictions['predictions'][name]
        results['instances'][name] = {'programs': programs, 'observed': observed}
        if predicted['alphabetSize'] != observed['alphabetSize']:
            results['misses'].append({'instance': name, 'field': 'alphabetSize', 'predicted': predicted['alphabetSize'], 'observed': observed['alphabetSize']})
        for key in ('unrestricted', 'witnessThreshold2'):
            for field, value in predicted[key].items():
                if observed[key][field] != value:
                    results['misses'].append({'instance': name, 'rule': key, 'field': field, 'predicted': value, 'observed': observed[key][field]})
        failed = proved_claims(programs, observed)
        if failed:
            results['provedClaimFailures'].append({'instance': name, 'claims': failed})
    for name, predicted in predictions['wholeProgramsAllowedAblation'].items():
        programs = instances['instances'][name]['programs']
        minimum, curve = minimum_and_curve(programs, eligible(programs, 'U+'))
        results['ablation'][name] = {'minimumEntries': minimum, 'coverageByBudget': curve}
        for field, value in predicted.items():
            if results['ablation'][name][field] != value:
                results['misses'].append({'instance': name, 'rule': 'whole programs allowed', 'field': field, 'predicted': value, 'observed': results['ablation'][name][field]})

    frozen = results['instances']
    a_star = [n for n, r in frozen.items() if r['observed']['witnessThreshold2']['minimumEntries'] != r['observed']['witnessThreshold2']['blockRank']]
    b_star = [n for n, r in frozen.items()
              if (r['observed']['unrestricted']['minimumEntries'] == r['observed']['unrestricted']['programRank']) != r['observed']['unrestricted']['everyProgramHasACuttablePrefix']]
    results['conjecturesOnFrozenInstances'] = {'A*: W2 minimum equals block rank': {'holdsOn': len(frozen) - len(a_star), 'of': len(frozen), 'fails': a_star},
                                               'B*: U minimum equals rank iff every program cuttable': {'holdsOn': len(frozen) - len(b_star), 'of': len(frozen), 'fails': b_star}}

    tally = {'corpora': 0, 'provedClaimFailures': [], 'aStarHolds': 0, 'bStarHolds': 0, 'firstAStarCounterexample': None,
             'firstBStarCounterexample': None, 'saturated': 0, 'saturatedButDisjointBoundMisses': 0, 'firstSaturationMiss': None,
             'unrestrictedMinimumAboveRank': 0}
    for programs in instances['randomSearchFamily']:
        m = measure(programs)
        u, w = m['unrestricted'], m['witnessThreshold2']
        tally['corpora'] += 1
        failed = proved_claims(programs, m)
        if failed:
            tally['provedClaimFailures'].append({'programs': programs, 'claims': failed})
        if w['minimumEntries'] == max(w['blockRank'], w['disjointBound']):
            tally['aStarHolds'] += 1
        elif tally['firstAStarCounterexample'] is None:
            tally['firstAStarCounterexample'] = {'programs': programs, 'minimum': w['minimumEntries'], 'blockRank': w['blockRank'], 'disjointBound': w['disjointBound']}
        attained = u['minimumEntries'] == u['programRank']
        if attained == u['everyProgramHasACuttablePrefix']:
            tally['bStarHolds'] += 1
        elif tally['firstBStarCounterexample'] is None:
            tally['firstBStarCounterexample'] = {'programs': programs, 'minimum': u['minimumEntries'], 'programRank': u['programRank'],
                                                 'everyProgramHasACuttablePrefix': u['everyProgramHasACuttablePrefix']}
        tally['unrestrictedMinimumAboveRank'] += not attained
        if w['minimumEntries'] == m['alphabetSize']:
            tally['saturated'] += 1
            if w['disjointBound'] < m['alphabetSize']:
                tally['saturatedButDisjointBoundMisses'] += 1
                if tally['firstSaturationMiss'] is None:
                    tally['firstSaturationMiss'] = {'programs': programs, 'alphabetSize': m['alphabetSize'], 'disjointBound': w['disjointBound'], 'blockRank': w['blockRank']}
    results['random'] = tally
    json.dump(results, open(os.path.join(HERE, 'results.json'), 'w'), indent=1)
    print('frozen instances:', len(frozen), '| predicted numbers that differ:', len(results['misses']), '| proved-claim failures:', len(results['provedClaimFailures']))
    for miss in results['misses']:
        print('  MISS', miss)
    print(json.dumps(results['conjecturesOnFrozenInstances'], indent=1))
    print(json.dumps(tally, indent=1))


if __name__ == '__main__':
    selftest() if '--selftest' in sys.argv else main()
