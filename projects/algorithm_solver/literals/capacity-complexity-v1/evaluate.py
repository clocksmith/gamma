#!/usr/bin/env python3
"""Check every claim of PREREGISTRATION.md by exhaustive search and exact fractions. Python 3.8+; no solver.

    python3 -B evaluate.py --selftest     the checker's own tests, on corpora outside the frozen files
    python3 -B evaluate.py                all claims; writes results.json; exits 1 if a proved claim fails

Rules: 'U' any substring that is not a whole program; 'R' any substring, whole programs included (the rank
of a word set); 'W2', 'W3', ... a single character, or a longer substring that occurs in at least that many
programs and is not a whole program.
"""
import importlib.util
import itertools
import json
import math
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
THEOREMS = os.path.join(HERE, '..', 'capacity-theorems-v1')


def load_theorems_evaluator():
    spec = importlib.util.spec_from_file_location('theorems_evaluate', os.path.join(THEOREMS, 'evaluate.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------ eligibility and exact minimum
def eligible(programs, rule):
    owners = {}
    for n, p in enumerate(programs):
        for i in range(len(p)):
            for j in range(i + 1, len(p) + 1):
                owners.setdefault(p[i:j], set()).add(n)
    if rule == 'R':
        return sorted(owners)
    whole = set(programs)
    if rule == 'U':
        return sorted(t for t in owners if t not in whole)
    threshold = int(rule[1:])
    return sorted(t for t, o in owners.items() if t not in whole and (len(t) == 1 or len(o) >= threshold))


def spellings(p, index):
    """One bitmask of entries per way of cutting p into entries, keeping only the minimal sets."""
    ways = [set() for _ in range(len(p) + 1)]
    ways[len(p)] = {0}
    for i in range(len(p) - 1, -1, -1):
        for j in range(i + 1, len(p) + 1):
            t = index.get(p[i:j])
            if t is not None:
                ways[i].update(m | (1 << t) for m in ways[j])
    return [m for m in ways[0] if not any(o != m and o & m == o for o in ways[0])]


def minimum(programs, tokens):
    """Smallest dictionary that spells every program, by exhaustive search over spellings. (size, dictionary)."""
    index = {t: i for i, t in enumerate(tokens)}
    need = [spellings(p, index) for p in programs]
    if any(not masks for masks in need):
        return None, None
    start = 0                                # an entry in every spelling of some program is in every dictionary
    for masks in need:
        common = masks[0]
        for m in masks:
            common &= m
        start |= common
    order = sorted(range(len(programs)), key=lambda n: len(need[n]))

    def search(d, k, budget, failed):
        while k < len(order) and any(m & ~d == 0 for m in need[order[k]]):
            k += 1
        if k == len(order):
            return d
        if (d, k) in failed:
            return None
        for m in need[order[k]]:
            extra = m & ~d
            cost = bin(extra).count('1')
            if cost <= budget:
                found = search(d | extra, k + 1, budget - cost, failed)
                if found is not None:
                    return found
        failed.add((d, k))
        return None

    size = bin(start).count('1')
    while True:
        found = search(start, 0, size - bin(start).count('1'), set())
        if found is not None:
            return size, [tokens[i] for i in range(len(tokens)) if found >> i & 1]
        size += 1


def plain_minimum(programs, tokens, limit=300_000):
    """The same minimum by trying every dictionary, smallest first. None if that needs more than `limit` tries."""
    index = {t: i for i, t in enumerate(tokens)}
    need = [spellings(p, index) for p in programs]
    tries = 0
    for size in range(len(tokens) + 1):
        for combo in itertools.combinations(range(len(tokens)), size):
            tries += 1
            if tries > limit:
                return None
            d = sum(1 << i for i in combo)
            if all(any(m & ~d == 0 for m in masks) for masks in need):
                return size
    return None


def vertex_cover_number(edges):
    vertices = sorted({v for e in edges for v in e})
    for size in range(len(vertices) + 1):
        for chosen in itertools.combinations(vertices, size):
            if all(u in chosen or v in chosen for u, v in edges):
                return size


def terminator_corpus(words, copies):
    """Theorem 2: `copies` copies of each word, each followed by an end character that occurs nowhere else."""
    return [w + chr(0x100 + c * len(words) + n) for c in range(copies) for n, w in enumerate(words)]


# ------------------------------------------------------------------ certificates, in exact fractions
def certificate_value(programs, tokens, potentials):
    """(valid, value). Valid when, for every eligible entry, the rises across all its occurrences sum to at most 1."""
    allowed, charge, value = set(tokens), {}, Fraction(0)
    if len(potentials) != len(programs):
        return False, None
    for p, raw in zip(programs, potentials):
        phi = [Fraction(x) for x in raw]
        if len(phi) != len(p) + 1:
            return False, None
        value += phi[-1] - phi[0]
        for i in range(len(p)):
            for j in range(i + 1, len(p) + 1):
                if p[i:j] in allowed and phi[j] > phi[i]:
                    charge[p[i:j]] = charge.get(p[i:j], 0) + phi[j] - phi[i]
    return all(c <= 1 for c in charge.values()), value


def fractional_dictionary_value(programs, tokens, amounts, mixes):
    """(valid, size). `amounts` gives a fraction of each entry; `mixes` gives, per program, weighted spellings.
    Valid when each program's weights sum to 1 and the weight through any one occurrence is at most that
    entry's amount. No certificate can be worth more than a valid fractional dictionary."""
    allowed = set(tokens)
    amounts = {t: Fraction(a) for t, a in amounts.items()}
    if any(t not in allowed or a < 0 for t, a in amounts.items()) or len(mixes) != len(programs):
        return False, None
    for p, mix in zip(programs, mixes):
        through, total = {}, Fraction(0)
        for weight, parts in mix:
            weight = Fraction(weight)
            if weight < 0 or ''.join(parts) != p or any(part not in allowed for part in parts):
                return False, None
            total += weight
            at = 0
            for part in parts:
                through[(at, part)] = through.get((at, part), 0) + weight
                at += len(part)
        if total != 1 or any(w > amounts.get(part, 0) for (_, part), w in through.items()):
            return False, None
    return True, sum(amounts.values(), Fraction(0))


def graph_fractional_dictionary(programs, cover):
    """Theorem 1 words: spell edge word u m v as u + (m v) with weight y_u and as (u m) + v with the rest."""
    letters = sorted({p[0] for p in programs} | {p[2] for p in programs})
    y = {letter: Fraction(c) for letter, c in zip(letters, cover)}
    amounts, mixes = {letter: weight for letter, weight in y.items() if weight}, []
    for u, m, v in programs:
        first = min(y[u], Fraction(1))
        mix = []
        if first:
            mix.append((first, [u, m + v]))
            amounts[m + v] = first
        if first != 1:
            mix.append((1 - first, [u + m, v]))
            amounts[u + m] = 1 - first
        mixes.append(mix)
    return amounts, mixes


def ceiling(value):
    return math.ceil(value)


# ------------------------------------------------------------------ self-test, on corpora outside the frozen files
def selftest():
    import random
    theorems = load_theorems_evaluator()
    rng = random.Random(7)
    for _ in range(60):
        programs = sorted({''.join(rng.choice('vwxyz') for _ in range(rng.randint(2, 4))) for _ in range(rng.randint(2, 4))})
        for rule in ('U', 'W2', 'R', 'W3'):
            tokens = eligible(programs, rule)
            if rule in ('U', 'W2'):
                assert tokens == sorted(theorems.eligible(programs, rule)), (programs, rule)
            size, dictionary = minimum(programs, tokens)
            plain = plain_minimum(programs, tokens)
            if size is None:
                assert plain is None
                continue
            assert plain is None or plain == size, (programs, rule, size, plain)
            assert set(dictionary) <= set(tokens) and len(dictionary) == size
            assert all(spellings(p, {t: i for i, t in enumerate(dictionary)}) for p in programs)
    # Theorem 1 on two graphs that are not frozen: two disjoint edges, and a path on five vertices.
    for edges, cover in (([(0, 1), (2, 3)], 2), ([(0, 1), (1, 2), (2, 3), (3, 4)], 2)):
        programs = ['PQRST'[u] + 'pqrs'[n] + 'PQRST'[v] for n, (u, v) in enumerate(edges)]
        assert vertex_cover_number(edges) == cover
        assert minimum(programs, eligible(programs, 'U'))[0] == len(edges) + cover
    # Theorem 2 on two word sets that are not frozen.
    for words, rank in ((['xy', 'xyxy'], 1), (['x', 'y', 'xyx'], 2)):
        assert minimum(words, eligible(words, 'R'))[0] == rank
        for copies in (2, 3):
            corpus = terminator_corpus(words, copies)
            assert len(set(corpus)) == copies * len(words)
            assert minimum(corpus, eligible(corpus, f'W{copies}'))[0] == copies * len(words) + rank
    # Certificates: a valid one, the same one overcharged, and one with a wrong shape.
    programs = ['pq', 'pr']
    tokens = eligible(programs, 'U')
    assert certificate_value(programs, tokens, [['0', '1', '2'], ['0', '0', '1']]) == (True, 3)
    assert certificate_value(programs, tokens, [['0', '1', '2'], ['0', '1', '2']])[0] is False
    assert certificate_value(programs, tokens, [['0', '1', '2']])[0] is False
    assert certificate_value(['zzz'], eligible(['zzz'], 'U'), [['0', '1/3', '2/3', '1']])[0] is False     # zz is charged 2/3 twice
    assert certificate_value(['zzz'], eligible(['zzz'], 'U'), [['0', '1/2', '1/2', '1']]) == (True, 1)
    # Fractional dictionaries: half of everything spells two disjoint edges' words; a starved entry is rejected.
    programs = ['PpQ', 'RqS']
    tokens = eligible(programs, 'U')
    amounts, mixes = graph_fractional_dictionary(programs, ['1/2'] * 4)
    assert fractional_dictionary_value(programs, tokens, amounts, mixes) == (True, 4)
    starved = dict(amounts, P=Fraction(1, 4))
    assert fractional_dictionary_value(programs, tokens, starved, mixes)[0] is False
    print('selftest passed')


# ------------------------------------------------------------------ the frozen claims
def main():
    theorems = load_theorems_evaluator()
    frozen = json.load(open(os.path.join(HERE, 'instances.json')))
    certificates = json.load(open(os.path.join(HERE, 'certificates.json')))['certificates']
    failures, misses = [], []
    out = {'schema': 'capacity-complexity-results/v1'}

    # T1 and T4: the words of a graph, unrestricted rule.
    out['graphs'] = {}
    for name, g in frozen['graphs'].items():
        programs, predicted, edges = g['programs'], g['predicted'], [tuple(e) for e in g['edges']]
        tokens = eligible(programs, 'U')
        size, dictionary = minimum(programs, tokens)
        cover = vertex_cover_number(edges)
        amounts, mixes = graph_fractional_dictionary(programs, g['fractionalCover'])
        fractional_ok, fractional = fractional_dictionary_value(programs, tokens, amounts, mixes)
        valid, value = certificate_value(programs, tokens, certificates[f'graph/{name}/U'])
        if size != len(edges) + cover:
            failures.append(f'T1 {name}: minimum {size}, |E| + cover {len(edges) + cover}')
        if not valid or value > size:
            failures.append(f'T3 graph {name}: certificate valid={valid} value={value} minimum={size}')
        if not fractional_ok or not valid or value != fractional:
            failures.append(f'T4 {name}: fractional dictionary ok={fractional_ok} size={fractional}, certificate {value}')
        observed = {'minimumVertexCover': cover, 'unrestrictedMinimum': size,
                    'linearProgramTwice': int(2 * fractional) if fractional_ok else None,
                    'certificateReachesMinimum': bool(valid and ceiling(value) == size)}
        for key in predicted:
            if predicted[key] != observed[key]:
                misses.append(f'graph {name} {key}: predicted {predicted[key]}, observed {observed[key]}')
        out['graphs'][name] = {'edges': len(edges), 'observed': observed, 'certificate': str(value), 'dictionary': dictionary}

    # T2: word sets, witness rule with 2 and 3 copies.
    out['wordSets'], random_rows = {}, []
    named = [(name, w['words'], w['predicted']) for name, w in frozen['wordSets'].items()]
    for name, words, predicted in named + [(None, words, None) for words in frozen['randomWordSets']]:
        rank = minimum(words, eligible(words, 'R'))[0]
        observed = {'rank': rank, 'witnessMinimum': {}}
        for copies in (2, 3):
            corpus = terminator_corpus(words, copies)
            size = minimum(corpus, eligible(corpus, f'W{copies}'))[0]
            observed['witnessMinimum'][str(copies)] = size
            if size != copies * len(words) + rank:
                failures.append(f'T2 {words} copies={copies}: minimum {size}, expected {copies * len(words) + rank}')
        if name is None:
            random_rows.append({'words': words, **observed})
        else:
            if predicted != observed:
                misses.append(f'word set {name}: predicted {predicted}, observed {observed}')
            out['wordSets'][name] = {'words': words, 'observed': observed}
    out['randomWordSets'] = {'sets': len(random_rows), 'rankCounts': {str(r): sum(1 for row in random_rows if row['rank'] == r)
                                                                      for r in sorted({row['rank'] for row in random_rows})},
                             'rows': random_rows}

    # T3, L* and R*: the frozen corpora of capacity-theorems-v1 and the counterexamples.
    first = json.load(open(os.path.join(THEOREMS, 'instances.json')))
    second = json.load(open(os.path.join(THEOREMS, 'instances-round2.json')))
    stored = json.load(open(os.path.join(THEOREMS, 'results.json')))['instances']
    groups = {
        'frozenInstances': [(f'instance/{name}', v['programs']) for name, v in first['instances'].items()],
        'counterexamples': [(f'counterexample/{name}', programs) for name, programs in frozen['counterexamples'].items()],
        'randomFamily': [(f'random/{n}', programs) for n, programs in enumerate(first['randomSearchFamily'])],
        'roundTwoFamily': [(f'round2/{n}', programs) for n, programs in enumerate(second['corpora'])],
    }
    out['certificateOnFrozenCorpora'] = {}
    for group, members in groups.items():
        summary = {'queries': 0, 'certificateReachesMinimum': 0, 'rankOrDisjointReachesMinimum': 0, 'onlyCertificateReaches': 0,
                   'rankAboveCertificate': 0, 'shortfalls': [], 'rankAbove': [], 'rows': []}
        for key, programs in members:
            for rule in ('U', 'W2'):
                tokens = eligible(programs, rule)
                size = minimum(programs, tokens)[0]
                plain = plain_minimum(programs, tokens)
                if plain is not None and plain != size:
                    failures.append(f'search {key} {rule}: two exhaustive searches disagree, {size} and {plain}')
                if group == 'frozenInstances':
                    kept = stored[key.split('/')[1]]['observed']['unrestricted' if rule == 'U' else 'witnessThreshold2']['minimumEntries']
                    if kept != size:
                        failures.append(f'search {key} {rule}: minimum {size}, capacity-theorems-v1 recorded {kept}')
                valid, value = certificate_value(programs, tokens, certificates[f'{key}/{rule}'])
                if not valid or value > size:
                    failures.append(f'T3 {key} {rule}: certificate valid={valid} value={value} minimum={size}')
                rank = theorems.program_rank(programs) if rule == 'U' else theorems.block_rank(programs)
                disjoint = theorems.disjoint_bound(programs, tokens)
                reaches, older = ceiling(value) == size, max(rank, disjoint) == size
                row = {'key': key, 'rule': rule, 'programs': programs, 'minimum': size, 'certificate': str(value),
                       'rank': rank, 'disjoint': disjoint}
                summary['queries'] += 1
                summary['certificateReachesMinimum'] += reaches
                summary['rankOrDisjointReachesMinimum'] += older
                summary['onlyCertificateReaches'] += reaches and not older
                if not reaches:
                    summary['shortfalls'].append(row)
                if rank > ceiling(value):
                    summary['rankAboveCertificate'] += 1
                    summary['rankAbove'].append(row)
                if group in ('frozenInstances', 'counterexamples') or not reaches or not older:
                    summary['rows'].append(row)
        out['certificateOnFrozenCorpora'][group] = summary

    out['misses'], out['provedClaimFailures'] = misses, failures
    with open(os.path.join(HERE, 'results.json'), 'w') as f:
        json.dump(out, f, indent=1)
        f.write('\n')

    reached = sum(1 for g in out['graphs'].values() if g['observed']['certificateReachesMinimum'])
    print(f"graphs: {len(out['graphs'])}; certificate reaches the minimum on {reached}")
    print(f"word sets: {len(out['wordSets'])} named, {len(random_rows)} random, both thresholds")
    for group, s in out['certificateOnFrozenCorpora'].items():
        print(f"{group}: {s['queries']} queries; certificate reaches {s['certificateReachesMinimum']}, "
              f"rank or disjoint reaches {s['rankOrDisjointReachesMinimum']}, only the certificate {s['onlyCertificateReaches']}, "
              f"rank above certificate {s['rankAboveCertificate']}")
    print(f'misses: {len(misses)}')
    for m in misses:
        print('  miss:', m)
    print(f'proved-claim failures: {len(failures)}')
    for f_ in failures:
        print('  FAILED:', f_)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        selftest()
    else:
        main()
