"""Qualify explicit development call graphs, never protected evaluation tasks.

This expands development beyond the old 60-row audit using only the permitted
research index. Existing recognition, solving, and fresh confirmation families
stay excluded. Independent tests qualify training labels, not runtime predictions.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

from .. import splits, validate
from ..records import LANE_ROOT, load_hidden_tests
from . import audit, call_graph, mine, training_pairs


def graph_pattern(target):
    # Conservatively group identical AST shapes, ignoring names/scalars (even
    # different port bindings). This is not a semantic novelty proof.
    def shape(source):
        return [type(n).__name__ for n in ast.walk(ast.parse(source, mode='eval'))]
    return mine.digest([[(node['operator'], [shape(arg) for arg in node['arguments']])
                        for node in target['nodes']], shape(target['answer'])])


def qualify(row, allowed, problems):
    uid = row['uid']
    if uid not in allowed:
        return None, {'reason': 'not_permitted_development'}
    problem, entry = problems[uid], allowed[uid]
    if (problem.io_mode != 'functional' or not problem.public_tests
            or problem.evidence_ceiling != 'independent_tests_passed'):
        return None, {'reason': 'missing_functional_io_or_public_or_independent_tests'}
    target = {'schema': call_graph.SCHEMA, 'vocabulary_sha256': call_graph.vocabulary_hash(),
              'nodes': row['nodes'], 'answer': row['answer']}
    started = time.perf_counter()
    try:
        compiled = call_graph.compile_graph(target, method=problem.entry['method'], params=[p[0] for p in problem.params])
    except (ValueError, TypeError, SyntaxError, KeyError) as error:
        return None, {'reason': 'structural_rejection', 'error': str(error)}
    compile_seconds = time.perf_counter() - started
    independent = load_hidden_tests(problem)
    if not independent:
        return None, {'reason': 'missing_independent_tests'}
    started = time.perf_counter()
    public = validate.judge_problem(problem, compiled.source, problem.public_tests)
    hidden = validate.judge_problem(problem, compiled.source, independent) if public.passed else None
    verdict = {'reason': 'qualified' if hidden and hidden.passed else 'test_failure',
               'public': public.to_dict(), 'independent': hidden.to_dict() if hidden else None,
               'source_sha256': hashlib.sha256(compiled.source.encode()).hexdigest(),
               'glue_ast_nodes': compiled.glue_nodes, 'compile_seconds': compile_seconds,
               'verification_seconds': time.perf_counter() - started}
    if verdict['reason'] != 'qualified':
        return None, verdict
    pair = {'schema': 'algsolve.composition-pair.v2', 'uid': uid, 'key': entry.key,
            'problem_family': splits.sibling_base(entry.slug),
            'input': {'statement': problem.statement, 'starter_code': problem.starter_code,
                      'params': problem.params, 'public_examples': problem.public_tests},
            'target': target, 'pattern_sha256': graph_pattern(target),
            'provenance': {'license': entry.license, 'attribution': entry.attribution,
                           'proposer': row['proposer'], 'source_sha256': verdict['source_sha256'],
                           'independent_tests_sha256': mine.digest(independent),
                           'public_tests_passed': public.tests_passed,
                           'independent_tests_passed': hidden.tests_passed,
                           'qualification': 'fresh development tests; finite agreement, not equivalence'}}
    return pair, verdict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposals', type=Path, required=True)
    parser.add_argument('--confirmation', type=Path, required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum():
        raise ValueError('Invalid run name')
    audit.require_frozen()  # V1 hash must remain unchanged.
    proposals = json.loads(args.proposals.read_text())
    if proposals.get('schema') != 'algsolve.call-graph-proposals.v2':
        raise ValueError('Unknown proposal schema')
    entries, problems, manifest = splits.read_index_entries(), splits.load_all(), splits.load_manifest()
    confirmation = json.loads(args.confirmation.read_text())
    allowed = training_pairs.policy(entries, problems, manifest, confirmation, set(problems))
    directory = LANE_ROOT/'runs'/args.name
    directory.mkdir(parents=True, exist_ok=False)
    contract = {'schema': 'algsolve.call-graph-qualification.v2', 'vocabulary_sha256': call_graph.vocabulary_hash(),
                'v1_sha256': audit.vocabulary_hash(), 'research_index_sha256': mine.digest([e.__dict__ for e in entries]),
                'proposals_sha256': training_pairs.sha(args.proposals),
                'confirmation_sha256': training_pairs.sha(args.confirmation),
                'manifest_sha256': mine.digest(manifest),
                'exporter_sha256': training_pairs.sha(Path(__file__)),
                'judge_sources': {name: training_pairs.sha(LANE_ROOT/'algsolve'/name) for name in
                                  ['validate.py', 'records.py', 'test_corrections.py', 'judge/judge.py',
                                   'judge/functional_semantics.py', 'judge/harness_functional.py', 'judge/sandbox.py']},
                'development_policy': 'research index minus solving, recognition, and reserved confirmation sibling families',
                'input_policy': 'statement, starter, params, public examples; no independent tests',
                'limits': {'nodes': call_graph.MAX_NODES, 'glue_ast_nodes': call_graph.MAX_GLUE_NODES},
                'catalog': call_graph.catalog(), 'model_calls': 0, 'student_trained': False}
    (directory/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    print(f'[run-contract] run_name={args.name} pairs_input_spec={args.proposals} '
          'resume_from=none resume_stage=none decode=none eval_dataset_paths=development-only '
          'device=cpu schedule=serial runtime_mode=linux-sandbox sweep_mode=after_train', flush=True)
    pairs, counts, reuse, seen = [], Counter(), {}, set()
    with (directory/'verdicts.jsonl').open('w') as stream:
        for row in proposals['rows']:
            identity = mine.digest(row)
            if identity in seen:
                raise ValueError('Duplicate proposal')
            seen.add(identity)
            pair, verdict = qualify(row, allowed, problems)
            counts[verdict['reason']] += 1
            stream.write(json.dumps({'uid': row['uid'], **verdict})+'\n'); stream.flush()
            if pair:
                pair['provenance']['proposals_sha256'] = contract['proposals_sha256']
                pairs.append(pair)
                for operator in {node['operator'] for node in pair['target']['nodes']}:
                    reuse.setdefault(operator, set()).add(pair['key'])
            print(f'[graph] {row["uid"]} {verdict["reason"]} {verdict.get("error", "")}', flush=True)
    training_pairs.assign_splits(pairs)
    (directory/'pairs.jsonl').write_text(''.join(json.dumps(pair)+'\n' for pair in pairs))
    summary = {'counts': dict(counts), 'distinct_problems': len({p['uid'] for p in pairs}),
               'learning_splits': dict(Counter(p['learning_split'] for p in pairs)),
               'operator_reuse': {op: sorted(keys) for op, keys in reuse.items()},
               'new_algorithm': 'window_sums; all other algorithm implementations reused unchanged from v1',
               'window_sums_three_problem_gate': len(reuse.get('window_sums', ())) >= 3,
               'pairs_sha256': training_pairs.sha(directory/'pairs.jsonl'),
               'verdicts_sha256': training_pairs.sha(directory/'verdicts.jsonl'),
               'contract_sha256': training_pairs.sha(directory/'contract.json'),
               'limits': ['Manually composed development labels, not student predictions.',
                          'Selected expressible development tasks; no whole-benchmark coverage estimate.',
                          'Compilation and test times exclude problem understanding.',
                          'Pattern holdout is not yet an executed predictor evaluation.']}
    (directory/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
