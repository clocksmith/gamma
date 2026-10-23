"""lagrange-select-v2: Lagrangian global dictionary selection with exact polish (FREEZE.md, contract.json).

  selection.py --work DIR --output DIR/lagrange-select/run-v2 [--smoke ITERATIONS]

Problem (per width): choose at most B = 2^w - 96 learned entries from a fit-witnessed pool (substrings of 2-64
characters shared by at least two dev-fit programs, never a complete source or solve body) so that the exact
minimum number of selections over the 300 dev-fit sources, with the 96 mandatory characters, is smallest.

Relaxation: each pool occurrence o of entry e in program p is an edge that may be used only if e is chosen
(y_o <= x_e). Relaxing those constraints with lambda_o >= 0 gives, for every lambda,
    L(lambda) = sum_p SP_p(edge costs 1 + lambda_o) - max_{|S| <= B} sum_{e in S} Lambda_e,  Lambda_e = sum_o lambda_o,
a valid lower bound on the fit selections of every dictionary of that form (weak duality). Subgradient steps
(Polyak, target = best exact primal) update lambda. Primal dictionaries (top-B by Lambda, and top-B by relaxed
usage) are scored exactly; the best is polished by the matched80-v3 exact local search with the minify-control
proposer, the same search the control arm continues from the pinned L-R dictionary. Validation sources are
loaded only after every dictionary is sealed.
"""
import argparse, concurrent.futures, hashlib, importlib.util, json, math, multiprocessing, os, subprocess, sys, time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
import analyze  # load_sources (allowlist only), shortest_encode, encode/decode, distribution, dictionary_bytes

sha = lambda raw: hashlib.sha256(raw).hexdigest()
ALPHABET = [chr(i) for i in range(32, 127)] + ['\n']


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def forbidden_strings(texts):
    """Complete sources and solve definitions/bodies (tail-search-v1 structure.cjs), never pool entries."""
    out = subprocess.run(['/usr/bin/node', str(LIT / 'tail-search-v1/structure.cjs')], input=json.dumps({str(k): v for k, v in texts.items()}),
                         text=True, capture_output=True, check=True).stdout
    return set(texts.values()) | {b for r in json.loads(out).values() for b in r['bodies']}


def build_pool(texts, forbidden, lmax):
    owners = defaultdict(set)
    for pid, t in texts.items():
        for i in range(len(t)):
            for l in range(2, min(lmax, len(t) - i) + 1):
                owners[t[i:i + l]].add(pid)
    return sorted(s for s, o in owners.items() if len(o) >= 2 and s not in forbidden)


class Graph:
    """Occurrence edges per program: at[p][i] = [(end, occurrence index)]; occ_entry[o] = entry index."""
    def __init__(self, texts, pool, lmax):
        index = {s: k for k, s in enumerate(pool)}
        self.pids = sorted(texts)
        self.lengths = [len(texts[p]) for p in self.pids]
        self.at, entry = [], []
        for p in self.pids:
            t = texts[p]; rows = []
            for i in range(len(t)):
                row = []
                for l in range(2, min(lmax, len(t) - i) + 1):
                    k = index.get(t[i:i + l])
                    if k is not None:
                        row.append((i + l, len(entry))); entry.append(k)
                rows.append(row)
            self.at.append(rows)
        self.occ_entry = np.array(entry, dtype=np.int64)
        self.entries = len(pool)

    def shortest(self, lam):
        """Total relaxed cost and the used-occurrence indicator y."""
        y = np.zeros(len(self.occ_entry)); total = 0.
        for rows, n in zip(self.at, self.lengths):
            cost = [0.] * (n + 1); back = [-1] * n
            for i in range(n - 1, -1, -1):
                best, arg = 1. + cost[i + 1], -1
                for j, o in rows[i]:
                    c = 1. + lam[o] + cost[j]
                    if c < best: best, arg = c, o
                cost[i] = best; back[i] = arg
            total += cost[0]
            i = 0
            while i < n:
                o = back[i]
                if o < 0: i += 1
                else:
                    y[o] = 1.
                    i = next(j for j, oo in rows[i] if oo == o)
        return total, y


