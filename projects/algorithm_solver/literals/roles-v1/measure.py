"""roles-v1: declare each identifier once, reference it by role (FREEZE.md, contract.json).

  measure.py audit   --work DIR                       dev-fit 300 only: role statistics, slot ranking, full-rename execution check
  measure.py run     --work DIR --output DIR/roles/run-v1 [--parallel N] [--smoke TRIALS]   (smoke: measured on 40 dev-fit)
  measure.py execute --work DIR --run DIR/roles/run-v1 [--workers N]   execution tests on every decoded dev-val program

Arms: pool (Om minified, R shared style; minify-control-v1 sources and partition) x representation (L literal,
B bind, N rename-only) x width (7, 8). Every arm fits on dev-fit 300 from the fallback alphabet (B also starts with
END), greedy refill, matched80-v3 exact local search, 60,000 trials, then is measured unchanged on dev-val 100. The
final held-out 100 is not opened: its sources never pass through the role classifier and no measurement includes
them. L arms must reproduce minify-control-v1's Fdev arms exactly.
"""
import argparse, concurrent.futures, hashlib, importlib.util, json, math, os, re, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
sys.path.insert(0, str(HERE))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


control = module('minify_control', LIT / 'minify-control-v1/control.py')
import binding
v3, joint, v1, m2, write = control.v3, control.joint, control.v1, control.m2, control.write
ALPHABET = control.ALPHABET
POOLS = ('Om', 'R')
REPS = ('L', 'B', 'N')


def inputs(work):
    c = control.contract()
    P, files = control.pools(work, c)
    rows = {r['id']: r for r in json.loads((work / 'population500/manifest.json').read_text())['rows']}
    return c, P, files, rows


def interface(pool, row):
    """Names the entry interface fixes: the entry function, or the class an entry like `new Solution().f(...)` builds."""
    if pool == 'R':
        return {'entry': 'solve', 'names': ['solve']}
    e = row['entry']
    if re.fullmatch(r'[A-Za-z_$][\w$]*', e):
        return {'entry': e, 'names': [e]}
    m = re.fullmatch(r'\(\.\.\.a\)=>new ([A-Za-z_$][\w$]*)\(\)\.[A-Za-z_$][\w$]*\(\.\.\.a\)', e)
    assert m, e
    return {'entry': e, 'names': [m.group(1)]}


def entry(pool, row):
    return 'solve' if pool == 'R' else row['entry']


def records(P, rows, pool, ids):
    """{text: role record} for this pool's sources of `ids` only."""
    texts = {str(pid): (next(iter(P[pool][pid].values())), interface(pool, rows[pid])) for pid in ids}
    got = binding.classify(texts)
    return {texts[k][0]: got[k] for k in texts}, got


def parity_all(work, jobs, workers):
    """Strict parity on every frozen case, {key: (text, entry, row)} -> {key: result}. A sandbox kill with no parity
    mismatch (infrastructure, not behavior) is rerun once serially; both attempts are kept and the rerun decides."""
    minify = module('minify', LIT / 'minify-control-v1/minify.py')
    style, shim = minify.style, minify.shim(work)
    check = lambda k: style.parity(shim, k[1], jobs[k][0], jobs[k][1], jobs[k][2], None)
    record = lambda r: {'passed': r[0], 'checks': f'{r[1]}/{r[2]}', 'cases': r[2], 'failure': None if r[0] else (r[3][0] if r[3] else 'unknown')}
    out = {}
    with concurrent.futures.ProcessPoolExecutor(workers) as ex:
        futs = {ex.submit(style.parity, shim, k[1], *v, None): k for k, v in jobs.items()}
        for f in concurrent.futures.as_completed(futs):
            out[futs[f]] = record(f.result())
    for k, r in sorted(out.items(), key=str):
        bad = r['failure']
        if not r['passed'] and isinstance(bad, dict) and str(bad.get('error', '')).startswith('sandbox failure') and 'parity' not in bad:
            out[k] = {**record(check(k)), 'first_attempt': r}
    return out


