"""Admission qualification stage for the 213 candidates beyond the current 150.

  stage.py freeze   --work DIR   write DIR/stage-freeze.json (refuses to overwrite)
  stage.py prepare  --work DIR   copy hash-checked sources and cases into DIR/inputs
  stage.py qualify  --work DIR   run every admitted source in the literal harness

The work directory is private (sources and cases are not published). The freeze binds
problem IDs, source, receipt and case hashes, code hashes, limits and the pass rule
before any candidate is executed in the literal harness.
"""
import argparse, concurrent.futures, hashlib, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = HERE.parents[1]
sys.path[:0] = [str(P), str(P / 'literals')]
sha = lambda b: hashlib.sha256(b).hexdigest()
CONSTRUCTOR_SOURCE = P / 'findings/js-exact-integer-transport-128-v1/harness.cjs'
CONSTRUCTORS = {  # exact lines of CONSTRUCTOR_SOURCE, appended and charged when a source uses them undefined
    'ListNode': 'class ListNode { constructor(val = 0, next = null) { this.val = val; this.next = next; } }\n',
    'TreeNode': 'class TreeNode { constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; } }\n',
}
LIMITS = {'batch_cases': 16, 'sandbox_cpu_seconds': 3, 'sandbox_wall_seconds': 8, 'sandbox_memory_bytes': 1024 ** 3,
          'max_output_bytes': 4 * 1024 ** 2, 'workers': 4, 'qualification_seconds': 3600}
CODE = [HERE / 'inventory.py', HERE / 'stage.py', HERE / 'qualify_rules.py', HERE / 'harness.cjs', P / 'algsolve/judge/sandbox.py',
        P / 'algsolve/judge/judge.py', P / 'literals/verify_execution.py', CONSTRUCTOR_SOURCE]


def write(p, v): p.write_text(json.dumps(v, indent=2, sort_keys=True) + '\n')


def freeze(work):
    out = work / 'stage-freeze.json'
    assert not out.exists(), 'stage already frozen'
    inv_raw = (work / 'admission-inventory.json').read_bytes(); inv = json.loads(inv_raw)
    for ln in CONSTRUCTORS.values(): assert ln in CONSTRUCTOR_SOURCE.read_text()
    node = subprocess.run(['/usr/bin/node', '--version'], capture_output=True, text=True).stdout.strip()
    rows = []
    for r in inv['rows']:
        rows.append({k: r.get(k) for k in ('id', 'uid', 'key', 'family', 'difficulty', 'route', 'source_sha256',
                                           'independent_cases', 'entry_method', 'entry_form', 'external_constructors')})
    write(out, {
        'schema': 'gamma.literal-admission500-stage-freeze.v1',
        'scope': 'Admission qualification of the 213 metadata-eligible JavaScript problems beyond the current 150 (ledger revision 1810). Representation development only: every one is previously consumed corpus material, never unseen.',
        'inventory_sha256': sha(inv_raw), 'ledger_revision': 1810, 'ledger_sha256': inv['summary']['ledger_sha256'],
        'ids': [r['id'] for r in rows], 'rows': rows,
        'source_policy': 'Admitted source is the hash-bound normalized ledger artifact (catalog source for 1464 and 1748). A source that constructs ListNode or TreeNode without defining it gets the exact constructor line from the support source appended; those bytes are part of the admitted source and are charged in every later encoding. No other change.',
        'entry': "class Solution sources run through the entry expression (...a)=>new Solution().<method>(...a); named functions run directly.",
        'pass_rule': 'Every independent case passes the unchanged return oracle (judge _matches, exact big-integer transport, unsafe numbers fail closed) with no error, timeout or protocol failure. Observed result, result type, arguments after the call and alias edges are stored as the parity baseline for later rewrites.',
        'failure_policy': 'A failing problem stays in the 363 denominator with its full logs. It is not replaced. At most one separately frozen packaging or adapter repair (no algorithm change) may follow, as in scale150-v1 attempt-002.',
        'admission': 'A passing problem joins the literal development population as admitted development. No ledger, claim or catalog is written.',
        'limits': LIMITS, 'node_version': node,
        'code_hashes': {str(p.relative_to(P)): sha(p.read_bytes()) for p in CODE},
        'protected': 'The 66-problem reservation and its 60 families stay closed; the inventory checks each candidate against them.',
        'no_threshold_change': 'M1 thresholds unchanged.',
    })
    print(sha(out.read_bytes()))


