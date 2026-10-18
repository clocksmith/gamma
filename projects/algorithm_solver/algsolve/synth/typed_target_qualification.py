"""Teacher-only qualification of reserved targets; never a training data source.

Proposals are sealed before independent tests are loaded. Raw targets, failure
details and test receipts stay under runs/protected/. Only aggregate counts and
hashes may be published. This does not qualify a student or authorize changing
the frozen development corpus in response to protected failures.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from .. import public_examples, splits, validate
from ..records import LANE_ROOT, load_hidden_tests
from . import typed_codec as codec, typed_confirmation as confirmation, typed_support


def problem_identity(problem):
    return codec.digest({'uid': problem.uid, 'statement': problem.statement,
                         'params': problem.params, 'entry': problem.entry,
                         'public': problem.public_tests})


def validate_proposals(rows, contract):
    pool = {r['key']: r for r in contract['reservation']['pool']}
    keys = [r['key'] for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != set(pool):
        raise ValueError('Proposals must retain every reserved key exactly once')
    for row in rows:
        if row.get('disposition') not in ('candidate', 'excluded'):
            raise ValueError('Every reserved key requires an explicit disposition')
        if row['disposition'] == 'excluded':
            if not row.get('reason') or not row.get('detail') or 'program' in row:
                raise ValueError('Exclusion requires reason and review, not a target')
        else:
            for field in ('program', 'requirements', 'bound_probe', 'problem_sha256', 'proposer'):
                if not row.get(field):
                    raise ValueError('Candidate missing ' + field)
            if not row['requirements'].get('declared_input_bounds') or not row['requirements'].get('complexity_review'):
                raise ValueError('Candidate lacks bounds and complexity review')
            if 'args' not in row['bound_probe'] or 'expected' not in row['bound_probe']:
                raise ValueError('Candidate lacks a declared-bound probe')
    return pool


def qualify(row, entry, problem, pairs, identity, *, judge=validate.judge_problem,
            independent_loader=load_hidden_tests):
    if row['disposition'] == 'excluded':
        return {'key': row['key'], 'status': 'excluded', 'reason': row['reason'], 'detail': row['detail']}, None
    record = {'key': row['key'], 'uid': entry['judge_uid'], 'status': 'rejected'}
    if problem is None:
        return {**record, 'reason': 'missing_problem'}, None
    problem = public_examples.recover(problem)
    if row['problem_sha256'] != problem_identity(problem):
        raise ValueError('Problem source differs from sealed proposal')
    if problem.io_mode != 'functional' or not problem.public_tests or problem.evidence_ceiling != 'independent_tests_passed':
        return {**record, 'reason': 'missing_public_or_independent_evidence'}, None
    try:
        target = codec.encode(row['program'], identity)
        source = codec.render(target, identity, method=problem.entry['method'], params=[p[0] for p in problem.params])
        candidate = {'uid': problem.uid, 'problem_family': entry['family'], 'target': target,
                     'pattern_sha256': typed_support.pattern(row['program'])}
        fit = [p for p in pairs if p['learning_split'] == 'development_fit']
        support = typed_support.audit(fit, [candidate])['candidates'][0]
        # Feature support is fit-only; novelty must exclude both fit and audit.
        overlap = typed_support.audit(pairs, [candidate])['candidates'][0]['overlap']
    except (ValueError, KeyError, TypeError) as error:
        return {**record, 'reason': 'structural_rejection', 'error': str(error)}, None
    record.update(graph_sha256=codec.digest(target), support=support, development_overlap=overlap)
    if not support['supported']:
        return {**record, 'reason': 'unsupported_training_features'}, None
    if overlap:
        return {**record, 'reason': 'development_overlap'}, None
    # No tests are read before the sealed graph passes support/novelty gates.
    independent = independent_loader(problem)
    if not independent:
        return {**record, 'reason': 'missing_independent_tests'}, None
    record['independent_tests_sha256'] = codec.digest(independent)
    record['public_tests_sha256'] = codec.digest(problem.public_tests)
    record['source_sha256'] = codec.digest(source)
    for stage, tests in (('public', problem.public_tests), ('independent', independent),
                         ('declared_bound_probe', [row['bound_probe']])):
        verdict = judge(problem, source, tests)
        record[stage] = verdict.to_dict()
        if not verdict.passed:
            return {**record, 'reason': stage + '_failure'}, None
    record.update(status='qualified', reason='qualified')
    # Deliberately not a typed-pair schema: no learning_split or model input.
    protected = {**candidate, 'schema': 'algsolve.protected-target.v1',
                 'purpose': 'teacher qualification and final scoring only; forbidden training/retrieval input',
                 'graph_sha256': record['graph_sha256'], 'problem_sha256': row['problem_sha256'],
                 'required_features': typed_support.features(row['program']),
                 'requirements': row['requirements'], 'proposer': row['proposer']}
    return record, protected


def run(contract_path, pairs_path, proposals_path, output):
    contract, pairs = confirmation.check(contract_path, pairs_path)
    output = Path(output).resolve()
    if not output.is_relative_to((LANE_ROOT/'runs/protected').resolve()):
        raise ValueError('Protected qualification must stay under runs/protected/')
    rows = confirmation.read_rows(proposals_path)
    pool = validate_proposals(rows, contract)
    # Source and data seal precedes loading independent tests or judging.
    source_files = [Path(__file__), LANE_ROOT/'algsolve/validate.py', LANE_ROOT/'algsolve/records.py',
                    LANE_ROOT/'algsolve/public_examples.py', LANE_ROOT/'algsolve/test_corrections.py',
                    *sorted((LANE_ROOT/'algsolve/judge').glob('*.py'))]
    sources = {str(p.relative_to(LANE_ROOT)): confirmation.sha(p) for p in source_files}
    proposal_hash = confirmation.sha(proposals_path)
    seal = {'schema': 'algsolve.protected-target-qualification.v1',
            'confirmation_sha256': confirmation.sha(contract_path), 'codec_sha256': contract['codec_sha256'],
            'development_sha256': confirmation.sha(pairs_path), 'proposals_sha256': proposal_hash,
            'sources_sha256': sources, 'reserved_entries': len(pool),
            'policy': 'one frozen teacher proposal per entry; no test-driven repair or corpus/vocabulary feedback',
            'test_authority': 'existing independent suites; no protected-suite replacement',
            'teacher': 'offline agent-authored; independent refers to tests, not a second author',
            'student_trained': False, 'student_evaluated': False}
    output.mkdir(parents=True, exist_ok=False)
    (output/'seal.json').write_text(json.dumps(seal, indent=2)+'\n')
    (output/'proposals.jsonl').write_bytes(Path(proposals_path).read_bytes())
    problems = splits.load_all()
    counts, records, targets = Counter(), [], []
    print('[run-contract] run_name='+output.name+' pairs_input_spec=frozen-protected-teacher-proposals '
          'resume_from=none decode=none device=cpu runtime_mode=linux-sandbox training=none', flush=True)
    for row in rows:
        entry = pool[row['key']]
        record, target = qualify(row, entry, problems.get(entry['judge_uid']), pairs, contract['codec_sha256'])
        records.append(record)
        counts[record['reason']] += 1
        if target:
            targets.append(target)
        with (output/'qualification.jsonl').open('a') as stream:
            stream.write(json.dumps(record)+'\n')
        print(json.dumps({'completed': len(records), 'total': len(rows), 'qualified': len(targets)}), flush=True)
    confirmation.check(contract_path, pairs_path)
    if confirmation.sha(proposals_path) != proposal_hash or any(confirmation.sha(LANE_ROOT/p) != h for p,h in sources.items()):
        raise ValueError('Qualification inputs or implementation changed during run')
    (output/'targets.jsonl').write_text(''.join(json.dumps(t)+'\n' for t in targets))
    summary = {'schema': 'algsolve.protected-target-summary.v1', 'reserved_entries': len(pool),
               'reviewed_entries': len(records), 'teacher_candidates': sum(r['disposition']=='candidate' for r in rows),
               'qualified_targets': len(targets), 'counts': dict(counts),
               'public_test_executions_passed': sum(r.get('public',{}).get('tests_passed',0) for r in records),
               'independent_test_executions_passed': sum(r.get('independent',{}).get('tests_passed',0) for r in records),
               'declared_bound_probes_passed': sum(r.get('declared_bound_probe',{}).get('passed',False) for r in records),
               'confirmation_sha256': seal['confirmation_sha256'], 'codec_sha256': seal['codec_sha256'],
               'development_sha256': seal['development_sha256'], 'development_unchanged': True,
               'artifacts_sha256': {name: confirmation.sha(output/name) for name in
                                   ('seal.json','proposals.jsonl','qualification.jsonl','targets.jsonl')},
               'teacher_qualification_complete': True, 'student_trained': False, 'student_evaluated': False,
               'limits': ['Selected teacher decompositions, not the representational ceiling.',
                          'Independent finite test agreement, not formal equivalence or benchmark acceptance.',
                          'One maximum-size probe and reviewed complexity do not prove all resource bounds.',
                          'Unsupported and failed targets remain in the 66-entry denominator.',
                          'Do not adapt development data, vocabulary or model selection to protected diagnostics.'],
               'next_gate': 'Train using frozen development data only; seal routes/checkpoint before protected student scoring.'}
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--pairs', type=Path, default=LANE_ROOT/'runs/typed-real-dev-v5/pairs.jsonl')
    parser.add_argument('--proposals', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.contract, args.pairs, args.proposals, args.output)


if __name__ == '__main__':
    main()
