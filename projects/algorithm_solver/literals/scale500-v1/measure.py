"""Vocabulary search at scale on the frozen 500 (contract.json), with a held-out slice.

  measure.py --work DIR --output DIR/scale500/run-v1 [--parallel N] [--smoke TRIALS]

Sources:
  P1  the first 150's style150 pool (998 requalified alternatives plus 150 shared-style rewrites)
      and each other problem's admitted source
  P2  P1 plus each qualified shared-style rewrite of the other 350
Arms per width (7 and 8 bits):
  W1, W2   local search on P1, P2 from the style150-v2 D dictionary of that size
  I2-s1..s5  seeded iterated local search from W2 (matched80-v3 iterated, seeds 1-5)
  H1, H2   P1, P2 fitted on the 400 training problems only (fallback alphabet, greedy refill,
           local search), the final dictionary then fixed and measured on the 100 held-out problems
All search uses matched80-v3 local_search / iterated with the style150-v2 chosen-source hybrid
proposer and STYLE.md designed forms. Every packet is decoded independently.
"""
import argparse, concurrent.futures, hashlib, importlib.util, json, math, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
sys.path.insert(0, str(LIT / 'style150-v1')); sys.path.insert(0, str(LIT / 'admission500-v1'))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


m2 = module('style150_v2_measure', LIT / 'style150-v2/measure.py')
m1, v3, joint, v1, write = m2.m1, m2.v3, m2.joint, m2.v1, m2.write


def contract():
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    return c


def pools(work, c):
    import rewrite
    rows = rewrite.population(work)
    c1 = m1.contract(); P150, files, _ = m1.pools(work, c1)
    p1 = {pid: dict(vs) for pid, vs in P150['S2'].items()}
    for pid in rows:
        p1[pid] = {'admitted': (work / 'population500' / f'{pid}.js').read_text()}
        files[(pid, 'admitted')] = {'file': str(work / 'population500' / f'{pid}.js')}
    assert len(p1) == 500
    p2 = {pid: dict(vs) for pid, vs in p1.items()}
    q = work / 'scale500/qualification'; styled = 0
    for f in sorted(q.glob('*.json')) if q.exists() else []:
        r = json.loads(f.read_text())
        if r['passed']:
            text = (work / 'scale500/submitted' / f"{r['id']}.js").read_text(); assert sha(text.encode()) == r['sha256']
            p2[r['id']]['style'] = text; files[(r['id'], 'style')] = {'file': str(work / 'scale500/submitted' / f"{r['id']}.js")}; styled += 1
    return {'P1': p1, 'P2': p2}, files, styled


