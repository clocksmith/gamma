"""breadth13-v1: breadth-aware exact repairs on item 13's ready candidate, as a frozen successor attempt (FREEZE.md).

  succ.py --work DIR --output DIR/breadth13/run-v1          launcher: one pinned process per searched arm
  succ.py --work DIR --output DIR/breadth13/run-v1 --arm A --cores X   (started by the launcher)

Sources stay fixed at item 13's selected fit and validation sources (scope_joint256); only the dictionary changes.
Arms (256 entries), all starting from item 13's dictionary and using breadth-lns-v1's exact repair: unweighted (total
fit selections), nonregress (total fit selections, with no fit program allowed to cost more than under the current
incumbent) and relative (sum of w_p * cost_p, w_p = round(10^6 / start_p)). The seed is evaluated directly. Moves are accepted only on a strict improvement of
the arm's own objective under exact canonical rescoring. Validation opens only after the arm's dictionary is sealed.
"""
import argparse, hashlib, json, os, random, resource, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(LIT / 'breadth-lns-v1'), str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
import breadth  # repair(), per_program()

sha = lambda raw: hashlib.sha256(raw).hexdigest()
ARMS = ('unweighted', 'nonregress', 'relative')


def contract():
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    assert sha((LIT / 'cost-decomposition-v1/contract.json').read_bytes()) == c['parent_contract_sha256']
    rt = c['runtime']; exe = os.path.realpath(sys.executable)
    assert exe == rt['python_realpath'] and sha(Path(exe).read_bytes()) == rt['python_sha256'], exe
    import scipy; assert sys.version.split()[0] == rt['python_version'] and scipy.__version__ == rt['scipy']
    return c


def load_seed(work, c, part):
    """part 'fit': the seed dictionary and item 13's fit-sources.json only. part 'all': all 400 sources (after the seal)."""
    folder = work / c['seed']['relative_path']
    names = ['dictionary.json', 'fit-sources.json'] if part == 'fit' else ['dictionary.json', 'fit-sources.json', 'sources.json']
    raw = {f: (folder / f).read_bytes() for f in names}
    for f in names: assert sha(raw[f]) == c['seed']['private_sha256'][f], f
    vocab = json.loads(raw['dictionary.json'])
    fit = {int(k): v for k, v in json.loads(raw['fit-sources.json']).items()}
    if part == 'fit': return vocab, fit
    allsrc = {int(k): v for k, v in json.loads(raw['sources.json']).items()}
    assert all(allsrc[p] == fit[p] for p in fit)
    return vocab, allsrc


