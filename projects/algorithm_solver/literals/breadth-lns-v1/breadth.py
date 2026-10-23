"""breadth-lns-v1: does a breadth-aware exact LNS objective trade total gain for fewer regressions? (FREEZE.md)

  breadth.py --work DIR --output DIR/breadth-lns/run-v1             launcher: one pinned process per arm
  breadth.py --work DIR --output DIR/breadth-lns/run-v1 --arm A --cores X,Y   (started by the launcher)

Three matched 256-entry arms from the pinned L-R dictionary, same seed, candidates and budget as mip-lns-v1:
  unweighted  minimise total dev-fit selections (item 11's objective, under this code: the matched control);
  nonregress  the same objective, plus a per-program constraint inside every repair: no fit program may cost more
              than it does under the current incumbent;
  relative    minimise sum_p w_p * cost_p with integer w_p = round(10^6 / start_p), start_p the program's cost under
              the pinned dictionary (each program's relative cost counts equally).
Moves are accepted only on a strict improvement of the arm's own objective under exact canonical rescoring (nonregress
also asserts no fit program got worse). No polish. Validation opens only after all of an arm's dictionaries are sealed.
"""
import argparse, hashlib, json, os, random, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
sha = lambda raw: hashlib.sha256(raw).hexdigest()
ARMS = ('unweighted', 'nonregress', 'relative')


def contract():
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    return c


def repair(texts, fixed, cand, k, seconds, weights=None, caps=None):
    """Exact best <= k additions from `cand` given fixed entries, minimising sum_p weights[p] * selections_p, with optional
    per-program caps selections_p <= caps[p]. Returns (chosen, solver record)."""
    import numpy as np
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import coo_matrix
    fixset = {s for s in fixed if len(s) > 1}; cidx = {s: i for i, s in enumerate(cand)}; C = len(cand)
    maxlen = max(map(len, list(fixset) + cand))
    tail, head, ent, owner, src, snk, base = [], [], [], [], [], [], 0
    pids = sorted(texts)
    for q, p in enumerate(pids):
        t = texts[p]; m = len(t); src.append(base); snk.append(base + m)
        for i in range(m):
            tail.append(base + i); head.append(base + i + 1); ent.append(-1); owner.append(q)
            for l in range(2, min(maxlen, m - i) + 1):
                s = t[i:i + l]
                if s in fixset: tail.append(base + i); head.append(base + i + l); ent.append(-1); owner.append(q)
                elif s in cidx: tail.append(base + i); head.append(base + i + l); ent.append(cidx[s]); owner.append(q)
        base += m + 1
    na = len(tail); nv = C + na
    tail, head, ent, owner = map(np.array, (tail, head, ent, owner))
    w = np.ones(len(pids)) if weights is None else np.array([weights[p] for p in pids], dtype=float)
    cost = np.zeros(nv); cost[C:] = w[owner]; arcs = np.arange(na)
    eq = coo_matrix((np.concatenate([np.ones(na), -np.ones(na)]), (np.concatenate([tail, head]), np.concatenate([C + arcs, C + arcs]))),
                    shape=(base, nv)).tocsr()
    rhs = np.zeros(base); rhs[src] = 1; rhs[snk] = -1
    f = np.flatnonzero(ent >= 0)
    link = coo_matrix((np.concatenate([np.ones(len(f)), -np.ones(len(f))]), (np.concatenate([np.arange(len(f))] * 2), np.concatenate([C + f, ent[f]]))),
                      shape=(len(f), nv)).tocsr()
    bud = np.zeros(nv); bud[:C] = 1; integ = np.zeros(nv); integ[:C] = 1
    cons = [LinearConstraint(eq, rhs, rhs), LinearConstraint(link, -np.inf, 0), LinearConstraint(bud[None, :], -np.inf, k)]
    if caps is not None:
        rows = coo_matrix((np.ones(na), (owner, C + arcs)), shape=(len(pids), nv)).tocsr()
        cons.append(LinearConstraint(rows, -np.inf, np.array([caps[p] for p in pids], dtype=float)))
    t0 = time.monotonic()
    res = milp(cost, constraints=cons, integrality=integ, bounds=Bounds(0, 1), options={'time_limit': float(seconds), 'mip_rel_gap': 0.0, 'disp': False})
    chosen = [cand[i] for i in range(C) if res.x is not None and res.x[i] > 0.5]
    assert len(chosen) <= k
    return chosen, {'status': int(res.status), 'message': str(res.message), 'objective': None if res.fun is None else float(res.fun),
                    'dual_bound': getattr(res, 'mip_dual_bound', None), 'gap': getattr(res, 'mip_gap', None),
                    'seconds': time.monotonic() - t0, 'feasible': res.x is not None}


def per_program(texts, vocab, analyze):
    return {p: len(analyze.shortest_encode(t, vocab)) for p, t in texts.items()}


