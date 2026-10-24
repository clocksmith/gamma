"""python-slackcap-v1 (board item 74): item 69's matched Python repair with per-program caps relaxed to a fixed slack over the
start dictionary, from item 69's best Python development dictionaries (FREEZE.md).

  run.py --work DIR --output DIR/python-slackcap/run-v1          launcher: one pinned process per arm
  run.py --work DIR --output DIR/python-slackcap/run-v1 --arm A --cores X   (started by the launcher)

Arms (w8 from item 69's w8lex dictionary with item 69's lex model, w7 from item 69's w7ratio dictionary with item 69's ratio
model; item 73's uniform random removal, LNS seed 10 and removal seed 1010; binary arcs; canonical set-determined order; only
learned entries are freed; lexicographic M*N + C with acceptance on a strict decrease of (canonical N, canonical C)):
  w8s1, w7s1   every fit program's canonical N may exceed its START value by at most 1 selection (caps start + 1, never
               ratcheted to the incumbent, so the bound is cumulative over the whole run);
  w8s3, w7s3   the same with slack 3.
Item 73's w8rnd and w7rnd are the matched slack-0 controls (identical seeds, settings and code path with caps = incumbent).
Validation sources are read only after the arm's dictionary is sealed.
"""
import argparse, hashlib, importlib.util, json, os, random, resource, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(HERE), str(LIT / 'breadth-lns-v1'), str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
sha = lambda raw: hashlib.sha256(raw).hexdigest()
ARMS = ('w8s1', 'w8s3', 'w7s1', 'w7s3')


def adjacency(texts, vocab, analyze, learned):
    """Symmetric counts of consecutive selections between learned entries in the canonical encodings of the fit texts."""
    keep = set(learned); w = {}
    for p in sorted(texts):
        seq = [vocab[i] for i in analyze.shortest_encode(texts[p], vocab)]
        for a, b in zip(seq, seq[1:]):
            if a in keep and b in keep and a != b:
                w.setdefault(a, {}); w.setdefault(b, {})
                w[a][b] = w[a].get(b, 0) + 1; w[b][a] = w[b].get(a, 0) + 1
    return w


def related_removal(rng, learned, k, w):
    """A random learned seed entry, then greedily the learned entry with the largest total adjacency to the freed set; ties broken
    by one rng draw per entry per move, and a random remaining entry when no remaining entry is adjacent to the freed set."""
    learned = sorted(learned); k = min(k, len(learned))
    tie = {s: rng.random() for s in learned}
    removed = [rng.choice(learned)]; score = dict.fromkeys(learned, 0); left = set(learned) - set(removed)
    for b, x in w.get(removed[0], {}).items(): score[b] += x
    while len(removed) < k:
        pick = max(left, key=lambda s: (score[s], tie[s]))
        if score[pick] == 0: pick = rng.choice(sorted(left))
        removed.append(pick); left.discard(pick)
        for b, x in w.get(pick, {}).items(): score[b] += x
    return removed


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


