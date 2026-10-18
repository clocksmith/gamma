"""Qualify real development targets under a frozen codec; no student training."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import time

from .. import public_examples, splits, validate
from ..records import LANE_ROOT, load_hidden_tests
from . import audit, mine, training_pairs, typed_codec as codec
from . import development_tests, typed_development as dev, typed_program as ir, typed_recipes, typed_support


def qualify(row, allowed, problems, identity):
    uid = row['uid']
    if uid not in allowed:
        return None, {'reason': 'not_permitted_development'}
    problem = public_examples.recover(problems[uid])
    if (problem.io_mode != 'functional' or not problem.public_tests
            or problem.evidence_ceiling != 'independent_tests_passed'):
        return None, {'reason': 'missing_functional_public_or_independent_evidence'}
    if row['requirements']['unsupported_requirements']:
        return None, {'reason': 'unsupported_requirements', 'details': row['requirements']}
    started = time.perf_counter()
    try:
        target = codec.encode(row['program'], identity)
        source = codec.render(target, identity, method=problem.entry['method'], params=[p[0] for p in problem.params])
        required = typed_support.features(row['program'])
    except (ValueError, KeyError, TypeError) as error:
        return None, {'reason': 'structural_rejection', 'error': str(error)}
    assembly = time.perf_counter() - started
    independent = load_hidden_tests(problem)
    if not independent: return None, {'reason': 'missing_independent_tests'}
    independent, test_source = development_tests.select(uid, independent)
    public = validate.judge_problem(problem, source, problem.public_tests)
    hidden = validate.judge_problem(problem, source, independent) if public.passed else None
    bounds = validate.judge_problem(problem, source, [row['bound_probe']]) if hidden and hidden.passed else None
    ok = bool(bounds and bounds.passed)
    verdict = {'reason': 'qualified' if ok else 'test_failure',
               'public': public.to_dict(), 'independent': hidden.to_dict() if hidden else None,
               'declared_bound_probe': bounds.to_dict() if bounds else None,
               'test_source': test_source,
               'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
               'assembly_seconds': assembly, 'total_seconds': time.perf_counter()-started}
    if not ok: return None, verdict
    entry = allowed[uid]
    pair = {'schema': 'algsolve.typed-pair.v1', 'uid': uid, 'key': entry.key, 'variant': row['variant'],
            'problem_family': splits.sibling_base(entry.slug),
            'input': {'statement': problem.statement, 'starter_code': problem.starter_code,
                      'params': problem.params, 'public_examples': problem.public_tests},
            'target': target, 'graph_sha256': codec.digest(target),
            'pattern_sha256': typed_support.pattern(row['program']),
            'required_features': required, 'recipe_usage': [f.removeprefix('recipe:') for f in required if f.startswith('recipe:')],
            'requirements': row['requirements'],
            'provenance': {'license': entry.license, 'attribution': entry.attribution,
                           'proposer': row['proposer'], 'source_sha256': verdict['source_sha256'],
                           'problem_sha256': codec.digest({'statement': problem.statement, 'starter': problem.starter_code,
                                                          'params': problem.params, 'public': problem.public_tests}),
                           'independent_tests_sha256': mine.digest(independent),
                           'test_source': test_source,
                           'public_tests_passed': public.tests_passed, 'independent_tests_passed': hidden.tests_passed,
                           'declared_bound_probe_passed': True, 'codec_sha256': identity,
                           'qualification': 'finite development-test agreement plus declared-bound probe; no prediction or formal proof'}}
    return pair, verdict


def negatives(qualified, problems, identity):
    rows = []
    for pair in qualified:
        program = copy.deepcopy(pair['target']['program'])
        if pair['uid'] == 'lcd:1464' and pair['variant'] == 'max_heap':
            program['return']['op'] = 'add'
            reason = 'wrong_aggregation_operator'
        elif pair['uid'] == 'lcd:1512' and pair['variant'] == 'frequency_map':
            program['body'][2]['body'][0]['args'][-1] = {'literal': 1}
            reason = 'incorrect_missing_key_default'
        else: continue
        target = codec.encode(program, identity)
        problem = public_examples.recover(problems[pair['uid']])
        source = codec.render(target, identity, method=problem.entry['method'], params=[p[0] for p in problem.params])
        verdict = validate.judge_problem(problem, source, problem.public_tests)
        if verdict.passed or not verdict.first_failure:
            raise ValueError('Proposed negative has no counterexample')
        rows.append({'uid': pair['uid'], 'reason': reason, 'target': target,
                     'counterexample_source': 'public development example', 'verdict': verdict.to_dict()})
    return rows


def corpus_support(pairs):
    all_features = set().union(*(set(p['required_features']) for p in pairs))
    admitted = ({'pure:' + op for op in ir.PURE} | {'effect_operator:' + op for op in ir.EFFECTS}
                | {'resource:' + t for t in ir.RESOURCES} | {'recipe:' + r for r in typed_recipes.catalog()})
    leave_family_out = []
    # Audit before any proposed split. All targets were already inspected and
    # cannot become a protected set. This diagnoses support gaps only.
    for family in sorted({p['problem_family'] for p in pairs}):
        training = [p for p in pairs if p['problem_family'] != family]
        candidates = [p for p in pairs if p['problem_family'] == family]
        report = typed_support.audit(training, candidates)
        leave_family_out.append({'family': family, **report})
    return {'admitted_features': sorted(admitted), 'observed_features': sorted(all_features),
            'missing_admitted_features': sorted(admitted-all_features),
            'leave_family_out': leave_family_out,
            'fresh_protected_set_reserved': False, 'training_authorized_by_this_audit': False,
            'limitations': ['Corpus-wide coverage does not ensure support survives a family-disjoint split.',
                           'All these targets and variants are development-only; no protected evaluation has run.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codec', type=Path, required=True)
    parser.add_argument('--confirmation', type=Path, required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum(): raise ValueError('Invalid run name')
    identity = codec.frozen(args.codec)
    audit.require_frozen()
    es, ps, manifest = splits.read_index_entries(), splits.load_all(), splits.load_manifest()
    reserved = json.loads(args.confirmation.read_text())
    allowed = training_pairs.policy(es, ps, manifest, reserved, set(ps))
    rows = dev.proposed()
    directory = LANE_ROOT/'runs'/args.name
    directory.mkdir(parents=True, exist_ok=False)
    sources = ['synth/typed_pairs.py', 'synth/typed_development.py', 'synth/typed_support.py', 'synth/development_tests.py',
               'synth/training_pairs.py', 'public_examples.py', 'values.py', 'importers.py',
               'validate.py', 'records.py', 'test_corrections.py', 'judge/judge.py',
               'judge/functional_semantics.py', 'judge/harness_functional.py', 'judge/sandbox.py']
    contract = {'schema': 'algsolve.typed-qualification.v1', 'codec_sha256': identity,
                'codec_file_sha256': training_pairs.sha(args.codec), 'proposal_sha256': codec.digest(rows),
                'source_sha256': {n: training_pairs.sha(LANE_ROOT/'algsolve'/n) for n in sources},
                'research_index_sha256': mine.digest([e.__dict__ for e in es]),
                'manifest_sha256': mine.digest(manifest), 'confirmation_sha256': training_pairs.sha(args.confirmation),
                'policy': 'permitted research development only; excludes solving, recognition and reserved sibling families',
                'model_calls': 0, 'student_trained': False,
                'execution_budget': codec.EXECUTION_BUDGET,
                'teacher': 'offline hand-authored typed decomposition',
                'test_boundary': 'expected outputs remain on host; candidate receives inputs only'}
    (directory/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    print(f'[run-contract] run_name={args.name} pairs_input_spec=permitted-real-development '
          f'codec={identity} resume_from=none decode=none device=cpu runtime_mode=linux-sandbox '
          'schedule=serial eval_dataset_paths=development-only training=none', flush=True)
    pairs, verdicts = [], []
    for row in rows:
        pair, verdict = qualify(row, allowed, ps, identity)
        record = {'uid': row['uid'], 'variant': row['variant'], **verdict}
        verdicts.append(record)
        with (directory/'verdicts.jsonl').open('a') as stream: stream.write(json.dumps(record)+'\n')
        if pair: pairs.append(pair)
        print(json.dumps({'uid': row['uid'], 'variant': row['variant'], 'reason': verdict['reason']}), flush=True)
    exclusions = [{**r, 'development_policy_passed': r['uid'] in allowed} for r in dev.unsupported() if r['uid'] in allowed]
    rejected = negatives(pairs, ps, identity)
    support = corpus_support(pairs)
    # Preserve grouping of problems, sibling families, and alternative patterns.
    training_pairs.assign_splits(pairs)
    for p in pairs:
        p['learning_split'] = ('development_fit' if p['learning_split'] == 'training' else 'development_audit')
    split = typed_support.audit([p for p in pairs if p['learning_split']=='development_fit'],
                                [p for p in pairs if p['learning_split']=='development_audit'])
    support['proposed_development_split'] = split
    summary = {'proposals': len(rows), 'qualified_pairs': len(pairs), 'distinct_problems': len({p['uid'] for p in pairs}),
               'codec_sha256': identity,
               'counts': dict(Counter(v['reason'] for v in verdicts)),
               'independent_tests_passed': sum(p['provenance']['independent_tests_passed'] for p in pairs),
               'public_tests_passed': sum(p['provenance']['public_tests_passed'] for p in pairs),
               'bound_probes_passed': len(pairs), 'explicit_exclusions': exclusions,
               'test_sources': dict(Counter(p['provenance']['test_source']['kind'] for p in pairs)),
               'counterexample_backed_negatives': len(rejected),
               'missing_admitted_features': support['missing_admitted_features'],
               'development_partitions': dict(Counter(p['learning_split'] for p in pairs)),
               'proposed_split_supported': split['all_supported'],
               'student_trained': False, 'protected_generalization': None,
               'next_gate': 'Preserve all examined targets as development; build support across disjoint families, reserve fresh protected structures, then train.',
               'limits': ['Selected authored targets, not random problem coverage.',
                          'Passing sandbox tests and maximum-input probes qualifies development labels, not neural prediction.',
                          'Requirement complexity is reviewed, not mechanically proven; probe sizes do not prove all resource bounds.',
                          'Different correct graphs and their tests are retained together.']}
    for name, value in [('pairs',pairs), ('negatives',rejected)]:
        (directory/f'{name}.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in value))
    summary['artifacts_sha256'] = {name: training_pairs.sha(directory/name)
                                  for name in ['pairs.jsonl','negatives.jsonl','verdicts.jsonl','contract.json']}
    summary['support_audit_sha256'] = codec.digest(support)
    for name, value in [('summary', summary), ('support_audit', support), ('exclusions', exclusions)]:
        (directory/f'{name}.json').write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
