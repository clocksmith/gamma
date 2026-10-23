"""structural-v1: typed components against literal-only dictionaries on dev-val (FREEZE.md, contract.json).

  measure.py audit --work DIR                       dev-fit 300 only: per-pool component support and guard rejections
  measure.py run   --work DIR --output DIR/structural/run-v1 [--parallel N] [--smoke TRIALS]

Arms: pool (O, Om, R; minify-control-v1 sources and partition) x representation (L literal, T typed) x width
(7, 8). Every arm fits on dev-fit 300 from the fallback alphabet (T also starts with END and the pool's
admissible components), greedy refill, matched80-v3 exact local search, 60,000 trials, then is measured
unchanged on dev-val 100. The final held-out 100 is not opened. L arms must reproduce minify-control-v1's
Fdev arms exactly; T arms differ only by components and the typed parse. Every T packet is decoded by
decoder.mjs; every L packet by the canonical codec.
"""
import argparse, concurrent.futures, hashlib, importlib.util, json, math, os, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
sys.path.insert(0, str(HERE))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


control = module('minify_control', LIT / 'minify-control-v1/control.py')
import typed
v3, joint, v1, m2, write = control.v3, control.joint, control.v1, control.m2, control.write
ALPHABET = control.ALPHABET


def inputs(work):
    c = control.contract()
    P, files = control.pools(work, c)
    return c, P, files


def match_table(P, ids):
    """Matches for dev-fit and dev-val sources only; the final held-out 100 never pass through the matcher."""
    texts = {f'{pool}:{pid}': next(iter(P[pool][pid].values())) for pool in P for pid in ids}
    rows = typed.find_matches(texts)
    return {texts[k]: r['matches'] for k, r in rows.items()}, rows


def audit(work):
    c, P, _ = inputs(work)
    fit = c['partition']['dev_fit']
    texts = {f'{pool}:{pid}': next(iter(P[pool][pid].values())) for pool in P for pid in fit}
    rows = typed.find_matches(texts)
    out = {}
    for pool in P:
        support, instances, near, rejected = Counter(), Counter(), Counter(), Counter()
        for pid in fit:
            text = next(iter(P[pool][pid].values())); r = rows[f'{pool}:{pid}']
            seen = set()
            for m in r['matches']:
                if typed.admissible(m, text): instances[m['c']] += 1; seen.add(m['c'])
                else: near[m['c']] += 1
            support.update(seen)
            for cid, reasons in r['rejected'].items():
                for reason, n in reasons.items(): rejected[f'{cid}: {reason}'] += n
        out[pool] = {'admissible': sorted(cid for cid in typed.COMPONENTS if support[cid] >= 2),
                     'support_problems': dict(sorted(support.items())), 'instances': dict(sorted(instances.items())),
                     'near_whole_rejected': dict(sorted(near.items())), 'guard_rejections': dict(sorted(rejected.items()))}
    d = work / 'structural'; d.mkdir(parents=True, exist_ok=True)
    write(d / 'audit.json', {'partition': 'dev_fit', 'problems': len(fit), 'pools': out})
    for pool, a in out.items():
        print(pool, 'admissible', len(a['admissible']), a['admissible'])
        print('   support', a['support_problems'])
    print(sha((d / 'audit.json').read_bytes()))


