"""python-nonregress-v1 (board item 65): the JS current-best pipeline (item 43's capped direct-HiGHS nonregression repair,
with a fixed canonical entry order as in item 51) carried onto the Python panel (FREEZE.md).

  run.py --work DIR --output DIR/python-nonregress/run-v1          launcher: one pinned process per width
  run.py --work DIR --output DIR/python-nonregress/run-v1 --arm A --cores X   (started by the launcher)

Two arms, w7 and w8, each from its own-width item 31 scope_joint anchor (dictionary and fit sources), never compared
across widths. Item 31's/34's Python bans, canonical order (alphabet, then sorted learned entries) and coverage-safe
evaluation are reused unchanged. Moves are accepted only on a strict decrease of exact rescored total fit selections
with no fit program worse; only learned entries are ever freed, so every character stays paid and present.
Validation sources are read only after the arm's dictionary is sealed.
"""
import argparse, hashlib, importlib.util, json, os, random, resource, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(HERE), str(LIT / 'breadth-lns-v1'), str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
sha = lambda raw: hashlib.sha256(raw).hexdigest()
ARMS = ('w7', 'w8')


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
    width = int(a.arm[1:]); inp = c['inputs'][str(width)]; cfg = {**c['lns'], **c['arm_overrides'][a.arm]}
    work, out = a.work.resolve(), a.output.resolve()
    seed = checked(work, inp['seed_dictionary']); fit = {int(k): v for k, v in checked(work, inp['fit']).items()}
    assert sorted(fit) == sorted(c['partition']['dev_fit']) and seed == cm.ordered(seed) and len(seed) <= 2 ** width
    forbidden = cm.banned(fit, c['entries'])  # Python Solution entry-method/body and whole-source bans (item 34)
    pool = sel.build_pool(fit, forbidden, c['pool_max_length'])
    graph = sel.Graph(fit, pool, c['pool_max_length'])
    score = np.bincount(graph.occ_entry, minlength=len(pool)) * np.array([len(s) - 1 for s in pool])
    ranked = [pool[i] for i in np.lexsort((np.arange(len(pool)), -score))]
    start = breadth.per_program(fit, seed, analyze); costs = dict(start)
    TOL = c['objective_tolerance']; rng = random.Random(cfg['seed'])
    incumbent = list(seed); best = sum(costs.values())
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
        model = capped.build(fit, fixed, cand, capacity, incumbent, dict(costs))
        chosen, solver = capped.solve(model, cand, True, min(cfg['milp_seconds'], max(1., remaining)), seed=cfg['seed'])
        solver = {**solver, 'build_seconds': model['build_seconds'], 'arcs': model['arcs'], 'initial': model['initial']}
        trial = cm.ordered(fixed + chosen)  # canonical order: the same entry set always gets the same IDs
        trial_costs = breadth.per_program(fit, trial, analyze) if solver['feasible'] else None
        trial_obj = sum(trial_costs.values()) if trial_costs else None
        if solver['feasible']:
            assert trial_obj <= solver['objective'] + TOL, 'exact rescoring exceeds the MILP objective'
            if solver['optimal']: assert abs(trial_obj - solver['objective']) <= TOL, 'solver-optimal mismatch'
            assert all(trial_costs[p] <= costs[p] for p in fit), 'nonregression violated'
        accepted = trial_obj is not None and trial_obj < best and not set(trial) & forbidden
        if accepted:
            incumbent, costs, best = trial, trial_costs, trial_obj
            (live / f'incumbent-{len(moves):04d}.json').write_text(json.dumps(incumbent) + '\n')
        row = {'move': len(moves), **solver, 'capacity': capacity, 'chosen': len(chosen), 'trial_objective': trial_obj, 'accepted': accepted,
               'incumbent_selections': sum(costs.values()), 'candidates': len(cand)}
        moves.append(row)
        with open(live / 'moves.jsonl', 'a') as fh: fh.write(json.dumps(row) + '\n')
        print(json.dumps({'arm': a.arm, **row}), flush=True)
    folder = out / a.arm; folder.mkdir()
    (folder / 'dictionary.json').write_text(json.dumps(incumbent) + '\n')
    seal = sha((folder / 'dictionary.json').read_bytes())
    (folder / 'fit-seal.json').write_text(json.dumps({'dictionary_sha256': seal, 'validation_loaded': False}) + '\n')
    report = {'arm': a.arm, 'width': width, 'moves': len(moves), 'accepted_moves': sum(m['accepted'] for m in moves),
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
