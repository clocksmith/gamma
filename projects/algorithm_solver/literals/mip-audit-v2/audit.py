"""mip-audit-v2: exact MILP optima on random dev-fit sub-instances vs the frozen local search (FREEZE.md).

  audit.py --work DIR --output DIR/mip-audit/run-v2 [--shards 6]      launcher: one pinned process per shard
  audit.py --work DIR --output DIR/mip-audit/run-v2 --shard I --cores A,B --of N   (started by the launcher)

Per frozen (programs, seed): the subset `random.Random(seed).sample(dev_fit, n)`; its pool (substrings of 2-32
characters shared by at least two subset programs, never a complete source or solve body); HiGHS MILP (scipy
milp, mip_rel_gap=0) for the fewest selections with the 96 characters plus at most B pool entries; the frozen
local search (unrestricted proposals) and a matched pool-restricted local search on the same subset. Each worker
process is pinned to two cores with sched_setaffinity, because scipy exposes no HiGHS thread option. Receipts are
written per instance as it finishes. Validation sources are never opened.
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


def model(texts, pool, lmax, B):
    import numpy as np
    from scipy.optimize import LinearConstraint
    from scipy.sparse import coo_matrix
    idx = {s: k for k, s in enumerate(pool)}; E = len(pool)
    tail, head, ent, src, snk, base = [], [], [], [], [], 0
    for p in sorted(texts):
        t = texts[p]; m = len(t); src.append(base); snk.append(base + m)
        for i in range(m):
            tail.append(base + i); head.append(base + i + 1); ent.append(-1)
            for l in range(2, min(lmax, m - i) + 1):
                k = idx.get(t[i:i + l])
                if k is not None: tail.append(base + i); head.append(base + i + l); ent.append(k)
        base += m + 1
    na = len(tail); nv = E + na
    tail, head, ent = np.array(tail), np.array(head), np.array(ent)
    cost = np.zeros(nv); cost[E:] = 1
    arcs = np.arange(na)
    eq = coo_matrix((np.concatenate([np.ones(na), -np.ones(na)]), (np.concatenate([tail, head]), np.concatenate([E + arcs, E + arcs]))),
                    shape=(base, nv)).tocsr()
    rhs = np.zeros(base); rhs[src] = 1; rhs[snk] = -1
    f = np.flatnonzero(ent >= 0)
    link = coo_matrix((np.concatenate([np.ones(len(f)), -np.ones(len(f))]), (np.concatenate([np.arange(len(f))] * 2), np.concatenate([E + f, ent[f]]))),
                      shape=(len(f), nv)).tocsr()
    bud = np.zeros(nv); bud[:E] = 1
    integ = np.zeros(nv); integ[:E] = 1
    cons = [LinearConstraint(eq, rhs, rhs), LinearConstraint(link, -np.inf, 0), LinearConstraint(bud[None, :], -np.inf, B)]
    return cost, cons, integ, na


def local(texts, width, propose_filter, c, sel):
    m2 = sel.module(f'audit_m2_{os.getpid()}_{time.monotonic_ns()}', LIT / 'style150-v2/measure.py'); v3 = m2.v3
    sources = {pid: {'style': t} for pid, t in texts.items()}
    mc = json.loads((LIT / 'minify-control-v1/contract.json').read_text())['search']
    budget = v3.Budget({'trials': c['local']['trials'], 'seconds': c['local']['seconds']})
    nb = {**mc['neighborhood'], 'refill_shortlist': mc['refill_shortlist']}
    base = m2.hybrid_chosen([], sources)
    propose = base if propose_filter is None else (lambda s, st, limit, fr: [p for p in base(s, st, 10 ** 6, fr) if p in propose_filter][:limit])
    st = v3.evaluate(sources, list(sel.ALPHABET), width, None, budget)
    st, _ = v3.refill(sources, st, width, propose, nb, nb['refill_shortlist'], budget)
    st, stop = v3.local_search(sources, st, width, propose, mc['neighborhood'], budget, [])
    return st['vocab'], {'fit_selections': st['selections'], 'trials': budget.trials, 'stop': stop, 'seconds': budget.elapsed()}


def check_dictionary(texts, vocab, width, forbidden, analyze):
    """Legality and independent canonical encode/decode of every subset program; returns exact selections."""
    assert len(vocab) == len(set(vocab)) <= 2 ** width and not set(vocab) & forbidden
    db = analyze.dictionary_bytes(vocab); total = 0
    for t in texts.values():
        seq = analyze.shortest_encode(t, vocab)
        assert analyze.decode(db, analyze.encode(vocab, seq, width)) == t
        total += len(seq)
    return total


def instance(n, seed, c, work, out):
    import numpy as np
    from scipy.optimize import milp, Bounds
    import analyze, selection as sel
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    assert sha((LIT / 'cost-decomposition-v1/contract.json').read_bytes()) == c['parent_contract_sha256']
    ids = random.Random(seed).sample(parent['partition']['dev_fit'], n)
    texts = analyze.load_sources(work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(ids)]})
    forbidden = sel.forbidden_strings(texts)
    B, lmax, width = c['B'], c['max_length'], c['width']
    assert 2 ** width == len(sel.ALPHABET) + B
    pool = sel.build_pool(texts, forbidden, lmax)
    cost, cons, integ, na = model(texts, pool, lmax, B)
    t0 = time.monotonic()
    res = milp(cost, constraints=cons, integrality=integ, bounds=Bounds(0, 1),
               options={'time_limit': float(c['milp_seconds']), 'mip_rel_gap': 0.0, 'disp': False})
    milp_seconds = time.monotonic() - t0
    row = {'n': n, 'seed': seed, 'ids': sorted(ids), 'pool': len(pool), 'arcs': na, 'milp_status': int(res.status),
           'milp_message': str(res.message), 'milp_objective': None if res.fun is None else float(res.fun),
           'milp_dual_bound': getattr(res, 'mip_dual_bound', None), 'milp_gap': getattr(res, 'mip_gap', None),
           'milp_seconds': milp_seconds, 'label': 'solver-reported (HiGHS tolerances), not an independent proof'}
    dictionaries = {}
    if res.x is not None:
        chosen = [pool[k] for k in range(len(pool)) if res.x[k] > 0.5]
        assert len(chosen) <= B and set(chosen) <= set(pool)
        vocab = list(sel.ALPHABET) + sorted(chosen)
        exact = check_dictionary(texts, vocab, width, forbidden, analyze)
        assert exact <= round(res.fun) + 1e-6, 'exact rescoring exceeds the MILP objective'
        if res.status == 0: assert abs(exact - res.fun) <= 1e-6, 'solver-optimal objective disagrees with exact rescoring'
        row['milp_exact_fit'] = exact; dictionaries['milp'] = vocab
    for arm, flt in (('local', None), ('local_pool', set(pool))):
        vocab, info = local(texts, width, flt, c, sel)
        if flt is not None: assert set(vocab) - set(sel.ALPHABET) <= flt
        info['exact_fit'] = check_dictionary(texts, vocab, width, forbidden, analyze)
        assert info['exact_fit'] == info['fit_selections']
        row[arm] = info; dictionaries[arm] = vocab
    if 'milp_exact_fit' in row:
        for arm in ('local', 'local_pool'):
            row[arm]['witness_gap'] = (row[arm]['exact_fit'] - row['milp_exact_fit']) / row['milp_exact_fit']
    row['dictionary_sha256'] = {k: sha(json.dumps(v).encode()) for k, v in dictionaries.items()}
    folder = out / f'n{n}-s{seed}'; folder.mkdir()
    for k, v in dictionaries.items(): (folder / f'{k}.json').write_text(json.dumps(v) + '\n')
    (folder / 'receipt.json').write_text(json.dumps(row, indent=1) + '\n')
    return row


def shard(a, c):
    os.sched_setaffinity(0, {int(x) for x in a.cores.split(',')})
    os.environ['PYTHONHASHSEED'] = '0'
    jobs = [(n, s) for n in c['sizes'] for s in c['seeds'][str(n)]][a.shard::a.of]
    for n, s in jobs:
        row = instance(n, s, c, a.work.resolve(), a.output.resolve())
        print(json.dumps({k: row.get(k) for k in ('n', 'seed', 'milp_status', 'milp_objective', 'milp_exact_fit')}
                         | {k: row[k]['exact_fit'] for k in ('local', 'local_pool')}), flush=True)


def launch(a, c):
    a.output.mkdir(parents=True, exist_ok=False)
    cores = c['cores']; assert a.shards <= 6 and len(cores) >= 2 * a.shards
    env = {**os.environ, 'PYTHONHASHSEED': '0', 'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2'}
    procs = [subprocess.Popen([sys.executable, '-B', __file__, '--work', str(a.work), '--output', str(a.output), '--shard', str(i),
                               '--of', str(a.shards), '--cores', f'{cores[2 * i]},{cores[2 * i + 1]}'], env=env) for i in range(a.shards)]
    codes = [p.wait() for p in procs]
    rows = [json.loads(f.read_text()) for f in sorted(a.output.glob('*/receipt.json'))]
    (a.output / 'results.json').write_text(json.dumps({'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'exit_codes': codes,
                                                       'instances': len(rows), 'rows': rows}, indent=1) + '\n')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--shards', type=int, default=6); ap.add_argument('--shard', type=int); ap.add_argument('--of', type=int); ap.add_argument('--cores')
    a = ap.parse_args(); c = contract()
    shard(a, c) if a.shard is not None else launch(a, c)


if __name__ == '__main__':
    main()
