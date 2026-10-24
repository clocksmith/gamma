"""alphabet96-v2 (board item 78): repair from item 77's exact coverage-robust drop dictionary with corrected solver checks, and
the effect of the restored characters' dictionary IDs (FREEZE.md).

  run.py --work DIR --output DIR/alphabet96-v2/run-v1          launcher: one pinned process per arm
  run.py --work DIR --output DIR/alphabet96-v2/run-v1 --arm A --cores X   (started by the launcher)

Seed: item 77's sealed drop dictionary (all 96 characters, 160 learned entries). Arms:
  lastdrop    the same entry set re-serialized with the four restored characters (B, P, R, _) at the END of the universe;
  repair43    item 51's capped LNS repair (k = 24, LNS seed 13, 300 s repairs, 3,000 s), all 96 characters fixed, in item 77's
              universe order (restored characters right after item 43's entries);
  repairlast  the same repair in the 'last' universe order.
capped.solve has a relative objective tolerance (item 77's repair abort); M = 32,768 > any capped total N.
Validation opens only after the arm's dictionary is sealed.
"""
import argparse, hashlib, json, os, random, resource, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(HERE), str(LIT / 'breadth-lns-v1'), str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]

sha = lambda raw: hashlib.sha256(raw).hexdigest()
ARMS = ('lastdrop', 'repair43', 'repairlast')


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
    missing = c['missing_characters']
    assert all(s in set(seed_vocab) for s in sel.ALPHABET) and not any(s in set(order_vocab) for s in missing)
    forbidden = sel.forbidden_strings(fit)
    pool = sel.build_pool(fit, forbidden, c['pool_max_length'])
    graph = sel.Graph(fit, pool, c['pool_max_length'])
    score = np.bincount(graph.occ_entry, minlength=len(pool)) * np.array([len(s) - 1 for s in pool])
    ranked = [pool[i] for i in np.lexsort((np.arange(len(pool)), -score))]
    rest = sorted(set(pool) - set(order_vocab) - set(missing))
    # universe 'after43' is item 77's (restored characters right after item 43's entries); 'last' moves them to the very end
    universe = list(order_vocab) + missing + rest if spec['universe'] == 'after43' else list(order_vocab) + rest + missing
    uidx = {s: i for i, s in enumerate(universe)}
    after43 = {s: i for i, s in enumerate(list(order_vocab) + missing + rest)}
    assert ordered(after43, seed_vocab) == list(seed_vocab), 'item 77 drop dictionary is not in its universe order'
    def nc(vocab):  # canonical (shortest, smaller-ID ties) per-program selections N and single-character selections C
        res = {}
        for p, t in fit.items():
            seq = analyze.shortest_encode(t, vocab); res[p] = (len(seq), sum(len(vocab[i]) == 1 for i in seq))
        return res
    M = c['char_scale']; TOL = c['objective_tolerance']
    objective = lambda v: M * sum(x[0] for x in v.values()) + sum(x[1] for x in v.values())
    seed_nc = nc(seed_vocab)
    incumbent = ordered(uidx, seed_vocab)  # the 'last' arms re-serialize the same entry set; 'after43' keeps it byte-identical
    cur_nc = nc(incumbent); costs = {p: v[0] for p, v in cur_nc.items()}
    assert all(costs[p] == seed_nc[p][0] for p in fit), 'a re-serialization never changes per-program N'
    assert M > sum(costs.values()), 'char_scale must exceed any capped total N (>= any total C), so M*N + C is lexicographic'
    live = out / f'{arm}-live'; live.mkdir(parents=True)
    start_nc, start = dict(cur_nc), dict(costs); best = objective(cur_nc)
    # repair arms only: item 51's capped LNS; all 96 characters are fixed (never freed)
    rng = random.Random(cfg['seed']); moves = []; started = time.monotonic(); budget_s = (a.smoke or cfg['lns_seconds']) if spec['repair'] else 0
    while time.monotonic() - started < budget_s:
        learned = sorted(s for s in incumbent if s not in sel.ALPHABET)
        removed = rng.sample(learned, min(cfg['k'], len(learned)))
        fixed = [s for s in incumbent if s not in set(removed)]; fixset = set(fixed)
        top = [s for s in ranked if s not in fixset][:cfg['top']]
        extra = [s for s in rng.sample(pool, min(len(pool), cfg['random'] * 3)) if s not in fixset and s not in set(top)][:cfg['random']]
        cand = [s for s in dict.fromkeys(removed + top + extra) if s not in fixset]
        remaining = budget_s - (time.monotonic() - started)
        model = capped.build(fit, fixed, cand, 2 ** width - len(fixed), incumbent, dict(costs), None, M)
        chosen, solver = capped.solve(model, cand, True, min(cfg['milp_seconds'], max(1., remaining)), seed=cfg['seed'])  # corrected checks
        solver = {**solver, 'build_seconds': model['build_seconds'], 'arcs': model['arcs'], 'initial': model['initial']}
        trial = ordered(uidx, fixed + chosen)
        trial_nc = nc(trial) if solver['feasible'] else None
        trial_costs = {p: v[0] for p, v in trial_nc.items()} if trial_nc else None
        trial_obj = objective(trial_nc) if trial_nc else None
        if solver['feasible']:
            n_path = int((solver['objective'] + TOL) // M)
            assert sum(trial_costs.values()) <= n_path + TOL, 'exact rescoring exceeds the MILP selections'
            if solver['optimal']: assert abs(sum(trial_costs.values()) - n_path) <= TOL, 'solver-optimal N mismatch'
            assert all(trial_costs[p] <= costs[p] for p in fit), 'nonregression violated'
        accepted = trial_obj is not None and trial_obj < best and not set(trial) & forbidden
        if accepted:
            incumbent, costs, cur_nc, best = trial, trial_costs, trial_nc, trial_obj
            (live / f'incumbent-{len(moves):04d}.json').write_text(json.dumps(incumbent) + '\n')
        row = {'move': len(moves), **solver, 'chosen': len(chosen), 'trial_objective': trial_obj, 'accepted': accepted,
               'incumbent_objective': best, 'incumbent_selections': sum(costs.values()),
               'incumbent_characters': sum(x[1] for x in cur_nc.values()), 'candidates': len(cand)}
        moves.append(row)
        with open(live / 'moves.jsonl', 'a') as fh: fh.write(json.dumps(row) + '\n')
        print(json.dumps({'arm': arm, **row}), flush=True)
    if not moves: (live / 'moves.jsonl').write_text('')
    assert all(s in set(incumbent) for s in sel.ALPHABET), 'a restored dictionary must hold all 96 characters'
    folder = out / arm; folder.mkdir()
    (folder / 'dictionary.json').write_text(json.dumps(incumbent) + '\n')
    seal = sha((folder / 'dictionary.json').read_bytes())
    (folder / 'fit-seal.json').write_text(json.dumps({'dictionary_sha256': seal, 'validation_loaded': False}) + '\n')
    report = {'arm': arm, 'k': spec['k'], 'repair': spec['repair'], 'universe': spec['universe'], 'moves': len(moves), 'accepted_moves': sum(m['accepted'] for m in moves),
              'lns_seconds': time.monotonic() - started, 'seed_fit': sum(x[0] for x in seed_nc.values()), 'seed_characters': sum(x[1] for x in seed_nc.values()),
              'start_dictionary_sha256': sha((json.dumps(ordered(uidx, seed_vocab)) + '\n').encode()),
              'start_fit': sum(start.values()), 'final_fit': sum(costs.values()), 'final_objective': best,
              'start_characters': sum(x[1] for x in start_nc.values()), 'final_characters': sum(x[1] for x in cur_nc.values()),
              'fit_programs_worse_than_start': sum(costs[p] > start[p] for p in fit), 'fit_programs_better_than_start': sum(costs[p] < start[p] for p in fit),
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
    print(json.dumps({'arm': arm, 'done': True, 'fit': report['final_fit']}), flush=True)


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