def audit(work, workers):
    c, P, _, rows = inputs(work)
    fit = c['partition']['dev_fit']
    out = {}
    d = work / 'roles'; d.mkdir(parents=True, exist_ok=True)
    rename_jobs = []
    for pool in POOLS:
        recs, by_id = records(P, rows, pool, fit)
        binding.install(joint, 'N', recs)
        per_role = {r: Counter() for r in binding.ROLES}
        occurrences, excluded = Counter(), Counter()
        for pid in fit:
            rec = by_id[str(pid)]
            names = Counter(n['role'] for n in rec['names'])
            for r in binding.ROLES: per_role[r][names[r]] += 1
            for n in rec['names']: occurrences[n['role']] += len(n['spans'])
            for k, v in rec['excluded'].items(): excluded[k] += len(v)
            text = next(iter(P[pool][pid].values()))
            full = {n['slot'] for n in rec['names']}
            rename_jobs.append((pool, pid, binding.renamed(text, rec, full), rows[pid]))
        ranking = binding.slot_ranking({pid: P[pool][pid] for pid in fit})
        out[pool] = {'names_per_program_by_role': {r: dict(sorted(v.items())) for r, v in per_role.items()},
                     'occurrences_by_role': dict(occurrences), 'excluded_names': dict(excluded),
                     'bound_names': sum(len(by_id[str(p)]['names']) for p in fit),
                     'bound_occurrences': sum(occurrences.values()),
                     'slots_with_support_2': len(ranking),
                     'top_slots': [list(binding.slot_of(s)) for s in ranking[:32]]}
    # Plumbing check on dev-fit only: rename every bound name; each renamed program must pass every frozen case.
    results = {f'{pool}:{pid}': r for (pool, pid, _), r in
               parity_all(work, {(pool, pid, None): (text, entry(pool, row), row) for pool, pid, text, row in rename_jobs}, workers).items()}
    for pool in POOLS:
        rs = [v for k, v in results.items() if k.startswith(pool + ':')]
        out[pool]['full_rename_execution'] = {'programs': len(rs), 'passed': sum(r['passed'] for r in rs),
                                              'failures': {k: v for k, v in sorted(results.items()) if k.startswith(pool + ':') and not v['passed']}}
    write(d / 'audit.json', {'partition': 'dev_fit', 'problems': len(fit), 'pools': out})
    for pool, a in out.items():
        print(pool, 'bound', a['bound_names'], 'occurrences', a['bound_occurrences'], a['occurrences_by_role'], 'excluded', a['excluded_names'])
        print('   slots(support>=2)', a['slots_with_support_2'], 'rename passed', a['full_rename_execution']['passed'], '/', a['full_rename_execution']['programs'])
    print(sha((d / 'audit.json').read_bytes()))


def quantile(xs, q):
    return xs[math.ceil(q * len(xs)) - 1]