def trial_check(n_canon, c_canon, n_path, optimal, ratio_ref, tol):
    """Return whether the canonical trial meets the ratio (always True without a ratio row). Canonical N is per-program
    minimal, so it never exceeds the solver path's N. Equality is required only at optimality AND when the canonical
    trial itself meets the ratio: otherwise a longer ratio-feasible path can be optimal for the same dictionary
    (AMENDMENT-1), which must reach rejection, not an abort."""
    assert n_canon <= n_path + tol, 'exact rescoring exceeds the MILP selections'
    ratio_ok = True if ratio_ref is None else ratio_ref[0] * c_canon <= ratio_ref[1] * n_canon
    if optimal and ratio_ok: assert abs(n_canon - n_path) <= tol, 'solver-optimal N mismatch'
    return ratio_ok


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
    removal_rng = random.Random(cfg['removal_seed'])  # AMENDMENT-1: removal draws never shift the shared candidate stream
    incumbent = list(seed); best = objective(cur_nc)
    live = out / f'{a.arm}-live'; live.mkdir(parents=True)
    moves, started = [], time.monotonic(); budget_s = a.smoke or cfg['lns_seconds']
    while time.monotonic() - started < budget_s:
        learned = sorted(s for s in incumbent if len(s) > 1)  # characters are never freed
        if spec['removal'] == 'related':
            removed = related_removal(removal_rng, learned, cfg['k'], adjacency(fit, incumbent, analyze, learned))
        else:
            removed = removal_rng.sample(learned, min(cfg['k'], len(learned)))
        fixed = [s for s in incumbent if s not in set(removed)]; fixset = set(fixed)
        top = [s for s in ranked if s not in fixset][:cfg['top']]
        extra = [s for s in rng.sample(pool, min(len(pool), cfg['random'] * 3)) if s not in fixset and s not in set(top)][:cfg['random']]
        cand = [s for s in dict.fromkeys(removed + top + extra) if s not in fixset]
        remaining = budget_s - (time.monotonic() - started)
        capacity = 2 ** width - len(fixed)
        n_inc = sum(x[0] for x in cur_nc.values()); c_inc = sum(x[1] for x in cur_nc.values())
        caps = {p: start[p] + spec['slack'] for p in fit}  # fixed over the run: relative to the START, not the incumbent
        model = capped.build(fit, fixed, cand, capacity, incumbent, caps, None, M if lex else None,
                             ratio=(n_inc, c_inc) if spec['ratio'] else None)
        chosen, solver = capped.solve(model, cand, True, min(cfg['milp_seconds'], max(1., remaining)), seed=cfg['seed'], integral_arcs=True)
        solver = {**solver, 'build_seconds': model['build_seconds'], 'arcs': model['arcs'], 'initial': model['initial']}
        trial = cm.ordered(fixed + chosen)  # canonical order: the same entry set always gets the same IDs
        trial_nc = nc(trial) if solver['feasible'] else None
        trial_costs = {p: v[0] for p, v in trial_nc.items()} if trial_nc else None
        trial_obj = objective(trial_nc) if trial_nc else None
        ratio_ok = True
        if solver['feasible']:
            n_path = int((solver['objective'] + TOL) // M) if lex else solver['objective']
            # the fraction predicate is enforced on the canonical decoded trial, not only on the solver path
            ratio_ok = trial_check(sum(trial_costs.values()), sum(x[1] for x in trial_nc.values()), n_path, solver['optimal'],
                                   (n_inc, c_inc) if spec['ratio'] else None, TOL)
            assert all(trial_costs[p] <= start[p] + spec['slack'] for p in fit), 'slack cap violated'
        accepted = trial_obj is not None and trial_obj < best and ratio_ok and not set(trial) & forbidden
        if accepted:
            incumbent, costs, cur_nc, best = trial, trial_costs, trial_nc, trial_obj
            (live / f'incumbent-{len(moves):04d}.json').write_text(json.dumps(incumbent) + '\n')
        row = {'move': len(moves), **solver, 'capacity': capacity, 'chosen': len(chosen), 'trial_objective': trial_obj, 'accepted': accepted,
               'incumbent_selections': sum(costs.values()), 'incumbent_characters': sum(x[1] for x in cur_nc.values()), 'candidates': len(cand),
               'canonical_ratio_ok': ratio_ok, 'ratio_rejected': bool(trial_obj is not None and trial_obj < best and not ratio_ok)}
        moves.append(row)
        with open(live / 'moves.jsonl', 'a') as fh: fh.write(json.dumps(row) + '\n')
        print(json.dumps({'arm': a.arm, **row}), flush=True)
    folder = out / a.arm; folder.mkdir()
    (folder / 'dictionary.json').write_text(json.dumps(incumbent) + '\n')
    seal = sha((folder / 'dictionary.json').read_bytes())
    (folder / 'fit-seal.json').write_text(json.dumps({'dictionary_sha256': seal, 'validation_loaded': False}) + '\n')
    report = {'arm': a.arm, 'width': width, 'objective': spec['objective'], 'seed': spec['seed'], 'removal': spec['removal'], 'slack': spec['slack'], 'final_objective': best,
              'fit_max_worsening': max(costs[p] - start[p] for p in fit),
              'start_characters': sum(x[1] for x in start_nc.values()), 'final_characters': sum(x[1] for x in cur_nc.values()),
              'ratio': spec['ratio'], 'ratio_rejections': sum(m['ratio_rejected'] for m in moves),
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
