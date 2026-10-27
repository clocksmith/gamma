"""Matched exact idiom pools over an explicitly pinned development fitting set.

This does not qualify sources, create authoring variants, freeze a new corpus,
publish browser assets, or establish human readability/fluency. Historical
source identities and bounded qualification remain attached to their own bytes.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import io
import tokenize
import json
from pathlib import Path
import subprocess
import sys
import time

import search as joint
from fitting_inputs import load_fitting_inputs

PINS = {
    'generated/manifest.json': 'c39f1a8697ca5296c6376f8e5dca3c5d9cd4d553551bdd872d023ab21c183143',
    'qualification/report.json': '9802eaadddcaa28d4041a507f942202deb9518719ac135768c6753896fb5b557',
    'protected-boundary.json': '2ac829a3bca4aac395845ae4e6c3fc5ad3c6a38e606b2441dfe841e0be9fa0ea',
}
MAX_CANDIDATES = 250000
MAX_SPAN_BYTES = 160
MAX_SPANS_PER_SOURCE = 2048
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


FALLBACK = frozenset('()[]{}.,:;+-*/%=!<>&|^~?\\ \t\n\r')


def arm_pool(pool, sources, arm):
    """No alphabet preallocation, even in the restricted fallback arm."""
    if arm not in ('strict', 'punctuation_fallback'):
        raise ValueError('unknown singleton policy')
    longer = list(dict.fromkeys(piece for piece in pool if len(piece) > 1))
    chars = Counter(char for variants in sources.values() for text in variants.values()
                    for char in text if char in FALLBACK)
    return longer + (sorted(chars, key=lambda c: (-chars[c], c))
                     if arm == 'punctuation_fallback' else [])


def seed_vocabulary(sources, pool, width, boundaries=None):
    """Try complete complementary bundles, not a prefix of frequent characters.

    Every bundle is a minimum segmentation using the entire admitted pool.
    Select bundles within budget; unused capacity goes to the ranked longer
    candidates. This bounded initializer does not claim globally optimal sets.
    """
    vocab = joint.order(pool, [])
    if not vocab:
        return []  # Report zero coverage; never invent an alphabet or padding entry.
    tree, bundles = joint.base.trie(vocab), []
    for pid, variants in sorted(sources.items()):
        for variant, text in sorted(variants.items()):
            try:
                path = joint.segment(text, tree, None if boundaries is None else boundaries[pid, variant])
            except ValueError:
                continue
            pieces = tuple(vocab[i] for i in path)
            if len(set(pieces)) <= 2**width:
                bundles.append((pid, variant, pieces))
    selected = set()
    while bundles:
        choices = [(len(set(parts) - selected), len(parts), pid, variant, parts)
                   for pid, variant, parts in bundles
                   if len(selected | set(parts)) <= 2**width and set(parts) - selected]
        if not choices:
            break
        _, _, _, _, pieces = min(choices)
        selected.update(pieces)
    for piece in pool:
        if len(selected) == 2**width:
            break
        selected.add(piece)
    return joint.order(selected, [])


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def python_spans(sources, maximum_bytes=MAX_SPAN_BYTES):
    """UTF-8-aware exact AST spans; parsing never imports or runs a source."""
    spans, excluded, boundaries = {}, set(), {}
    allowed = (ast.expr, ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Return,
               ast.If, ast.For, ast.While, ast.With, ast.Try, ast.Raise)
    for key, text in sources.items():
        tree = ast.parse(text)
        lines = text.splitlines(keepends=True)
        offsets = [0]
        for line in lines: offsets.append(offsets[-1] + len(line))
        safe = set(range(len(text) + 1))
        tokens = []
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type in (tokenize.ENCODING, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.NEWLINE, tokenize.ENDMARKER):
                continue
            start = offsets[token.start[0] - 1] + token.start[1]
            end = offsets[token.end[0] - 1] + token.end[1]
            safe.difference_update(range(start + 1, end))
            if end > start:
                tokens.append((start, end))
        boundaries[key] = sorted(safe)
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
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
            if len(found) > MAX_SPANS_PER_SOURCE:
                raise ValueError('per-source syntactic span budget exceeded')
        # Complete lexical tokens bridge the gaps between AST nodes. No source
        # rewriting or split inside an identifier, number or string is allowed.
        for index, (start, _) in enumerate(tokens):
            for size in (1, 2, 3):
                if index + size > len(tokens):
                    continue
                end = tokens[index + size - 1][1]
                after = end
                while after < len(text) and text[after].isspace():
                    after += 1
                for stop in (end, after):
                    value = text[start:stop]
                    if value.strip() and len(value.encode()) <= maximum_bytes:
                        found.add(value)
                if len(found) > MAX_SPANS_PER_SOURCE:
                    raise ValueError('per-source syntactic span budget exceeded')
        spans[key] = sorted(found)
    return {'parser': 'python-ast', 'runtime_version': sys.version,
            'runtime_sha256': digest(sys.executable),
            'spans': spans, 'boundaries': boundaries, 'excluded_units': sorted(x for x in excluded if x)}


def syntactic_spans(sources, language, node=None, node_sha256=None, *, include_tokens=False):
    flat = {f'{pid}/{variant}': text for pid, variants in sources.items() for variant, text in variants.items()}
    if language == 'python':
        return python_spans(flat)
    if language != 'javascript' or node is None or not node.is_absolute() or digest(node) != node_sha256:
        raise ValueError('explicit pinned JavaScript parser runtime required')
    script = Path(__file__).with_name('idiom_spans.cjs')
    result = subprocess.run([str(node), '--expose-internals', str(script)],
        input=json.dumps({'sources': flat, 'max_span_bytes': MAX_SPAN_BYTES,
                          'max_spans_per_source': MAX_SPANS_PER_SOURCE, 'include_tokens': include_tokens}),
        capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError('syntactic parser failed: ' + result.stderr[-2000:])
    return dict(json.loads(result.stdout), runtime_sha256=node_sha256)


def occurrence_index(sources, candidates, boundaries=None):
    """One trie pass per source, with per-problem maxima across variants."""
    tree = joint.base.trie(sorted(candidates))
    ordered = sorted(candidates)
    owners, totals = defaultdict(set), Counter()
    for pid, variants in sources.items():
        best = Counter()
        for variant, text in variants.items():
            allowed = None if boundaries is None else boundaries[pid, variant]
            counts, ends = Counter(), {}
            for start in range(len(text)):
                node, stop = tree, start
                while stop < len(text) and text[stop] in node:
                    node = node[text[stop]]; stop += 1
                    if None in node and (allowed is None or start in allowed and stop in allowed):
                        fragment = ordered[node[None]]
                        if start >= ends.get(fragment, 0):
                            counts[fragment] += 1; ends[fragment] = stop
            for fragment, count in counts.items():
                best[fragment] = max(best[fragment], count)
        for fragment, count in best.items():
            owners[fragment].add(pid); totals[fragment] += count
    return owners, totals


def admitted_pools(sources, spans, excluded_units=(), language='javascript', *, boundaries=None):
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
    human_owners, human_counts = occurrence_index(sources, eligible & (set(seeds) | machine), boundaries)
    # Whitespace cannot disguise a character alphabet as longer literals.
    # Real separators remain charged inside multi-token/whole-token pieces;
    # the fallback arm admits actual punctuation singletons explicitly.
    human_eligible = {s for s in human_owners if len(human_owners[s]) >= 2 and len(s.strip()) > 1}
    def ranked(pool, human=False):
        accepted = human_eligible if human else eligible
        counts = human_counts if human else occurrences
        return sorted(set(pool) & accepted,
                      key=lambda s: (-counts[s] * (len(s) - 1), len(s.encode()), s))
    return {'assistant_seed': ranked(seeds, True), 'ast_spans': ranked(machine, True),
            'seed_ast_union': ranked(set(seeds) | machine, True),
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
                         'selections': len(parts), 'literal_ids': ids,
                         'singleton_selections': sum(len(piece) == 1 for piece in parts),
                         'singleton_bits': width * sum(len(piece) == 1 for piece in parts)}
    keys = ('coverage', 'target', 'selections', 'literal_bits', 'singleton_bits',
            'singleton_selections', 'singleton_bit_share', 'median_selections',
            'p95_selections', 'dictionary_bytes', 'packet_bytes', 'package_bytes',
            'singleton_compliant_programs', 'within_32_selections', 'within_96_selections',
            'source_utf8_bytes', 'packet_header_bytes', 'payload_padding_bits')
    failures = []
    if state['coverage'] != len(sources): failures.append('incomplete_supplied_population')
    if state['median_selections'] is None or state['median_selections'] > 32: failures.append('median_above_32_or_undefined')
    if state['p95_selections'] is None or state['p95_selections'] > 96: failures.append('p95_above_96_or_undefined')
    if state['singleton_bit_share'] is None or state['singleton_bit_share'] > .1: failures.append('singleton_share_above_10_percent_or_undefined')
    return {**{key: state[key] for key in keys}, 'entries': len(state['vocab']),
            'serializable_dictionary': state['serializable_dictionary'],
            'supplied_population_gate_failures': failures,
            'interaction_presses': None, 'human_effort': None,
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
    for width, arm in sorted({(row['width'], row.get('arm', 'legacy')) for row in rows}):
        group = [row for row in rows if row['width'] == width and row.get('arm', 'legacy') == arm]
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
            result.append({'width': width, 'arm': arm, 'pool': row['pool'], 'baseline': 'assistant_seed',
                           'matched_covered_problems': len(common),
                           'coverage_gained': len(metric['programs'].keys() - baseline['programs'].keys()),
                           'coverage_lost': len(baseline['programs'].keys() - metric['programs'].keys()),
                           'fewer_selections': sum(d < 0 for d in delta),
                           'more_selections': sum(d > 0 for d in delta),
                           'equal_selections': sum(d == 0 for d in delta)})
        result.append({'width': width, 'arm': arm, 'pareto_pools': pareto,
                       'dimensions': ['coverage', 'literal_bits', 'absolute_singleton_bits', 'dictionary_plus_packet_bytes'],
                       'readability': 'Separate candidate policy and whitespace diagnostics only; no human evidence'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--legacy-scale80-control', action='store_true', help='Reproduce only the pinned already-exposed historical control')
    parser.add_argument('--config-sha256')
    parser.add_argument('--objective', choices=('compact', 'input', 'storage', 'singleton'), default='compact')
    parser.add_argument('--node', type=Path, help='Pinned parser runtime; required only for JavaScript')
    parser.add_argument('--node-sha256')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.legacy_scale80_control:
        if args.config or args.config_sha256:
            parser.error('legacy control and new fitting inputs are mutually exclusive')
        for name, expected in PINS.items():
            if digest(joint.SCALE / name) != expected:
                raise ValueError('historical evidence pin mismatch: ' + name)
        boundary = json.loads((joint.SCALE / 'protected-boundary.json').read_text())
        if boundary['checked_problem_count'] != 80 or boundary['reserved_problem_overlap']:
            raise ValueError('historical development boundary differs')
        sources, _ = joint.load_sources()
        inputs = {'schema': 'gamma.legacy-scale80-control.v1', 'language': 'javascript',
                  'source_count': 160, 'problem_count': 80, 'pins': PINS,
                  'exposure': 'Previously exposed historical control; not new admission or confirmation'}
    else:
        if not args.config or not args.config_sha256:
            parser.error('pinned fitting config required')
        sources, inputs = load_fitting_inputs(args.config, args.config_sha256)
    if not args.output.is_absolute():
        raise ValueError('absolute private output directory required')
    args.output.mkdir(parents=True, exist_ok=False)
    ast_script = Path(__file__).with_name('idiom_spans.cjs')
    ast_result = syntactic_spans(sources, inputs['language'], args.node, args.node_sha256)
    boundaries = {(pid, v): frozenset(ast_result['boundaries'][f'{pid}/{v}'])
                  for pid, variants in sources.items() for v in variants}
    pools, owners = admitted_pools(sources, ast_result['spans'], ast_result['excluded_units'], inputs['language'], boundaries=boundaries)
    # Fixed bounds and pool identities precede comparisons; no new membership,
    # qualification or independent confirmation is inferred from fitting.
    limits = {'rounds_per_start': 1, 'trials_per_start': 400, 'seconds_per_start': 6,
              'removal_shortlist': 3, 'addition_shortlist': 5,
              'pair_removal_sets': 2, 'pair_addition_shortlist': 3}
    contract = {'schema': 'gamma.exposed-idiom-pilot.v2', 'fitting_inputs': inputs,
                'source_count': inputs['source_count'], 'problem_count': len(sources), 'language': inputs['language'],
                'source_exposure': 'Previously exposed historical control' if args.legacy_scale80_control else 'Explicit previously_exposed development_fit selection; no fresh confirmation',
                'source_evidence': 'Historical finite qualification only' if args.legacy_scale80_control else 'Exact existing canonical receipts; input route declares its historical or authoring-owner identity',
                'authoring_registry_reconciliation': 'Legacy semantics join unavailable' if args.legacy_scale80_control else 'Historical route retains canonical identities without inventing sidecars; modern route queries existing authoring owner',
                'family_reuse': 'Unknown for legacy control' if args.legacy_scale80_control else 'Distinct canonical problems; input records retain grouping scope and known conflicts; no independent family-confirmation claim',
                'source_rewrites': 0, 'candidate_executions': 0, 'limits': limits,
                'proposal_limits': {'max_span_bytes': MAX_SPAN_BYTES,
                                    'max_spans_per_source': MAX_SPANS_PER_SOURCE,
                                    'max_candidates': MAX_CANDIDATES},
                'objective': args.objective,
                'selection': 'Default compact objective prefers aggregate-gate-compliant dictionaries, then compliant program counts, coverage, reachable prefixes and cost. Alternatives retain exact minimum paths.',
                'singleton_arms': ['strict', 'punctuation_fallback'],
                'fallback_characters': sorted(FALLBACK),
                'initialization': 'Complete complementary bundles; strict incumbent included; no character floor',
                'lexical_boundaries': 'Required for human-oriented pools; compression control unrestricted',
                'path_tie': 'Minimum selections; equal costs use lower dictionary ID at first differing position',
                'operand_cost': 'All operands, names, constants, punctuation and whitespace are literal source bytes',
                'controls': 'Offline representation only; no Finish/Undo or human interaction claim',
                'parser': ast_result['parser'], 'parser_runtime_sha256': ast_result['runtime_sha256'],
                'parser_runtime_version': ast_result.get('runtime_version'),
                'code_sha256': {p.name: digest(p) for p in [Path(__file__), ast_script, Path(joint.__file__),
                    Path(__file__).with_name('fitting_inputs.py'),
                    *[Path(__file__).resolve().parents[2] / 'catalogue' / name for name in
                      ('guide_admission.py', 'known_spec_service.py', 'boundary_policy.py', 'catalogue.py')]]},
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
      for arm in ('strict', 'punctuation_fallback'):
        for name, original_pool in pools.items():
            pool = arm_pool(original_pool, sources, arm)
            lexical = None if name == 'compression_fragments' else boundaries
            initial_vocab = seed_vocabulary(sources, pool, width, lexical)
            initial = joint.evaluate(sources, initial_vocab, width, alphabet=[], allow_partial=True,
                                     boundaries=lexical, source_objective=args.objective)
            strict_vocab = seed_vocabulary(sources, arm_pool(original_pool, sources, 'strict'), width, lexical)
            strict_initial = joint.evaluate(sources, strict_vocab, width, alphabet=[], allow_partial=True,
                                            boundaries=lexical, source_objective=args.objective)
            initial = min((initial, strict_initial), key=lambda state: joint.cost(state, args.objective))
            # The same existing paired search alternates exact source selection
            # with dictionary moves. No separate optimizer is introduced.
            final, trace = joint.improve(sources, initial, width, args.objective, limits,
                                        alphabet=[], allow_partial=True, candidate_pool=pool,
                                        boundaries=lexical)
            initial_metrics, final_metrics = metrics(initial, sources, owners, width), metrics(final, sources, owners, width)
            common = initial['chosen'].keys() & final['chosen'].keys()
            deltas = [len(final['parsed'][pid, final['chosen'][pid]]) - len(initial['parsed'][pid, initial['chosen'][pid]]) for pid in common]
            row = {'pool': name, 'arm': arm, 'pool_status': 'available' if pool else 'empty',
                   'width': width, 'budget': 2**width, 'initial': initial_metrics,
                   'final': final_metrics, 'source_switches': sum(final['chosen'][pid] != initial['chosen'][pid] for pid in common),
                   'regressions': sum(d > 0 for d in deltas), 'improvements': sum(d < 0 for d in deltas),
                   'trace': trace}
            rows.append(row)
            joint.write(args.output / f'{width}-{arm}-{name}.json', row)
            print(json.dumps({'width': width, 'arm': arm, 'pool': name, **{key: final[key] for key in ('coverage', 'selections', 'median_selections', 'p95_selections', 'singleton_bits')}}), flush=True)
    joint.write(args.output / 'summary.json', {'contract_sha256': digest(args.output / 'contract.json'),
        'elapsed_seconds': time.monotonic() - started, 'rows': rows, 'comparisons': comparisons(rows),
        'publication': 'None; no browser admission or current catalogue promotion',
        'confirmation_blocker': 'New independently permitted grouped corpus and frozen nonreserved holdout still required'})


if __name__ == '__main__':
    main()
