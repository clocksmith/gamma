"""Measure the frozen style150-v1 arms (contract.json) and verify every packet.

  measure.py --work DIR --output DIR/style150/run-v1 [--parallel N] [--smoke TRIALS]

Arms per width (7 and 8 bits; 128 and 256 entries):
  A   existing pool (S1), starting dictionary D0 fixed           exact-parse control
  A0  originals only (S0), D0 fixed                              one fixed source per problem
  B   S1 plus qualified rewrites (S2), D0 fixed                  source-only effect
  C   S1, local search from D0                                    dictionary-only effect
  D   S2, local search from D0                                    joint effect
  E   rewrites only (original where a rewrite failed), search     style alone
  CH, DH  C and D fitted on the 120 training problems only: start from the fallback alphabet,
      greedy refill and local search on training problems; the final dictionary is then fixed and
      measured on the 30 held-out problems (and on all 150)
Search is matched80-v3 local_search with the hybrid proposer (3/4 joint-v1 span order, 1/4 the
style guide's designed forms), identical neighborhoods and trial caps for every search arm.
"""
import argparse, concurrent.futures, hashlib, importlib.util, json, math, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(LIT / 'admission500-v1'))
sha = lambda b: hashlib.sha256(b).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


v3 = module('matched80_v3', LIT / 'matched80-v3/run.py')
joint, v1, write = v3.joint, v3.v1, v3.write


def contract():
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    return c


def pools(work, c):
    import style
    req = json.loads((work / 'style150/pool/requalification.json').read_text())
    assert sha((work / 'style150/pool/requalification.json').read_bytes()) == c['inputs']['pool_requalification_sha256']
    ss, meta = style.load_pool()
    s1, s0, files = {}, {}, {}
    for r in req['rows']:
        if not r['passed']: continue
        text = ss[r['id']][r['variant']]; assert sha(text.encode()) == r['sha256']
        s1.setdefault(r['id'], {})[r['variant']] = text; files[(r['id'], r['variant'])] = {'file': meta[r['id'], r['variant']]['file']}
    for pid, vs in s1.items():
        orig = vs.get('original') or vs.get('old-original') or sorted(vs.items())[0][1]
        s0[pid] = {'original' if 'original' in vs else sorted(vs)[0]: orig}
    rewrites = {}
    q = work / 'style150/qualification'
    for f in sorted(q.glob('*.json')):
        r = json.loads(f.read_text())
        if r['passed']:
            text = (work / 'style150/submitted' / f"{r['id']}.js").read_text(); assert sha(text.encode()) == r['sha256']
            rewrites[r['id']] = text; files[(r['id'], 'style')] = {'file': str(work / 'style150/submitted' / f"{r['id']}.js")}
    s2 = {pid: {**vs, **({'style': rewrites[pid]} if pid in rewrites else {})} for pid, vs in s1.items()}
    se = {pid: ({'style': rewrites[pid]} if pid in rewrites else dict(s0[pid])) for pid in s1}
    return {'S0': s0, 'S1': s1, 'S2': s2, 'SE': se}, files, len(rewrites)


