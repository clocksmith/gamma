"""Freeze the 500-problem M1 population: the 363 admitted problems plus the 137 qualified gap problems.

  freeze500.py --work DIR   copy the frozen 363 inputs to DIR/population500, add the gap problems,
                            run their baselines and write evidence/population-500.json (refuses to overwrite)

The 363-problem inputs (DIR/population, pinned by style150-v1) are copied, never modified.
"""
import argparse, concurrent.futures, gzip, json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stage
from stage import P, sha, write, LIMITS
from inventory import LEDGER, test_hash_forms
from population import finish, method_of


def freeze500(work):
    import gap_tools
    out_pub = HERE / 'evidence/population-500.json'; assert not out_pub.exists(), 'population already frozen'
    summary = gap_tools.status(work)
    qualified = sorted(i for d in summary.values() for i in d['qualified'])
    assert len(qualified) == 137 and all(not d['open'] for d in summary.values()), 'gap not complete'
    raw = gzip.open(LEDGER).read(); E = json.loads(raw)['entries']
    probs = {json.loads(l)['uid']: json.loads(l) for l in (P / 'data/derived/problems.jsonl').open()}
    import shutil
    src_dir, src_base = work / 'population', work / 'population-baseline'
    man = json.loads((src_dir / 'manifest.json').read_text()); assert len(man['rows']) == 363
    out, bd = work / 'population500', work / 'population500-baseline'
    assert not out.exists() and not bd.exists()
    shutil.copytree(src_dir, out); shutil.copytree(src_base, bd)  # the frozen 363 inputs stay untouched
    rows = list(man['rows'])
    for pid in qualified:
        q = json.loads((work / 'gap/qualification' / f'{pid}.json').read_text())
        src = (work / 'gap/submitted' / f'{pid}.js').read_bytes(); assert sha(src) == q['submission_sha256']
        cases = []
        for t in E[f'{pid:04d}:javascript']['independent_sets']:
            part, forms = test_hash_forms((P / 'data/derived' / t['path']).read_bytes()); assert t['sha256'] in forms; cases += part
        row = finish(out, pid, src, cases, method_of(probs[f'lcd:{pid}']), 'gap-written', None, 'gap-137')
        assert row['admitted_sha256'] == q['admitted_sha256']
        rows.append(row)
    write(out / 'manifest.json', {**man, 'problems': len(rows), 'rows': rows, 'code_sha256': sha(Path(__file__).read_bytes())})
    # Baselines for the gap problems, in the same harness and limits.
    plain = (HERE / 'harness.cjs').read_text()
    with concurrent.futures.ProcessPoolExecutor(LIMITS['workers']) as pool:
        futs = []
        for r in rows[363:]:
            write(bd / 'inputs' / f"{r['id']}-tests.json", json.loads((out / f"{r['id']}-tests.json").read_text()))
            (bd / 'inputs' / f"{r['id']}.js").write_bytes((out / f"{r['id']}.js").read_bytes())
            futs.append(pool.submit(stage.run_one, bd, {'id': r['id'], 'admitted_sha256': r['admitted_sha256'], 'entry': r['entry']}, plain, LIMITS))
        gap_rows = sorted((f.result() for f in futs), key=lambda r: r['id'])
    assert all(r['passed'] for r in gap_rows), [r['id'] for r in gap_rows if not r['passed']]
    rep = json.loads((bd / 'report.json').read_text())
    rep['rows'] = sorted(rep['rows'] + gap_rows, key=lambda r: r['id'])
    rep.update(problems=len(rep['rows']), qualified=sum(r['passed'] for r in rep['rows']),
               checks_passed=sum(r['checks_passed'] for r in rep['rows']), checks_total=sum(r['checks_total'] for r in rep['rows']),
               manifest_sha256=sha((out / 'manifest.json').read_bytes()))
    write(bd / 'report.json', rep)
    assert rep['problems'] == rep['qualified'] == 500
    pub = []
    for r in rows:
        m = probs[f"lcd:{r['id']}"]
        e = E.get(f"{r['id']:04d}:javascript") or {}
        pub.append({'id': r['id'], 'key': e.get('key') or m['slug'], 'family': e.get('family') or m['slug'], 'difficulty': m['difficulty'],
                    'cohort': r['cohort'], 'admitted_sha256': r['admitted_sha256'], 'charged_helper_bytes': r['helper_bytes'],
                    'entry_form': r['entry_form'], 'transport': r['transport'], 'adapter': r['adapter'],
                    'cases': r['cases'], 'tests_sha256': r['tests_sha256']})
    import collections
    write(out_pub, {'schema': 'gamma.literal-m1-population-500.v1', 'frozen_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    'problems': len(pub), 'cases': sum(r['cases'] for r in pub),
                    'by_cohort': dict(collections.Counter(r['cohort'] for r in pub)),
                    'by_difficulty': dict(collections.Counter(r['difficulty'] for r in pub)),
                    'manifest_sha256': sha((out / 'manifest.json').read_bytes()), 'baseline_report_sha256': sha((bd / 'report.json').read_bytes()),
                    'requirements': {'oracle': 'unchanged return oracle on every corpus case (qualify_rules.judge_case), with the declared transport and adapter',
                                     'parity': 'a successor source must match the admitted source\'s recorded result, result type, arguments after the call and alias edges on every case',
                                     'numeric': 'exact integers; unsafe Number outputs fail closed; BigInt where the transport requires it',
                                     'complexity': 'stage limits per batch of 16 cases (3 CPU s, 8 s wall, 1 GiB, 64 MB V8 heap); finite tests, not a complexity proof',
                                     'denominator': 'all 500 stay in the M1 denominator whatever later measurement finds'},
                    'protected_reservation_opened': False, 'rows': pub})
    print(len(pub), sha(out_pub.read_bytes()))



if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True)
    freeze500(ap.parse_args().work.resolve())