def arm_run(a, c):
    os.sched_setaffinity(0, {int(x) for x in a.cores.split(',')})
    import numpy as np
    import analyze, selection as sel
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    assert sha((LIT / 'cost-decomposition-v1/contract.json').read_bytes()) == c['parent_contract_sha256']
    work, out, arm, width, cfg = a.work.resolve(), a.output.resolve(), a.arm, 8, c['lns']
    fit_ids, val_ids = parent['partition']['dev_fit'], parent['partition']['dev_val']
    fit = analyze.load_sources(work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(fit_ids)]})
    raw = (work / parent['dictionaries'][str(width)]['relative_path']).read_bytes()
    assert sha(raw) == parent['dictionaries'][str(width)]['sha256']
    baseline = json.loads(raw)
    forbidden = sel.forbidden_strings(fit)
    pool = sel.build_pool(fit, forbidden, c['pool_max_length'])
    graph = sel.Graph(fit, pool, c['pool_max_length'])
    score = np.bincount(graph.occ_entry, minlength=len(pool)) * np.array([len(s) - 1 for s in pool])
    ranked = [pool[i] for i in np.lexsort((np.arange(len(pool)), -score))]
    start = per_program(fit, baseline, analyze)
    weights = {p: round(c['relative_scale'] / start[p]) for p in fit} if arm == 'relative' else None
    objective = (lambda costs: sum(weights[p] * costs[p] for p in costs)) if weights else (lambda costs: sum(costs.values()))
    rng = random.Random(cfg['seed'])
    incumbent, costs = list(baseline), dict(start)
    best = objective(costs)
    live = out / f'{arm}-live'; live.mkdir(parents=True)
    moves, started = [], time.monotonic()
    while time.monotonic() - started < (a.smoke or cfg['lns_seconds']):
        learned = sorted(s for s in incumbent if s not in sel.ALPHABET)
        removed = rng.sample(learned, min(cfg['k'], len(learned)))
        fixed = [s for s in incumbent if s not in set(removed)]; fixset = set(fixed)
        top = [s for s in ranked if s not in fixset][:cfg['top']]
        extra = [s for s in rng.sample(pool, min(len(pool), cfg['random'] * 3)) if s not in fixset and s not in set(top)][:cfg['random']]
        cand = list(dict.fromkeys(removed + top + extra))
        remaining = (a.smoke or cfg['lns_seconds']) - (time.monotonic() - started)
        capacity = 2 ** width - len(fixed)
        chosen, solver = repair(fit, fixed, cand, capacity, min(cfg['milp_seconds'], max(1., remaining)),
                                weights=weights, caps=dict(costs) if arm == 'nonregress' else None)
        trial = fixed + chosen
        trial_costs = per_program(fit, trial, analyze) if solver['feasible'] else None
        trial_obj = objective(trial_costs) if trial_costs else None
        if solver['feasible']:
            assert trial_obj <= solver['objective'] + 1e-6 * max(1, abs(solver['objective'])), 'exact rescoring exceeds the MILP objective'
            if solver['status'] == 0: assert abs(trial_obj - solver['objective']) <= 1e-6 * max(1, abs(solver['objective'])), 'solver-optimal mismatch'
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
    fit_regressions = sum(costs[p] > start[p] for p in fit)
    (folder / 'fit-seal.json').write_text(json.dumps({'dictionary_sha256': seal, 'validation_loaded': False}) + '\n')
    report = {'arm': arm, 'moves': len(moves), 'accepted_moves': sum(m['accepted'] for m in moves), 'lns_seconds': time.monotonic() - started,
              'start_fit': sum(start.values()), 'final_fit': sum(costs.values()), 'final_objective': best,
              'fit_programs_worse_than_start': fit_regressions, 'fit_programs_better_than_start': sum(costs[p] < start[p] for p in fit),
              'statuses': {str(s): sum(m['status'] == s for m in moves) for s in sorted({m['status'] for m in moves})},
              'dictionary_sha256': seal}
    if a.smoke:  # plumbing on dev-fit only; validation is never opened
        print(json.dumps({'smoke': True, **report}), flush=True); return
    # Validation is opened only now, after this arm's dictionary is sealed.
    val = analyze.load_sources(work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(val_ids)]})
    forbidden_all = forbidden | sel.forbidden_strings(val)
    for name, vocab in (('pinned', baseline), (arm, incumbent)):
        rows, illegal, db = sel.measure(val, vocab, width, forbidden_all)
        sel_total = sum(r['selections'] for r in rows.values())
        report[f'validation_{"pinned" if name == "pinned" else "arm"}'] = {
            'illegal_entry_sha256': illegal, 'dictionary_bytes': db,
            'actions': analyze.distribution([r['actions'] for r in rows.values()]),
            'single_character_fraction': sum(r['single_characters'] for r in rows.values()) / sel_total,
            'package_bytes': db + sum(r['packet_bytes'] for r in rows.values()),
            'per_problem_actions': {p: r['actions'] for p, r in rows.items()}}
    (folder / 'results.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({'arm': arm, 'done': True, 'fit': report['final_fit'], 'val_actions': report['validation_arm']['actions']['total']}), flush=True)


def launch(a, c):
    a.output.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, 'PYTHONHASHSEED': '0', 'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2'}
    procs = [subprocess.Popen([sys.executable, '-B', __file__, '--work', str(a.work), '--output', str(a.output), '--arm', arm,
                               '--cores', ','.join(map(str, c['cores'][arm]))] + (['--smoke', str(a.smoke)] if a.smoke else []), env=env)
             for arm in ARMS]
    codes = [p.wait() for p in procs]
    arms = [json.loads((a.output / arm / 'results.json').read_text()) for arm in ARMS if (a.output / arm / 'results.json').exists()]
    (a.output / 'results.json').write_text(json.dumps({'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'exit_codes': codes,
                                                       'arms': arms}, indent=1) + '\n')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--arm', choices=ARMS); ap.add_argument('--cores'); ap.add_argument('--smoke', type=float, help='LNS seconds; fit only')
    a = ap.parse_args(); c = contract()
    arm_run(a, c) if a.arm else launch(a, c)


if __name__ == '__main__':
    main()
