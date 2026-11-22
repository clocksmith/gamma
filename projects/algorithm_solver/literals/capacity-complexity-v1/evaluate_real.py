#!/usr/bin/env python3
"""Check the stored certificates and dictionaries for the corpora of PREREGISTRATION-REAL.md. Python 3.8+; no solver.

    python3 -B evaluate_real.py --selftest     tests on corpora outside the frozen files
    python3 -B evaluate_real.py                checks certificates-real.json; writes results-real.json
"""
import hashlib
import json
import math
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, '..', 'capacity-diagnostic-v1', 'independent-eval', 'independent-instances.json')
SOURCE_SHA256 = '941688ab7511851178f62b63fd655f971986a4a0a2d9af7f2e9e3458d963c0b2'
CORPORA = ('C-1', 'C-2')
STORED_LOWER_BOUND = {'C-1': 61, 'C-2': 65}          # from capacity-diagnostic-v1/independent-eval/RESULTS-INDEPENDENT.md


def occurrences(programs):
    """Every occurrence (program, start, end) of an entry eligible under the witness rule with threshold 2:
    a single character, or a longer string that also occurs in another program. No entry is a whole program."""
    assert len(set(programs)) == len(programs)
    whole = set(programs)
    for n, p in enumerate(programs):
        others = [q for m, q in enumerate(programs) if m != n]
        for i in range(len(p)):
            if p[i] not in whole:
                yield n, i, i + 1
            for j in range(i + 2, len(p) + 1):
                s = p[i:j]
                if not any(s in q for q in others):
                    break                    # no longer string from this start occurs in another program either
                if s not in whole:
                    yield n, i, j


def certificate_value(programs, potentials):
    """(valid, value). Valid when the rises across all occurrences of each eligible entry sum to at most 1."""
    if len(potentials) != len(programs) or any(len(row) != len(p) + 1 for row, p in zip(potentials, programs)):
        return False, None
    phi = [[Fraction(x) for x in row] for row in potentials]
    charge = {}
    for n, i, j in occurrences(programs):
        rise = phi[n][j] - phi[n][i]
        if rise > 0:
            s = programs[n][i:j]
            charge[s] = charge.get(s, 0) + rise
    return all(c <= 1 for c in charge.values()), sum((row[-1] - row[0] for row in phi), Fraction(0))


def dictionary_spells(programs, dictionary):
    """True when every entry is eligible, none repeats, and every program is a concatenation of entries."""
    eligible = {programs[n][i:j] for n, i, j in occurrences(programs)}
    if len(set(dictionary)) != len(dictionary) or any(d not in eligible for d in dictionary):
        return False
    for p in programs:
        reach = [True] + [False] * len(p)
        for i in range(len(p)):
            if reach[i]:
                for d in dictionary:
                    if p.startswith(d, i):
                        reach[i + len(d)] = True
        if not reach[len(p)]:
            return False
    return True


def load_corpora():
    raw = open(SOURCE, 'rb').read()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise SystemExit('FAILED: independent-instances.json is not the frozen file')
    corpora = json.loads(raw)['corpora']
    return {name: corpora[name]['programs'] for name in CORPORA}


def selftest():
    import random
    import evaluate
    rng = random.Random(11)
    for _ in range(80):
        programs = sorted({''.join(rng.choice('vwxyz') for _ in range(rng.randint(2, 7))) for _ in range(rng.randint(2, 4))})
        tokens = set(evaluate.eligible(programs, 'W2'))
        seen = list(occurrences(programs))
        assert {programs[n][i:j] for n, i, j in seen} == tokens, programs
        assert len(seen) == sum(1 for p in programs for i in range(len(p)) for j in range(i + 1, len(p) + 1) if p[i:j] in tokens)
        potentials = [[str(Fraction(rng.randint(0, 6), 12)) for _ in range(len(p) + 1)] for p in programs]
        assert certificate_value(programs, potentials) == evaluate.certificate_value(programs, sorted(tokens), potentials)
        size, dictionary = evaluate.minimum(programs, sorted(tokens))
        assert dictionary_spells(programs, dictionary)
        assert not dictionary_spells(programs, dictionary[1:]) or size == 0
        assert not dictionary_spells(programs, dictionary + [programs[0]])            # a whole program is not eligible
    assert certificate_value(['vw', 'vx'], [['0', '1', '2']])[0] is False              # wrong shape
    print('selftest passed')


def main():
    stored = json.load(open(os.path.join(HERE, 'certificates-real.json')))['corpora']
    out, failures = {'schema': 'capacity-complexity-results-real/v1', 'corpora': {}}, []
    for name, programs in load_corpora().items():
        entry = stored[name]
        alphabet = len(set(''.join(programs)))
        valid, value = certificate_value(programs, entry['potentials'])
        if not valid:
            failures.append(f'{name}: the stored certificate is not valid')
            continue
        lower = math.ceil(value)
        dictionary = entry.get('dictionary')
        upper = alphabet
        if dictionary is not None:
            if not dictionary_spells(programs, dictionary):
                failures.append(f'{name}: the stored dictionary has an ineligible entry or does not spell every program')
                continue
            upper = min(upper, len(dictionary))
        if lower > upper:
            failures.append(f'{name}: certificate {value} exceeds a dictionary of {upper} entries')
        outcome = ('one entry per character is the minimum' if lower == alphabet else
                   'a smaller dictionary is the minimum' if lower == upper else 'narrowed to an interval')
        out['corpora'][name] = {
            'programs': len(programs), 'bytes': sum(len(p.encode()) for p in programs), 'alphabet': alphabet,
            'eligibleOccurrences': sum(1 for _ in occurrences(programs)),
            'storedLowerBound': STORED_LOWER_BOUND[name], 'certificate': str(value), 'certificateRoundedUp': lower,
            'dictionaryEntries': None if dictionary is None else len(dictionary), 'minimumInterval': [lower, upper], 'outcome': outcome,
            'predictionHolds': lower >= STORED_LOWER_BOUND[name] + 1,
        }
        print(f"{name}: alphabet {alphabet}, stored lower bound {STORED_LOWER_BOUND[name]}, certificate {value} -> {lower}, "
              f"dictionary {'none' if dictionary is None else len(dictionary)}, minimum in [{lower}, {upper}]: {outcome}")
    out['provedClaimFailures'] = failures
    with open(os.path.join(HERE, 'results-real.json'), 'w') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    for failure in failures:
        print('FAILED:', failure)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    selftest() if '--selftest' in sys.argv else main()