def report(state, sources, ids, width):
    counts = sorted(len(state['parsed'][pid, state['chosen'][pid]]) for pid in ids)
    codes = [s for pid in ids for s in state['parsed'][pid, state['chosen'][pid]]]
    lits = [s for s in codes if not typed.is_code(s)]
    single = [s for s in lits if len(s) == 1]
    src = sum(len(sources[pid][state['chosen'][pid]].encode()) for pid in ids)
    n = len(counts)
    return {'problems': n, 'source_bytes': src, 'selections': len(codes),
            'median': counts[n // 2] if n % 2 else (counts[n // 2 - 1] + counts[n // 2]) / 2,
            'p95': counts[math.ceil(.95 * n) - 1], 'worst': counts[-1],
            'within_32': sum(x <= 32 for x in counts), 'within_96': sum(x <= 96 for x in counts),
            'bytes_per_selection': src / len(codes),
            'single_character_selection_fraction': len(single) / len(codes),
            'single_character_byte_fraction': sum(len(s.encode()) for s in single) / src,
            'component_code_fraction': sum(typed.is_code(s) and s != typed.END for s in codes) / len(codes),
            'end_code_fraction': sum(s == typed.END for s in codes) / len(codes),
            'packet_bytes': sum(41 + (width * x + 7) // 8 for x in counts)}


def arm(job):
    os.environ['PYTHONHASHSEED'] = '0'
    work, out, s = Path(job['work']), Path(job['out']), job['search']
    pool, rep, width = job['pool'], job['rep'], job['width']
    c, P, files = inputs(work)
    fit_ids, val_ids = c['partition']['dev_fit'], c['partition']['dev_val']
    matches, _ = match_table(P, fit_ids + val_ids)
    typed.install(joint, matches)
    fitted = {pid: P[pool][pid] for pid in fit_ids}
    nb = {**s['neighborhood'], 'refill_shortlist': s['refill_shortlist']}
    budget = v3.Budget({'trials': job['trials'], 'seconds': s['seconds']})
    allowed = job['admissible'] if rep == 'T' else []
    if rep == 'T':
        start = list(ALPHABET) + [typed.code(x) for x in allowed] + [typed.END]
        propose = lambda srcs, st, limit, fraction: typed.proposals(srcs, st, limit, allowed)
    else:
        start = list(ALPHABET)
        propose = m2.hybrid_chosen([], fitted)
    state = v3.evaluate(fitted, start, width, None, budget)
    state, _ = v3.refill(fitted, state, width, propose, nb, nb['refill_shortlist'], budget)
    log = []
    state, stop = v3.local_search(fitted, state, width, propose, s['neighborhood'], budget, log)
    name = f'{rep}-{pool}-{2 ** width}'
    val = {pid: P[pool][pid] for pid in val_ids}
    final = joint.evaluate(val, state['vocab'], width)
    if rep == 'T':
        man = typed.save_and_verify(out / name, val, final, width)
        verified = man['verified']
    else:
        met = v3.save(out, name, val, files, final, width, f'structural-{name}', v1.provenance_of([]), {'pool': pool, 'rep': rep})
        verified = met['covered_programs']
    vocab = final['vocab']
    used = Counter(x for pid in val_ids for x in final['parsed'][pid, final['chosen'][pid]] if typed.is_code(x) and x != typed.END)
    decoder = len((HERE / 'decoder.mjs').read_bytes()) if rep == 'T' else 0
    res = {'arm': name, 'pool': pool, 'rep': rep, 'width': width, 'stop': stop, 'trials': budget.trials, 'seconds': budget.elapsed(),
           'entries': len(vocab), 'components_in_dictionary': sorted(x[1:] for x in vocab if typed.is_code(x) and x != typed.END),
           'end_in_dictionary': typed.END in vocab, 'component_uses_devval': {k[1:]: v for k, v in sorted(used.items())},
           'dictionary_bytes': final['dictionary_bytes'], 'package_bytes': final['package_bytes'], 'decoder_bytes': decoder,
           'package_bytes_with_decoder': final['package_bytes'] + decoder, 'packets_verified': verified,
           'dictionary_sha256': sha(json.dumps(vocab).encode()),
           'devval': report(final, val, sorted(val_ids), width),
           'per_problem': {str(pid): len(final['parsed'][pid, final['chosen'][pid]]) for pid in sorted(val_ids)}}
    (out / 'dictionaries').mkdir(exist_ok=True)
    write(out / 'dictionaries' / f'{name}.json', vocab)
    write(out / f'{name}-trace.json', {'rounds': log, 'stop': stop})
    write(out / f'{name}-result.json', res)
    return res


def run(work, output, parallel, smoke):
    sc = json.loads((HERE / 'contract.json').read_text())
    for rel, h in sc['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    assert sha((work / 'structural/audit.json').read_bytes()) == sc['inputs']['audit_sha256']
    aud = json.loads((work / 'structural/audit.json').read_text())['pools']
    output.mkdir(parents=True, exist_ok=False); out = output.resolve()
    jobs = [{'work': str(work), 'out': str(out), 'search': sc['search'], 'pool': p, 'rep': r, 'width': w,
             'admissible': aud[p]['admissible'], 'trials': smoke or sc['search']['trials']}
            for w in (7, 8) for p in ('O', 'Om', 'R') for r in ('L', 'T')]
    start = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(parallel) as ex:
        results = list(ex.map(arm, jobs))
    write(out / 'results.json', {'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'seconds': time.monotonic() - start,
                                 'smoke_trials': smoke, 'arms': results})
    for r in results:
        d = r['devval']
        print(f"{r['arm']:10} devval sel {d['selections']:6} med {d['median']:6} p95 {d['p95']:4} 1ch {d['single_character_selection_fraction']:.3f} "
              f"comp {d['component_code_fraction']:.3f} end {d['end_code_fraction']:.3f} pkg {r['package_bytes_with_decoder']} trials {r['trials']} {r['stop']}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=['audit', 'run']); ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--output', type=Path); ap.add_argument('--parallel', type=int, default=12); ap.add_argument('--smoke', type=int)
    a = ap.parse_args()
    audit(a.work.resolve()) if a.step == 'audit' else run(a.work.resolve(), a.output, a.parallel, a.smoke)
