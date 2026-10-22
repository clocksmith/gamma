"""Uniform inputs for the admitted population: source, entry, transport and corpus cases.

  population.py build    --work DIR   write DIR/population/<id>.js, <id>-tests.json and manifest.json
  population.py baseline --work DIR   run every original in the stage harness; record parity baselines

Earlier literal stages qualified their 150 problems on stage-specific case sets. This module
rebuilds all 363 from primary records with the corpus independent cases, so later rewrite
and M1 measurements use one case contract. Each original must hash-match the source the
earlier stage admitted (or the 213 admission contract). Each case set must hash-match the
receipt that qualified it. Anything that does not bind fails closed.
"""
import argparse, concurrent.futures, gzip, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stage, repair
from stage import P, sha, write, CONSTRUCTORS, LIMITS
from inventory import LEDGER, LEDGER_SHA, STAGE150, test_hash_forms, source_traits

LIT = P / 'literals'
TASK = Path('/home/x/Documents/Codex/2026-10-19/task')
EXACT_INTEGER = {633, 670, 738, 868, 989, 1056, 9, 69, 115}  # corpus exact-integer profiles / successors
ALWAYS_BIGINT = {633}


def recorded_originals():
    """Source hash each earlier stage admitted as the problem's original."""
    out = {}
    m = json.loads((LIT / 'scale-v2/generated/manifest.json').read_text()); m = m['rows'] if isinstance(m, dict) else m
    for r in m:
        if r['variant'] == 'original': out[int(r['id'])] = r['sha256']
    for stage_dir in ('literal-scale125-v1', 'literal-scale150-v1'):
        for r in json.loads((TASK / stage_dir / 'stage-freeze.json').read_text())['rows']:
            out.setdefault(r['id'], r['implementation']['source_sha256'])
    cat = {r['id']: r for r in json.loads((P / 'data/derived/bilingual_development_catalog_v4.json').read_text())['rows']}
    for pid in [54, 56, 57, 59, 63, 66, 71, 72, 76, 77, 78, 84, 85, 90, 91, 93, 96, 97, 128, 1512]:  # scale100-v1 IDS
        impl = next(i for i in cat[pid]['implementations'] if i['language'] == 'javascript')
        out.setdefault(pid, impl['source_sha256'])
    return out, cat


def cases_from(paths_and_hashes, expected_count):
    cases = []
    for path, h in paths_and_hashes:
        part, forms = test_hash_forms(Path(path).read_bytes())
        assert h is None or h in forms, f'case hash mismatch {path}'
        cases += part
    assert len(cases) == expected_count and cases, (paths_and_hashes, len(cases), expected_count)
    return cases


