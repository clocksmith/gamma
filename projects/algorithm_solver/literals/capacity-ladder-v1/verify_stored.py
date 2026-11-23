#!/usr/bin/env python3
"""Re-check what real-corpora.json stores, without running the ladder. Python 3.10+; no numpy, no solver.

For each of the 59 corpora it recomputes the block rank with capacity-boundary-v1, replays the stored dictionary
with the capped checker, verifies the stored defect-tree certificate with check_certificate.py, and compares the
interval these give with the stored one. It then damages one certificate four ways and requires each damaged
copy to be rejected.

One certificate (4,141 nodes, 8.9 MB) is stored compressed as certificates/<name>.json.gz. Without --deep only its
SHA-256 is compared with the one recorded when it was made, which shows it is the same file and verifies nothing;
that corpus is then scored at its rank. With --deep it is verified in full.

    python3 -B verify_stored.py            about a minute; exits 1 on any failure
    python3 -B verify_stored.py --deep     also verifies the compressed certificate, about a quarter of an hour
"""
import copy
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'capacity-boundary-v1'))
import capped                                   # noqa: E402
import check_certificate                        # noqa: E402
import evaluate as boundary                     # noqa: E402
import real_corpora                             # noqa: E402

stored = json.load(open(os.path.join(HERE, 'real-corpora.json')))['corpora']
rule, failures, exact, not_reverified = capped.Capped(), [], 0, []
sets = real_corpora.corpora()
if set(sets) != set(stored):
    failures.append('the corpora on disk are not the ones in real-corpora.json')
for name, programs in sets.items():
    row = stored[name]
    alphabet, rank = len(set(''.join(programs))), boundary.block_rank(programs)
    if (alphabet, rank) != (row['alphabet'], row['rank']):
        failures.append(f'{name}: alphabet and rank recomputed {alphabet}, {rank}; stored {row["alphabet"]}, {row["rank"]}')
    upper = alphabet
    if row['dictionary'] is not None:
        if rule.dictionary_spells(programs, row['dictionary']):
            upper = min(upper, len(row['dictionary']))
        else:
            failures.append(f'{name}: the stored dictionary does not replay')
    lower = rank
    path = os.path.join(HERE, 'certificates', name.replace('/', '-') + '.json')
    if row['certificateStored']:
        try:
            lower = max(lower, check_certificate.check(programs, json.load(open(path))))
        except ValueError as problem:
            failures.append(f'{name}: certificate rejected: {problem}')
    elif row['lowerBound'] > rank:
        verified = False
        if os.path.exists(path + '.gz'):
            text = gzip.decompress(open(path + '.gz', 'rb').read())
            if hashlib.sha256(text).hexdigest() != row['certificateSha256']:
                failures.append(f'{name}: the compressed certificate is not the recorded one')
            elif '--deep' in sys.argv:
                try:
                    lower = max(lower, check_certificate.check(programs, json.loads(text)))
                    verified = True
                except ValueError as problem:
                    failures.append(f'{name}: certificate rejected: {problem}')
        if not verified:
            not_reverified.append(f"{name}: bound {row['lowerBound']} (certificate of {row['certificateNodes']} nodes; use --deep); rank {rank} used")
    expected = [row['lowerBound'] if row['certificateStored'] or row['lowerBound'] == rank or lower == row['lowerBound'] else rank, row['minimumInterval'][1]]
    if [lower, upper] != expected:
        failures.append(f'{name}: interval re-derived {lower}..{upper}, stored {expected[0]}..{expected[1]}')
    exact += lower == upper
    print(f"{name:18} alphabet {alphabet:3} rank {rank:3} re-derived {lower}..{upper}", flush=True)

# Tampering: each damaged copy of the A08 certificate must be rejected.
programs = sets['families/A08']
good = json.load(open(os.path.join(HERE, 'certificates', 'families-A08.json')))


def damaged(kind):
    bad = copy.deepcopy(good)
    if kind == 'kernel entry':
        bad['kernel'][0][0] = (bad['kernel'][0][0] + 1) % bad['prime']
    elif kind == 'kernel row':
        bad['kernel'] = bad['kernel'][:-1]
    elif kind == 'child':
        n = next(i for i, node in enumerate(bad['nodes']) if len(node['children']) > 1)
        bad['nodes'][n]['children'] = bad['nodes'][n]['children'][:-1]
    else:
        bad['refutes'] += 1
        bad['nodes'][0]['spare'] += 1
    return bad


for kind in ('kernel entry', 'kernel row', 'child', 'one more level'):
    try:
        check_certificate.check(programs, damaged(kind))
        failures.append(f'tampering not detected: {kind}')
    except ValueError:
        pass
print(len(stored), 'corpora;', exact, 'exact from stored evidence alone; 4 damaged certificates rejected')
for line in not_reverified:
    print('not re-verified here:', line)
for failure in failures:
    print('FAILED:', failure)
sys.exit(1 if failures else 0)