def report(state, sources, ids, width, rep):
    streams = {pid: state['parsed'][pid, state['chosen'][pid]] for pid in ids}
    acts = {pid: (binding.categorize(s) if rep in 'BN' else
                  {'literal': len(s), 'reference': 0, 'declaration': 0, 'binding': 0, 'navigation': 0, 'correction': 0, 'submission': 1})
            for pid, s in streams.items()}
    totals = {pid: sum(a.values()) for pid, a in acts.items()}
    a = sorted(totals.values()); n = len(a)
    codes = [x for s in streams.values() for x in s]
    alphabet = set(ALPHABET)
    src = sum(len(sources[pid][state['chosen'][pid]].encode()) for pid in ids)
    return {'problems': n, 'source_bytes': src, 'selections': len(codes), 'actions': sum(a),
            'actions_by_category': {k: sum(x[k] for x in acts.values()) for k in next(iter(acts.values()))},
            'median': a[n // 2] if n % 2 else (a[n // 2 - 1] + a[n // 2]) / 2, 'p90': quantile(a, .90), 'p95': quantile(a, .95), 'worst': a[-1],
            'within_32': sum(x <= 32 for x in a), 'within_96': sum(x <= 96 for x in a),
            'fallback_selection_fraction': sum(x in alphabet for x in codes) / len(codes),
            'bytes_per_selection': src / len(codes),
            'packet_bytes': sum(41 + (width * len(s) + 7) // 8 for s in streams.values())}, totals, acts


def arm(job):
    os.environ['PYTHONHASHSEED'] = '0'
    work, out, s = Path(job['work']), Path(job['out']), job['search']
    pool, rep, width = job['pool'], job['rep'], job['width']
    c, P, files, rows = inputs(work)
    fit_ids, val_ids = c['partition']['dev_fit'], c['partition']['dev_val']
    if job['smoke']:  # plumbing only: a smoke run measures on 40 dev-fit problems and never reads dev-val
        val_ids = fit_ids[:40]
    fitted = {pid: P[pool][pid] for pid in fit_ids}
    if rep in 'BN':
        recs, _ = records(P, rows, pool, fit_ids + val_ids)
        binding.install(joint, rep, recs)
        start = list(ALPHABET) + ([binding.END] if rep == 'B' else [])
        propose = binding.proposer(fitted, s['absent_slot_proposals'])
    else:
        binding.install(joint, 'L', {})
        start = list(ALPHABET)
        propose = m2.hybrid_chosen([], fitted)
    nb = {**s['neighborhood'], 'refill_shortlist': s['refill_shortlist']}
    budget = v3.Budget({'trials': job['trials'], 'seconds': s['seconds']})
    state = v3.evaluate(fitted, start, width, None, budget)
    state, _ = v3.refill(fitted, state, width, propose, nb, nb['refill_shortlist'], budget)
    log = []
    state, stop = v3.local_search(fitted, state, width, propose, s['neighborhood'], budget, log)
    name = f'{rep}-{pool}-{2 ** width}'
    val = {pid: P[pool][pid] for pid in val_ids}
    final = joint.evaluate(val, state['vocab'], width)
    if rep in 'BN':
        man = binding.save_and_verify(out / name, val, final, width)
        verified = man['verified']
        decoded = {str(r['id']): r['decoded_sha256'] for r in man['programs']}
    else:
        met = v3.save(out, name, val, files, final, width, f'roles-{name}', v1.provenance_of([]), {'pool': pool, 'rep': rep})
        verified = met['covered_programs']
        decoded = {str(pid): sha(val[pid][final['chosen'][pid]].encode()) for pid in val_ids}
    vocab = final['vocab']
    summary, totals, acts = report(final, val, sorted(val_ids), width, rep)
    slots = sorted(x for x in vocab if binding.is_slot(x))
    decoder = len((HERE / 'decoder.mjs').read_bytes()) if rep in 'BN' else 0
    res = {'arm': name, 'pool': pool, 'rep': rep, 'width': width, 'stop': stop, 'trials': budget.trials, 'seconds': budget.elapsed(),
           'entries': len(vocab), 'slots_in_dictionary': [list(binding.slot_of(x)) for x in slots],
           'end_in_dictionary': binding.END in vocab,
           'entries_with_slots': sum(any(binding.is_slot(ch) for ch in x) and not binding.is_slot(x) for x in vocab),
           'dictionary_bytes': final['dictionary_bytes'], 'package_bytes': final['package_bytes'], 'decoder_bytes': decoder,
           'package_bytes_with_decoder': final['package_bytes'] + decoder, 'packets_verified': verified,
           'dictionary_sha256': sha(json.dumps(vocab).encode()),
           'devval': summary,
           'per_problem_actions': {str(pid): totals[pid] for pid in sorted(val_ids)},
           'per_problem_categories': {str(pid): acts[pid] for pid in sorted(val_ids)},
           'decoded_sha256': decoded}
    (out / 'dictionaries').mkdir(exist_ok=True)
    write(out / 'dictionaries' / f'{name}.json', vocab)
    write(out / f'{name}-trace.json', {'rounds': log, 'stop': stop})
    write(out / f'{name}-result.json', res)
    return res


def contract_check(work):
    sc = json.loads((HERE / 'contract.json').read_text())
    for rel, h in sc['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    assert sha((work / 'roles/audit.json').read_bytes()) == sc['inputs']['audit_sha256']
    return sc


def run(work, output, parallel, smoke):
    sc = contract_check(work)
    output.mkdir(parents=True, exist_ok=False); out = output.resolve()
    jobs = [{'work': str(work), 'out': str(out), 'search': sc['search'], 'pool': p, 'rep': r, 'width': w,
             'trials': smoke or sc['search']['trials'], 'smoke': bool(smoke)}
            for w in (7, 8) for p in POOLS for r in REPS]
    start = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(parallel) as ex:
        results = list(ex.map(arm, jobs))
    write(out / 'results.json', {'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'seconds': time.monotonic() - start,
                                 'smoke_trials': smoke, 'arms': results})
    for r in results:
        d = r['devval']
        print(f"{r['arm']:9} devval actions {d['actions']:6} sel {d['selections']:6} med {d['median']:6} p90 {d['p90']:4} "
              f"fallback {d['fallback_selection_fraction']:.3f} slots {len(r['slots_in_dictionary']):3} pkg+dec {r['package_bytes_with_decoder']} "
              f"trials {r['trials']} {r['stop']}")


def execute(work, run_dir, workers):
    """Run every distinct decoded dev-val program (by hash) against every frozen case, with strict parity."""
    sc = contract_check(work)
    c, P, _, rows = inputs(work)
    res = json.loads((run_dir / 'results.json').read_text())
    assert res['contract_sha256'] == sha((HERE / 'contract.json').read_bytes())
    jobs = {}
    for r in res['arms']:
        for pid, h in r['decoded_sha256'].items():
            pid = int(pid)
            if r['rep'] in 'BN':
                text = (run_dir / r['arm'] / 'decoded' / f'{pid}.js').read_text()
            else:
                text = next(iter(P[r['pool']][pid].values()))  # the canonical codec decoded this exact text (v3.save verified it)
            assert sha(text.encode()) == h
            jobs.setdefault((r['pool'], pid, h), text)
    got = parity_all(work, {k: (text, entry(k[0], rows[k[1]]), rows[k[1]]) for k, text in jobs.items()}, workers)
    results = {h: {'pool': pool, 'id': pid, **r} for (pool, pid, h), r in got.items()}
    arms = {r['arm']: {'programs': len(r['decoded_sha256']), 'passed': sum(results[h]['passed'] for h in r['decoded_sha256'].values()),
                       'cases': sum(results[h]['cases'] for h in r['decoded_sha256'].values()),
                       'failed_ids': sorted(int(p) for p, h in r['decoded_sha256'].items() if not results[h]['passed'])}
            for r in res['arms']}
    write(run_dir / 'execution.json', {'smoke_trials': res['smoke_trials'], 'results_sha256': sha((run_dir / 'results.json').read_bytes()),
                                       'distinct_programs': len(results), 'programs': {h: results[h] for h in sorted(results)}, 'arms': arms})
    for k, v in arms.items():
        print(f"{k:9} passed {v['passed']}/{v['programs']} cases {v['cases']} failed {v['failed_ids']}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=['audit', 'run', 'execute']); ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--output', type=Path); ap.add_argument('--run', type=Path); ap.add_argument('--parallel', type=int, default=12)
    ap.add_argument('--workers', type=int, default=4); ap.add_argument('--smoke', type=int)
    a = ap.parse_args(); work = a.work.resolve()
    if a.step == 'audit': audit(work, a.workers)
    elif a.step == 'run': run(work, a.output, a.parallel, a.smoke)
    else: execute(work, a.run.resolve(), a.workers)
