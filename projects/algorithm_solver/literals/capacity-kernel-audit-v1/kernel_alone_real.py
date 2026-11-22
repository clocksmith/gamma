#!/usr/bin/env python3
"""Run nullspace_kernel_certificate alone (no other tier, no fallback, no heuristic) on the 23 real corpora
already frozen in the sibling folders, and replay every dictionary it builds with the capped checker of
capacity-boundary-v1. Python 3.10+; no solver. Writes kernel-alone-real.json.

    python3 -B kernel_alone_real.py
"""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


diagnostic = load('diag', os.path.join(ROOT, 'capacity-diagnostic-v1', 'diagnostic.py'))
sys.path.insert(0, os.path.join(ROOT, 'capacity-boundary-v1'))
import capped                                  # noqa: E402
import evaluate as boundary                    # noqa: E402

rule = capped.Capped()
sets = {'boundary/' + k: c['programs'] for k, c in boundary.load_instances().items()}
independent = json.load(open(os.path.join(ROOT, 'capacity-diagnostic-v1', 'independent-eval', 'independent-instances.json')))['corpora']
for k in ('C-1', 'C-2'):
    sets['independent/' + k] = independent[k]['programs']
race = json.load(open(os.path.join(ROOT, 'capacity-race-v1', 'boundary-instances.json')))
race = race.get('corpora', race)
for k, c in (race.items() if isinstance(race, dict) else [(c.get('corpusId') or c.get('id'), c) for c in race]):
    if isinstance(c, dict) and 'programs' in c:
        sets['race/' + k] = c['programs']
# Minimums established elsewhere by a checked certificate and a replayed dictionary.
KNOWN = {'boundary/JS-1': 69, 'boundary/JS-2': 65, 'boundary/JS-3': 70, 'boundary/PY-1': 69, 'boundary/PY-2': 68, 'boundary/C-1': 68,
         'boundary/C-2': 65, 'boundary/C-3': 66, 'independent/C-1': 61, 'independent/C-2': 65}
out, failures = {}, []
for name, programs in sets.items():
    alphabet = len(set(''.join(programs)))
    started = time.time()
    c = diagnostic.nullspace_kernel_certificate(programs, 2)
    seconds = time.time() - started
    dictionary = (c.get('attainingConstruction') or {}).get('dictionary')
    replays = None if dictionary is None else rule.dictionary_spells(programs, dictionary)
    rank = boundary.block_rank(programs)
    exact = alphabet if c['status'] == 'SATURATED' else c['rank'] if c['status'] == 'RANK_ATTAINED' and replays else None
    if rank != c['rank'] or replays is False or (exact is not None and name in KNOWN and exact != KNOWN[name]) or (name in KNOWN and c['certifiedLowerBound'] > KNOWN[name]):
        failures.append(name)
    out[name] = {'alphabet': alphabet, 'blockRank': rank, 'status': c['status'], 'nullity': c['nullity'], 'kFree': c.get('kFree'),
                 'deltaDetStar': c.get('deltaDetStar'), 'kernelLowerBound': c['certifiedLowerBound'],
                 'dictionaryEntries': None if dictionary is None else len(dictionary), 'dictionaryReplays': replays,
                 'exactMinimumFromRankAndKernel': exact, 'knownMinimum': KNOWN.get(name), 'seconds': round(seconds, 2)}
    print(f"{name:18} alphabet {alphabet:3} rank {rank:3} {c['status']:18} bound {c['certifiedLowerBound']:3} "
          f"dictionary {str(out[name]['dictionaryEntries']):>4} replay {str(replays):>5} exact {str(exact):>4} known {str(KNOWN.get(name)):>4} {seconds:6.2f} s")
with open(os.path.join(HERE, 'kernel-alone-real.json'), 'w') as f:
    json.dump({'schema': 'capacity-kernel-audit-real/v1', 'corpora': out, 'failures': failures}, f, indent=1)
    f.write('\n')
print(len(out), 'corpora;', sum(1 for r in out.values() if r['exactMinimumFromRankAndKernel'] is not None), 'exact from rank and kernel alone;', len(failures), 'failures')
sys.exit(1 if failures else 0)
