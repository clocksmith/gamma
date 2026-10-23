"""The frozen minify-only control (FREEZE.md, contract.json).

  control.py --work DIR --output DIR/minify/run-v1 [--parallel N] [--smoke TRIALS]

Pools (one source per problem): O admitted original, Om terser-compacted original (O where Om
failed qualification), R shared-style rewrite. Search arms (12): each pool at 7 and 8 bits, fitted
on all 500 (F500) or on dev-fit 300 (Fdev); every arm starts from the fallback alphabet, refills
greedily and runs matched80-v3 exact local search with chosen-source span proposals only (no designed
forms), under the same trial cap. Fixed evaluations: the alphabet A, the prior style150-v2 D (P), and
every refitted dictionary applied to every pool (F500 dictionaries on all 500, Fdev on dev-val 100).
Every packet is decoded independently through the canonical codec.
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
v3, joint, v1, write = m2.v3, m2.joint, m2.v1, m2.write
ALPHABET = list(v3.base.ALPHABET)
VARIANT = {'O': 'original', 'Om': 'minified', 'R': 'style'}


def contract():
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    return c


def pools(work, c):
    """{'O'|'Om'|'R': {pid: {variant: text}}} and file metadata, every text bound to its pinned hash."""
    pin = c['inputs']; P, files = {k: {} for k in VARIANT}, {}
    receipt = json.loads((work / 'minify/receipt.json').read_text())
    assert sha((work / 'minify/receipt.json').read_bytes()) == pin['om_receipt_sha256']
    om_ok = {r['id']: r for r in receipt['rows'] if r['passed']}
    first = set(c['cohorts']['first-150'])
    for pid in c['ids']:
        o = work / 'population500' / f'{pid}.js'
        m = work / 'minify/om' / f'{pid}.js' if pid in om_ok else o
        r = work / ('style150' if pid in first else 'scale500') / 'submitted' / f'{pid}.js'
        for pool, f in (('O', o), ('Om', m), ('R', r)):
            text = f.read_text(); assert sha(text.encode()) == pin['source_sha256'][pool][str(pid)], (pool, pid)
            P[pool][pid] = {VARIANT[pool]: text}; files[(pid, VARIANT[pool])] = {'file': str(f)}
    return P, files


def report(state, ids, width):
    counts = sorted(len(state['parsed'][pid, state['chosen'][pid]]) for pid in ids)
    parts = [p for pid in ids for p in state['parsed'][pid, state['chosen'][pid]]]
    n, src = len(counts), sum(len(p.encode()) for p in parts)
    single = [p for p in parts if len(p) == 1]
    return {'problems': n, 'source_bytes': src, 'selections': sum(counts),
            'median': counts[n // 2] if n % 2 else (counts[n // 2 - 1] + counts[n // 2]) / 2,
            'p95': counts[math.ceil(.95 * n) - 1], 'worst': counts[-1],
            'within_32': sum(x <= 32 for x in counts), 'within_96': sum(x <= 96 for x in counts),
            'bytes_per_selection': src / len(parts),
            'single_character_selection_fraction': len(single) / len(parts),
            'single_character_byte_fraction': sum(len(p.encode()) for p in single) / src,
            'payload_bits': width * len(parts), 'packet_bytes': sum(41 + (width * x + 7) // 8 for x in counts)}


def evaluate(work, out, c, name, pool, width, vocab, ids, extra):
    """Exact parse of `pool` on `ids` with a fixed dictionary; packets saved and independently decoded."""
    P, files = pools(work, c)
    sources = {pid: P[pool][pid] for pid in ids}
    try:
        final = joint.evaluate(sources, vocab, width)
    except ValueError as e:  # e.g. a cross-applied entry equal to a whole program of this pool: recorded, not hidden
        res = {'name': name, 'pool': pool, 'width': width, **extra, 'error': str(e)}
        write(out / f'{name}-result.json', res); return res
    met = v3.save(out, name, sources, files, final, width, f'minify-control-{name}', v1.provenance_of([]), {'pool': pool, **extra})
    res = {'name': name, 'pool': pool, 'width': width, **extra, 'entries': len(final['vocab']), 'dictionary_bytes': final['dictionary_bytes'],
           'package_bytes': final['package_bytes'], 'whole_program_literals': met['whole_program_literals'],
           'report': report(final, sorted(ids), width),
           'by_cohort': {k: report(final, [i for i in sorted(ids) if i in set(v)], width) for k, v in c['cohorts'].items()
                         if any(i in set(v) for i in ids)},
           'per_problem': {str(pid): len(final['parsed'][pid, final['chosen'][pid]]) for pid in sorted(ids)}}
    write(out / f'{name}-result.json', res)
    return res


def decompose(sel, x, y):
    """Pools x -> y. sel[(dictionary, pool)] = selections. Both paths, since the split depends on the order."""
    dx, dy = f'D_{x}', f'D_{y}'
    return {'total': sel[dy, y] - sel[dx, x],
            'via_D_x': {'source': sel[dx, y] - sel[dx, x], 'adaptation': sel[dy, y] - sel[dx, y]},
            'via_D_y': {'adaptation': sel[dy, x] - sel[dx, x], 'source': sel[dy, y] - sel[dy, x]}}


def search(job):
    os.environ['PYTHONHASHSEED'] = '0'
    work, out, c = Path(job['work']), Path(job['out']), job['c']
    pool, width, fit = job['pool'], job['width'], job['fit']
    P, _ = pools(work, c)
    fit_ids = c['ids'] if fit == 'F500' else c['partition']['dev_fit']
    fitted = {pid: P[pool][pid] for pid in fit_ids}
    s = c['search']; nb = {**s['neighborhood'], 'refill_shortlist': s['refill_shortlist']}
    budget = v3.Budget({'trials': job['trials'], 'seconds': s['seconds']})
    propose = m2.hybrid_chosen([], fitted)  # spans only: no designed forms for any arm
    empty = v3.evaluate(fitted, list(ALPHABET), width, None, budget)
    state, _ = v3.refill(fitted, empty, width, propose, nb, nb['refill_shortlist'], budget)
    log = []
    state, stop = v3.local_search(fitted, state, width, propose, s['neighborhood'], budget, log)
    name = f'{pool}-{fit}-{2 ** width}'
    folder = out / 'dictionaries'; folder.mkdir(exist_ok=True)
    write(folder / f'{name}.json', state['vocab'])
    write(out / f'{name}-trace.json', {'rounds': log, 'stop': stop})
    return {'name': name, 'pool': pool, 'width': width, 'fit': fit, 'stop': stop, 'trials': budget.trials, 'seconds': budget.elapsed(),
            'dictionary_sha256': sha((folder / f'{name}.json').read_bytes())}


def fixed(job):
    os.environ['PYTHONHASHSEED'] = '0'
    work, out, c = Path(job['work']), Path(job['out']), job['c']
    return evaluate(work, out, c, job['name'], job['pool'], job['width'], job['vocab'], job['ids'], job['extra'])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--parallel', type=int, default=20); ap.add_argument('--smoke', type=int)
    a = ap.parse_args(); c = contract(); a.output.mkdir(parents=True, exist_ok=False)
    out = a.output.resolve(); base = {'work': str(a.work.resolve()), 'out': str(out), 'c': c}
    trials = a.smoke or c['search']['trials']
    phase1 = [{**base, 'pool': p, 'width': w, 'fit': f, 'trials': trials} for f in ('F500', 'Fdev') for w in (7, 8) for p in VARIANT]
    start = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(a.parallel) as ex:
        searched = list(ex.map(search, phase1))
        prior = {w: json.loads(Path(c['inputs']['prior_dictionaries'][str(2 ** w)]).read_text()) for w in (7, 8)}
        jobs = []
        for f, ids in (('F500', c['ids']), ('Fdev', c['partition']['dev_val'])):
            for w in (7, 8):
                dicts = {'A': list(ALPHABET), 'P': prior[w]}
                dicts.update({f'D_{r["pool"]}': json.loads((out / 'dictionaries' / f'{r["name"]}.json').read_text())
                              for r in searched if r['fit'] == f and r['width'] == w})
                for dname, vocab in dicts.items():
                    for p in VARIANT:
                        jobs.append({**base, 'name': f'{f}-{2 ** w}-{dname}-on-{p}', 'pool': p, 'width': w, 'vocab': vocab, 'ids': ids,
                                     'extra': {'fit': f, 'dictionary': dname, 'diagonal': dname == f'D_{p}'}})
        evaluated = list(ex.map(fixed, jobs))
    write(out / 'results.json', {'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'seconds': time.monotonic() - start,
                                 'smoke_trials': a.smoke, 'search': searched, 'evaluations': evaluated})
    for r in searched:
        print(f"{r['name']:14} trials {r['trials']:6} {r['seconds']:7.0f}s {r['stop']}")
    for e in evaluated:
        s = e['report']
        print(f"{e['name']:26} sel {s['selections']:7} med {s['median']:6} p95 {s['p95']:5} B/sel {s['bytes_per_selection']:.2f} "
              f"1ch {s['single_character_selection_fraction']:.3f} src {s['source_bytes']:7} pkg {e['package_bytes']}")


if __name__ == '__main__':
    main()
