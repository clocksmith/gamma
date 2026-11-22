#!/usr/bin/env python3
"""Run the deficit hierarchy on the 35 real corpora frozen in the sibling folders and replay every dictionary
it builds with the capped checker of capacity-boundary-v1. Python 3.10+; no solver. Writes real-corpora.json.

    python3 -B real_corpora.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'capacity-boundary-v1'))
import capped                                  # noqa: E402
import evaluate as boundary                    # noqa: E402
import deficit                                 # noqa: E402

rule = capped.Capped()
sets = {'boundary/' + k: c['programs'] for k, c in boundary.load_instances().items()}
independent = json.load(open(os.path.join(ROOT, 'capacity-diagnostic-v1', 'independent-eval', 'independent-instances.json')))['corpora']
for k in ('C-1', 'C-2'):
    sets['independent/' + k] = independent[k]['programs']
for folder, file_name, prefix in (('capacity-race-v1', 'boundary-instances.json', 'race/'), ('capacity-lagrangian-race-v1', 'public-instances.json', 'public/')):
    data = json.load(open(os.path.join(ROOT, folder, file_name)))
    data = data.get('corpora', data)
    for k, c in (data.items() if isinstance(data, dict) else [(c.get('corpusId') or c.get('id'), c) for c in data]):
        if isinstance(c, dict) and 'programs' in c:
            sets[prefix + k] = c['programs']
only = sys.argv[1:]
out, failures = {}, []
for name, programs in sets.items():
    if only and name not in only:
        continue
    started = time.time()
    r = deficit.analyze(programs, 'W2')
    seconds = time.time() - started
    alphabet = len(set(''.join(programs)))
    d = r['dictionary']
    replays = None if d is None else rule.dictionary_spells(programs, d)
    if replays is False:
        failures.append(name)
        d = None
    upper = min(alphabet, len(d)) if d is not None else alphabet
    out[name] = {'alphabet': alphabet, 'rank': r['rank'], 'lowerBound': r['lowerBound'], 'dictionaryEntries': None if d is None else len(d),
                 'dictionaryReplays': replays, 'minimumInterval': [r['lowerBound'], upper], 'exact': r['lowerBound'] == upper,
                 'levelOne': r['levelOne'], 'note': r['note'], 'lines': r.get('lines')}
    print(f"{name:18} alphabet {alphabet:3} rank {r['rank']:3} bound {r['lowerBound']:3} dictionary {str(None if d is None else len(d)):>4} replay {str(replays):>5} "
          f"{'EXACT ' + str(upper) if r['lowerBound'] == upper else 'open ' + str(r['lowerBound']) + '..' + str(upper):12} level one: {r['levelOne']}; {r['note']} {seconds:6.1f} s", flush=True)
if not only:
    with open(os.path.join(HERE, 'real-corpora.json'), 'w') as f:
        json.dump({'schema': 'capacity-deficit-real/v1', 'corpora': out, 'failures': failures}, f, indent=1)
        f.write('\n')
print(len(out), 'corpora;', sum(1 for v in out.values() if v['exact']), 'exact;', len(failures), 'failures')
sys.exit(1 if failures else 0)
