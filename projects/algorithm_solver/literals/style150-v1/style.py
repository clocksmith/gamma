"""Shared-style source rewriting on the first 150 development problems.

  style.py requalify --work DIR                      rerun the 1,006 existing alternatives on the corpus cases
  style.py check     --work DIR --id N --file F      parity check of a draft rewrite (all cases)
  style.py submit    --work DIR --id N --file F      record the single rewrite for N (immutable)
  style.py qualify   --work DIR                      qualify every submitted rewrite

Every source is judged on the population's corpus cases (admission500-v1/population.py) with
the unchanged return oracle plus strict parity with the original's recorded observation
(result, result type, arguments before and after, alias edges), as in scale150-v1 qualify.py.
"""
import argparse, concurrent.futures, importlib.util, json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADM = HERE.parent / 'admission500-v1'
sys.path.insert(0, str(ADM))
import stage, repair
from stage import P, sha, write, LIMITS
from population import transported, ALWAYS_BIGINT

REFINE = Path('/home/x/Documents/Codex/2026-10-19/task/literal-scale150-refine-v1/load_sources.py')
CHECK_LIMIT = 8  # parity checks a rewriter may run per problem before submitting


def exact(a, b):
    if isinstance(a, bool) or isinstance(b, bool): return type(a) == type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)): return a == b
    if type(a) != type(b): return False
    if isinstance(a, list): return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    if isinstance(a, dict): return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def population(work):
    man = json.loads((work / 'population/manifest.json').read_text())
    rows = {r['id']: r for r in man['rows'] if r['cohort'] == 'first-150'}
    assert len(rows) == 150
    rep = json.loads((work / 'population-baseline/report.json').read_text())
    assert rep['qualified'] == rep['problems'] == 363 and rep['manifest_sha256'] == sha((work / 'population/manifest.json').read_bytes())
    return rows


def load_pool():
    spec = importlib.util.spec_from_file_location('refine150', REFINE); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.expanded, m.meta


def entry_of(meta, method):
    e = meta.get('entry', 'solve')
    if meta.get('interface') == 'class' or e == 'Solution':
        return f"(...a)=>new Solution().{meta.get('method') or method}(...a)"
    return e


def parity(work, pid, source, entry, spec, scratch):
    """Run all cases; return (passed, checks_passed, total, mismatches[:3])."""
    from algsolve.judge import sandbox
    from qualify_rules import judge_case
    from verify_execution import strict_object
    cases = transported(spec, json.loads((work / 'population' / f'{pid}-tests.json').read_text()))
    base = json.loads((work / 'population-baseline/qualification/baselines' / f'{pid}.json').read_text())
    harness = (ADM / ('harness-exact-integer.cjs' if spec['transport'] == 'exact-integer' else 'harness.cjs')).read_text()
    ok, bad = 0, []
    for off in range(0, len(cases), LIMITS['batch_cases']):
        batch = cases[off:off + LIMITS['batch_cases']]
        res = sandbox.run(['/usr/bin/node', '--jitless', '--single-threaded', '--max-old-space-size=64', 'harness.cjs'],
                          files={'program.js': source, 'harness.cjs': harness,
                                 'inputs.json': json.dumps({'entry': entry, 'calls': [{'args': t['args']} for t in batch]})},
                          limits=sandbox.Limits(cpu_seconds=LIMITS['sandbox_cpu_seconds'], wall_seconds=LIMITS['sandbox_wall_seconds'],
                                                memory_bytes=LIMITS['sandbox_memory_bytes'], max_output_bytes=LIMITS['max_output_bytes']))
        if scratch:
            (scratch / f'{pid}-{off}.stdout').write_bytes(res.stdout); (scratch / f'{pid}-{off}.stderr').write_bytes(res.stderr)
        try:
            assert res.ok, f'sandbox failure (exit {res.exit_code}, timed out {res.timed_out}) {res.stderr.decode(errors="replace")[-200:]}'
            recs = [json.loads(l, object_pairs_hook=strict_object) for l in res.stdout.splitlines()]
            assert len(recs) == len(batch) + 1 and recs[-1] == {'done': len(batch)}, 'protocol'
            for k, rec in enumerate(recs[:-1]):
                valid, o = judge_case(batch[k], rec)
                same = exact(o, base[off + k])
                if valid and same: ok += 1
                elif len(bad) < 3:
                    bad.append({'case': off + k, 'oracle': valid, 'parity': same, 'error': rec.get('error'),
                                'observed': {k2: o.get(k2) for k2 in ('result', 'args_after')},
                                'original': {k2: base[off + k].get(k2) for k2 in ('result', 'args_after')}})
        except Exception as e:
            if len(bad) < 3: bad.append({'offset': off, 'error': str(e)})
    return ok == len(cases) and not bad, ok, len(cases), bad


