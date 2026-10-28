"""Rebuild host expectations and replay every raw observation without running candidates."""
import argparse
import json
from pathlib import Path

import oracles as o
from qualify import artifacts, encoded, load_cases, sha, verdict, write


def verify(freeze, statements, output):
    raw = freeze.read_bytes()
    contract = json.loads(raw)
    if artifacts() != contract['artifact_hashes']:
        raise ValueError('verifier sources differ from freeze')
    identity = json.loads((output / 'run-identity.json').read_bytes())
    assert identity['freeze_sha256'] == sha(raw)
    assert identity['artifact_hashes'] == contract['artifact_hashes']
    data = load_cases(statements, contract['statement_pins'])
    assert sha(encoded(data)) == contract['cases_sha256']
    observations, summaries, evidence = 0, [], {}
    for pid in o.IDS:
        for language in ('python', 'javascript'):
            failures, total = [], 0
            for b, indices in enumerate(contract['batch_plan'][str(pid)]):
                stem = f'{pid}-{language}-{b:03d}'
                start = json.loads((output / (stem + '.start.json')).read_bytes())
                packet = {'entry': 'solve', 'calls': [{'args': data[pid][i]['args']} for i in indices]}
                assert start == {'problem_id': pid, 'language': language, 'indices': indices,
                                 'inputs_sha256': sha(encoded(packet))}
                metadata = json.loads((output / (stem + '.result.json')).read_bytes())
                for stream in ('stdout', 'stderr'):
                    assert sha((output / (stem + '.' + stream)).read_bytes()) == metadata[stream + '_sha256']
                failures += verdict(pid, language, data[pid], indices, metadata,
                                    (output / (stem + '.stdout')).read_bytes())
                total += len(indices)
                observations += 1
            row = {'problem_id': pid, 'language': language, 'distinct_cases': len(data[pid]),
                   'generated_cases': len(data[pid]), 'executed_calls': total,
                   'failures': failures, 'passed': not failures,
                   'mandatory_constraint_failure': o.MANDATORY_FAILURES.get((pid,language)),
                   'qualified': not failures and pid!=760 and (pid,language) not in o.MANDATORY_FAILURES,
                   'official_wrapper_execution_qualified': False,
                   'definition_gate_failure': 'Official premium definition unavailable; mapping semantics provisional' if pid==760 else None,
                   'scoped_test_qualified': not failures and pid!=760}
            assert json.loads((output / f'{pid}-{language}.summary.json').read_bytes()) == row
            summaries.append(row)
    expected_report = {'freeze_sha256': sha(raw), 'programs': summaries,
                       'passed': all(r['passed'] for r in summaries), 'canonical_admission_changed': False,
                       'qualification_scope': 'Functional solve adapter only; official wrappers not execution-qualified'}
    assert json.loads((output / 'report.json').read_bytes()) == expected_report
    for p in sorted(output.iterdir()):
        if p.is_file() and p.name not in ('replay.json',):
            evidence[p.name] = sha(p.read_bytes())
    return {'schema': 'gamma.downloaded-remaining-raw-replay.v1', 'freeze_sha256': sha(raw),
            'sandbox_batches_replayed': observations, 'programs_replayed': len(summaries),
            'programs_passed': sum(r['passed'] for r in summaries),
            'programs_qualified':sum(r['qualified'] for r in summaries),
            'calls_replayed': sum(r['executed_calls'] for r in summaries),
            'independently_regenerated_cases': sum(len(v) for v in data.values()),
            'raw_artifact_hashes': evidence, 'all_observations_match_report': True,
            'canonical_admission_changed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--statements', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.freeze, args.statements, args.output)
    write(args.output / 'replay.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'raw_artifact_hashes'}))