def tests_for(row, ledger_sets):
    from inventory import test_hash_forms
    cases = []
    for s in ledger_sets:
        part, forms = test_hash_forms((P / 'data/derived' / s['path']).read_bytes())
        assert s['sha256'] in forms and len(part) == s['tests']
        cases.extend(part)
    assert len(cases) == row['independent_cases'] and cases
    return cases


def prepare(work):
    import gzip
    from inventory import LEDGER, LEDGER_SHA
    st = json.loads((work / 'stage-freeze.json').read_text())
    for p, h in st['code_hashes'].items(): assert sha((P / p).read_bytes()) == h, p
    raw = gzip.open(LEDGER).read(); assert sha(raw) == LEDGER_SHA; E = json.loads(raw)['entries']
    inp = work / 'inputs'; inp.mkdir()
    seal = {x['uid']: x for x in json.loads((P / 'runs/source-corpus-js-py-128-v2/source-seal.json').read_text())}
    cat = {r['id']: r for r in json.loads((P / 'data/derived/bilingual_development_catalog_v2.json').read_text())['rows']}
    rows = []
    for r in st['rows']:
        pid = r['id']; e = E.get(f'{pid:04d}:javascript')
        if r['route'].startswith('ledger'):
            src = Path(e['normalized']['path']).read_bytes(); sets = e['independent_sets']
        else:
            impl = next(i for i in cat[pid]['implementations'] if i['language'] == 'javascript')
            src = (P / impl['source']).read_bytes()
            sets = [{'path': f'tests/lcd__{pid}.json', 'sha256': seal[r['uid']]['independent_tests_sha256'], 'tests': r['independent_cases']}]
        assert sha(src) == r['source_sha256']
        admitted = src.decode() + ''.join(CONSTRUCTORS[c] for c in r['external_constructors'])
        entry = f"(...a)=>new Solution().{r['entry_method']}(...a)" if r['entry_form'] == 'class Solution method' else r['entry_method']
        cases = tests_for(r, sets)
        (inp / f'{pid}.raw.js').write_bytes(src); (inp / f'{pid}.js').write_text(admitted); write(inp / f'{pid}-tests.json', cases)
        rows.append({'id': pid, 'raw_sha256': sha(src), 'admitted_sha256': sha(admitted.encode()),
                     'helper_bytes': len(admitted.encode()) - len(src), 'entry': entry, 'cases': len(cases),
                     'tests_sha256': sha((inp / f'{pid}-tests.json').read_bytes())})
    write(work / 'contract.json', {'schema': 'gamma.literal-admission500-inputs.v1',
                                   'stage_sha256': sha((work / 'stage-freeze.json').read_bytes()), 'rows': rows})
    print(json.dumps({'problems': len(rows), 'cases': sum(r['cases'] for r in rows),
                      'contract_sha256': sha((work / 'contract.json').read_bytes())}))


