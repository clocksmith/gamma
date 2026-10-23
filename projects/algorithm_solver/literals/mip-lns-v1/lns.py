"""mip-lns-v1: exact large-neighbourhood search over dev-fit dictionaries (FREEZE.md, contract.json).

  lns.py --work DIR --output DIR/mip-lns/run-v1          launcher: one pinned process per width
  lns.py --work DIR --output DIR/mip-lns/run-v1 --width W --cores A,B   (started by the launcher)

Per width, starting from the pinned L-R dictionary: repeat until the LNS wall budget is spent: free k random learned
entries (seeded), offer HiGHS the freed entries plus a candidate set (the top M fit-pool strings by
occurrences x (length - 1), plus R pool strings drawn at random per move), and solve exactly for the best <= k
additions over all 300 dev-fit programs (fixed entries and characters are free arcs). Accept a move only if exact
canonical rescoring strictly improves the incumbent. Then run the same exact local-search polish as the control,
which continues from the pinned dictionary. Dictionaries are sealed before validation is opened.
"""
import argparse, hashlib, json, os, random, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def contract():
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    return c


def repair(texts, fixed, cand, k, seconds):
    """Exact best <= k additions from `cand` given the fixed entries. Returns (chosen, status, objective, seconds)."""
    import numpy as np
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import coo_matrix
    fixset = {s for s in fixed if len(s) > 1}; cidx = {s: i for i, s in enumerate(cand)}; C = len(cand)
    maxlen = max(map(len, list(fixset) + cand))
    tail, head, ent, src, snk, base = [], [], [], [], [], 0
    for p in sorted(texts):
        t = texts[p]; m = len(t); src.append(base); snk.append(base + m)
        for i in range(m):
            tail.append(base + i); head.append(base + i + 1); ent.append(-1)
            for l in range(2, min(maxlen, m - i) + 1):
                s = t[i:i + l]
                if s in fixset: tail.append(base + i); head.append(base + i + l); ent.append(-1)
                elif s in cidx: tail.append(base + i); head.append(base + i + l); ent.append(cidx[s])
        base += m + 1
    na = len(tail); nv = C + na
    tail, head, ent = np.array(tail), np.array(head), np.array(ent)
    cost = np.zeros(nv); cost[C:] = 1; arcs = np.arange(na)
    eq = coo_matrix((np.concatenate([np.ones(na), -np.ones(na)]), (np.concatenate([tail, head]), np.concatenate([C + arcs, C + arcs]))),
                    shape=(base, nv)).tocsr()
    rhs = np.zeros(base); rhs[src] = 1; rhs[snk] = -1
    f = np.flatnonzero(ent >= 0)
    link = coo_matrix((np.concatenate([np.ones(len(f)), -np.ones(len(f))]), (np.concatenate([np.arange(len(f))] * 2), np.concatenate([C + f, ent[f]]))),
                      shape=(len(f), nv)).tocsr()
    bud = np.zeros(nv); bud[:C] = 1; integ = np.zeros(nv); integ[:C] = 1
    t0 = time.monotonic()
    res = milp(cost, constraints=[LinearConstraint(eq, rhs, rhs), LinearConstraint(link, -np.inf, 0), LinearConstraint(bud[None, :], -np.inf, k)],
               integrality=integ, bounds=Bounds(0, 1), options={'time_limit': float(seconds), 'mip_rel_gap': 0.0, 'disp': False})
    chosen = [cand[i] for i in range(C) if res.x is not None and res.x[i] > 0.5]
    assert len(chosen) <= k
    return chosen, int(res.status), None if res.fun is None else float(res.fun), time.monotonic() - t0