def requalify(work):
    rows = population(work); ss, meta = load_pool()
    probs = {json.loads(l)['uid']: json.loads(l) for l in (P / 'data/derived/problems.jsonl').open()}
    out = HERE / 'evidence'; out.mkdir(exist_ok=True); d = work / 'style150' / 'pool'; d.mkdir(parents=True, exist_ok=True)
    jobs = []
    for pid, variants in sorted(ss.items()):
        method = (eval(probs[f'lcd:{pid}']['entry']) if isinstance(probs[f'lcd:{pid}']['entry'], str) else probs[f'lcd:{pid}']['entry'])['method']
        for v, text in sorted(variants.items()):
            jobs.append((pid, v, text, entry_of(meta[pid, v], method)))
    start = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(LIMITS['workers']) as pool:
        futs = {pool.submit(parity, work, pid, text, entry, rows[pid], None): (pid, v, text, entry) for pid, v, text, entry in jobs}
        res = []
        for f in concurrent.futures.as_completed(futs):
            pid, v, text, entry = futs[f]; passed, ok, n, bad = f.result()
            res.append({'id': pid, 'variant': v, 'sha256': sha(text.encode()), 'entry': entry, 'passed': passed, 'checks': f'{ok}/{n}',
                        'first_mismatch_kind': None if passed else ('error' if bad and bad[0].get('error') else 'oracle' if bad and not bad[0].get('oracle') else 'parity')})
    res.sort(key=lambda r: (r['id'], r['variant']))
    rep = {'schema': 'gamma.style150-pool-requalification.v1', 'alternatives': len(res), 'passed': sum(r['passed'] for r in res),
           'problems_with_original_passing': len({r['id'] for r in res if r['passed']}), 'elapsed_seconds': time.monotonic() - start,
           'population_manifest_sha256': sha((work / 'population/manifest.json').read_bytes()), 'rows': res}
    write(d / 'requalification.json', rep); write(out / 'pool-requalification.json', rep)
    print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}))
    for r in res:
        if not r['passed']: print(r['id'], r['variant'], r['checks'], r['first_mismatch_kind'])


def check(work, pid, file):
    rows = population(work); d = work / 'style150' / 'checks'; d.mkdir(parents=True, exist_ok=True)
    log = d / f'{pid}.jsonl'; used = len(log.read_text().splitlines()) if log.exists() else 0
    assert used < CHECK_LIMIT, f'{pid}: check limit {CHECK_LIMIT} reached; submit your best draft'
    text = Path(file).read_text()
    passed, ok, n, bad = parity(work, pid, text, 'solve', rows[pid], None)
    with log.open('a') as f: f.write(json.dumps({'sha256': sha(text.encode()), 'passed': passed, 'checks': f'{ok}/{n}'}) + '\n')
    print(json.dumps({'id': pid, 'passed': passed, 'checks': f'{ok}/{n}', 'bytes': len(text.encode()), 'checks_used': used + 1,
                      'mismatches': bad}, indent=1)[:3000])


def submit(work, pid, file):
    d = work / 'style150' / 'submitted'; d.mkdir(parents=True, exist_ok=True); dst = d / f'{pid}.js'
    assert pid in population(work) and not dst.exists(), f'{pid}: not in the 150 or already submitted'
    b = Path(file).read_bytes(); dst.write_bytes(b)
    with (work / 'style150' / 'submissions.jsonl').open('a') as f:
        f.write(json.dumps({'id': pid, 'sha256': sha(b), 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}) + '\n')
    print(pid, sha(b))


def qualify(work):
    rows = population(work); d = work / 'style150'; q = d / 'qualification'; q.mkdir(exist_ok=True)
    subs = [json.loads(l) for l in (d / 'submissions.jsonl').open()]
    todo = [s for s in subs if not (q / f"{s['id']}.json").exists()]
    with concurrent.futures.ProcessPoolExecutor(LIMITS['workers']) as pool:
        futs = {}
        for s in todo:
            text = (d / 'submitted' / f"{s['id']}.js").read_text(); assert sha(text.encode()) == s['sha256']
            futs[pool.submit(parity, work, s['id'], text, 'solve', rows[s['id']], None)] = (s, text)
        for f in concurrent.futures.as_completed(futs):
            s, text = futs[f]; passed, ok, n, bad = f.result()
            write(q / f"{s['id']}.json", {'id': s['id'], 'sha256': s['sha256'], 'bytes': len(text.encode()), 'passed': passed, 'checks': f'{ok}/{n}',
                                         'failure': None if passed else (bad[0] if bad else 'unknown')})
            print(json.dumps({'id': s['id'], 'passed': passed, 'checks': f'{ok}/{n}'}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['requalify', 'check', 'submit', 'qualify']); ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--id', type=int); ap.add_argument('--file')
    a = ap.parse_args(); w = a.work.resolve()
    if a.step == 'check': check(w, a.id, a.file)
    elif a.step == 'submit': submit(w, a.id, a.file)
    else: {'requalify': requalify, 'qualify': qualify}[a.step](w)
