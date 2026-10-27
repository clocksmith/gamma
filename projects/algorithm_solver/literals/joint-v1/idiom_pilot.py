"""Matched exact idiom pools over an explicitly pinned development fitting set.

This does not qualify sources, create authoring variants, freeze a new corpus,
publish browser assets, or establish human readability/fluency. Historical
source identities and bounded qualification remain attached to their own bytes.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import search as joint
from fitting_inputs import load_fitting_inputs

MAX_CANDIDATES = 250000
MAX_SPAN_BYTES = 160
# Assistant-authored suggestions, not human proposals or reviewed usability data.
# Every entry is concrete text. Operand names and spaces are emitted and charged.
SEEDS = [
    'function solve(', 'return ', 'return false;', 'return true;', 'return -1;',
    'return 0;', 'return 1;', 'return [];', 'return null;', 'return res;',
    'const ', 'let ', 'var ', 'if (', 'if(', ') {', '){', '} else {', '}else{',
    'for (let ', 'for(let ', 'for (const ', 'for(const ', 'while (', 'while(',
    ' of ', ' in ', '.length', '.push(', '.pop()', '.shift()', '.join(',
    '.split(', '.slice(', '.sort(', '.reverse()', '.includes(', '.indexOf(',
    '.charCodeAt(', '.get(', '.set(', '.has(', '.add(', 'new Map()', 'new Set()',
    'new Array(', 'Array.from(', 'Math.max(', 'Math.min(', 'Math.abs(',
    'Math.floor(', 'Math.ceil(', 'Number(', 'String(', 'Object.keys(',
    '===', '!==', '<=', '>=', '&&', '||', '++', '--', '+=', '-=',
    'i++', 'j++', 'i--', 'j--', 'i = 0', 'i=0', 'res = []', 'res=[]',
]
PYTHON_SEEDS = [
    'def solve(', 'return ', 'return False', 'return True', 'return None',
    'return -1', 'return 0', 'return 1', 'return []', 'if ', 'elif ', 'else:',
    'for ', 'while ', ' in ', ' not in ', ' and ', ' or ', ' is None',
    'range(', 'len(', 'enumerate(', 'zip(', 'sorted(', 'reversed(',
    '.append(', '.pop(', '.get(', '.items()', '.values()', '.keys()',
    'set(', 'dict(', 'list(', 'sum(', 'max(', 'min(', 'abs(',
    '==', '!=', '<=', '>=', '+=', '-=', '//', '**',
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def python_spans(sources, maximum_bytes=MAX_SPAN_BYTES):
    """UTF-8-aware exact AST spans; parsing never imports or runs a source."""
    spans, excluded = {}, set()
    allowed = (ast.expr, ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Return,
               ast.If, ast.For, ast.While, ast.With, ast.Try, ast.Raise)
    for key, text in sources.items():
        tree = ast.parse(text)
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                excluded.add(ast.get_source_segment(text, node))
                if isinstance(node.body, list) and node.body:
                    first, last = node.body[0], node.body[-1]
                    body = ast.copy_location(ast.Pass(), first)
                    body.end_lineno, body.end_col_offset = last.end_lineno, last.end_col_offset
                    excluded.add(ast.get_source_segment(text, body))
                elif isinstance(node, ast.Lambda):
                    excluded.add(ast.get_source_segment(text, node.body))
            if isinstance(node, allowed) and not isinstance(node, (ast.Name, ast.Constant, ast.Lambda)):
                value = ast.get_source_segment(text, node)
                if value and value.strip() and len(value.encode()) <= maximum_bytes:
                    found.add(value)
            # Adjacent statements are a contiguous exact slice, including their
            # original indentation/newlines; never concatenate disjoint spans.
            for items in vars(node).values():
                if not isinstance(items, list) or not items or not all(isinstance(x, ast.stmt) for x in items):
                    continue
                for start in range(len(items)):
                    for size in (2, 3):
                        if start + size > len(items):
                            continue
                        first, last = items[start], items[start + size - 1]
                        interval = ast.copy_location(ast.Pass(), first)
                        interval.end_lineno, interval.end_col_offset = last.end_lineno, last.end_col_offset
                        value = ast.get_source_segment(text, interval)
                        if value and value.strip() and len(value.encode()) <= maximum_bytes:
                            found.add(value)
            if len(found) > 512:
                raise ValueError('per-source syntactic span budget exceeded')
        spans[key] = sorted(found)
    return {'parser': 'python-ast', 'runtime_version': sys.version,
            'runtime_sha256': digest(sys.executable),
            'spans': spans, 'excluded_units': sorted(x for x in excluded if x)}


def syntactic_spans(sources, language, node=None, node_sha256=None):
    flat = {f'{pid}/{variant}': text for pid, variants in sources.items() for variant, text in variants.items()}
    if language == 'python':
        return python_spans(flat)
    if language != 'javascript' or node is None or not node.is_absolute() or digest(node) != node_sha256:
        raise ValueError('explicit pinned JavaScript parser runtime required')
    script = Path(__file__).with_name('idiom_spans.cjs')
    result = subprocess.run([str(node), '--expose-internals', str(script)],
        input=json.dumps({'sources': flat, 'max_span_bytes': MAX_SPAN_BYTES}),
        capture_output=True, text=True, timeout=30, check=True)
    return dict(json.loads(result.stdout), runtime_sha256=node_sha256)


def occurrence_index(sources, candidates):
    """One trie pass per source, with per-problem maxima across variants."""
    tree = joint.base.trie(sorted(candidates))
    ordered = sorted(candidates)
    owners, totals = defaultdict(set), Counter()
    for pid, variants in sources.items():
        best = Counter()
        for text in variants.values():
            counts, ends = Counter(), {}
            for start in range(len(text)):
                node, stop = tree, start
                while stop < len(text) and text[stop] in node:
                    node = node[text[stop]]; stop += 1
                    if None in node:
                        fragment = ordered[node[None]]
                        if start >= ends.get(fragment, 0):
                            counts[fragment] += 1; ends[fragment] = stop
            for fragment, count in counts.items():
                best[fragment] = max(best[fragment], count)
        for fragment, count in best.items():
            owners[fragment].add(pid); totals[fragment] += count
    return owners, totals


def admitted_pools(sources, spans, excluded_units=(), language='javascript'):
    """At least two distinct problems, never variant count masquerading as reuse."""
    texts = [text for variants in sources.values() for text in variants.values()]
    full = {text.strip() for text in texts + list(excluded_units)}
    if language not in ('javascript', 'python'):
        raise ValueError('explicit supported pool language required')
    seeds = PYTHON_SEEDS if language == 'python' else SEEDS
    machine, fragments = set(), set()
    for pid, variants in sources.items():
        for variant, text in variants.items():
            extracted = spans[f'{pid}/{variant}']
            if any(fragment not in text for fragment in extracted):
                raise ValueError('AST proposal is not an exact source span')
            machine.update(extracted)
            for start in range(len(text)):
                for length in (2, 3, 4, 6, 8, 12, 16):
                    if start + length <= len(text):
                        fragments.add(text[start:start + length])
            if len(fragments) + len(machine) > MAX_CANDIDATES:
                raise ValueError('candidate mining budget exceeded; reduce or explicitly regroup the fitting selection')
    # Check every pool by actual source occurrence, including assistant seeds.
    all_candidates = set(seeds) | machine | fragments
    all_candidates = {s for s in all_candidates if len(s) >= 2 and s.strip() and s.strip() not in full
                      and len(s.encode()) <= MAX_SPAN_BYTES}
    owners, occurrences = occurrence_index(sources, all_candidates)
    eligible = {s for s in all_candidates if len(owners[s]) >= 2}
    def ranked(pool):
        return sorted(set(pool) & eligible,
                      key=lambda s: (-occurrences[s] * (len(s) - 1), len(s.encode()), s))
    return {'assistant_seed': ranked(seeds), 'ast_spans': ranked(machine),
            'seed_ast_union': ranked(set(seeds) | machine),
            'compression_fragments': ranked(fragments)}, owners


def metrics(state, sources, owners, width):
    counts = Counter(piece for pid, variant in state['chosen'].items()
                     for piece in state['parsed'][pid, variant])
    per = {}
    for pid, variant in state['chosen'].items():
        parts = state['parsed'][pid, variant]
        if ''.join(parts) != sources[pid][variant]:
            raise ValueError('reconstruction drift')
        ids = [state['vocab'].index(piece) for piece in parts]
        packet = joint.base.encode(state['vocab'], ids, width)
        if joint.base.decode(joint.base.dictionary_bytes(state['vocab']), packet) != sources[pid][variant]:
            raise ValueError('packet round trip drift')
        per[str(pid)] = {'variant': variant, 'source_sha256': state['source_hashes'][pid, variant],
                         'selections': len(parts), 'literal_ids': ids}
    keys = ('coverage', 'target', 'selections', 'literal_bits', 'singleton_bits',
            'singleton_selections', 'singleton_bit_share', 'median_selections',
            'p95_selections', 'dictionary_bytes', 'packet_bytes', 'package_bytes',
            'source_utf8_bytes', 'packet_header_bytes', 'payload_padding_bits')
    return {**{key: state[key] for key in keys}, 'entries': len(state['vocab']),
            'single_character_entries': sum(len(s) == 1 for s in state['vocab']),
            'whitespace_only_entries': sum(not s.strip() for s in state['vocab']),
            'whitespace_only_selections': sum(n for s, n in counts.items() if not s.strip()),
            'cross_problem_multichar_entries': sum(len(s) > 1 and len(owners[s]) >= 2 for s in state['vocab']),
            'uncovered_problems': len(sources) - len(state['chosen']),
            'uncovered_variants': {f'{pid}/{v}': {
                                       **{k: value for k, value in row.items() if k != 'prefix'},
                                       'prefix_literal_ids': [state['vocab'].index(piece) for piece in row['prefix']],
                                       'source_sha256': state['source_hashes'][pid, v]}
                                   for (pid, v), row in state['uncovered'].items()},
            'programs': per, 'dictionary': state['vocab'],
            'pilot_numeric_thresholds_met': bool(state['coverage'] == len(sources) and state['median_selections'] is not None and state['median_selections'] <= 32
                and state['p95_selections'] <= 96 and state['singleton_bit_share'] <= .1),
            'original_population_gate_evaluated': False,
            'milestone_qualified': False}


def comparisons(rows):
    """Expose tradeoffs, not an unsupported scalar readability score."""
    result = []
    for width in range(4, 9):
        group = [row for row in rows if row['width'] == width]
        baseline = next(row['final'] for row in group if row['pool'] == 'assistant_seed')
        pareto = []
        for row in group:
            metric = row['final']
            vector = joint.pareto_vector(metric)
            dominated = False
            for other in group:
                m = other['final']
                v = joint.pareto_vector(m)
                if all(a <= b for a, b in zip(v, vector)) and any(a < b for a, b in zip(v, vector)):
                    dominated = True
            if not dominated:
                pareto.append(row['pool'])
            common = baseline['programs'].keys() & metric['programs'].keys()
            delta = [metric['programs'][pid]['selections'] - baseline['programs'][pid]['selections'] for pid in common]
            result.append({'width': width, 'pool': row['pool'], 'baseline': 'assistant_seed',
                           'matched_covered_problems': len(common),
                           'coverage_gained': len(metric['programs'].keys() - baseline['programs'].keys()),
                           'coverage_lost': len(baseline['programs'].keys() - metric['programs'].keys()),
                           'fewer_selections': sum(d < 0 for d in delta),
                           'more_selections': sum(d > 0 for d in delta),
                           'equal_selections': sum(d == 0 for d in delta)})
        result.append({'width': width, 'pareto_pools': pareto,
                       'dimensions': ['coverage', 'absolute_singleton_bits', 'literal_bits', 'dictionary_plus_packet_bytes'],
                       'readability': 'Separate candidate policy and whitespace diagnostics only; no human evidence'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--objective', choices=('input', 'storage', 'singleton'), default='singleton')
    parser.add_argument('--node', type=Path, help='Pinned parser runtime; required only for JavaScript')
    parser.add_argument('--node-sha256')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sources, inputs = load_fitting_inputs(args.config, args.config_sha256)
    if not args.output.is_absolute():
        raise ValueError('absolute private output directory required')
    args.output.mkdir(parents=True, exist_ok=False)
    ast_script = Path(__file__).with_name('idiom_spans.cjs')
    ast_result = syntactic_spans(sources, inputs['language'], args.node, args.node_sha256)
    pools, owners = admitted_pools(sources, ast_result['spans'], ast_result['excluded_units'], inputs['language'])
    chars = Counter(char for variants in sources.values() for text in variants.values() for char in text)
    char_rank = sorted(chars, key=lambda char: (-chars[char], char))
    # Fixed bounds and pool identities precede comparisons; no new membership,
    # qualification or independent confirmation is inferred from fitting.
    limits = {'rounds_per_start': 1, 'trials_per_start': 400, 'seconds_per_start': 6,
              'removal_shortlist': 3, 'addition_shortlist': 5,
              'pair_removal_sets': 2, 'pair_addition_shortlist': 3}
    contract = {'schema': 'gamma.exposed-idiom-pilot.v2', 'fitting_inputs': inputs,
                'source_count': inputs['source_count'], 'problem_count': len(sources), 'language': inputs['language'],
                'source_exposure': 'Explicit previously_exposed development_fit selection; no fresh confirmation',
                'source_evidence': 'Exact existing canonical receipts and unchanged authoring variant identities',
                'authoring_registry_reconciliation': 'Existing owner queried; unknown authoring status retained',
                'family_reuse': 'Distinct canonical problems; reviewed grouping retained in fitting input',
                'source_rewrites': 0, 'candidate_executions': 0, 'limits': limits,
                'objective': args.objective,
                'selection': 'Exact minimum segmentation; source ties use UTF-8 size then stable variant ID',
                'path_tie': 'Minimum selections; equal costs use lower dictionary ID at first differing position',
                'operand_cost': 'All operands, names, constants, punctuation and whitespace are literal source bytes',
                'controls': 'Offline representation only; no Finish/Undo or human interaction claim',
                'parser': ast_result['parser'], 'parser_runtime_sha256': ast_result['runtime_sha256'],
                'parser_runtime_version': ast_result.get('runtime_version'),
                'code_sha256': {p.name: digest(p) for p in [Path(__file__), ast_script, Path(joint.__file__), Path(__file__).with_name('fitting_inputs.py')]},
                'decoder_storage': {p.name: {'sha256': digest(p), 'bytes': p.stat().st_size}
                                    for p in [joint.SCALE.parent / 'literals.py', joint.SCALE.parent / 'pass2/working/bitpack.py']},
                'decoder_storage_scope': 'Selected codec source files only, not the complete installed runtime footprint',
                'pool_sizes': {name: len(pool) for name, pool in pools.items()}, 'human_study': False}
    joint.write(args.output / 'contract.json', contract)
    joint.write(args.output / 'candidate-pools.json', pools)
    (args.output / 'implementation').mkdir()
    for path in [Path(__file__), ast_script, Path(joint.__file__), Path(__file__).with_name('fitting_inputs.py')]:
        (args.output / 'implementation' / path.name).write_bytes(path.read_bytes())
    started, rows = time.monotonic(), []
    for width in range(4, 9):
        alphabet = char_rank[:min(len(char_rank), 2**width)]
        for name, pool in pools.items():
            initial_vocab = alphabet + pool[:2**width - len(alphabet)]
            initial = joint.evaluate(sources, initial_vocab, width, alphabet=[], allow_partial=True)
            # The same existing paired search alternates exact source selection
            # with dictionary moves. No separate optimizer is introduced.
            final, trace = joint.improve(sources, initial, width, args.objective, limits,
                                        alphabet=[], allow_partial=True, candidate_pool=pool + char_rank)
            initial_metrics, final_metrics = metrics(initial, sources, owners, width), metrics(final, sources, owners, width)
            common = initial['chosen'].keys() & final['chosen'].keys()
            deltas = [len(final['parsed'][pid, final['chosen'][pid]]) - len(initial['parsed'][pid, initial['chosen'][pid]]) for pid in common]
            row = {'pool': name, 'width': width, 'budget': 2**width, 'initial': initial_metrics,
                   'final': final_metrics, 'source_switches': sum(final['chosen'][pid] != initial['chosen'][pid] for pid in common),
                   'regressions': sum(d > 0 for d in deltas), 'improvements': sum(d < 0 for d in deltas),
                   'trace': trace}
            rows.append(row)
            joint.write(args.output / f'{width}-{name}.json', row)
            print(json.dumps({'width': width, 'pool': name, **{key: final[key] for key in ('coverage', 'selections', 'median_selections', 'p95_selections', 'singleton_bits')}}), flush=True)
    joint.write(args.output / 'summary.json', {'contract_sha256': digest(args.output / 'contract.json'),
        'elapsed_seconds': time.monotonic() - started, 'rows': rows, 'comparisons': comparisons(rows),
        'publication': 'None; no browser admission or current catalogue promotion',
        'confirmation_blocker': 'New independently permitted grouped corpus and frozen nonreserved holdout still required'})


if __name__ == '__main__':
    main()
