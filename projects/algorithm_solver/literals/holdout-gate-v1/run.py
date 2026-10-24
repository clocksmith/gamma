"""holdout-gate-v1 (board item 75): does gating fit-only repair moves on a held-aside fit subset stop the fit-to-validation
regression seen in items 72 and 74? From the JS current best, item 51 flat (FREEZE.md).

  run.py --work DIR --output DIR/holdout-gate/run-v1          launcher: one pinned process per arm
  run.py --work DIR --output DIR/holdout-gate/run-v1 --arm A --cores X   (started by the launcher)

The 300 fit programs are split once (split(): the 60 IDs with the smallest SHA-256 of 'holdout-gate-v1:<id>' form the gate
subset, the other 240 the search set). The candidate pool, ranking, model and per-program caps use the search set only. Item
51's lexicographic M*N + C model (continuous arcs, item 26's solve), item 51's universe order and loop, LNS seed 11:
  gate24, gate40   a search-improving move is accepted only if the gate subset's canonical (total N, total C) does not rise
                   lexicographically (gate_ok); k = 24 and 40;
  free24, free40   the same search without the gate (matched controls).
Validation opens only after the arm's dictionary is sealed; unencodable rows are retained failures (measure_safe).
"""
import argparse, hashlib, json, os, random, resource, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(HERE), str(LIT / 'breadth-lns-v1'), str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]

sha = lambda raw: hashlib.sha256(raw).hexdigest()
ARMS = ('gate24', 'free24', 'gate40', 'free40')


def contract():
    if not __debug__ or os.environ.get('PYTHONOPTIMIZE') not in ('', '0', None):  # an assert would itself be compiled out under -O
        raise RuntimeError('assertions must stay enabled (no -O / PYTHONOPTIMIZE)')
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    assert sha((LIT / 'cost-decomposition-v1/contract.json').read_bytes()) == c['parent_contract_sha256']
    rt = c['runtime']; exe = os.path.realpath(sys.executable)
    assert exe == rt['python_realpath'] and sha(Path(exe).read_bytes()) == rt['python_sha256'], exe
    import scipy; assert sys.version.split()[0] == rt['python_version'] and scipy.__version__ == rt['scipy']
    from scipy.optimize._highspy import _core  # the HiGHS extension item 26's model module actually loads
    assert os.path.realpath(_core.__file__) == rt['highs_extension_path'] and sha(Path(_core.__file__).read_bytes()) == rt['highs_extension_sha256']
    return c


def measure_safe(texts, vocab, width, forbidden):
    """selection.measure per program; a program the dictionary cannot represent is a retained unencodable row, never a crash."""
    import analyze, selection as sel
    rows = {}
    for pid, t in sorted(texts.items()):
        try:
            r, _, _ = sel.measure({pid: t}, vocab, width, forbidden)
            rows.update({k: {**v, 'encodable': True} for k, v in r.items()})
        except ValueError as ex:
            assert 'cannot be represented' in str(ex), ex
            rows[str(pid)] = {'encodable': False}
    illegal = sorted(sha(s.encode()) for s in set(vocab) & forbidden)
    return rows, illegal, len(analyze.dictionary_bytes(vocab))


def ordered(universe_index, selected):
    """Serialize a selected entry set in the fixed universe order, so the same set always gets the same IDs (lexfrac-v1 AMENDMENT-1)."""
    assert all(s in universe_index for s in selected), 'entry outside the fixed universe'
    return sorted(set(selected), key=universe_index.__getitem__)


def checked(work, rel, digest):
    raw = (work / rel).read_bytes(); assert sha(raw) == digest, rel; return json.loads(raw)


def load_seed(work, c, part):
    """part 'fit': item 51's dictionary, item 43's (universe order) and item 13's fit-sources.json only. part 'all': all 400 sources."""
    s = c['seed']; folder = work / s['relative_path']
    names = ['fit-sources.json'] if part == 'fit' else ['fit-sources.json', 'sources.json']
    raw = {f: (folder / f).read_bytes() for f in names}
    for f in names: assert sha(raw[f]) == s['private_sha256'][f], f
    vocab = checked(work, s['dictionary'], s['dictionary_sha256'])
    order = checked(work, s['universe_order_dictionary'], s['universe_order_dictionary_sha256'])
    fit = {int(k): v for k, v in json.loads(raw['fit-sources.json']).items()}
    if part == 'fit': return vocab, order, fit
    allsrc = {int(k): v for k, v in json.loads(raw['sources.json']).items()}
    assert all(allsrc[p] == fit[p] for p in fit)
    return vocab, order, allsrc