def arm_run(a, c):
    os.sched_setaffinity(0, {int(x) for x in a.cores.split(',')})
    import numpy as np
    import analyze, selection as sel
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    fit_ids, val_ids = parent['partition']['dev_fit'], parent['partition']['dev_val']
    work, out, arm, width, cfg = a.work.resolve(), a.output.resolve(), a.arm, 8, c['lns']
    seed_vocab, fit = load_seed(work, c, 'fit')  # item 13's selected fit sources only; validation is not read before the seal
    assert sorted(fit) == sorted(fit_ids)
    forbidden = sel.forbidden_strings(fit)
    pool = sel.build_pool(fit, forbidden, c['pool_max_length'])
    graph = sel.Graph(fit, pool, c['pool_max_length'])
    score = np.bincount(graph.occ_entry, minlength=len(pool)) * np.array([len(s) - 1 for s in pool])
    ranked = [pool[i] for i in np.lexsort((np.arange(len(pool)), -score))]
    start = breadth.per_program(fit, seed_vocab, analyze)
    weights = {p: round(c['relative_scale'] / start[p]) for p in fit} if arm == 'relative' else None
    assert weights is None or min(weights.values()) >= 1
    objective = (lambda costs: sum(weights[p] * costs[p] for p in costs)) if weights else (lambda costs: sum(costs.values()))
    TOL = c['objective_tolerance']
    rng = random.Random(cfg['seed'])
    incumbent, costs = list(seed_vocab), dict(start); best = objective(costs)
    live = out / f'{arm}-live'; live.mkdir(parents=True)
    moves, started = [], time.monotonic()
    budget_s = a.smoke or cfg['lns_seconds']
    while time.monotonic() - started < budget_s:
        learned = sorted(s for s in incumbent if s not in sel.ALPHABET)
        removed = rng.sample(learned, min(cfg['k'], len(learned)))
        fixed = [s for s in incumbent if s not in set(removed)]; fixset = set(fixed)
        top = [s for s in ranked if s not in fixset][:cfg['top']]
        extra = [s for s in rng.sample(pool, min(len(pool), cfg['random'] * 3)) if s not in fixset and s not in set(top)][:cfg['random']]
        cand = list(dict.fromkeys(removed + top + extra))
        remaining = budget_s - (time.monotonic() - started)
        capacity = 2 ** width - len(fixed)
        chosen, solver = breadth.repair(fit, fixed, cand, capacity, min(cfg['milp_seconds'], max(1., remaining)),
                                        weights=weights, caps=dict(costs) if arm == 'nonregress' else None)
        trial = fixed + chosen
        trial_costs = breadth.per_program(fit, trial, analyze) if solver['feasible'] else None
        trial_obj = objective(trial_costs) if trial_costs else None
        if solver['feasible']:
            assert trial_obj <= solver['objective'] + TOL, 'exact rescoring exceeds the MILP objective'
            if solver['status'] == 0: assert abs(trial_obj - solver['objective']) <= TOL, 'solver-optimal mismatch'
            if arm == 'nonregress': assert all(trial_costs[p] <= costs[p] for p in fit), 'nonregression violated'
        accepted = trial_obj is not None and trial_obj < best and not set(trial) & forbidden
        if accepted:
            incumbent, costs, best = trial, trial_costs, trial_obj
            (live / f'incumbent-{len(moves):04d}.json').write_text(json.dumps(incumbent) + '\n')
        row = {'move': len(moves), **solver, 'capacity': capacity, 'chosen': len(chosen), 'trial_objective': trial_obj,
               'trial_selections': None if trial_costs is None else sum(trial_costs.values()), 'accepted': accepted,
               'incumbent_objective': best, 'incumbent_selections': sum(costs.values()), 'candidates': len(cand)}
        moves.append(row)
        with open(live / 'moves.jsonl', 'a') as fh: fh.write(json.dumps(row) + '\n')
        print(json.dumps({'arm': arm, **row}), flush=True)
    folder = out / arm; folder.mkdir()
    (folder / 'dictionary.json').write_text(json.dumps(incumbent) + '\n')
    seal = sha((folder / 'dictionary.json').read_bytes())
    (folder / 'fit-seal.json').write_text(json.dumps({'dictionary_sha256': seal, 'validation_loaded': False}) + '\n')
    report = {'arm': arm, 'moves': len(moves), 'accepted_moves': sum(m['accepted'] for m in moves), 'lns_seconds': time.monotonic() - started,
              'start_fit': sum(start.values()), 'final_fit': sum(costs.values()), 'final_objective': best,
              'fit_programs_worse_than_start': sum(costs[p] > start[p] for p in fit), 'fit_programs_better_than_start': sum(costs[p] < start[p] for p in fit),
              'statuses': {str(s): sum(m['status'] == s for m in moves) for s in sorted({m['status'] for m in moves})}, 'dictionary_sha256': seal}
    if a.smoke:
        print(json.dumps({'smoke': True, **report}), flush=True); return
    # Validation opens only now: item 13's own validation sources, unchanged, under the sealed dictionary.
    _, allsrc = load_seed(work, c, 'all')
    val = {p: allsrc[p] for p in val_ids}
    forbidden_all = forbidden | sel.forbidden_strings(val)
    allrows, illegal, db = sel.measure({**fit, **val}, incumbent, width, forbidden_all)
    assert len(allrows) == len(fit) + len(val)
    report.update(decoded=len(allrows), illegal_entry_sha256=illegal, dictionary_bytes=db,
                  per_problem={p: allrows[p] for p in allrows})
    (folder / 'results.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({'arm': arm, 'done': True, 'fit': report['final_fit']}), flush=True)


def launch(a, c):
    a.output.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, 'PYTHONHASHSEED': '0', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'}
    lim = c['limits']
    cap = lambda: resource.setrlimit(resource.RLIMIT_AS, (lim['address_space_bytes'],) * 2)
    procs = [subprocess.Popen(['timeout', str(lim['arm_seconds']), sys.executable, '-B', __file__, '--work', str(a.work), '--output', str(a.output), '--arm', arm,
                               '--cores', ','.join(map(str, c['cores'][arm]))] + (['--smoke', str(a.smoke)] if a.smoke else []),
                              env=env, preexec_fn=cap)
             for arm in ARMS]
    codes = [p.wait() for p in procs]
    arms = [json.loads((a.output / arm / 'results.json').read_text()) for arm in ARMS if (a.output / arm / 'results.json').exists()]
    (a.output / 'results.json').write_text(json.dumps({'contract_sha256': sha((HERE / 'contract.json').read_bytes()),
                                                       'exit_codes': dict(zip(ARMS, codes)), 'arms': arms}, indent=1) + '\n')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--arm', choices=ARMS); ap.add_argument('--cores'); ap.add_argument('--smoke', type=float, help='LNS seconds; fit only')
    a = ap.parse_args(); c = contract()
    arm_run(a, c) if a.arm else launch(a, c)


if __name__ == '__main__':
    main()
