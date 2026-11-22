#!/usr/bin/env python3
"""Three-arm race of PREREGISTRATION-THREE-ARM.md on the frozen public corpora. Python 3.10+.

    python3 -B three_arm.py --run      runs every arm, one child process per call; writes three-arm-measurements.json
    python3 -B three_arm.py            re-derives every answer from the measurements; writes three-arm-results.json
    python3 -B three_arm.py --one ID ARM [BUDGET]     one call, printed as JSON (used by --run)

Arms, witness rule with threshold 2 and the 160-byte cap:
  rank      forced single characters and block rank only (capacity-boundary-v1/evaluate.py)
  kernel    rank plus nullspace_kernel_certificate, nothing else: no other tier, no fallback, no heuristic
  baseline  canzar_lagrangian.py as frozen in this folder, 60 seconds per query
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
INSTANCES_SHA256 = '914e62b0de12b5193fc2e4b12e4e4e8c04a051ab7163dd8123567f5e2b70986b'
BASELINE_SECONDS, HARD_LIMIT_SECONDS, BUDGET = 60.0, 300, 64


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def corpora():
    raw = open(os.path.join(HERE, 'public-instances.json'), 'rb').read()
    if hashlib.sha256(raw).hexdigest() != INSTANCES_SHA256:
        raise SystemExit('FAILED: public-instances.json is not the frozen file')
    data = json.loads(raw)['corpora']
    items = data.items() if isinstance(data, dict) else [(c['id'], c) for c in data]
    return {key: c['programs'] for key, c in items}


def boundary_tools():
    sys.path.insert(0, os.path.join(ROOT, 'capacity-boundary-v1'))
    import capped
    import evaluate
    return evaluate, capped.Capped()


def one(key, arm, budget=None):
    programs = corpora()[key]
    started = time.perf_counter()
    if arm == 'rank':
        evaluate, _ = boundary_tools()
        out = {'forcedSingletons': len(evaluate.forced_singletons(programs)), 'blockRank': evaluate.block_rank(programs)}
    elif arm == 'kernel':
        diagnostic = load('diag', os.path.join(ROOT, 'capacity-diagnostic-v1', 'diagnostic.py'))
        c = diagnostic.nullspace_kernel_certificate(programs, 2)
        out = {'status': c['status'], 'rank': c['rank'], 'nullity': c['nullity'], 'kFree': c.get('kFree'), 'deltaDetStar': c.get('deltaDetStar'),
               'lowerBound': c['certifiedLowerBound'], 'dictionary': (c.get('attainingConstruction') or {}).get('dictionary')}
    else:
        baseline = load('canzar_lagrangian', os.path.join(HERE, 'canzar_lagrangian.py'))
        r = baseline.canzar_lagrangian_decide(programs, 2, budget, timeout_s=BASELINE_SECONDS)
        out = {'status': r['status'], 'lowerBound': r.get('certifiedLowerBound'), 'dictionarySize': r.get('dictionarySize'),
               'dictionaryMulti': r.get('dictionaryMulti'), 'phase': r.get('phase'), 'iterations': r.get('iterations')}
    out['seconds'] = round(time.perf_counter() - started, 3)
    return out


def call(key, arm, budget=None):
    args = [sys.executable, '-B', os.path.abspath(__file__), '--one', key, arm] + ([str(budget)] if budget is not None else [])
    started = time.time()
    try:
        run = subprocess.run(args, capture_output=True, text=True, timeout=HARD_LIMIT_SECONDS)
    except subprocess.TimeoutExpired:
        return {'status': 'TIMEOUT', 'seconds': round(time.time() - started, 1), 'note': f'killed after {HARD_LIMIT_SECONDS} s'}
    if run.returncode != 0:
        return {'status': 'ERROR', 'seconds': round(time.time() - started, 1), 'note': run.stderr[-400:]}
    return json.loads(run.stdout)


def run():
    out = {}
    for key, programs in corpora().items():
        rank = call(key, 'rank')
        kernel = call(key, 'kernel')
        budgets = sorted({rank['blockRank'], rank['blockRank'] + 1, BUDGET})
        out[key] = {'rank': rank, 'kernel': kernel, 'baseline': {str(k): call(key, 'baseline', k) for k in budgets}}
        print(key, 'rank', rank['blockRank'], 'kernel', kernel.get('status'), 'baseline', {k: v.get('status') for k, v in out[key]['baseline'].items()}, flush=True)
    with open(os.path.join(HERE, 'three-arm-measurements.json'), 'w') as f:
        json.dump({'schema': 'bits-three-arm-measurements/v1', 'baselineSeconds': BASELINE_SECONDS, 'hardLimitSeconds': HARD_LIMIT_SECONDS, 'corpora': out}, f, separators=(',', ':'))
        f.write('\n')


def fewest_singles(programs, multi, rule):
    """A dictionary made of the given multi-character entries plus single characters: start from the whole
    alphabet and drop every single character the corpus can be spelled without, rarest first."""
    eligible = {programs[n][i:j] for n, i, j in rule.occurrences(programs)}
    text = ''.join(programs)
    dictionary = sorted({t for t in multi if t in eligible}) + sorted(set(text))
    for c in sorted(set(text), key=lambda ch: (text.count(ch), ch)):
        rest = [d for d in dictionary if d != c]
        if rule.dictionary_spells(programs, rest):
            dictionary = rest
    return dictionary


def main():
    evaluate, rule = boundary_tools()
    measured = json.load(open(os.path.join(HERE, 'three-arm-measurements.json')))['corpora']
    rows, failures = [], []
    for key, programs in corpora().items():
        m = measured[key]
        alphabet = len(set(''.join(programs)))
        forced, blocks = len(evaluate.forced_singletons(programs)), evaluate.block_rank(programs)
        if blocks != m['rank']['blockRank']:
            failures.append(f'{key}: block rank recomputed {blocks}, measured {m["rank"]["blockRank"]}')
        kernel = m['kernel']
        kernel_dictionary = kernel.get('dictionary')
        if kernel_dictionary is not None and not rule.dictionary_spells(programs, kernel_dictionary):
            failures.append(f'{key}: the kernel dictionary does not replay')
            kernel_dictionary = None
        kernel_bound = kernel.get('lowerBound') if kernel.get('status') in ('SATURATED', 'RANK_ATTAINED', 'RANK_UNATTAINABLE', 'UNRESOLVED') else None
        for budget in sorted({blocks, blocks + 1, BUDGET}):
            base = m['baseline'][str(budget)]
            rank_answer = 'FEASIBLE' if alphabet <= budget else 'IMPOSSIBLE' if max(forced, blocks) > budget else 'UNRESOLVED'
            kernel_answer = ('FEASIBLE' if alphabet <= budget or (kernel_dictionary is not None and len(kernel_dictionary) <= budget) else
                             'IMPOSSIBLE' if max(forced, blocks, kernel_bound or 0) > budget else
                             'TIMEOUT' if kernel.get('status') in ('TIMEOUT', 'ERROR') else 'UNRESOLVED')
            base_answer = base['status'] if base['status'] in ('FEASIBLE', 'IMPOSSIBLE') else 'TIMEOUT' if base['status'] in ('TIMEOUT', 'ERROR') else 'UNRESOLVED'
            base_replayed = None
            if base_answer == 'FEASIBLE':
                rebuilt = sorted(set(''.join(programs))) if base.get('phase') == 'singleton' else fewest_singles(programs, base.get('dictionaryMulti') or [], rule)
                base_replayed = rule.dictionary_spells(programs, rebuilt) and len(rebuilt) <= budget
            answers = {rank_answer, kernel_answer, base_answer}
            if 'FEASIBLE' in answers and 'IMPOSSIBLE' in answers:
                failures.append(f'{key} at {budget}: arms contradict each other: rank {rank_answer}, kernel {kernel_answer}, baseline {base_answer}')
            settled_by = ('alphabet' if alphabet <= budget else 'block rank' if rank_answer == 'IMPOSSIBLE' else
                          'kernel dictionary' if kernel_answer == 'FEASIBLE' else 'kernel +1' if kernel_answer == 'IMPOSSIBLE' else
                          'baseline only' if base_answer in ('FEASIBLE', 'IMPOSSIBLE') else 'nobody')
            rows.append({'corpus': key, 'alphabet': alphabet, 'blockRank': blocks, 'budget': budget,
                         'kinds': [name for name, value in (('rank', blocks), ('rank+1', blocks + 1), ('64', BUDGET)) if value == budget],
                         'rank': rank_answer, 'kernel': kernel_answer, 'baseline': base_answer, 'baselinePhase': base.get('phase'),
                         'baselineFeasibleReplayed': base_replayed, 'settledFirstBy': settled_by,
                         'seconds': {'rank': m['rank']['seconds'], 'kernel': kernel.get('seconds'), 'baseline': base.get('seconds')},
                         'kernelStatus': kernel.get('status')})
    count = lambda arm: sum(1 for r in rows if r[arm] in ('FEASIBLE', 'IMPOSSIBLE'))
    out = {'schema': 'bits-three-arm-results/v1', 'queries': len(rows),
           'settled': {arm: count(arm) for arm in ('rank', 'kernel', 'baseline')},
           'settledByBudgetKind': {kind: {arm: sum(1 for r in rows if kind in r['kinds'] and r[arm] in ('FEASIBLE', 'IMPOSSIBLE')) for arm in ('rank', 'kernel', 'baseline')}
                                   | {'queries': sum(1 for r in rows if kind in r['kinds'])} for kind in ('rank', 'rank+1', '64')},
           'rows': rows, 'failures': failures}
    with open(os.path.join(HERE, 'three-arm-results.json'), 'w') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    print(f"{'corpus':6} {'alph':>4} {'rank':>4} {'K':>3} {'kind':12} {'rank arm':>10} {'kernel arm':>10} {'baseline':>10} {'settled first by':18} {'s rank':>7} {'s kern':>7} {'s base':>7}")
    for r in rows:
        s = r['seconds']
        print(f"{r['corpus']:6} {r['alphabet']:4} {r['blockRank']:4} {r['budget']:3} {','.join(r['kinds']):12} {r['rank']:>10} {r['kernel']:>10} {r['baseline']:>10} "
              f"{r['settledFirstBy']:18} {s['rank']:7.2f} {str(s['kernel']):>7} {str(s['baseline']):>7}")
    print('distinct queries', len(rows), 'settled', out['settled'])
    print(json.dumps(out['settledByBudgetKind']))
    for failure in failures:
        print('FAILED:', failure)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    if '--one' in sys.argv:
        i = sys.argv.index('--one')
        print(json.dumps(one(sys.argv[i + 1], sys.argv[i + 2], int(sys.argv[i + 3]) if len(sys.argv) > i + 3 else None)))
    elif '--run' in sys.argv:
        run()
    else:
        main()
