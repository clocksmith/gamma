#!/usr/bin/env python3
"""Check the benchmark of PREREGISTRATION.md from its stored measurements. Python 3.8+; no solver.

    python3 -B evaluate.py --selftest     tests on corpora outside the frozen file
    python3 -B evaluate.py                re-checks measurements.json; writes results.json

Everything that decides an answer is recomputed here: the alphabet, the forced single characters, the
block rank in two prime fields, every stored certificate in exact fractions, and every stored dictionary
by replaying it. Times and memory are measurements and are copied, not checked.
"""
import hashlib
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTANCES_SHA256 = '035f7b0a3416c8b4a177723a3e24952469010602a041ec893eefb4d703b2579f'
BUDGET = 64
FIELDS = ((1_000_000_007, 2), (998_244_353, 3))


def load_sibling():
    """occurrences, certificate_value and dictionary_spells, as frozen in capacity-complexity-v1."""
    path = os.path.join(HERE, '..', 'capacity-complexity-v1', 'evaluate_real.py')
    spec = importlib.util.spec_from_file_location('complexity_evaluate_real', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def window_owners(programs):
    owners = {}
    for n, p in enumerate(programs):
        for i in range(len(p) - 1):
            owners.setdefault(p[i:i + 2], set()).add(n)
    return owners


def forced_singletons(programs):
    """Characters with an occurrence that no multi-character entry can span: neither two-character window
    around it occurs in two programs. Each must be a dictionary entry."""
    owners, forced = window_owners(programs), set()
    for p in programs:
        for i, c in enumerate(p):
            left = i > 0 and len(owners[p[i - 1:i + 1]]) >= 2
            right = i + 1 < len(p) and len(owners[p[i:i + 2]]) >= 2
            if not left and not right:
                forced.add(c)
    return forced


def forced_blocks(programs):
    """Cut every program where the two-character window occurs in fewer than two programs."""
    owners, blocks = window_owners(programs), []
    for p in programs:
        start = 0
        for i in range(len(p) - 1):
            if len(owners[p[i:i + 2]]) < 2:
                blocks.append(p[start:i + 1])
                start = i + 1
        blocks.append(p[start:])
    return blocks


def rank(words, prime, base):
    letters = {c: n for n, c in enumerate(sorted(set(''.join(words))))}
    rows = []
    for w in set(words):
        v, weight = [0] * len(letters), 1
        for c in w:
            v[letters[c]] = (v[letters[c]] + weight) % prime
            weight = weight * base % prime
        rows.append(v)
    r = 0
    for col in range(len(letters)):
        pivot = next((i for i in range(r, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        inverse = pow(rows[r][col], prime - 2, prime)
        rows[r] = [x * inverse % prime for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][col]:
                f = rows[i][col]
                rows[i] = [(x - f * y) % prime for x, y in zip(rows[i], rows[r])]
        r += 1
    return r


def block_rank(programs):
    """The rank of the forced blocks. Any one field gives a valid lower bound; the larger of two is used."""
    blocks = forced_blocks(programs)
    return max(rank(blocks, prime, base) for prime, base in FIELDS)


def load_instances():
    raw = open(os.path.join(HERE, 'instances.json'), 'rb').read()
    if hashlib.sha256(raw).hexdigest() != INSTANCES_SHA256:
        raise SystemExit('FAILED: instances.json is not the frozen file')
    return json.loads(raw)['corpora']


def selftest():
    sibling = load_sibling()
    programs = ['abd', 'abe', 'fbd']                       # known: forced e and f, block rank 5, minimum 5
    assert forced_singletons(programs) == {'e', 'f'} and block_rank(programs) == 5
    programs = ['axby', 'byax', 'aybx', 'bxay']            # known: block rank 3, minimum 4
    assert forced_singletons(programs) == set() and block_rank(programs) == 3
    made_up = ['#include <a.h>\nint f(void);\n', '#include <b.h>\nint g(void);\n', '#include <a.h>\nlong h(int);\n']
    assert block_rank(made_up) <= 15 and forced_singletons(made_up) <= set(''.join(made_up))
    assert sum(len(b) for b in forced_blocks(made_up)) == sum(len(p) for p in made_up)
    assert sibling.dictionary_spells(made_up, sorted(set(''.join(made_up))))
    print('selftest passed')


def main():
    sibling = load_sibling()
    corpora = load_instances()
    measured = json.load(open(os.path.join(HERE, 'measurements.json')))['corpora']
    rows, failures = {}, []
    for key, corpus in corpora.items():
        programs, m = corpus['programs'], measured[key]
        alphabet = len(set(''.join(programs)))
        forced, blocks = len(forced_singletons(programs)), block_rank(programs)
        certificate = None
        if m['flow'].get('potentials') is not None:
            valid, value = sibling.certificate_value(programs, m['flow']['potentials'])
            if not valid:
                failures.append(f'{key}: stored certificate is not valid')
            else:
                certificate = value
        dictionary = m['flow'].get('dictionary')
        if dictionary is not None and not sibling.dictionary_spells(programs, dictionary):
            failures.append(f'{key}: stored dictionary has an ineligible entry or does not spell every program')
            dictionary = None
        lower = max(forced, blocks, math.ceil(certificate) if certificate is not None else 0)
        upper = min(alphabet, len(dictionary) if dictionary is not None else alphabet)
        if lower > upper:
            failures.append(f'{key}: lower bound {lower} above a dictionary of {upper} entries')
        cheap = 'IMPOSSIBLE' if max(forced, blocks) > BUDGET else 'FEASIBLE' if alphabet <= BUDGET else 'UNRESOLVED'
        flow = ('IMPOSSIBLE' if certificate is not None and math.ceil(certificate) > BUDGET else
                'FEASIBLE' if dictionary is not None and len(dictionary) <= BUDGET else 'UNRESOLVED')
        rows[key] = {
            'repo': corpus['repo'], 'directory': corpus['directory'], 'bytes': corpus['bytes'], 'alphabet': alphabet,
            'eligibleOccurrences': m['eligibleOccurrences'],
            'forcedSingletons': forced, 'blockRank': blocks,
            'certificate': None if certificate is None else str(certificate),
            'dictionaryEntries': None if dictionary is None else len(dictionary),
            'minimumInterval': [lower, upper], 'minimumEstablished': lower == upper,
            'fitsBudget': 'yes' if upper <= BUDGET else 'no' if lower > BUDGET else 'unknown',
            'characterCountFits': alphabet <= BUDGET,
            'gridDecisionChanges': alphabet > BUDGET and upper <= BUDGET,
            'cheapChecksAtBudget': cheap, 'shippedDiagnosticAtBudget': m['diagnostic'].get('status'),
            'shippedDiagnosticLowerBound': m['diagnostic'].get('certifiedLowerBound'), 'flowMethodAtBudget': flow,
            'seconds': {'cheapChecks': m['cheap']['seconds'], 'shippedDiagnostic': m['diagnostic'].get('wallSeconds'),
                        'flowLinearProgram': m['flow'].get('linearProgramSeconds'), 'flowSearch': m['flow'].get('searchSeconds')},
            'flowPeakMemoryMiB': m['flow'].get('peakMemoryMiB'), 'shippedDiagnosticPeakMiB': m['diagnostic'].get('peakMiB'),
            'flowNotes': m['flow'].get('notes'),
        }
    settled = [r for r in rows.values() if r['minimumEstablished']]
    fits = [k for k, r in rows.items() if r['fitsBudget'] == 'yes']
    not_fit = [k for k, r in rows.items() if r['fitsBudget'] == 'no']
    under_limit = [k for k, r in rows.items() if not (r['flowNotes'] or {}).get('overSizeLimit')]
    finished = [r for r in rows.values() if r['seconds']['flowSearch'] is not None]
    predictions = {
        'B1 block rank equals every established minimum':
            all(r['blockRank'] == r['minimumInterval'][0] for r in settled),
        'B2 flow method establishes the minimum on at least 7 of the 8 corpora under the size limit':
            sum(1 for k in under_limit if rows[k]['minimumEstablished']) >= 7,
        'B3 between 2 and 4 corpora fit 64 entries, JS-2 among them':
            2 <= len(fits) <= 4 and 'JS-2' in fits,
        'B4a every corpus shown not to fit is certified by block rank alone':
            all(rows[k]['cheapChecksAtBudget'] == 'IMPOSSIBLE' for k in not_fit),
        'B4b no corpus shown to fit is certified by the cheap checks or the shipped diagnostic':
            all(rows[k]['cheapChecksAtBudget'] != 'FEASIBLE' and rows[k]['shippedDiagnosticAtBudget'] != 'FEASIBLE' for k in fits),
        'B5a cheap checks take under 1 second on every corpus':
            all(r['seconds']['cheapChecks'] < 1 for r in rows.values()),
        'B5b flow method takes at least 50 times as long as the cheap checks on every corpus it finishes':
            all(((r['seconds']['flowLinearProgram'] or 0) + r['seconds']['flowSearch']) >= 50 * r['seconds']['cheapChecks'] for r in finished),
        'B6 alphabet minus minimum is between 1 and 8 on every settled corpus':
            all(1 <= r['alphabet'] - r['minimumInterval'][0] <= 8 for r in settled),
    }
    out = {'schema': 'capacity-boundary-results/v1', 'budget': BUDGET, 'corpora': rows,
           'counts': {'corpora': len(rows), 'minimumEstablished': len(settled), 'fit': fits, 'doNotFit': not_fit,
                      'unknown': [k for k, r in rows.items() if r['fitsBudget'] == 'unknown'],
                      'gridDecisionChanges': [k for k, r in rows.items() if r['gridDecisionChanges']]},
           'predictions': predictions, 'provedClaimFailures': failures}
    with open(os.path.join(HERE, 'results.json'), 'w') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    print(f"{'corpus':6} {'alph':>4} {'forced':>6} {'rank':>4} {'cert':>6} {'dict':>4} {'minimum':>9} {'fits 64':>7} {'cheap':>10} {'shipped':>10} {'flow':>10}")
    for key, r in rows.items():
        low, high = r['minimumInterval']
        print(f"{key:6} {r['alphabet']:4} {r['forcedSingletons']:6} {r['blockRank']:4} {str(r['certificate']):>6} {str(r['dictionaryEntries']):>4} "
              f"{(str(low) if low == high else f'{low}-{high}'):>9} {r['fitsBudget']:>7} {r['cheapChecksAtBudget']:>10} "
              f"{str(r['shippedDiagnosticAtBudget']):>10} {r['flowMethodAtBudget']:>10}")
    for name, holds in predictions.items():
        print(('held   ' if holds else 'WRONG  ') + name)
    for failure in failures:
        print('FAILED:', failure)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    selftest() if '--selftest' in sys.argv else main()
