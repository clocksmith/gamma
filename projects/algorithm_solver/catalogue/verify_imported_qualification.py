"""Recompute complete frozen-test verdicts from retained isolated observations.

This does not rerun candidates or trust their pass flags. Expectations originate
in the independently authored, historically pinned test files. It intentionally
implements comparison separately from the execution runner.
"""
import argparse
import json
from pathlib import Path

from . import imported_qualification as q


def equal(left, right):
    if type(left) != type(right):
        return False
    if type(left) is dict:
        return set(left) == set(right) and all(equal(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(equal(left[i], right[i]) for i in range(len(left)))
    return left == right


def independent_failures(raw, cases, language, policy='exact'):
    observations = [q.decode(line) for line in raw.splitlines()]
    if len(observations) != len(cases) + 1 or observations.pop() != {'done': len(cases)}:
        raise ValueError('incomplete output protocol')
    failures = []
    for i in range(len(cases)):
        record, case = observations[i], cases[i]
        if type(record) is not dict or type(record.get('i')) is not int or record['i'] != i:
            raise ValueError('out-of-order or duplicate observation')
        expected = case['expected']
        kind = type(expected).__name__
        if language == 'javascript':
            kind = {'int': 'number', 'float': 'number', 'bool': 'boolean', 'str': 'string',
                    'NoneType': 'object', 'dict': 'object', 'list': 'object'}[kind]
        got = record.get('result')
        if policy == 'set-of-strings':
            same = (type(got) is list and all(type(x) is str for x in got)
                    and len(got) == len(set(got)) and set(got) == set(expected))
        elif policy == 'permutation-of-chars':
            from collections import Counter
            same = type(got) is str and Counter(got) == Counter(expected)
        elif policy == 'exact':
            same = equal(got, expected)
        else:
            raise ValueError('unregistered comparison policy')
        if 'error' in record:
            reason = 'candidate_error'
        elif record.get('result_type') != kind:
            reason = 'result_type'
        elif not same:
            reason = 'result_value'
        elif not equal(record.get('args_before'), case['args']) or not equal(record.get('args_after'), case['args']):
            reason = 'input_effects'
        elif not equal(record.get('alias_edges'), []):
            reason = 'return_aliases'
        else:
            continue
        failures.append({'index': i, 'reason': reason})
    return failures


def verify(path):
    raw = q.read(path, 32 * 1024**2)
    report = q.decode(raw)
    freeze = Path(report['freeze'])
    frozen, contract, gate = q.load_freeze(freeze)
    if report['status'] != 'completed' or report['freeze_sha256'] != q.sha(frozen):
        raise ValueError('completed hash-bound execution required')
    jobs, rows = contract['jobs'], report['rows']
    if [(r['id'], r['language']) for r in rows] != [(j['id'], j['language']) for j in jobs]:
        raise ValueError('missing/duplicate/reordered candidate outcomes')
    outcomes = []
    for job, row in zip(jobs, rows):
        source, cases = q.job_inputs(freeze, job, gate)
        if row['source_sha256'] != q.sha(source) or row['cases'] != len(cases):
            raise ValueError('source/case identity mismatch')
        groups = list(q.batches(cases))
        if len(groups) != len(row['calls']):
            raise ValueError('missing batch observations')
        failures = []
        for call, (offset, batch) in zip(row['calls'], groups):
            stem = f"{job['id']}-{job['language']}-{offset}"
            if call['stem'] != stem or call['offset'] != offset or call['count'] != len(batch):
                raise ValueError('batch binding mismatch')
            stdout = q.read(path.parent / (stem + '.stdout'))
            stderr = q.read(path.parent / (stem + '.stderr'))
            if q.sha(stdout) != call['stdout_sha256'] or q.sha(stderr) != call['stderr_sha256']:
                raise ValueError('raw observation hash mismatch')
            if call['exit_code'] != 0 or call['timed_out'] or call['output_limit_exceeded']:
                failures.append({'offset': offset, 'reason': 'isolated_execution_failed'})
            else:
                try:
                    failures.extend({'offset': offset, **f} for f in independent_failures(stdout, batch, job['language'], job.get('comparison_policy', 'exact')))
                except (ValueError, TypeError, KeyError) as error:
                    failures.append({'offset': offset, 'reason': 'invalid_output', 'error': str(error)})
        if row['failures'] != failures or row['passed'] is not (not failures):
            raise ValueError('independent observation replay disagrees')
        outcomes.append({'id': job['id'], 'language': job['language'], 'passed': not failures,
                         'source_sha256': q.sha(source), 'tests_raw_sha256': job['tests_raw_sha256'],
                         'cases': len(cases), 'failure_count': len(failures)})
    return {'schema': 'gamma.imported-independent-verification.v1', 'verified': True,
            'report_sha256': q.sha(raw), 'freeze_sha256': q.sha(frozen),
            'verifier_sha256': q.file_hash(__file__), 'outcomes': outcomes,
            'passed': sum(o['passed'] for o in outcomes), 'total': len(outcomes),
            'cases': sum(o['cases'] for o in outcomes), 'new_qualifications': 0,
            'scope': contract['scope'], 'automatic_promotion': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.report)
    q.write(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'outcomes'}))


if __name__ == '__main__':
    main()
