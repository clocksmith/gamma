#!/usr/bin/env python3
"""Run the deficit ladder on every real corpus frozen in the sibling folders: the 35 seen before it was written
and the 24 families of capacity-deficit-race-v1. Every dictionary is replayed with the capped checker of
capacity-boundary-v1 and every certificate is verified by check_certificate.py. Python 3.10+, numpy; no solver.

    python3 -B real_corpora.py [SECONDS] [MAX_LEVEL]      writes real-corpora.json and certificates/<name>.json
"""
import concurrent.futures
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
CHECK_NODES, WRITE_BYTES = 20_000, 300_000   # larger certificates are not checked here; checked ones above the size are not stored, only hashed
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'capacity-boundary-v1'))


def corpora():
    import evaluate as boundary
    sets = {'boundary/' + k: c['programs'] for k, c in boundary.load_instances().items()}
    independent = json.load(open(os.path.join(ROOT, 'capacity-diagnostic-v1', 'independent-eval', 'independent-instances.json')))['corpora']
    for k in ('C-1', 'C-2'):
        sets['independent/' + k] = independent[k]['programs']
    for folder, file_name, prefix in (('capacity-race-v1', 'boundary-instances.json', 'race/'), ('capacity-lagrangian-race-v1', 'public-instances.json', 'public/'),
                                      ('capacity-deficit-race-v1', 'instances-a.json', 'families/')):
        data = json.load(open(os.path.join(ROOT, folder, file_name)))
        data = data.get('corpora', data)
        for k, c in (data.items() if isinstance(data, dict) else [(c.get('corpusId') or c.get('id'), c) for c in data]):
            if isinstance(c, dict) and 'programs' in c:
                sets[prefix + k] = c['programs']
    return sets


def one(args):
    name, programs, seconds, max_level = args
    import capped
    import check_certificate
    import ladder
    started = time.time()
    r = ladder.analyze(programs, 'W2', max_level=max_level, seconds=seconds)
    spent = round(time.time() - started, 1)
    alphabet = len(set(''.join(programs)))
    d, c = r['dictionary'], r.get('certificate')
    replays = None if d is None else capped.Capped().dictionary_spells(programs, d)
    certified, stored, digest = None, None, None
    if c is not None and len(c['nodes']) > CHECK_NODES:
        certified = f'not checked: {len(c["nodes"])} nodes'
    elif c is not None:
        try:
            certified = check_certificate.check(programs, c)
        except ValueError as problem:
            certified = 'INVALID: ' + str(problem)
        text = json.dumps(c, separators=(',', ':')) + '\n'
        stored = len(text) <= WRITE_BYTES
        digest = hashlib.sha256(text.encode()).hexdigest()
        if stored:
            os.makedirs(os.path.join(HERE, 'certificates'), exist_ok=True)
            with open(os.path.join(HERE, 'certificates', name.replace('/', '-') + '.json'), 'w') as f:
                f.write(text)
    upper = min(alphabet, len(d)) if d is not None and replays else alphabet
    row = {'alphabet': alphabet, 'rank': r['rank'], 'lowerBound': r['lowerBound'], 'boundBy': r.get('boundBy'), 'certificateCheck': certified,
           'certificateNodes': None if c is None else len(c['nodes']), 'certificateStored': stored, 'certificateSha256': digest, 'dictionaryEntries': None if d is None else len(d), 'dictionaryReplays': replays,
           'dictionary': d if d is not None and replays and len(d) < alphabet else None,
           'minimumInterval': [r['lowerBound'], upper], 'exact': r['lowerBound'] == upper, 'level': r.get('level'), 'note': r['note'], 'spaces': r.get('spaces'),
           'fixedSearches': r.get('fixedSearches')}
    print(f"{name:18} alphabet {alphabet:3} rank {r['rank']:3} bound {r['lowerBound']:3} ({r.get('boundBy')}, check {certified}) dictionary {str(None if d is None else len(d)):>4} "
          f"{'EXACT ' + str(upper) if row['exact'] else 'open ' + str(r['lowerBound']) + '..' + str(upper):12} {r['note']} {spent:6.1f} s", flush=True)
    return name, row


if __name__ == '__main__':
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
    max_level = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    sets = corpora()
    with concurrent.futures.ProcessPoolExecutor(3) as pool:
        out = dict(pool.map(one, [(name, programs, seconds, max_level) for name, programs in sets.items()]))
    failures = [name for name, row in out.items() if row['dictionaryReplays'] is False
                or (isinstance(row['certificateCheck'], str) and row['certificateCheck'].startswith('INVALID'))
                or (isinstance(row['certificateCheck'], int) and row['certificateCheck'] != row['lowerBound'])]
    with open(os.path.join(HERE, 'real-corpora.json'), 'w') as f:
        json.dump({'schema': 'capacity-ladder-real/v1', 'secondsLimit': seconds, 'maxLevel': max_level, 'corpora': {k: out[k] for k in sets}, 'failures': failures}, f, indent=1)
        f.write('\n')
    print(len(out), 'corpora;', sum(1 for v in out.values() if v['exact']), 'exact;', len(failures), 'failures')
    sys.exit(1 if failures else 0)