def width_run(a, c):
    os.sched_setaffinity(0, {int(x) for x in a.cores.split(',')})
    import numpy as np
    import analyze, selection as sel
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    assert sha((LIT / 'cost-decomposition-v1/contract.json').read_bytes()) == c['parent_contract_sha256']
    work, out, width = a.work.resolve(), a.output.resolve(), a.width
    cfg = {**c['widths'][str(width)], **({'lns_seconds': a.smoke} if a.smoke else {})}
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
    rng = random.Random(cfg['seed'])
    incumbent, best = list(baseline), sel.exact_fit(fit, baseline)
    moves, started = [], time.monotonic()
    while time.monotonic() - started < cfg['lns_seconds']:
        learned = sorted(s for s in incumbent if s not in sel.ALPHABET)
        removed = rng.sample(learned, min(cfg['k'], len(learned)))
        fixed = [s for s in incumbent if s not in set(removed)]
        fixset = set(fixed)
        top = [s for s in ranked if s not in fixset][:cfg['top']]
        extra = [s for s in rng.sample(pool, min(len(pool), cfg['random'] * 3)) if s not in fixset and s not in set(top)][:cfg['random']]
        cand = list(dict.fromkeys(removed + top + extra))
        remaining = cfg['lns_seconds'] - (time.monotonic() - started)
        chosen, status, objective, secs = repair(fit, fixed, cand, len(removed), min(cfg['milp_seconds'], max(1., remaining)))
        trial = fixed + chosen
        exact = sel.exact_fit(fit, trial)
        accepted = exact < best and not set(trial) & forbidden
        if accepted: incumbent, best = trial, exact
        moves.append({'move': len(moves), 'status': status, 'objective': objective, 'exact': exact, 'accepted': accepted,
                      'incumbent': best, 'seconds': secs, 'candidates': len(cand), 'kept_removed': len(set(chosen) & set(removed))})
        print(json.dumps({'width': width, **moves[-1]}), flush=True)
    lns_seconds = time.monotonic() - started
    pcfg = {**c['polish'], 'trials': 50 if a.smoke else c['polish']['trials']}
    m2 = sel.module(f'lns_m2_{width}', LIT / 'style150-v2/measure.py')
    results = {}
    for name, start in (('control', baseline), ('lns', incumbent)):
        vocab, info = sel.polish(fit, start, width, pcfg, m2)
        assert not set(vocab) & forbidden
        results[name] = {'vocab': vocab, 'polish': info}
    results['lns_raw'] = {'vocab': incumbent, 'polish': None}
    folder = out / f'w{width}'; folder.mkdir(parents=True)
    seal = {}
    for name, r in results.items():
        (folder / f'{name}.json').write_text(json.dumps(r['vocab']) + '\n'); seal[name] = sha((folder / f'{name}.json').read_bytes())
    (folder / 'moves.json').write_text(json.dumps(moves) + '\n')
    (folder / 'fit-seal.json').write_text(json.dumps({'dictionaries_sha256': seal, 'validation_loaded': False}) + '\n')
    if a.smoke:  # plumbing and timing on dev-fit only; validation is never opened
        print(json.dumps({'width': width, 'smoke': True, 'moves': len(moves), 'accepted': sum(m['accepted'] for m in moves),
                          'start_fit': sel.exact_fit(fit, baseline), 'lns_fit': best,
                          'fit': {k: sel.exact_fit(fit, r['vocab']) for k, r in results.items()}}), flush=True)
        return
    # Validation is opened only now, after this width's dictionaries are sealed.
    val = analyze.load_sources(work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(val_ids)]})
    forbidden_all = forbidden | sel.forbidden_strings(val)
    report = {'width': width, 'pool_entries': len(pool), 'moves': len(moves), 'accepted_moves': sum(m['accepted'] for m in moves),
              'lns_seconds': lns_seconds, 'start_fit': sel.exact_fit(fit, baseline), 'lns_fit': best,
              'milp_statuses': {str(s): sum(m['status'] == s for m in moves) for s in sorted({m['status'] for m in moves})}, 'arms': {}}
    for name, r in results.items():
        rows, illegal, db = sel.measure({**fit, **val}, r['vocab'], width, forbidden_all)
        fit_rows = [rows[str(p)] for p in fit_ids]; val_rows = [rows[str(p)] for p in val_ids]
        selections = sum(x['selections'] for x in val_rows)
        report['arms'][name] = {'entries': len(r['vocab']), 'dictionary_sha256': seal[name], 'dictionary_bytes': db, 'polish': r['polish'],
                                'illegal_entry_sha256': illegal, 'fit_selections': sum(x['selections'] for x in fit_rows),
                                'validation': {'selections': analyze.distribution([x['selections'] for x in val_rows]),
                                               'actions': analyze.distribution([x['actions'] for x in val_rows]),
                                               'single_character_fraction': sum(x['single_characters'] for x in val_rows) / selections,
                                               'package_bytes': db + sum(x['packet_bytes'] for x in val_rows)},
                                'per_problem_validation_actions': {str(p): rows[str(p)]['actions'] for p in val_ids}}
    (folder / 'results.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({'width': width, 'done': True, 'arms': {k: (v['fit_selections'], v['validation']['actions']['total']) for k, v in report['arms'].items()}}), flush=True)


def launch(a, c):
    a.output.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, 'PYTHONHASHSEED': '0', 'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2'}
    procs = [subprocess.Popen([sys.executable, '-B', __file__, '--work', str(a.work), '--output', str(a.output), '--width', str(w),
                               '--cores', ','.join(map(str, c['cores'][str(w)]))] + (['--smoke', str(a.smoke)] if a.smoke else []), env=env)
             for w in (7, 8)]
    codes = [p.wait() for p in procs]
    widths = [json.loads((a.output / f'w{w}' / 'results.json').read_text()) for w in (7, 8) if (a.output / f'w{w}' / 'results.json').exists()]
    (a.output / 'results.json').write_text(json.dumps({'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'exit_codes': codes,
                                                       'widths': widths}, indent=1) + '\n')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--width', type=int); ap.add_argument('--cores'); ap.add_argument('--smoke', type=float, help='LNS seconds; fit only, never opens validation')
    a = ap.parse_args(); c = contract()
    width_run(a, c) if a.width else launch(a, c)


if __name__ == '__main__':
    main()
