"""Attempt 002: exact-integer input transport for the six profile-bound problems.

  repair.py freeze  --work DIR   write DIR/attempt-002/repair-contract.json (refuses to overwrite)
  repair.py qualify --work DIR   rerun only those problems with the transport

The six (633, 670, 738, 868, 989, 1056) were qualified in the corpus under exact-integer
runtime profiles. The literal harness passed every integer as a JSON Number, which loses
precision above 2^53-1, so they failed in attempt 001 (preserved). This repair changes input
transport only: integers are tagged and decoded to BigInt by the profile rule. Sources,
cases, expected values and the oracle rule are unchanged.
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stage
from stage import P, sha, write

IDS = [633, 670, 738, 868, 989, 1056]
SAFE = 2 ** 53 - 1
# Corpus profile rule (algsolve/campaign_633_integer.py, campaign_exact_integer.py, campaign_738_integer.py,
# campaign_868_integer.py, campaign_989_integer.py, campaign_1056_transport.py).
ALWAYS_BIGINT = {633}


def tag(value, always):
    if isinstance(value, bool): return value
    if isinstance(value, int) and (always or abs(value) > SAFE): return {'__gamma_bigint_v1__': str(value)}
    if isinstance(value, list): return [tag(v, always) for v in value]
    if isinstance(value, dict): return {k: tag(v, always) for k, v in value.items()}
    return value


def freeze(work):
    d = work / 'attempt-002'; out = d / 'repair-contract.json'
    assert not out.exists(); d.mkdir(exist_ok=True)
    first = json.loads((work / 'qualification/report.json').read_bytes())
    failed = sorted(r['id'] for r in first['rows'] if not r['passed']); assert failed == IDS, failed
    code = [HERE / 'repair.py', HERE / 'harness-exact-integer.cjs'] + [P / p for p in
            ('algsolve/campaign_633_integer.py', 'algsolve/campaign_exact_integer.py', 'algsolve/campaign_738_integer.py',
             'algsolve/campaign_868_integer.py', 'algsolve/campaign_989_integer.py', 'algsolve/campaign_1056_transport.py')]
    write(out, {'schema': 'gamma.literal-admission500-exact-integer-transport.v1', 'problem_ids': IDS,
                'attempt_001_report_sha256': sha((work / 'qualification/report.json').read_bytes()),
                'stage_sha256': sha((work / 'stage-freeze.json').read_bytes()),
                'change': 'Input transport only. 633: every integer argument is passed as BigInt (corpus profile lc633-uint64-bigint-bool-v1). 670, 738, 868, 989, 1056: an integer argument is a Number when |v| <= 2^53-1 and a BigInt otherwise (number-or-bigint profiles). Integers travel as {"__gamma_bigint_v1__": decimal} and harness-exact-integer.cjs decodes them; it differs from harness.cjs only in that decoder line. Results, expected values, oracle and pass rule unchanged; BigInt results are already transported exactly.',
                'no_source_change': True, 'limits': stage.LIMITS,
                'code_hashes': {str(p.relative_to(P)): sha(p.read_bytes()) for p in code}})
    print(sha(out.read_bytes()))


def qualify(work):
    import concurrent.futures, time
    d = work / 'attempt-002'; rc = json.loads((d / 'repair-contract.json').read_text())
    for p, h in rc['code_hashes'].items(): assert sha((P / p).read_bytes()) == h, p
    c = json.loads((work / 'contract.json').read_text())
    (d / 'inputs').mkdir(); q = d / 'qualification'; q.mkdir(); (q / 'observations').mkdir(); (q / 'baselines').mkdir()
    specs = []
    for spec in c['rows']:
        if spec['id'] not in IDS: continue
        tests = json.loads((work / 'inputs' / f"{spec['id']}-tests.json").read_text())
        assert sha((work / 'inputs' / f"{spec['id']}-tests.json").read_bytes()) == spec['tests_sha256']
        tagged = [{**t, 'args': tag(t['args'], spec['id'] in ALWAYS_BIGINT)} for t in tests]
        write(d / 'inputs' / f"{spec['id']}-tests.json", tagged)
        (d / 'inputs' / f"{spec['id']}.js").write_bytes((work / 'inputs' / f"{spec['id']}.js").read_bytes())
        specs.append(spec)
    harness = (HERE / 'harness-exact-integer.cjs').read_text(); start = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(stage.LIMITS['workers']) as pool:
        rows = sorted(pool.map(stage.run_one, [d] * len(specs), specs, [harness] * len(specs), [stage.LIMITS] * len(specs)), key=lambda r: r['id'])
    report = {'schema': 'gamma.literal-admission500-qualification.v1', 'attempt': 2, 'denominator': len(IDS), 'rows': rows,
              'qualified': sum(r['passed'] for r in rows), 'checks_passed': sum(r['checks_passed'] for r in rows),
              'checks_total': sum(r['checks_total'] for r in rows), 'elapsed_seconds': time.monotonic() - start,
              'repair_contract_sha256': sha((d / 'repair-contract.json').read_bytes())}
    write(q / 'report.json', report); print(json.dumps({k: v for k, v in report.items() if k != 'rows'}))
    for r in rows: print(r['id'], r['passed'], r['checks_passed'], '/', r['checks_total'], json.dumps(r['failures'][:2])[:300])


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=['freeze', 'qualify']); ap.add_argument('--work', type=Path, required=True)
    a = ap.parse_args(); {'freeze': freeze, 'qualify': qualify}[a.step](a.work.resolve())