def top(values, b, tiebreak):
    order = np.lexsort((tiebreak, -values))
    return order[:b]


def exact_fit(texts, vocab):
    return sum(len(analyze.shortest_encode(t, vocab)) for t in texts.values())


def lagrange(texts, pool, graph, b, incumbent, cfg, log):
    """Subgradient ascent on L(lambda).

    Returns (best real bound, its multiplier vector, best *generated* primal vocabulary, its exact fit selections).
    The incumbent (baseline) only sets the Polyak target; it is never returned as the generated primal, so a
    generated start that is worse than the baseline is still reported and polished.
    """
    lam = np.zeros(len(graph.occ_entry)); rank = np.arange(graph.entries)
    ub = exact_fit(texts, incumbent)  # Polyak target: best exact cost known, incumbent or generated
    gen_vocab, gen_cost, best_lam = None, math.inf, lam.copy()
    best_lb, theta, stall, started = -math.inf, cfg['theta'], 0, time.monotonic()
    ergodic = np.zeros(graph.entries)  # exponentially averaged relaxed usage, a third primal ranking
    for it in range(cfg['iterations']):
        if time.monotonic() - started > cfg['seconds']:
            log.append({'stop': 'time_limit', 'iteration': it}); break
        sp, y = graph.shortest(lam)
        Lam = np.bincount(graph.occ_entry, weights=lam, minlength=graph.entries)
        chosen = top(Lam, b, rank)
        lb = sp - Lam[chosen].sum()
        if lb > best_lb + 1e-9: best_lb, stall, best_lam = lb, 0, lam.copy()
        else: stall += 1
        if stall >= cfg['halve_after']: theta, stall = theta / 2, 0
        usage = np.bincount(graph.occ_entry, weights=y, minlength=graph.entries)
        ergodic = 0.9 * ergodic + 0.1 * usage
        if it % cfg['primal_every'] == 0:
            for score in (Lam, usage, ergodic):
                sel = top(score, b, rank)
                vocab = ALPHABET + [pool[k] for k in sorted(sel) if score[k] > 0]
                cost = exact_fit(texts, vocab)
                if cost < gen_cost: gen_cost, gen_vocab = cost, vocab
                ub = min(ub, cost)
        x = np.zeros(graph.entries); x[chosen] = 1.
        g = y - x[graph.occ_entry]
        norm = float(g @ g)
        log.append({'iteration': it, 'relaxed_paths': sp, 'lower_bound': lb, 'best_lower_bound': best_lb, 'upper_bound': ub,
                    'best_generated': gen_cost, 'theta': theta})
        if norm == 0 or ub - best_lb < 1:
            log.append({'stop': 'converged', 'iteration': it}); break
        lam = np.maximum(0., lam + theta * (ub - lb) / norm * g)
    else:
        log.append({'stop': 'iteration_limit', 'iteration': cfg['iterations']})
    return best_lb, best_lam, gen_vocab, gen_cost


