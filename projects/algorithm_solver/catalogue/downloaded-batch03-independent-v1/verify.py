"""Rebuild host expectations and verify frozen contracts and observation receipts without running candidates."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))

import oracles as o
from qualify import artifacts, encoded, load_cases, sha, verdict, write


def verify(freeze_path, statements_path, output_path=None):
    raw = freeze_path.read_bytes()
    contract = json.loads(raw)
    current_artifacts = artifacts()
    for p, h in contract['artifact_hashes'].items():
        if current_artifacts.get(p) != h:
            raise ValueError(f'verifier source drift: {p}')

    data = load_cases(statements_path, contract['statement_pins'])
    if sha(encoded(data)) != contract['cases_sha256']:
        raise ValueError('cases sha256 mismatch')

    res = {
        'schema': 'gamma.downloaded-batch03-independent-v1.verification-receipt.v1',
        'freeze_sha256': sha(raw),
        'statement_pins_verified': len(contract['statement_pins']),
        'artifact_files_verified': len(contract['artifact_hashes']),
        'problems_verified': len(data),
        'cases_regenerated': sum(len(v) for v in data.values()),
        'all_contracts_intact': True,
        'canonical_admission_changed': False
    }

    if output_path and output_path.exists():
        identity = json.loads((output_path / 'run-identity.json').read_bytes())
        assert identity['freeze_sha256'] == sha(raw)
        report = json.loads((output_path / 'report.json').read_bytes())
        assert report['freeze_sha256'] == sha(raw)
        if report.get('execution_status') == 'unexecuted':
            receipt = json.loads((output_path / 'unexecuted-receipt.json').read_bytes())
            assert receipt['freeze_sha256'] == sha(raw)
            res['execution_status'] = 'unexecuted'
            res['unexecuted_receipt_verified'] = True
            res['judge_tool_missing'] = receipt.get('judge_binary_required')
        else:
            # Replay executed observations
            observations, summaries, evidence = 0, [], {}
            for pid in o.IDS:
                for language in ('python', 'javascript'):
                    failures, total = [], 0
                    for b, indices in enumerate(contract['batch_plan'][str(pid)]):
                        stem = f'{pid}-{language}-{b:03d}'
                        start = json.loads((output_path / (stem + '.start.json')).read_bytes())
                        packet = {'entry': 'solve', 'calls': [{'args': data[pid][i]['args']} for i in indices]}
                        assert start == {'problem_id': pid, 'language': language, 'indices': indices,
                                         'inputs_sha256': sha(encoded(packet))}
                        metadata = json.loads((output_path / (stem + '.result.json')).read_bytes())
                        for stream in ('stdout', 'stderr'):
                            assert sha((output_path / (stem + '.' + stream)).read_bytes()) == metadata[stream + '_sha256']
                        failures += verdict(pid, language, data[pid], indices, metadata,
                                            (output_path / (stem + '.stdout')).read_bytes())
                        total += len(indices)
                        observations += 1
                    row = {
                        'problem_id': pid, 'language': language, 'distinct_cases': len(data[pid]),
                        'generated_cases': len(data[pid]), 'executed_calls': total,
                        'failures': failures, 'passed': not failures,
                        'mandatory_constraint_failure': o.MANDATORY_FAILURES.get((pid, language)),
                        'qualified': not failures and (pid, language) not in o.MANDATORY_FAILURES,
                        'official_wrapper_execution_qualified': False
                    }
                    assert json.loads((output_path / f'{pid}-{language}.summary.json').read_bytes()) == row
                    summaries.append(row)
            res['execution_status'] = 'executed'
            res['batches_replayed'] = observations
            res['programs_replayed'] = len(summaries)
            res['programs_passed'] = sum(r['passed'] for r in summaries)
            res['all_observations_match_report'] = True

    return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--statements', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(args.freeze, args.statements, args.output)
    if args.output and args.output.exists():
        write(args.output / 'replay.json', result)
    print(json.dumps(result, indent=2))
