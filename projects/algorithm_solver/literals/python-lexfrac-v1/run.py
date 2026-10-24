"""python-lexfrac-v1 (board item 67): a fraction-aware continuation of item 65 at w8 and a smaller-k w7 repair on the
Python panel (FREEZE.md).

  run.py --work DIR --output DIR/python-lexfrac/run-v1          launcher: one pinned process per arm
  run.py --work DIR --output DIR/python-lexfrac/run-v1 --arm A --cores X   (started by the launcher)

Arms (each capped: no fit program's canonical N may rise; only learned entries are freed; canonical set-determined order):
  w8lex   from item 65's sealed w8 dictionary; arcs cost M + [single character] (M*N + C); accept a strict lexicographic
          decrease of (total canonical N, total canonical C);
  w8flat  from the same seed; N-only objective (matched control);
  w7k8    from the w7 item 31 anchor (= R); N-only objective with k = 8 instead of item 65's 32.
Item 31's/34's Python bans and coverage-safe evaluation are reused unchanged.
Validation sources are read only after the arm's dictionary is sealed.
"""
import argparse, hashlib, importlib.util, json, os, random, resource, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(HERE), str(LIT / 'breadth-lns-v1'), str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
sha = lambda raw: hashlib.sha256(raw).hexdigest()
ARMS = ('w8lex', 'w8flat', 'w7k8')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def contract():
    if not __debug__ or os.environ.get('PYTHONOPTIMIZE') not in ('', '0', None):  # an assert would itself be compiled out under -O
        raise RuntimeError('assertions must stay enabled (no -O / PYTHONOPTIMIZE)')
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    rt = c['runtime']; exe = os.path.realpath(sys.executable)
    assert exe == rt['python_realpath'] and sha(Path(exe).read_bytes()) == rt['python_sha256'], exe
    import scipy; assert sys.version.split()[0] == rt['python_version'] and scipy.__version__ == rt['scipy']
    from scipy.optimize._highspy import _core
    assert os.path.realpath(_core.__file__) == rt['highs_extension_path'] and sha(Path(_core.__file__).read_bytes()) == rt['highs_extension_sha256']
    return c


def checked(work, spec):
    raw = (work / spec['relative_path']).read_bytes(); assert sha(raw) == spec['sha256'], spec['relative_path']; return json.loads(raw)


def common():
    return module('python_slots_common', LIT / 'python-character-slots-v1/common.py')