def summary(state, sources, ids, width):
    counts = sorted(len(state['parsed'][pid, state['chosen'][pid]]) for pid in ids)
    parts = [p for pid in ids for p in state['parsed'][pid, state['chosen'][pid]]]
    chars = sum(len(p.encode()) for p in parts)
    return {'problems': len(ids), 'selections': sum(counts), 'median': counts[len(counts) // 2] if len(counts) % 2 else (counts[len(counts) // 2 - 1] + counts[len(counts) // 2]) / 2,
            'p95': counts[math.ceil(.95 * len(counts)) - 1], 'worst': counts[-1],
            'single_character_selection_fraction': sum(len(p) == 1 for p in parts) / len(parts),
            'source_bytes': chars, 'bytes_per_selection': chars / len(parts),
            'chosen_style': sum(state['chosen'][pid] == 'style' for pid in ids),
            'packet_bytes': sum(41 + (width * n + 7) // 8 for n in counts)}


def run_arm(job):
    work, out, c, name, width, pool, search, fit = (Path(job['work']), Path(job['out']), job['c'], job['name'], job['width'],
                                                     job['pool'], job['search'], job['fit'])
    os.environ['PYTHONHASHSEED'] = '0'
    P, files, _ = pools(work, c); sources = P[pool]
    size = 2 ** width; designed = c['designed_forms']
    d0 = json.loads(Path(c['inputs']['start_dictionaries'][str(size)]).read_text())
    budget = v3.Budget({'trials': job['trials'], 'seconds': c['search']['seconds']})
    fit_ids = sorted(sources) if fit == 'all' else sorted(c['split']['train'])
    fitted = {pid: sources[pid] for pid in fit_ids}
    if fit == 'train':
        # Held-out arms never see held-out problems: start from the fallback alphabet, refill greedily on training problems.
        nb = {**c['search']['neighborhood'], 'refill_shortlist': c['search']['refill_shortlist']}
        empty = v3.evaluate(fitted, list(v3.FALLBACK), width, None, budget)
        initial, _ = v3.refill(fitted, empty, width, v3.hybrid_proposer(designed, fitted), nb, nb['refill_shortlist'], budget)
    else:
        initial, _ = v3.prune(fitted, v3.evaluate(fitted, d0, width, None, budget), width, budget)
    log, stop = [], 'fixed'
    state = initial
    if search:
        state, stop = v3.local_search(fitted, initial, width, v3.hybrid_proposer(designed, fitted), c['search']['neighborhood'], budget, log)
    final = joint.evaluate(sources, state['vocab'], width)  # every arm reported on all 150 with its final dictionary
    folder = out / name
    meta = {k: v for k, v in files.items()}
    v3.save(out, name, sources, meta, final, width, f'style150-{name}', v1.provenance_of(designed),
            {'arm': name, 'pool': pool, 'search': search, 'fit': fit})
    res = {'arm': name, 'width': width, 'pool': pool, 'search': search, 'fit': fit, 'stop': stop, 'trials': budget.trials,
           'seconds': budget.elapsed(), 'entries': len(final['vocab']), 'dictionary_bytes': final['dictionary_bytes'],
           'package_bytes': final['package_bytes'], 'all150': summary(final, sources, sorted(sources), width),
           'per_problem': {str(pid): len(final['parsed'][pid, final['chosen'][pid]]) for pid in sorted(sources)},
           'chosen': {str(pid): final['chosen'][pid] for pid in sorted(sources)}}
    if fit == 'train':
        res['train120'] = summary(final, sources, sorted(c['split']['train']), width)
        res['heldout30'] = summary(final, sources, sorted(c['split']['heldout']), width)
    write(out / f'{name}-trace.json', {'initial': joint.brief(initial), 'rounds': log, 'stop': stop})
    write(out / f'{name}-result.json', res)
    return res


def jobs(work, out, c, smoke):
    js = []
    for width in (7, 8):
        size = 2 ** width; t = smoke or c['search']['trials']
        for name, pool, search, fit in [('A', 'S1', False, 'all'), ('A0', 'S0', False, 'all'), ('B', 'S2', False, 'all'),
                                        ('C', 'S1', True, 'all'), ('D', 'S2', True, 'all'), ('E', 'SE', True, 'all'),
                                        ('CH', 'S1', True, 'train'), ('DH', 'S2', True, 'train')]:
            js.append({'work': str(work), 'out': str(out), 'c': c, 'name': f'{name}-{size}', 'width': width, 'pool': pool,
                       'search': search, 'fit': fit, 'trials': t})
    return js


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--parallel', type=int, default=16); ap.add_argument('--smoke', type=int)
    a = ap.parse_args(); c = contract(); a.output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(a.parallel) as pool:
        results = list(pool.map(run_arm, jobs(a.work.resolve(), a.output.resolve(), c, a.smoke)))
    write(a.output / 'results.json', {'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'seconds': time.monotonic() - start,
                                      'smoke_trials': a.smoke, 'arms': results})
    for r in results:
        s = r['all150']; print(f"{r['arm']:8} sel {s['selections']:6} med {s['median']:6} p95 {s['p95']:4} char {s['single_character_selection_fraction']:.3f} pkg {r['package_bytes']} trials {r['trials']} {r['stop']}"
                               + (f" | heldout {r['heldout30']['selections']}" if 'heldout30' in r else ''))


if __name__ == '__main__':
    main()
