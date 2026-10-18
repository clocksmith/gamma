"""Reproducible development measurement; no dataset, weights, or predictor.

Run: python -m algsolve.synth.typed_experiment --output runs/typed-primitives-v1
Outputs bind source, graphs, seed, input cases and independent oracles. These
examined fixtures are permanently development/debugging material.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import platform
import random
import statistics
import time

from . import typed_program as ir
from . import typed_recipes as recipes

SEED = 20261017


def sha(value):
    return hashlib.sha256(ir.canonical(value).encode()).hexdigest()


def forest_oracle(n, edges):
    """Exhaustive spanning forests; no sorting, DSU, or greedy algorithm."""
    def parts(subset):
        reach = [{i} for i in range(n)]
        for _ in range(n):
            for u, v, _ in subset:
                merged = reach[u] | reach[v]
                for node in merged:
                    reach[node] = merged
        return len({frozenset(group) for group in reach})
    count = parts(edges)
    costs = [sum(e[2] for e in subset)
             for subset in itertools.combinations(edges, n - count)
             if parts(subset) == count]
    return min(costs), max(costs), count


def cases(seed=SEED):
    rng = random.Random(seed)
    rows = []
    for i in range(100):
        n = i % 7
        edges = ([[rng.randrange(n), rng.randrange(n), rng.randint(-9, 9)]
                  for _ in range(rng.randrange(9))] if n else [])
        low, high, count = forest_oracle(n, edges)
        answers = {'minimum_forest': low, 'maximum_forest': high, 'component_count': count,
                   'rejected_edge_weight': sum(e[2] for e in edges) - low}
        for key, answer in answers.items():
            rows.append({'fixture': key, 'input': {'n': n, 'edges': edges}, 'expected': answer})
        values = [rng.randint(-20, 20) for _ in range(i % 30)]
        answers = {'heap_sort': sorted(values), 'stable_unique': list(dict.fromkeys(values)),
                   'sorted_unique': sorted(set(values)), 'unique_sorted': sorted(set(values))}
        for key, answer in answers.items():
            rows.append({'fixture': key, 'input': {'values': values}, 'expected': answer})
    return rows


def alpha_fragment(value):
    """Normalize binding spellings, preserving reference identity and wiring."""
    names = {}
    def walk(v):
        if type(v) is list: return [walk(c) for c in v]
        if type(v) is not dict: return v
        result = {}
        for k, c in v.items():
            if k in ('name', 'ref', 'out', 'item'):
                if c not in names: names[c] = f'b{len(names)}'
                result[k] = names[c]
            else: result[k] = walk(c)
        return result
    return walk(value)


def shared_fragments(catalog):
    """Three consecutive statements shared by distinct recipes, not wrappers.

    This is a syntactic dataflow-sharing measurement, not semantic equivalence
    or mined corpus coverage. Capture names are normalized, not discarded.
    """
    found, payloads = defaultdict(set), {}
    def visit(body, owner):
        for i in range(len(body) - 2):
            value = alpha_fragment(body[i:i+3])
            key = sha(value)
            found[key].add(owner)
            payloads[key] = value
        for stmt in body:
            for child in ('body', 'then', 'else'):
                if child in stmt: visit(stmt[child], owner)
    for owner, p in catalog.items(): visit(p['body'], owner)
    return [{'sha256': k, 'recipes': sorted(v), 'statements': payloads[k]}
            for k, v in sorted(found.items()) if len(v) > 1]


def leaf_edits(a, b):
    """Mechanical graph-data differences, not measured human keystrokes."""
    if type(a) != type(b): return 1
    if type(a) is dict:
        return sum(leaf_edits(a[k], b[k]) if k in a and k in b else 1 for k in a.keys() | b.keys())
    if type(a) is list:
        return sum(leaf_edits(x, y) for x, y in zip(a, b)) + abs(len(a) - len(b))
    return int(a != b)


def measure():
    catalog, fixtures, rows = recipes.catalog(), recipes.fixtures(), cases()
    expanded, mapping = {}, {}
    for key, p in fixtures.items():
        expanded[key], mapping[key] = ir.expanded(p, catalog)
    counts, timings, records = defaultdict(int), defaultdict(list), []
    for row in rows:
        key, args = row['fixture'], row['input']
        start = time.perf_counter()
        answer = ir.execute(fixtures[key], args, recipes=catalog)
        elapsed = time.perf_counter() - start
        inline = ir.execute(expanded[key], {mapping[key][k]: v for k, v in args.items()})
        ok = answer == row['expected'] and inline == row['expected']
        if not ok: raise AssertionError((key, args, answer, inline, row['expected']))
        counts[key] += 1
        timings[key].append(elapsed)
        records.append({**row, 'passed': ok, 'validate_and_execute_seconds': elapsed})
    negatives = []
    for key, p, args, correct in recipes.negative_fixtures():
        actual = ir.execute(p, args)
        if actual == correct: raise AssertionError('Negative lacks counterexample')
        negatives.append({'name': key, 'graph_sha256': sha(p), 'input': args,
                          'correct': correct, 'actual': actual, 'counterexample_confirmed': True})
    # Compare representation size against the retained v2 graph on the same
    # forest workload. Its algorithm implementation remains opaque to the head.
    from . import call_graph
    old = {'schema': call_graph.SCHEMA, 'vocabulary_sha256': call_graph.vocabulary_hash(),
           'nodes': [{'operator': 'kruskal', 'arguments': ['n', 'edges'], 'output': 'forest'}],
           'answer': 'forest[0]'}
    old_compiled = call_graph.compile_graph(old, method='solve', params=['n', 'edges'])
    # Only this fixed repository fixture is executed here. No proposed graph
    # receives eval/exec and no hidden dataset is loaded.
    namespace = {}
    exec(old_compiled.source, namespace)
    old_results, old_times, old_full_times = [], [], []
    for row in rows:
        if row['fixture'] != 'minimum_forest': continue
        start = time.perf_counter()
        answer = namespace['Solution']().solve(**row['input'])
        old_times.append(time.perf_counter() - start)
        old_results.append(answer == row['expected'])
        start = time.perf_counter()
        rendered = call_graph.compile_graph(old, method='solve', params=['n', 'edges'])
        fresh = {}
        exec(rendered.source, fresh)
        complete_answer = fresh['Solution']().solve(**row['input'])
        old_full_times.append(time.perf_counter() - start)
        if complete_answer != row['expected']: raise AssertionError('Fresh v2 assembly failed')
    if not all(old_results): raise AssertionError('Existing algorithm disagrees with oracle')
    summary = {
        'evidence_class': 'hand-authored representation and execution development experiment',
        'seed': SEED, 'cases': len(rows), 'passed': sum(counts.values()),
        'per_fixture': {key: {'passed': counts[key],
                            'compact_operations': sum(ir.operation_counts(p).values()),
                            'expanded_operations': sum(ir.operation_counts(expanded[key]).values()),
                            'expanded_json_bytes': len(ir.canonical(expanded[key]).encode()),
                            'validate_and_execute_p50_seconds': statistics.median(timings[key]),
                            'validate_and_execute_p95_seconds': sorted(timings[key])[94]}
                        for key, p in fixtures.items()},
        'primitive_effect_operations': len(ir.EFFECTS), 'available_pure_operations': len(ir.PURE),
        'recipes': len(catalog), 'shared_three_statement_fragments': shared_fragments(catalog),
        'adaptation_graph_leaf_edits': {
            'minimum_to_maximum_forest': leaf_edits(fixtures['minimum_forest'], fixtures['maximum_forest']),
            'forest_weight_to_component_count': leaf_edits(fixtures['minimum_forest'], fixtures['component_count']),
            'sorted_unique_to_unique_sorted': leaf_edits(fixtures['sorted_unique'], fixtures['unique_sorted']),
        },
        'hard_negatives': negatives,
        'old_v2_matched_minimum_forest': {'passed': sum(old_results), 'cases': len(old_results),
            'algorithm_nodes': 1, 'glue_ast_nodes': old_compiled.glue_nodes,
            'execute_only_p50_seconds': statistics.median(old_times),
            'validate_compile_and_execute_p50_seconds': statistics.median(old_full_times),
            'new_validate_and_execute_p50_seconds': statistics.median(timings['minimum_forest']),
            'timing_comparability': 'same 100 small inputs; full old assembly versus new interpretation; neither includes prediction or retrieval; no solving-speed claim'},
        'prediction_seconds': None, 'learned_first_prediction_correctness': None,
        'limits': ['No predictor trained or adapted to this representation.',
                   'All generated cases and inspected variants are development/debugging data.',
                   'No held-out problem data was read; reserve fresh cases before future training/evaluation.',
                   'Bounded synthetic inputs and finite tests do not establish general correctness.',
                   'append copies lists: these examples prioritize representation, not optimal sequence construction.',
                   'Edit counts are graph-data changes, not human adaptation-time measurements.',
                   'Existing lookup, frozen v1 and call-graph v2 remain unchanged.'],
    }
    root = Path(__file__).parent
    contract = {'schema': 'algsolve.typed-development.v1', 'seed': SEED,
                'sources_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in [root/'typed_program.py', root/'typed_recipes.py',
                                             root/'typed_experiment.py', root/'call_graph.py', root/'components.py',
                                             root/'grammar.py', root/'render.py', root/'skeletons.py']},
                'cases_sha256': sha(rows), 'graphs_sha256': sha({'recipes': catalog, 'fixtures': fixtures}),
                'python': platform.python_version(), 'platform': platform.platform(),
                'machine': platform.machine(), 'processor': platform.processor(),
                'device': 'cpu', 'model': None, 'training': None,
                'data_policy': 'seeded synthetic development only; no corpus, confirmation or protected evaluation inputs'}
    return contract, summary, records, {'recipes': catalog, 'fixtures': fixtures, 'expanded': expanded}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    print(f'[run-contract] run_name={args.output.name} pairs_input_spec=synthetic-development-seed-{SEED} '
          'resume_from=none decode=none eval_dataset_paths=none device=cpu schedule=none '
          'runtime_mode=cpu sweep_mode=live', flush=True)
    contract, summary, rows, graphs = measure()
    for name, value in [('contract', contract), ('summary', summary), ('graphs', graphs)]:
        (args.output/f'{name}.json').write_text(json.dumps(value, indent=2)+'\n')
    (args.output/'rows.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    print(json.dumps({'cases': summary['cases'], 'passed': summary['passed'],
                      'shared_fragments': len(summary['shared_three_statement_fragments'])}))


if __name__ == '__main__': main()