def run_one(work, spec, harness, limits):
    from algsolve.judge import sandbox
    from qualify_rules import judge_case
    from verify_execution import strict_object
    q = work / 'qualification/observations'
    source = (work / 'inputs' / f"{spec['id']}.js").read_text(); assert sha(source.encode()) == spec['admitted_sha256']
    tests = json.loads((work / 'inputs' / f"{spec['id']}-tests.json").read_text())
    passed, failures, calls, obs = 0, [], [], []
    for off in range(0, len(tests), limits['batch_cases']):
        batch = tests[off:off + limits['batch_cases']]
        payload = {'entry': spec['entry'], 'calls': [{'args': t['args']} for t in batch]}
        res = sandbox.run(['/usr/bin/node', '--jitless', '--single-threaded', '--max-old-space-size=64', 'harness.cjs'],
                          files={'program.js': source, 'inputs.json': json.dumps(payload), 'harness.cjs': harness},
                          limits=sandbox.Limits(cpu_seconds=limits['sandbox_cpu_seconds'], wall_seconds=limits['sandbox_wall_seconds'],
                                                memory_bytes=limits['sandbox_memory_bytes'], max_output_bytes=limits['max_output_bytes']))
        stem = f"{spec['id']}-{off}"
        (q / f'{stem}.stdout').write_bytes(res.stdout); (q / f'{stem}.stderr').write_bytes(res.stderr)
        calls.append({'stem': stem, 'exit_code': res.exit_code, 'timed_out': res.timed_out, 'wall_seconds': res.wall_seconds,
                      'stdout_sha256': sha(res.stdout), 'stderr_sha256': sha(res.stderr)})
        try:
            assert res.ok, 'sandbox failure'
            recs = [json.loads(l, object_pairs_hook=strict_object, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                    for l in res.stdout.splitlines()]
            assert len(recs) == len(batch) + 1 and recs[-1] == {'done': len(batch)}
            for k, rec in enumerate(recs[:-1]):
                assert type(rec.get('i')) is int and rec['i'] == k
                ok, o = judge_case(batch[k], rec); obs.append(o); passed += ok
                if not ok: failures.append({'case': off + k, 'reason': 'oracle_or_numeric', 'error': rec.get('error')})
        except Exception as ex:
            failures.append({'offset': off, 'reason': 'execution_or_protocol', 'detail': str(ex)})
            obs.extend([None] * (off + len(batch) - len(obs)))
    write(work / 'qualification/baselines' / f"{spec['id']}.json", obs)
    return {'id': spec['id'], 'passed': passed == len(tests) and not failures, 'checks_passed': passed,
            'checks_total': len(tests), 'failures': failures, 'calls': calls}


def qualify(work):
    st = json.loads((work / 'stage-freeze.json').read_text()); c = json.loads((work / 'contract.json').read_text())
    assert c['stage_sha256'] == sha((work / 'stage-freeze.json').read_bytes())
    for p, h in st['code_hashes'].items(): assert sha((P / p).read_bytes()) == h, p
    q = work / 'qualification'; q.mkdir(); (q / 'observations').mkdir(); (q / 'baselines').mkdir()
    harness = (HERE / 'harness.cjs').read_text(); limits = st['limits']; start = time.monotonic(); rows = []; stopped = False
    with concurrent.futures.ProcessPoolExecutor(limits['workers']) as pool:
        futs = {pool.submit(run_one, work, spec, harness, limits): spec['id'] for spec in c['rows']}
        for f in concurrent.futures.as_completed(futs):
            rows.append(f.result()); r = rows[-1]
            print(json.dumps({'id': r['id'], 'passed': r['passed'], 'checks': f"{r['checks_passed']}/{r['checks_total']}"}), flush=True)
            if time.monotonic() - start > limits['qualification_seconds']:
                stopped = True
                for g in futs: g.cancel()
                break
    rows.sort(key=lambda r: r['id'])
    report = {'schema': 'gamma.literal-admission500-qualification.v1', 'denominator': len(c['rows']), 'rows': rows,
              'qualified': sum(r['passed'] for r in rows), 'checks_passed': sum(r['checks_passed'] for r in rows),
              'checks_total': sum(r['checks_total'] for r in rows), 'elapsed_seconds': time.monotonic() - start,
              'budget_stopped': stopped, 'stage_sha256': c['stage_sha256'], 'contract_sha256': sha((work / 'contract.json').read_bytes())}
    write(q / 'report.json', report); print(json.dumps({k: v for k, v in report.items() if k != 'rows'}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=['freeze', 'prepare', 'qualify']); ap.add_argument('--work', type=Path, required=True)
    a = ap.parse_args(); {'freeze': freeze, 'prepare': prepare, 'qualify': qualify}[a.step](a.work.resolve())