def m1_report(state, ids, width):
    counts = sorted(len(state['parsed'][pid, state['chosen'][pid]]) for pid in ids)
    parts = [p for pid in ids for p in state['parsed'][pid, state['chosen'][pid]]]
    n = len(counts)
    return {'problems': n, 'selections': sum(counts),
            'median': counts[n // 2] if n % 2 else (counts[n // 2 - 1] + counts[n // 2]) / 2,
            'p95': counts[math.ceil(.95 * n) - 1], 'worst': counts[-1],
            'single_character_selection_bit_fraction': sum(len(p) == 1 for p in parts) / len(parts),
            'source_bytes': sum(len(p.encode()) for p in parts), 'payload_bits': width * len(parts),
            'within_median_32': sum(x <= 32 for x in counts), 'within_96': sum(x <= 96 for x in counts)}


def run_arm(job):
    for name, fn in (('hybrid', m2.hybrid_chosen),): v3.hybrid_proposer = fn
    work, out, c = Path(job['work']), Path(job['out']), job['c']
    name, width, pool, kind = job['name'], job['width'], job['pool'], job['kind']
    P, files, styled = pools(work, c); sources = P[pool]; size = 2 ** width
    designed = c['designed_forms']; nb = {**c['search']['neighborhood'], 'refill_shortlist': c['search']['refill_shortlist']}
    budget = v3.Budget({'trials': job['trials'], 'seconds': c['search']['seconds']})
    log, extra = [], {}
    if kind == 'heldout':
        fitted = {pid: sources[pid] for pid in c['split']['train']}
        empty = v3.evaluate(fitted, list(v3.FALLBACK), width, None, budget)
        state, _ = v3.refill(fitted, empty, width, m2.hybrid_chosen(designed, fitted), nb, nb['refill_shortlist'], budget)
        state, stop = v3.local_search(fitted, state, width, m2.hybrid_chosen(designed, fitted), c['search']['neighborhood'], budget, log)
    elif kind == 'wide':
        d0 = json.loads(Path(c['inputs']['start_dictionaries'][str(size)]).read_text())
        start, _ = v3.prune(sources, v3.evaluate(sources, d0, width, None, budget), width, budget)
        state, stop = v3.local_search(sources, start, width, m2.hybrid_chosen(designed, sources), c['search']['neighborhood'], budget, log)
    else:  # ils
        vocab = json.loads((out / f"W2-{size}" / 'dictionary.json').read_text())
        start, _ = v3.prune(sources, v3.evaluate(sources, vocab, width, None, budget), width, budget)
        state, log = v3.iterated(sources, start, width, m2.hybrid_chosen(designed, sources), nb, c['ils']['kick'][str(size)], job['seed'], budget)
        stop = budget.reason(); assert v3.cost(state) <= v3.cost(start)
    final = joint.evaluate(sources, state['vocab'], width)
    v3.save(out, name, sources, files, final, width, f'scale500-{name}', v1.provenance_of(designed), {'arm': name, 'pool': pool, 'kind': kind})
    ids = sorted(sources)
    res = {'arm': name, 'width': width, 'pool': pool, 'kind': kind, 'seed': job.get('seed'), 'stop': stop, 'trials': budget.trials,
           'seconds': budget.elapsed(), 'entries': len(final['vocab']), 'dictionary_bytes': final['dictionary_bytes'],
           'package_bytes': final['package_bytes'], 'styled_rewrites_available': styled,
           'all500': m1_report(final, ids, width),
           'by_cohort': {k: m1_report(final, [i for i in ids if i in set(c['cohorts'][k])], width) for k in c['cohorts']},
           'per_problem': {str(pid): len(final['parsed'][pid, final['chosen'][pid]]) for pid in ids},
           'chosen': {str(pid): final['chosen'][pid] for pid in ids}}
    if kind == 'heldout':
        res['train400'] = m1_report(final, sorted(c['split']['train']), width)
        res['heldout100'] = m1_report(final, sorted(c['split']['heldout']), width)
    write(out / f'{name}-trace.json', {'rounds_or_kicks': log, 'stop': stop})
    write(out / f'{name}-result.json', res)
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--parallel', type=int, default=20); ap.add_argument('--smoke', type=int)
    a = ap.parse_args(); c = contract(); a.output.mkdir(parents=True, exist_ok=False)
    base = {'work': str(a.work.resolve()), 'out': str(a.output.resolve()), 'c': c}
    t = lambda k: a.smoke or c['search']['trials'][k]
    phase1 = [{**base, 'name': f'{n}-{2**w}', 'width': w, 'pool': p, 'kind': k, 'trials': t(k)}
              for w in (7, 8) for n, p, k in (('W1', 'P1', 'wide'), ('W2', 'P2', 'wide'), ('H1', 'P1', 'heldout'), ('H2', 'P2', 'heldout'))]
    phase2 = [{**base, 'name': f'I2-{2**w}-s{s}', 'width': w, 'pool': 'P2', 'kind': 'ils', 'seed': s, 'trials': t('ils')}
              for w in (7, 8) for s in c['ils']['seeds']]
    start = time.monotonic(); results = []
    with concurrent.futures.ProcessPoolExecutor(a.parallel) as pool:
        results += list(pool.map(run_arm, phase1))
        results += list(pool.map(run_arm, phase2))
    write(a.output / 'results.json', {'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'seconds': time.monotonic() - start,
                                      'smoke_trials': a.smoke, 'arms': results})
    for r in results:
        s = r['all500']
        print(f"{r['arm']:12} sel {s['selections']:7} med {s['median']:6} p95 {s['p95']:5} char {s['single_character_selection_bit_fraction']:.3f} pkg {r['package_bytes']} trials {r['trials']} {r['stop']}"
              + (f" | heldout {r['heldout100']['selections']} med {r['heldout100']['median']}" if 'heldout100' in r else ''))


if __name__ == '__main__':
    main()
