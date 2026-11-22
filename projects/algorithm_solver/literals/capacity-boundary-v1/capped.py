#!/usr/bin/env python3
"""Addendum: the same benchmark with entries capped at 160 UTF-8 bytes, the rule of sixbit-v1 and of the shipped
diagnostic. See ADDENDUM-CAPPED.md for why this exists.

    python3 -B capped.py --selftest     tests on corpora outside the frozen file
    python3 -B capped.py --run          reruns the flow method under the cap; needs scipy; writes measurements-capped.json
    python3 -B capped.py                re-checks measurements-capped.json without a solver; writes results-capped.json
"""
import json
import math
import os
import sys
from fractions import Fraction

import evaluate

HERE = os.path.dirname(os.path.abspath(__file__))
CAP, BUDGET = 160, 64


class Capped:
    """occurrences, certificate_value and dictionary_spells with multi-character entries of at most `cap` bytes."""

    def __init__(self, cap=CAP):
        self.cap = cap

    def occurrences(self, programs):
        assert len(set(programs)) == len(programs)
        whole = set(programs)
        for n, p in enumerate(programs):
            others = [q for m, q in enumerate(programs) if m != n]
            for i in range(len(p)):
                if p[i] not in whole:
                    yield n, i, i + 1
                for j in range(i + 2, len(p) + 1):
                    s = p[i:j]
                    if len(s.encode()) > self.cap or not any(s in q for q in others):
                        break
                    if s not in whole:
                        yield n, i, j

    def certificate_value(self, programs, potentials):
        if len(potentials) != len(programs) or any(len(row) != len(p) + 1 for row, p in zip(potentials, programs)):
            return False, None
        phi = [[Fraction(x) for x in row] for row in potentials]
        charge = {}
        for n, i, j in self.occurrences(programs):
            rise = phi[n][j] - phi[n][i]
            if rise > 0:
                s = programs[n][i:j]
                charge[s] = charge.get(s, 0) + rise
        return all(c <= 1 for c in charge.values()), sum((row[-1] - row[0] for row in phi), Fraction(0))

    def dictionary_spells(self, programs, dictionary):
        eligible = {programs[n][i:j] for n, i, j in self.occurrences(programs)}
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


def selftest():
    import random
    rng = random.Random(23)
    for _ in range(60):
        programs = sorted({''.join(rng.choice('vwxyz') for _ in range(rng.randint(3, 9))) for _ in range(rng.randint(2, 4))})
        for cap in (2, 3, 160):
            rule = Capped(cap)
            whole = set(programs)
            by_definition = set()
            for n, p in enumerate(programs):
                for i in range(len(p)):
                    for j in range(i + 1, len(p) + 1):
                        s = p[i:j]
                        if s not in whole and (len(s) == 1 or (len(s.encode()) <= cap and sum(s in q for q in programs) >= 2)):
                            by_definition.add((n, i, j))
            assert set(rule.occurrences(programs)) == by_definition, (programs, cap)
            alphabet = sorted(set(''.join(programs)) - whole)
            assert rule.dictionary_spells(programs, alphabet) or any(len(p) == 1 for p in programs)
    rule = Capped(2)
    assert not rule.dictionary_spells(['vwxy', 'vwxz'], ['vwx', 'y', 'z'])        # vwx is over a 2-byte cap
    assert Capped(3).dictionary_spells(['vwxy', 'vwxz'], ['vwx', 'y', 'z'])
    print('selftest passed')


def run():
    import resource
    import time
    import run_benchmark
    rule, out = Capped(), {}
    corpora = evaluate.load_instances()
    for key in sorted(corpora, key=lambda k: corpora[k]['bytes']):
        started = time.time()
        programs = corpora[key]['programs']
        flow, count = run_benchmark.flow_method(programs, rule)
        out[key] = {'flow': flow, 'eligibleOccurrences': count, 'diagnostic': run_benchmark.shipped_diagnostic(programs)}
        print(key, 'done in', round(time.time() - started), 's', flush=True)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with open(os.path.join(HERE, 'measurements-capped.json'), 'w') as f:
        json.dump({'schema': 'capacity-boundary-measurements-capped/v1', 'capBytes': CAP,
                   'peakMemoryMiBWholeRun': round(peak / (1 << 20 if sys.platform == 'darwin' else 1 << 10), 1), 'corpora': out}, f, separators=(',', ':'))
        f.write('\n')