def dev_row(pid, want, E, cat):
    """Locate the admitted original and its corpus cases for one of the first 150."""
    e = E.get(f'{pid:04d}:javascript')
    if e and e['status'] == 'complete' and e['normalized']['sha256'] == want:
        src = Path(e['normalized']['path']).read_bytes()
        cases = cases_from([(P / 'data/derived' / s['path'], s['sha256']) for s in e['independent_sets']],
                           sum(s['tests'] for s in e['independent_sets']))
        return src, cases, 'ledger-1810'
    impl = next(i for i in cat[pid]['implementations'] if i['language'] == 'javascript')
    assert impl['source_sha256'] == want, f'{pid}: recorded original is neither ledger nor catalog source'
    src = (P / impl['source']).read_bytes()
    rp = P / impl['qualification_receipt']; rj = json.loads(rp.read_bytes())
    meta = rj.get('independent_test_sets', rj.get('test_metadata'))
    n = int(impl['independent_cases'])
    if meta:
        return src, cases_from([(m['absolute_path'], m['sha256']) for m in meta], n), 'catalog-receipt'
    if pid in (9, 23, 30):
        man = json.loads((P / 'runs/js-corpus-b01-b02-review-128-v1/frozen-package/manifest.json').read_text())
        row = next(x for x in man['rows'] if x['id'] == pid)
        assert rj['qualified'] and rj['quarantined_independent'] == 0 and rj['valid_independent'] == n
        return src, cases_from([(m['absolute_path'], m['sha256']) for m in row['independent_test_sets']], n), 'b01-b02-frozen-package'
    if pid in (62, 69):
        assert str(rj['qualified']) == 'True' and int(rj['independent_passed']) == int(rj['independent_total']) == n
        contract = (rp.parent / 'contract.json').read_text()
        part, forms = test_hash_forms((P / f'data/derived/tests/lcd__{pid}.json').read_bytes())
        assert forms & set(re.findall(r'[0-9a-f]{64}', contract)), f'{pid}: cases not bound by successor contract'
        return src, cases_from([(P / f'data/derived/tests/lcd__{pid}.json', None)], n), 'successor-contract'
    if pid == 115:
        s = json.loads(rp.read_text())
        return src, cases_from([(P / 'data/derived/tests/lcd__115.json', s['tests_sha256'])], n), 'exact-integer-summary'
    if pid in (1046, 1512):
        # Five-family foundation: the case file must be bound by a hash in this source's own receipt or its seal.
        seal = next(x for x in json.loads((P / 'runs/source-corpus-js-py-128-v2/source-seal.json').read_text()) if x['uid'] == f'lcd:{pid}')
        part, forms = test_hash_forms((P / f'data/derived/tests/lcd__{pid}.json').read_bytes())
        bound = forms & (set(re.findall(r'[0-9a-f]{64}', rp.read_text())) | {seal['independent_tests_sha256']})
        assert bound, f'{pid}: cases not bound'
        return src, cases_from([(P / f'data/derived/tests/lcd__{pid}.json', bound.pop())], n), 'five-family-catalog'
    raise AssertionError(f'{pid}: no case route')


def entry_for(text, method):
    if re.search(r'class\s+Solution\s*\{', text): return f'(...a)=>new Solution().{method}(...a)', 'class Solution method'
    names = re.findall(r'\bfunction\s+([A-Za-z_$][\w$]*)\s*\(', text)
    if method in names: return method, 'named function'
    if 'solve' in names: return 'solve', 'named function'
    raise AssertionError(f'no entry for {method}')


def adapt(pid, cases):
    """Historical adapters restored exactly as scale150-v1 prepare.py applied them."""
    if pid == 30: return [{**t, 'compare': 'return:unordered_outer'} for t in cases], 'return:unordered_outer'
    if pid == 23:
        def node(v):
            if v is None: return None
            if isinstance(v, list): return {'__list_node__': v}
            assert isinstance(v, dict) and set(v) == {'__list_node__'}; return v
        return [{**t, 'args': [[node(v) for v in t['args'][0]]]} for t in cases], 'nested list-node input'
    return cases, None


def build(work):
    raw = gzip.open(LEDGER).read(); assert sha(raw) == LEDGER_SHA; E = json.loads(raw)['entries']
    probs = {json.loads(l)['uid']: json.loads(l) for l in (P / 'data/derived/problems.jsonl').open()}
    st = json.loads(STAGE150.read_text()); dev = sorted(set(st['prior_ids']) | set(st['additional_ids']))
    want, cat = recorded_originals(); assert set(dev) <= set(want)
    out = work / 'population'; out.mkdir(exist_ok=True); rows = []
    for pid in dev:
        src, cases, route = dev_row(pid, want[pid], E, cat)
        method = method_of(probs[f'lcd:{pid}'])
        cases, adapter = adapt(pid, cases)
        impl = next((i for i in cat.get(pid, {}).get('implementations', []) if i['language'] == 'javascript'), None)
        declared = ((impl or {}).get('evaluation_contract') or {}).get('comparison')
        if route != 'ledger-1810' and declared and declared != 'unchanged':
            cases, adapter = [{**t, 'compare': declared} for t in cases], f'declared comparison {declared}'
        rows.append(finish(out, pid, src, cases, method, route, adapter, 'first-150'))
    c = json.loads((work / 'contract.json').read_text())
    for spec in c['rows']:
        src = (work / 'inputs' / f"{spec['id']}.raw.js").read_bytes(); assert sha(src) == spec['raw_sha256']
        cases = json.loads((work / 'inputs' / f"{spec['id']}-tests.json").read_text())
        method = method_of(probs[f"lcd:{spec['id']}"])
        rows.append(finish(out, spec['id'], src, cases, method, 'admission500-stage', None, 'admitted-213'))
    write(out / 'manifest.json', {'schema': 'gamma.literal-population-inputs.v1', 'problems': len(rows), 'rows': rows,
                                  'ledger_sha256': LEDGER_SHA, 'code_sha256': sha(Path(__file__).read_bytes())})
    print(len(rows), sum(r['cases'] for r in rows))