def arm_run(a, c):
    os.sched_setaffinity(0, {int(x) for x in a.cores.split(',')})
    import numpy as np
    import analyze, selection as sel, breadth, capped
    cm = common()
    spec = c['arms'][a.arm]; width = spec['width']; inp = c['inputs'][str(width)]; cfg = {**c['lns'], 'k': spec['k']}
    work, out = a.work.resolve(), a.output.resolve()
    seed = checked(work, c['seeds'][spec['seed']]); fit = {int(k): v for k, v in checked(work, inp['fit']).items()}
    lex = spec['objective'] == 'lexnc'; M = c['char_scale']
    assert sorted(fit) == sorted(c['partition']['dev_fit']) and seed == cm.ordered(seed) and len(seed) <= 2 ** width
    forbidden = cm.banned(fit, c['entries'])  # Python Solution entry-method/body and whole-source bans (item 34)
    pool = sel.build_pool(fit, forbidden, c['pool_max_length'])
    graph = sel.Graph(fit, pool, c['pool_max_length'])
    score = np.bincount(graph.occ_entry, minlength=len(pool)) * np.array([len(s) - 1 for s in pool])
    ranked = [pool[i] for i in np.lexsort((np.arange(len(pool)), -score))]
    def nc(vocab):  # canonical per-program (N, C)
        res = {}
        for p, t in fit.items():
            seq = analyze.shortest_encode(t, vocab); res[p] = (len(seq), sum(len(vocab[i]) == 1 for i in seq))
        return res
    start_nc = nc(seed); start = {p: v[0] for p, v in start_nc.items()}; costs = dict(start); cur_nc = dict(start_nc)
    objective = (lambda v: M * sum(x[0] for x in v.values()) + sum(x[1] for x in v.values())) if lex else (lambda v: sum(x[0] for x in v.values()))
    assert M > sum(start.values())
    TOL = c['objective_tolerance']; rng = random.Random(cfg['seed'])
    incumbent = list(seed); best = objective(cur_nc)
    live = out / f'{a.arm}-live'; live.mkdir(parents=True)
    moves, started = [], time.monotonic(); budget_s = a.smoke or cfg['lns_seconds']
    while time.monotonic() - started < budget_s:
        learned = sorted(s for s in incumbent if len(s) > 1)  # characters are never freed
        removed = rng.sample(learned, min(cfg['k'], len(learned)))
        fixed = [s for s in incumbent if s not in set(removed)]; fixset = set(fixed)
        top = [s for s in ranked if s not in fixset][:cfg['top']]
        extra = [s for s in rng.sample(pool, min(len(pool), cfg['random'] * 3)) if s not in fixset and s not in set(top)][:cfg['random']]
        cand = [s for s in dict.fromkeys(removed + top + extra) if s not in fixset]
        remaining = budget_s - (time.monotonic() - started)
        capacity = 2 ** width - len(fixed)
        model = capped.build(fit, fixed, cand, capacity, incumbent, dict(costs), None, M if lex else None)
        chosen, solver = capped.solve(model, cand, True, min(cfg['milp_seconds'], max(1., remaining)), seed=cfg['seed'])
        solver = {**solver, 'build_seconds': model['build_seconds'], 'arcs': model['arcs'], 'initial': model['initial']}
        trial = cm.ordered(fixed + chosen)  # canonical order: the same entry set always gets the same IDs
        trial_nc = nc(trial) if solver['feasible'] else None
        trial_costs = {p: v[0] for p, v in trial_nc.items()} if trial_nc else None
        trial_obj = objective(trial_nc) if trial_nc else None
        if solver['feasible']:
            n_path = int((solver['objective'] + TOL) // M) if lex else solver['objective']
            # canonical N is per-program minimal; canonical C (ID ties) may exceed the solver path's C, so only N is checked
            assert sum(trial_costs.values()) <= n_path + TOL, 'exact rescoring exceeds the MILP selections'
            if solver['optimal']: assert abs(sum(trial_costs.values()) - n_path) <= TOL, 'solver-optimal N mismatch'
            assert all(trial_costs[p] <= costs[p] for p in fit), 'nonregression violated'
        accepted = trial_obj is not None and trial_obj < best and not set(trial) & forbidden
        if accepted:
            incumbent, costs, cur_nc, best = trial, trial_costs, trial_nc, trial_obj
            (live / f'incumbent-{len(moves):04d}.json').write_text(json.dumps(incumbent) + '\n')
        row = {'move': len(moves), **solver, 'capacity': capacity, 'chosen': len(chosen), 'trial_objective': trial_obj, 'accepted': accepted,
               'incumbent_selections': sum(costs.values()), 'incumbent_characters': sum(x[1] for x in cur_nc.values()), 'candidates': len(cand)}
        moves.append(row)
        with open(live / 'moves.jsonl', 'a') as fh: fh.write(json.dumps(row) + '\n')
        print(json.dumps({'arm': a.arm, **row}), flush=True)
    folder = out / a.arm; folder.mkdir()
    (folder / 'dictionary.json').write_text(json.dumps(incumbent) + '\n')
    seal = sha((folder / 'dictionary.json').read_bytes())
    (folder / 'fit-seal.json').write_text(json.dumps({'dictionary_sha256': seal, 'validation_loaded': False}) + '\n')
    report = {'arm': a.arm, 'width': width, 'objective': spec['objective'], 'seed': spec['seed'], 'final_objective': best,
              'start_characters': sum(x[1] for x in start_nc.values()), 'final_characters': sum(x[1] for x in cur_nc.values()),
              'moves': len(moves), 'accepted_moves': sum(m['accepted'] for m in moves),
              'lns_seconds': time.monotonic() - started, 'start_fit': sum(start.values()), 'final_fit': sum(costs.values()),
              'fit_programs_worse_than_start': sum(costs[p] > start[p] for p in fit), 'fit_programs_better_than_start': sum(costs[p] < start[p] for p in fit),
              'statuses': {str(s): sum(m['model_status'] == s for m in moves) for s in sorted({m['model_status'] for m in moves})},
              'feasible_moves': sum(m['feasible'] for m in moves), 'optimal_moves': sum(m['optimal'] for m in moves), 'dictionary_sha256': seal}
    if a.smoke:
        print(json.dumps({'smoke': True, **report}), flush=True); return
    # Validation opens only now: the anchor's own 36 sources (unchanged) under the sealed dictionary.
    texts = {str(k): v for k, v in checked(work, inp['sources']).items()}
    assert all(texts[str(p)] == fit[p] for p in fit)
    report['evaluation'] = cm.evaluate(texts, incumbent, width, c)
    (folder / 'results.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({'arm': a.arm, 'done': True, 'fit': report['final_fit']}), flush=True)


def launch(a, c):
    a.output.mkdir(parents=True, exist_ok=False); lim = c['limits']
    env = {**os.environ, 'PYTHONHASHSEED': '0', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    cap = lambda: resource.setrlimit(resource.RLIMIT_AS, (lim['address_space_bytes'],) * 2)
    procs = [subprocess.Popen(['timeout', '--kill-after=10', str(lim['arm_seconds']), sys.executable, '-B', __file__, '--work', str(a.work),
                               '--output', str(a.output), '--arm', arm, '--cores', ','.join(map(str, c['cores'][arm]))] + (['--smoke', str(a.smoke)] if a.smoke else []),
                              env=env, preexec_fn=cap) for arm in ARMS]
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