def certify(graph, lam, b, denominator):
    """Exact integer certificate: q = floor(lambda * D) is a nonnegative dual point, so
    L(q / D) = (sum_p SP_p(D + q_o, characters D) - topB_e sum_o q_o) / D is a valid lower bound computed in integers."""
    q = [int(v) for v in np.floor(lam * denominator)]
    assert min(q, default=0) >= 0
    total = 0
    for rows, n in zip(graph.at, graph.lengths):
        cost = [0] * (n + 1)
        for i in range(n - 1, -1, -1):
            best = denominator + cost[i + 1]
            for j, o in rows[i]:
                c = denominator + q[o] + cost[j]
                if c < best: best = c
            cost[i] = best
        total += cost[0]
    sums = [0] * graph.entries
    for o, e in enumerate(graph.occ_entry.tolist()): sums[e] += q[o]
    numerator = total - sum(sorted(sums, reverse=True)[:b])
    return {'numerator': numerator, 'denominator': denominator, 'integer_lower_bound': -(-numerator // denominator)}


def polish(texts, vocab, width, cfg, m2):
    """Exact matched80-v3 local search from `vocab`, minify-control proposer (chosen-source spans only)."""
    v3, joint = m2.v3, m2.joint
    sources = {pid: {'style': t} for pid, t in texts.items()}
    budget = v3.Budget({'trials': cfg['trials'], 'seconds': cfg['seconds']})
    state = v3.evaluate(sources, vocab, width, None, budget)
    state, _ = joint.prune(sources, state, width)
    nb = {**cfg['neighborhood'], 'refill_shortlist': cfg['refill_shortlist']}
    propose = m2.hybrid_chosen([], sources)
    state, _ = v3.refill(sources, state, width, propose, nb, nb['refill_shortlist'], budget)
    log = []
    state, stop = v3.local_search(sources, state, width, propose, cfg['neighborhood'], budget, log)
    return state['vocab'], {'trials': budget.trials, 'stop': stop, 'seconds': budget.elapsed(), 'rounds': len(log), 'fit_selections': state['selections']}


def measure(texts, vocab, width, forbidden):
    db = analyze.dictionary_bytes(vocab); rows = {}
    illegal = sorted(sha(s.encode()) for s in set(vocab) & forbidden)
    for pid, t in sorted(texts.items()):
        seq = analyze.shortest_encode(t, vocab); packet = analyze.encode(vocab, seq, width)
        assert analyze.decode(db, packet) == t
        rows[str(pid)] = {'selections': len(seq), 'actions': len(seq) + 1, 'packet_bytes': len(packet),
                          'single_characters': sum(len(vocab[i]) == 1 for i in seq)}
    return rows, illegal, len(db)


def arm(job):
    os.environ['PYTHONHASHSEED'] = '0'
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    assert sha((LIT / 'cost-decomposition-v1/contract.json').read_bytes()) == c['parent_contract_sha256']
    work, out, width = Path(job['work']), Path(job['output']), job['width']
    fit_ids, val_ids = parent['partition']['dev_fit'], parent['partition']['dev_val']
    fit = analyze.load_sources(work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(fit_ids)]})
    raw = (work / parent['dictionaries'][str(width)]['relative_path']).read_bytes()
    assert sha(raw) == parent['dictionaries'][str(width)]['sha256']
    baseline = json.loads(raw)
    m2 = module(f'lagrange_style_v2_{width}', LIT / 'style150-v2/measure.py')
    forbidden = forbidden_strings(fit)
    started = time.monotonic()
    pool = build_pool(fit, forbidden, c['pool']['max_length'])
    graph = Graph(fit, pool, c['pool']['max_length'])
    b = 2 ** width - len(ALPHABET)
    lcfg = {**c['lagrange'], 'iterations': job['iterations'] or c['lagrange']['iterations']}
    trace = []
    lower, best_lam, primal, primal_fit = lagrange(fit, pool, graph, b, baseline, lcfg, trace)
    certificate = certify(graph, best_lam, b, c['lagrange']['certificate_denominator'])
    lagrange_seconds = time.monotonic() - started
    assert primal is not None, 'no generated primal'
    pcfg = {**c['polish'], 'trials': job['trials'] or c['polish']['trials']}
    results = {}
    for name, start in (('control', baseline), ('global', primal)):
        vocab, info = polish(fit, start, width, pcfg, m2)
        assert not set(vocab) & forbidden
        results[name] = {'vocab': vocab, 'polish': info}
    results['global_raw'] = {'vocab': primal, 'polish': None}
    folder = out / f'w{width}'; folder.mkdir(parents=True)
    seal = {}
    for name, r in results.items():
        (folder / f'{name}.json').write_text(json.dumps(r['vocab']) + '\n'); seal[name] = sha((folder / f'{name}.json').read_bytes())
    (folder / 'trace.json').write_text(json.dumps(trace) + '\n')
    (folder / 'fit-seal.json').write_text(json.dumps({'dictionaries_sha256': seal, 'validation_loaded': False}) + '\n')
    if job['iterations']:  # smoke: plumbing and timing on dev-fit only; validation is never opened
        smoke = {'width': width, 'smoke': True, 'pool_entries': len(pool), 'occurrence_edges': int(len(graph.occ_entry)),
                 'lower_bound': lower, 'certificate': certificate, 'primal_fit': primal_fit, 'lagrange_seconds': lagrange_seconds,
                 'fit_selections': {k: exact_fit(fit, r['vocab']) for k, r in results.items()},
                 'polish': {k: r['polish'] for k, r in results.items()}}
        (folder / 'smoke.json').write_text(json.dumps(smoke, indent=1) + '\n')
        print(json.dumps(smoke), flush=True)
        return smoke
    # Validation is opened only now, after every dictionary of this width is sealed.
    val = analyze.load_sources(work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(val_ids)]})
    forbidden_all = forbidden | forbidden_strings(val)
    report = {'width': width, 'pool_entries': len(pool), 'occurrence_edges': int(len(graph.occ_entry)), 'learned_slots': b,
              'lagrange': {'best_real_lower_bound_fit_selections': lower, 'certificate': certificate,
                           'best_generated_primal_fit_selections': primal_fit, 'iterations': sum('iteration' in t and 'stop' not in t for t in trace),
                           'stop': next((t['stop'] for t in trace if 'stop' in t), None), 'seconds': lagrange_seconds,
                           'scope': 'valid lower bound on dev-fit selections for dictionaries of the 96 characters plus <= B pool entries'},
              'arms': {}}
    for name, r in results.items():
        rows, illegal, db = measure({**fit, **val}, r['vocab'], width, forbidden_all)
        fit_rows = [rows[str(p)] for p in fit_ids]; val_rows = [rows[str(p)] for p in val_ids]
        sel = sum(x['selections'] for x in val_rows)
        report['arms'][name] = {'entries': len(r['vocab']), 'dictionary_sha256': seal[name], 'dictionary_bytes': db, 'polish': r['polish'],
                                'illegal_entry_sha256': illegal,
                                'fit_selections': sum(x['selections'] for x in fit_rows),
                                'validation': {'selections': analyze.distribution([x['selections'] for x in val_rows]),
                                               'actions': analyze.distribution([x['actions'] for x in val_rows]),
                                               'single_character_fraction': sum(x['single_characters'] for x in val_rows) / sel,
                                               'package_bytes': db + sum(x['packet_bytes'] for x in val_rows)},
                                'per_problem_validation_actions': {str(p): rows[str(p)]['actions'] for p in val_ids}}
    (folder / 'results.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({'width': width, 'lower': lower, 'certified': certificate['integer_lower_bound'], 'primal_fit': primal_fit,
                      'arms': {k: (v['fit_selections'], v['validation']['actions']['total']) for k, v in report['arms'].items()}}), flush=True)
    return report


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--smoke', type=int, help='Lagrangian iterations and polish trials for a plumbing run (fit only matters)')
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=False)
    jobs = [{'width': w, 'work': str(a.work.resolve()), 'output': str(a.output.resolve()), 'iterations': a.smoke, 'trials': a.smoke} for w in (7, 8)]
    started = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(2, mp_context=multiprocessing.get_context('spawn')) as ex:
        reports = list(ex.map(arm, jobs))
    (a.output / 'results.json').write_text(json.dumps({'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'smoke': a.smoke,
                                                       'seconds': time.monotonic() - started, 'widths': reports}, indent=1) + '\n')


if __name__ == '__main__':
    main()