def method_of(meta):
    e = meta['entry']
    return (eval(e) if isinstance(e, str) else e)['method']


def finish(out, pid, src, cases, method, route, adapter, cohort):
    text = src.decode()
    admitted = text + ''.join(CONSTRUCTORS[c] for c in source_traits(text)['external_constructors'] if c in CONSTRUCTORS)
    entry, form = entry_for(text, method)
    (out / f'{pid}.js').write_text(admitted); write(out / f'{pid}-tests.json', cases)
    return {'id': pid, 'cohort': cohort, 'route': route, 'raw_sha256': sha(src), 'admitted_sha256': sha(admitted.encode()),
            'helper_bytes': len(admitted.encode()) - len(src), 'entry': entry, 'entry_form': form, 'adapter': adapter,
            'transport': 'exact-integer' if pid in EXACT_INTEGER else 'standard', 'cases': len(cases),
            'tests_sha256': sha((out / f'{pid}-tests.json').read_bytes())}


def transported(spec, cases):
    if spec['transport'] != 'exact-integer': return cases
    return [{**t, 'args': repair.tag(t['args'], spec['id'] in ALWAYS_BIGINT)} for t in cases]


def baseline(work):
    out = work / 'population'; man = json.loads((out / 'manifest.json').read_text())
    bd = work / 'population-baseline'; bd.mkdir(); (bd / 'inputs').mkdir(); (bd / 'qualification/observations').mkdir(parents=True); (bd / 'qualification/baselines').mkdir()
    specs = []
    for r in man['rows']:
        cases = transported(r, json.loads((out / f"{r['id']}-tests.json").read_text()))
        write(bd / 'inputs' / f"{r['id']}-tests.json", cases)
        (bd / 'inputs' / f"{r['id']}.js").write_bytes((out / f"{r['id']}.js").read_bytes())
        specs.append({'id': r['id'], 'admitted_sha256': r['admitted_sha256'], 'entry': r['entry'], 'transport': r['transport']})
    plain, exact = (HERE / 'harness.cjs').read_text(), (HERE / 'harness-exact-integer.cjs').read_text()
    start = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(LIMITS['workers']) as pool:
        futs = [pool.submit(stage.run_one, bd, {**s}, exact if s['transport'] == 'exact-integer' else plain, LIMITS) for s in specs]
        rows = sorted((f.result() for f in futs), key=lambda r: r['id'])
    rep = {'schema': 'gamma.literal-population-baseline.v1', 'problems': len(rows), 'qualified': sum(r['passed'] for r in rows),
           'checks_passed': sum(r['checks_passed'] for r in rows), 'checks_total': sum(r['checks_total'] for r in rows),
           'elapsed_seconds': time.monotonic() - start, 'manifest_sha256': sha((out / 'manifest.json').read_bytes()), 'rows': rows}
    write(bd / 'report.json', rep)
    print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}))
    for r in rows:
        if not r['passed']: print(r['id'], r['checks_passed'], '/', r['checks_total'], json.dumps(r['failures'][:2])[:300])


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=['build', 'baseline']); ap.add_argument('--work', type=Path, required=True)
    a = ap.parse_args(); {'build': build, 'baseline': baseline}[a.step](a.work.resolve())