def main():
    rule = Capped()
    corpora = evaluate.load_instances()
    measured = json.load(open(os.path.join(HERE, 'measurements-capped.json')))['corpora']
    rows, failures = {}, []
    for key, corpus in corpora.items():
        programs, m = corpus['programs'], measured[key]
        alphabet = len(set(''.join(programs)))
        forced, blocks = len(evaluate.forced_singletons(programs)), evaluate.block_rank(programs)
        certificate = None
        if m['flow'].get('potentials') is not None:
            valid, value = rule.certificate_value(programs, m['flow']['potentials'])
            if valid:
                certificate = value
            else:
                failures.append(f'{key}: stored certificate is not valid under the cap')
        dictionary = m['flow'].get('dictionary')
        if dictionary is not None and not rule.dictionary_spells(programs, dictionary):
            failures.append(f'{key}: stored dictionary is not legal under the cap or does not spell every file')
            dictionary = None
        lower = max(forced, blocks, math.ceil(certificate) if certificate is not None else 0)
        upper = min(alphabet, len(dictionary) if dictionary is not None else alphabet)
        if lower > upper:
            failures.append(f'{key}: lower bound {lower} above a dictionary of {upper} entries')
        shipped = m['diagnostic']
        if shipped.get('certifiedLowerBound') is not None and shipped['certifiedLowerBound'] > upper:
            failures.append(f"{key}: the shipped diagnostic certifies {shipped['certifiedLowerBound']}, above a replayed dictionary of {upper}")
        rows[key] = {
            'alphabet': alphabet, 'eligibleOccurrences': m['eligibleOccurrences'], 'forcedSingletons': forced, 'blockRank': blocks,
            'certificate': None if certificate is None else str(certificate), 'dictionaryEntries': None if dictionary is None else len(dictionary),
            'longestEntryBytes': None if dictionary is None else max(len(d.encode()) for d in dictionary),
            'minimumInterval': [lower, upper], 'minimumEstablished': lower == upper,
            'fitsBudget': 'yes' if upper <= BUDGET else 'no' if lower > BUDGET else 'unknown',
            'blockRankAtBudget': 'IMPOSSIBLE' if max(forced, blocks) > BUDGET else 'UNRESOLVED',
            'shippedDiagnosticAtBudget': shipped.get('status'), 'shippedDiagnosticLowerBound': shipped.get('certifiedLowerBound'),
            'flowCertificateAtBudget': 'IMPOSSIBLE' if certificate is not None and math.ceil(certificate) > BUDGET else 'UNRESOLVED',
            'seconds': {'shippedDiagnostic': shipped.get('wallSeconds'), 'flowLinearProgram': m['flow'].get('linearProgramSeconds'),
                        'flowSearch': m['flow'].get('searchSeconds')},
            'flowNotes': m['flow'].get('notes'),
        }
    with open(os.path.join(HERE, 'results-capped.json'), 'w') as f:
        json.dump({'schema': 'capacity-boundary-results-capped/v1', 'capBytes': CAP, 'budget': BUDGET, 'corpora': rows,
                   'provedClaimFailures': failures}, f, indent=1)
        f.write('\n')
    print(f"{'corpus':6} {'alph':>4} {'rank':>4} {'cert':>6} {'dict':>4} {'minimum':>9} {'fits 64':>7} {'block rank':>10} {'shipped':>14} {'flow cert':>10}")
    for key, r in rows.items():
        low, high = r['minimumInterval']
        shipped = f"{r['shippedDiagnosticAtBudget']} {r['shippedDiagnosticLowerBound']}"
        print(f"{key:6} {r['alphabet']:4} {r['blockRank']:4} {str(r['certificate']):>6} {str(r['dictionaryEntries']):>4} "
              f"{(str(low) if low == high else f'{low}-{high}'):>9} {r['fitsBudget']:>7} {r['blockRankAtBudget']:>10} {shipped:>14} {r['flowCertificateAtBudget']:>10}")
    for failure in failures:
        print('FAILED:', failure)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    selftest() if '--selftest' in sys.argv else run() if '--run' in sys.argv else main()