def split(ids, n_gate, salt):
    """The fixed held-aside gate subset: the n_gate fit IDs with the smallest SHA-256 of salt:id; the rest are the search set."""
    gate = sorted(sorted(ids, key=lambda p: sha(f'{salt}:{p}'.encode()))[:n_gate])
    return [p for p in sorted(ids) if p not in set(gate)], gate


def gate_ok(trial_gate, inc_gate):
    """A gated move may not raise the held-aside subset's canonical (total N, total C) lexicographically."""
    return trial_gate <= inc_gate


def arm_run(a, c):
    os.sched_setaffinity(0, {int(x) for x in a.cores.split(',')})
    import numpy as np
    import analyze, selection as sel, capped
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    fit_ids, val_ids = parent['partition']['dev_fit'], parent['partition']['dev_val']
    work, out, arm, width = a.work.resolve(), a.output.resolve(), a.arm, 8
    spec = c['arms'][arm]; cfg = {**c['lns'], 'k': spec['k']}
    seed_vocab, order_vocab, fit = load_seed(work, c, 'fit')  # validation is not read before the seal
    assert sorted(fit) == sorted(fit_ids)
    search_ids, gate_ids = split(fit_ids, c['gate']['programs'], c['gate']['salt'])
    assert len(gate_ids) == c['gate']['programs'] and sha(json.dumps(gate_ids).encode()) == c['gate']['ids_sha256']
    search = {p: fit[p] for p in search_ids}
    forbidden = sel.forbidden_strings(fit)  # legality covers every fit program, gate included
    pool = sel.build_pool(search, forbidden, c['pool_max_length'])  # candidates come from the search set only
    graph = sel.Graph(search, pool, c['pool_max_length'])
    score = np.bincount(graph.occ_entry, minlength=len(pool)) * np.array([len(s) - 1 for s in pool])
    ranked = [pool[i] for i in np.lexsort((np.arange(len(pool)), -score))]
    # item 43's order, then every other seed or search-pool entry sorted: the seed keeps item 51's own relative ID order
    universe = list(order_vocab) + sorted((set(pool) | set(seed_vocab)) - set(order_vocab))
    uidx = {s: i for i, s in enumerate(universe)}
    assert ordered(uidx, seed_vocab) == list(seed_vocab), 'item 51 seed is not in its universe order'
    def nc(vocab, ids):  # canonical (shortest, smaller-ID ties) per-program selections N and single-character selections C
        res = {}
        for p in ids:
            seq = analyze.shortest_encode(fit[p], vocab); res[p] = (len(seq), sum(len(vocab[i]) == 1 for i in seq))
        return res
    tot = lambda v: (sum(x[0] for x in v.values()), sum(x[1] for x in v.values()))
    M = c['char_scale']
    start_nc = nc(seed_vocab, search_ids); start = {p: v[0] for p, v in start_nc.items()}; start_gate = tot(nc(seed_vocab, gate_ids))
    objective = lambda v: M * tot(v)[0] + tot(v)[1]
    assert M > sum(start.values()), 'char_scale must exceed any capped total N (>= any total C), so M*N + C is lexicographic'
    TOL = c['objective_tolerance']
    rng = random.Random(cfg['seed'])
    incumbent, costs, cur_nc, cur_gate = list(seed_vocab), dict(start), dict(start_nc), start_gate; best = objective(cur_nc)
    live = out / f'{arm}-live'; live.mkdir(parents=True)
    moves, started = [], time.monotonic()
    budget_s = a.smoke or cfg['lns_seconds']
    while time.monotonic() - started < budget_s:
        learned = sorted(s for s in incumbent if s not in sel.ALPHABET)  # characters are never freed
        removed = rng.sample(learned, min(cfg['k'], len(learned)))
        fixed = [s for s in incumbent if s not in set(removed)]; fixset = set(fixed)
        top = [s for s in ranked if s not in fixset][:cfg['top']]
        extra = [s for s in rng.sample(pool, min(len(pool), cfg['random'] * 3)) if s not in fixset and s not in set(top)][:cfg['random']]
        cand = [s for s in dict.fromkeys(removed + top + extra) if s not in fixset]
        remaining = budget_s - (time.monotonic() - started)
        capacity = 2 ** width - len(fixed)
        model = capped.build(search, fixed, cand, capacity, incumbent, dict(costs), None, M)
        chosen, solver = capped.solve(model, cand, True, min(cfg['milp_seconds'], max(1., remaining)), seed=cfg['seed'])
        solver = {**solver, 'build_seconds': model['build_seconds'], 'arcs': model['arcs'], 'initial': model['initial']}
        trial = ordered(uidx, fixed + chosen)
        trial_nc = nc(trial, search_ids) if solver['feasible'] else None
        trial_costs = {p: v[0] for p, v in trial_nc.items()} if trial_nc else None
        trial_obj = objective(trial_nc) if trial_nc else None
        if solver['feasible']:
            n_path = int((solver['objective'] + TOL) // M)
            # lexfrac-v1's checks: canonical N is per-program minimal, so it never exceeds the solver path's N, with equality at optimality
            assert sum(trial_costs.values()) <= n_path + TOL, 'exact rescoring exceeds the MILP selections'
            if solver['optimal']: assert abs(sum(trial_costs.values()) - n_path) <= TOL, 'solver-optimal N mismatch'
            assert all(trial_costs[p] <= costs[p] for p in search), 'nonregression violated'
        improving = trial_obj is not None and trial_obj < best and not set(trial) & forbidden
        trial_gate = tot(nc(trial, gate_ids)) if improving else None  # the gate subset is scored only for improving trials
        passes = improving and (not spec['gated'] or gate_ok(trial_gate, cur_gate))
        if passes:
            incumbent, costs, cur_nc, best, cur_gate = trial, trial_costs, trial_nc, trial_obj, trial_gate
            (live / f'incumbent-{len(moves):04d}.json').write_text(json.dumps(incumbent) + '\n')
        row = {'move': len(moves), **solver, 'capacity': capacity, 'chosen': len(chosen), 'trial_objective': trial_obj,
               'trial_selections': None if trial_costs is None else sum(trial_costs.values()),
               'trial_characters': None if trial_nc is None else sum(x[1] for x in trial_nc.values()),
               'trial_gate': trial_gate, 'improving': improving, 'accepted': passes, 'gate_rejected': bool(improving and not passes),
               'incumbent_objective': best, 'incumbent_selections': sum(costs.values()),
               'incumbent_characters': sum(x[1] for x in cur_nc.values()), 'incumbent_gate': list(cur_gate), 'candidates': len(cand)}
        moves.append(row)
        with open(live / 'moves.jsonl', 'a') as fh: fh.write(json.dumps(row) + '\n')
        print(json.dumps({'arm': arm, **row}), flush=True)
    folder = out / arm; folder.mkdir()
    (folder / 'dictionary.json').write_text(json.dumps(incumbent) + '\n')
    seal = sha((folder / 'dictionary.json').read_bytes())
    (folder / 'fit-seal.json').write_text(json.dumps({'dictionary_sha256': seal, 'validation_loaded': False}) + '\n')
    report = {'arm': arm, 'k': spec['k'], 'gated': spec['gated'], 'moves': len(moves), 'accepted_moves': sum(m['accepted'] for m in moves),
              'improving_moves': sum(m['improving'] for m in moves), 'gate_rejections': sum(m['gate_rejected'] for m in moves),
              'lns_seconds': time.monotonic() - started,
              'start_search': sum(start.values()), 'final_search': sum(costs.values()), 'final_objective': best,
              'start_search_characters': sum(x[1] for x in start_nc.values()), 'final_search_characters': sum(x[1] for x in cur_nc.values()),
              'start_gate': list(start_gate), 'final_gate': list(cur_gate),
              'search_programs_worse_than_start': sum(costs[p] > start[p] for p in search), 'search_programs_better_than_start': sum(costs[p] < start[p] for p in search),
              'statuses': {str(s): sum(m['model_status'] == s for m in moves) for s in sorted({m['model_status'] for m in moves})},
              'feasible_moves': sum(m['feasible'] for m in moves), 'optimal_moves': sum(m['optimal'] for m in moves), 'dictionary_sha256': seal}
    if a.smoke:
        print(json.dumps({'smoke': True, **report}), flush=True); return
    # Validation opens only now: item 13's own validation sources, unchanged, under the sealed dictionary.
    _, _, allsrc = load_seed(work, c, 'all')
    val = {p: allsrc[p] for p in val_ids}
    forbidden_all = forbidden | sel.forbidden_strings(val)
    allrows, illegal, db = measure_safe({**fit, **val}, incumbent, width, forbidden_all)
    assert len(allrows) == len(fit) + len(val)
    report.update(decoded=sum(r['encodable'] for r in allrows.values()), illegal_entry_sha256=illegal, dictionary_bytes=db,
                  per_problem={p: allrows[p] for p in allrows})
    (folder / 'results.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({'arm': arm, 'done': True, 'search': report['final_search']}), flush=True)


def launch(a, c):
    a.output.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, 'PYTHONHASHSEED': '0', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    lim = c['limits']
    cap = lambda: resource.setrlimit(resource.RLIMIT_AS, (lim['address_space_bytes'],) * 2)
    procs = [subprocess.Popen(['timeout', '--kill-after=10', str(lim['arm_seconds']), sys.executable, '-B', __file__, '--work', str(a.work), '--output', str(a.output), '--arm', arm,
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
