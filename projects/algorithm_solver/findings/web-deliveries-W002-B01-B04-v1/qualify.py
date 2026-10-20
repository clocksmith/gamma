"""Bounded qualification of delivered bytes; never generate or repair candidates.

Uses Gamma's existing functional test construction, sandbox, JS harness and scorer.
Assignment conformance and function-level execution evidence stay separate.
"""
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
from unittest.mock import patch

LANE = Path(sys.argv[1]).resolve()
RUN = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(LANE))
from algsolve import validate, values
from algsolve.records import Problem, load_hidden_tests
from algsolve.judge import judge, sandbox


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def unsafe_number(value):
    if type(value) is int:
        return abs(value) > 2**53 - 1
    if type(value) is float:
        return not math.isfinite(value)
    if isinstance(value, list):
        return any(unsafe_number(item) for item in value)
    if isinstance(value, dict):
        return any(unsafe_number(item) for item in value.values())
    return False


def tests_for(problem, raw):
    # Obtain exactly the existing policy-selected comparisons without executing.
    with patch.object(judge, 'judge_functional', side_effect=lambda source, entry, tests, **kw: tests):
        return validate.judge_problem(problem, '', raw)


def main():
    sandbox.check_available()
    results_dir = RUN / 'results'
    results_dir.mkdir(exist_ok=False)
    harness_path = LANE / 'findings/source-corpus-js-py-128-v3/return_harness.cjs'
    harness = harness_path.read_text()
    data = LANE / 'data/derived'
    approved_path = LANE / 'runs/known-sortedcontainers-catalog-128-v1/approved-library.json'
    approved = json.loads(approved_path.read_text())['approved']
    problems = {p['uid']: Problem.from_dict(p) for p in map(json.loads, (data / 'problems.jsonl').read_text().splitlines())}
    entries = {e['key']: e for e in map(json.loads, (data / 'corpus_entries.jsonl').read_text().splitlines())}
    authority = json.loads((RUN / 'authority/manifest.json').read_text())
    contract = {'scope': 'Development delivery qualification; no repair, training, protected scoring or catalog promotion.',
                'host': platform.node(), 'python': sys.version, 'rows': [], 'inputs': {},
                'limits': {'chunk': 16, 'wall_seconds': 8, 'cpu_seconds': 3,
                           'node_heap_MiB': 64, 'memory_MiB': 1024, 'output_bytes': 65536,
                           'campaign_wall_seconds': 1800},
                'assignment': 'Solution class required; named-function harness results are diagnostic if absent.'}
    for path in [data / 'problems.jsonl', data / 'corpus_entries.jsonl', approved_path]:
        observed = sha(path.read_bytes())
        assert observed == authority['inputs_sha256'][str(path)], str(path)
        contract['inputs'][str(path)] = observed
    for path in [harness_path, Path(__file__), *sorted((LANE / 'algsolve').glob('*.py')),
                 *sorted((LANE / 'algsolve/judge').glob('*.py'))]:
        contract['inputs'][str(path)] = sha(path.read_bytes())
    tasks = []
    seen = set()
    for batch in ['W002-B01', 'W002-B02', 'W002-B03', 'W002-B04']:
        receipt = json.loads((RUN / 'imports' / f'{batch}.json').read_text())
        assert receipt['status'] == 'imported-unqualified'
        packet_bytes = (RUN / 'authority' / f'{batch}.json').read_bytes()
        assert sha(packet_bytes) == receipt['assignment_packet_sha256']
        packet = {p['id']: p for p in json.loads(packet_bytes)['problems']}
        for row in receipt['rows']:
            number, key = row['id'], row['key']
            assert number not in seen
            seen.add(number)
            src = RUN / 'candidates' / batch / f'{number:04d}.js'
            sem = RUN / 'candidates' / batch / f'{number:04d}-semantics.json'
            assert sha(src.read_bytes()) == row['source_sha256']
            assert sha(sem.read_bytes()) == row['semantics_sha256']
            approval = approved[key]
            problem = problems[approval['reference_uid']]
            assert problem.io_mode == 'functional'
            assert problem.entry == packet[number]['entry'] and problem.params == packet[number]['params']
            reference = next(r['code'] for r in entries[key]['references'] if r['uid'] == approval['reference_uid'])
            assert sha(reference.encode()) == approval['code_sha256']
            groups = [('public', problem, problem.public_tests)]
            for testset in approval['independent_test_sets']:
                test_problem = problems[testset['uid']]
                raw = load_hidden_tests(test_problem)
                assert len(raw) == testset['tests'] and digest(raw) == testset['sha256']
                assert test_problem.entry == problem.entry and test_problem.params == problem.params
                groups.append(('independent:' + test_problem.uid, test_problem, raw))
            seal = dict(batch=batch, id=number, key=key, source_sha256=row['source_sha256'],
                        semantics_sha256=row['semantics_sha256'], reference_sha256=approval['code_sha256'],
                        contract_issues=row['contract_issues'],
                        groups=[{'name': name, 'count': len(raw), 'sha256': digest(raw)} for name, _, raw in groups])
            contract['rows'].append(seal)
            tasks.append((seal, src.read_text(), reference, groups))
    assert len(seen) == 100
    write(results_dir / 'contract.json', contract)
    print('[run-contract] run_name=web-W002-B01-B04-v1 device=cpu runtime_mode=linux-bwrap '
          'schedule=serial decode=none protected_access=none candidate_repairs=none', flush=True)
    limits = sandbox.Limits(wall_seconds=8, cpu_seconds=3, memory_bytes=1024**3, max_output_bytes=65536)

    def js_run(source, problem, tests, capture=False):
        calls = {'method': problem.entry['method'], 'params': problem.params,
                 'calls': [{'args': t.args, 'capture_args': capture or t.compare.startswith('arg:')} for t in tests]}
        result = sandbox.run(['/usr/bin/node', '--jitless', '--max-old-space-size=64', 'harness.cjs'],
                             files={'harness.cjs': harness, 'candidate.cjs': source, 'calls.json': json.dumps(calls)}, limits=limits)
        return result, judge._score_functional(result, tests).to_dict()

    probe = Problem(uid='control', source='control', source_id='control', title='', slug='', statement='',
                    io_mode='functional', entry={'class': 'Solution', 'method': 'probe'}, params=[['value', 'int']])
    test = [judge.FunctionalTest(args=[7], expected=7)]
    controls = []
    for source, expected in [('function probe(value) { return value; }', True),
                             ('function probe(value) { return 0; }', False)]:
        _, verdict = js_run(source, probe, test)
        controls.append(verdict)
        assert verdict['passed'] is expected
    write(results_dir / 'js-controls.json', controls)
    started = time.monotonic()
    summary = []
    for seal, source, reference, groups in tasks:
        target = results_dir / seal['batch'] / f"{seal['id']:04d}"
        target.mkdir(parents=True)
        write(target / 'seal.json', seal)
        results = []
        try:
            for name, problem, raw in groups:
                if not raw or any(unsafe_number(t) for t in raw) or any(t.get('kwargs') for t in raw):
                    results.append({'group': name, 'status': 'missing_or_unsupported_test_transport', 'count': len(raw)})
                    continue
                for offset in range(0, len(raw), 16):
                    if time.monotonic() - started > 1800:
                        raise TimeoutError('campaign wall cap reached')
                    chunk = raw[offset:offset+16]
                    tests = tests_for(problem, chunk)
                    py = validate.judge_problem(problem, reference, chunk, wall_seconds=8).to_dict()
                    execution, js = js_run(source, problem, tests, capture=name == 'public')
                    row = {'group': name, 'offset': offset, 'status': 'scored', 'python': py, 'javascript': js,
                           'stdout': execution.stdout.decode(errors='replace'), 'stderr': execution.stderr.decode(errors='replace')}
                    if name == 'public' and execution.ok:
                        observed = [json.loads(line) for line in execution.stdout.splitlines()]
                        row['mutated_public_args'] = [r['i'] + offset for r in observed if 'args_after' in r and
                            values.canonicalize(r['args_after']) != values.canonicalize(tests[r['i']].args)]
                    write(target / f'verdict-{len(results):04d}.json', row)
                    results.append(row)
            executed_ok = bool(results) and all(r['status'] == 'scored' and r['javascript']['passed'] and r['python']['passed'] for r in results)
            record = dict(seal, execution_passed=executed_ok, qualified=executed_ok and not seal['contract_issues'],
                          results=results, independent_cases=sum(r['javascript']['tests_total'] for r in results
                              if r['status'] == 'scored' and r['group'].startswith('independent:')),
                          independent_passed=sum(r['javascript']['tests_passed'] for r in results
                              if r['status'] == 'scored' and r['group'].startswith('independent:')))
        except Exception as error:
            record = dict(seal, qualified=False, execution_passed=False, results=results,
                          infrastructure_error=f'{type(error).__name__}: {error}')
        write(target / 'receipt.json', record)
        small = {k: v for k, v in record.items() if k not in ['groups', 'results']}
        summary.append(small)
        print(json.dumps(small), flush=True)
    write(results_dir / 'summary.json', {'rows': summary, 'wall_seconds': time.monotonic() - started,
                                        'qualified': sum(r['qualified'] for r in summary),
                                        'execution_passed': sum(r['execution_passed'] for r in summary)})


if __name__ == '__main__':
    main()
