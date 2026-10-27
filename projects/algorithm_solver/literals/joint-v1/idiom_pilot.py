"""Matched exact idiom candidate pools on the already exposed scale80 control.

This does not qualify sources, create authoring variants, freeze a new corpus,
publish browser assets, or establish human readability/fluency. Historical
source identities and bounded qualification remain attached to their own bytes.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import time

import search as joint

PINS = {
    'generated/manifest.json': 'c39f1a8697ca5296c6376f8e5dca3c5d9cd4d553551bdd872d023ab21c183143',
    'qualification/report.json': '9802eaadddcaa28d4041a507f942202deb9518719ac135768c6753896fb5b557',
    'protected-boundary.json': '2ac829a3bca4aac395845ae4e6c3fc5ad3c6a38e606b2441dfe841e0be9fa0ea',
}
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


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def admitted_pools(sources, spans):
    """At least two distinct problems, never variant count masquerading as reuse."""
    texts = [text for variants in sources.values() for text in variants.values()]
    full = set(texts)
    owners, occurrences = defaultdict(set), Counter()
    machine, fragments = set(), set()
    for pid, variants in sources.items():
        local = set()
        for variant, text in variants.items():
            extracted = spans[f'{pid}/{variant}']
            if any(fragment not in text for fragment in extracted):
                raise ValueError('AST proposal is not an exact source span')
            machine.update(extracted)
            for start in range(len(text)):
                for length in (2, 3, 4, 6, 8, 12, 16):
                    if start + length <= len(text):
                        fragments.add(text[start:start + length])
            local.update(extracted)
        for fragment in local:
            owners[fragment].add(pid)
    # Check every pool by actual source occurrence, including assistant seeds.
    all_candidates = set(SEEDS) | machine | fragments
    eligible = set()
    for fragment in all_candidates:
        if len(fragment) < 2 or not fragment.strip() or fragment in full or len(fragment.encode()) > 48:
            continue
        found = {pid for pid, variants in sources.items() if any(fragment in text for text in variants.values())}
        if len(found) >= 2:
            eligible.add(fragment)
            owners[fragment] = found
            occurrences[fragment] = sum(max(text.count(fragment) for text in sources[pid].values()) for pid in found)
    def ranked(pool):
        return sorted(set(pool) & eligible,
                      key=lambda s: (-occurrences[s] * (len(s) - 1), len(s.encode()), s))
    return {'assistant_seed': ranked(SEEDS), 'ast_spans': ranked(machine),
            'seed_ast_union': ranked(set(SEEDS) | machine),
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
            'p95_selections', 'dictionary_bytes', 'packet_bytes', 'package_bytes')
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
            vector = (-metric['coverage'], metric['literal_bits'], metric['singleton_bits'], metric['package_bytes'])
            dominated = False
            for other in group:
                m = other['final']
                v = (-m['coverage'], m['literal_bits'], m['singleton_bits'], m['package_bytes'])
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
                       'dimensions': ['coverage', 'literal_bits', 'absolute_singleton_bits', 'dictionary_plus_packet_bytes'],
                       'readability': 'Separate candidate policy and whitespace diagnostics only; no human evidence'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, required=True, help='Explicit parser runtime; source is never executed')
    parser.add_argument('--node-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for name, expected in PINS.items():
        if digest(joint.SCALE / name) != expected:
            raise ValueError('Historical evidence pin mismatch: ' + name)
    boundary = json.loads((joint.SCALE / 'protected-boundary.json').read_text())
    if boundary['checked_problem_count'] != 80 or boundary['reserved_problem_overlap']:
        raise ValueError('Unexpected historical development boundary')
    if not args.node.is_absolute() or digest(args.node) != args.node_sha256:
        raise ValueError('Parser runtime pin mismatch')
    sources, _ = joint.load_sources()
    args.output.mkdir(parents=True, exist_ok=False)
    ast_script = Path(__file__).with_name('idiom_spans.cjs')
    flat = {f'{pid}/{v}': text for pid, variants in sources.items() for v, text in variants.items()}
    result = subprocess.run([str(args.node), '--expose-internals', str(ast_script)],
                            input=json.dumps(flat), capture_output=True, text=True, timeout=30, check=True)
    ast_result = json.loads(result.stdout)
    pools, owners = admitted_pools(sources, ast_result['spans'])
    chars = Counter(char for variants in sources.values() for text in variants.values() for char in text)
    char_rank = sorted(chars, key=lambda char: (-chars[char], char))
    # Fixed bounds and pool identities precede all comparisons. These 80 problems
    # were already exposed: this run cannot create independent confirmation.
    limits = {'rounds_per_start': 1, 'trials_per_start': 400, 'seconds_per_start': 6,
              'removal_shortlist': 3, 'addition_shortlist': 5,
              'pair_removal_sets': 2, 'pair_addition_shortlist': 3}
    contract = {'schema': 'gamma.exposed-idiom-pilot.v1', 'pins': PINS,
                'source_count': 160, 'problem_count': 80, 'language': 'javascript',
                'source_exposure': 'All 80 previously exposed development problems; no fresh confirmation',
                'source_evidence': 'Historical finite oracle checks plus original output/input-effect parity',
                'authoring_registry_reconciliation': 'Blocked: legacy scale80 has no semantics records; no new IDs fabricated',
                'family_reuse': 'Unknown: legacy metadata has no reconciled family labels',
                'source_rewrites': 0, 'candidate_executions': 0, 'limits': limits,
                'selection': 'Coverage first, then selections, then dictionary plus packet bytes; source ties use UTF-8 size then legacy variant name',
                'path_tie': 'Minimum selections; equal costs use lower dictionary ID at first differing position',
                'operand_cost': 'All operands, names, constants, punctuation and whitespace are literal source bytes',
                'controls': 'Offline representation only; no Finish/Undo or human interaction claim',
                'parser': ast_result['parser'], 'parser_runtime_sha256': args.node_sha256,
                'code_sha256': {p.name: digest(p) for p in [Path(__file__), ast_script, Path(joint.__file__)]},
                'decoder_storage': {p.name: {'sha256': digest(p), 'bytes': p.stat().st_size}
                                    for p in [joint.SCALE.parent / 'literals.py', joint.SCALE.parent / 'pass2/working/bitpack.py']},
                'decoder_storage_scope': 'Selected codec source files only, not the complete installed runtime footprint',
                'pool_sizes': {name: len(pool) for name, pool in pools.items()}, 'human_study': False}
    joint.write(args.output / 'contract.json', contract)
    joint.write(args.output / 'candidate-pools.json', pools)
    (args.output / 'implementation').mkdir()
    for path in [Path(__file__), ast_script, Path(joint.__file__)]:
        (args.output / 'implementation' / path.name).write_bytes(path.read_bytes())
    started, rows = time.monotonic(), []
    for width in range(4, 9):
        alphabet = char_rank[:min(len(char_rank), 2**width)]
        for name, pool in pools.items():
            initial_vocab = alphabet + pool[:2**width - len(alphabet)]
            initial = joint.evaluate(sources, initial_vocab, width, alphabet=[], allow_partial=True)
            # The same existing paired search alternates exact source selection
            # with dictionary moves. No separate optimizer is introduced.
            final, trace = joint.improve(sources, initial, width, 'input', limits,
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
