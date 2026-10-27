"""Explain a retained comparison without fitting, rewriting or executing sources.

Full-pool parsing is an unlimited-dictionary relaxation, not a legal shared
dictionary. A distinct-entry count on its minimum-selection path is only a
constructive witness when it fits; exceeding a budget proves nothing by itself.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import idiom_pilot as pilot

MAX_SOURCE_CHARACTERS = 32768
MAX_EDGES_PER_SOURCE = 200000
CATEGORIES = {'identifier', 'number', 'string', 'regexp', 'keyword', 'syntax', 'operator', 'comment', 'layout'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_analysis(text, vocab, *, boundaries=None, tokens=(), tree=None):
    """Exact occurrence graph, missing spans and a necessary forced-slot bound."""
    if len(text) > MAX_SOURCE_CHARACTERS or len(vocab) > pilot.MAX_CANDIDATES:
        raise ValueError('coverage diagnostic budget exceeded')
    if len(set(vocab)) != len(vocab) or any(not isinstance(s, str) or not s for s in vocab):
        raise ValueError('unique nonempty diagnostic literals required')
    tree = pilot.joint.base.trie(vocab) if tree is None else tree
    n = len(text)
    allowed = set(range(n + 1)) if boundaries is None else set(boundaries)
    if not {0, n} <= allowed or any(type(p) is not int or p < 0 or p > n for p in allowed):
        raise ValueError('invalid diagnostic boundaries')
    categories = ['layout' if c.isspace() else 'syntax' for c in text]
    for token in tokens:
        a, b, category = token['start'], token['end'], token['category']
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= n or category not in CATEGORIES:
            raise ValueError('invalid token interval/category')
        categories[a:b] = [category] * (b - a)
    coverers = [set() for _ in text]
    reachable, edges = {0}, 0
    for start in range(n):
        if start not in allowed:
            continue
        node, end = tree, start
        while end < n and text[end] in node:
            node = node[text[end]]; end += 1
            if None not in node or end not in allowed:
                continue
            edges += 1
            if edges > MAX_EDGES_PER_SOURCE:
                raise ValueError('per-source diagnostic edge budget exceeded')
            index = node[None]
            if start in reachable:
                reachable.add(end)
            for position in range(start, end):
                coverers[position].add(index)
    complete = n in reachable
    try:
        pilot.joint.segment(text, tree)
        unrestricted = True
    except ValueError:
        unrestricted = False
    path = pilot.joint.segment(text, tree, allowed) if complete else None
    forced = {next(iter(ids)) for ids in coverers if len(ids) == 1}
    gaps = []
    offset = 0
    while offset < n:
        if coverers[offset]:
            offset += 1; continue
        start, category = offset, categories[offset]
        while offset < n and not coverers[offset] and categories[offset] == category:
            offset += 1
        value = text[start:offset]
        gaps.append({'start': start, 'end': offset, 'category': category,
            'characters': len(value), 'utf8_bytes': len(value.encode()), 'text_sha256': sha(value.encode())})
    missing = Counter()
    for gap in gaps:
        missing[gap['category']] += gap['characters']
    unrestricted_missing = bool(gaps)
    if boundaries is not None and not unrestricted:
        changes = [0] * (n + 1); raw_edges = 0
        for start in range(n):
            node, end = tree, start
            while end < n and text[end] in node:
                node = node[text[end]]; end += 1
                if None in node:
                    raw_edges += 1
                    if raw_edges > MAX_EDGES_PER_SOURCE:
                        raise ValueError('unrestricted diagnostic edge budget exceeded')
                    changes[start] += 1; changes[end] -= 1
        active = 0; unrestricted_missing = False
        for delta in changes[:-1]:
            active += delta
            unrestricted_missing |= active == 0
    return {'source_sha256': sha(text.encode()), 'source_characters': n,
        'full_pool_complete': complete, 'unrestricted_pool_complete': unrestricted,
        'boundary_only_obstruction': unrestricted and not complete,
        'unrestricted_pool_incomplete': not unrestricted,
        'candidate_text_scarcity': not unrestricted and unrestricted_missing,
        'unrestricted_path_connectivity_obstruction': not unrestricted and not unrestricted_missing,
        'path_connectivity_obstruction': not complete and not gaps,
        'longest_reachable_prefix_characters': max(reachable),
        'missing_characters_by_category': dict(missing), 'unsupported_spans': gaps,
        'admitted_occurrence_edges': edges, 'necessary_forced_entry_count': len(forced),
        'necessary_forced_entry_sha256': sorted(sha(vocab[i].encode()) for i in forced),
        'minimum_selection_path_entry_sha256': sorted(sha(vocab[i].encode()) for i in set(path)) if path is not None else None,
        'minimum_selection_path_selections': len(path) if path is not None else None,
        'minimum_selection_path_distinct_entries': len(set(path)) if path is not None else None}


def shared_budget_bounds(analyses):
    """Necessary intersection across alternatives; one constructive union.

    Bounds concern only the full-pool-representable subset. They never certify
    the entire supplied population when other programs lack a full-pool path.
    """
    problems = {}; required, sufficient = set(), set()
    for (pid, _), analysis in analyses.items():
        if analysis['full_pool_complete']:
            problems.setdefault(pid, []).append(analysis)
    for variants in problems.values():
        forced = [set(v['necessary_forced_entry_sha256']) for v in variants]
        required.update(set.intersection(*forced))
        witness = min(variants, key=lambda v: (v['minimum_selection_path_distinct_entries'],
                                               v['minimum_selection_path_selections'], v['source_sha256']))
        sufficient.update(witness['minimum_selection_path_entry_sha256'])
    return {'full_pool_representable_problems': len(problems),
        'necessary_shared_entry_lower_bound': len(required),
        'constructive_path_union_entry_upper_bound': len(sufficient)}


def budget_diagnosis(analysis, width, selected_complete):
    if type(width) is not int or not 4 <= width <= 8:
        raise ValueError('width must be4..8')
    capacity = 2**width
    slots = analysis['minimum_selection_path_distinct_entries']
    return {'capacity': capacity, 'selected_dictionary_complete': selected_complete,
        'full_pool_complete': analysis['full_pool_complete'],
        'individual_constructive_witness_within_budget': slots is not None and slots <= capacity,
        'necessary_forced_slots_exceed_budget': analysis['necessary_forced_entry_count'] > capacity,
        'minimum_selection_path_over_budget_only': slots is not None and slots > capacity,
        'selection_search_gap_witness': selected_complete is False and slots is not None and slots <= capacity,
        'shared_dictionary_feasibility_proven': False}


def read_json(path, maximum=64 * 1024**2):
    with Path(path).open('rb') as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError('bounded diagnostic metadata read exceeded')
    return json.loads(raw), sha(raw)


def diagnose(sources, parsed, pools, comparison=None):
    """Return private per-source evidence and a payload-free public aggregate."""
    boundaries = {(pid, variant): frozenset(parsed['boundaries'][f'{pid}/{variant}'])
        for pid, variants in sources.items() for variant in variants}
    cache, records, pool_records, totals, gap_owners = {}, [], [], [], {}
    measured = comparison is not None
    rows = comparison['rows'] if measured else [
        {'width': width, 'arm': arm, 'pool': name} for width in range(4, 9)
        for arm in ('strict', 'punctuation_fallback') for name in pools]
    for row in rows:
        arm, name, width = row['arm'], row['pool'], row['width']
        key = (arm, name)
        lexical = None if name == 'compression_fragments' else boundaries
        if key not in cache:
            pool = pilot.arm_pool(pools[name], sources, arm)
            vocab = pilot.joint.order(pool, []); tree = pilot.joint.base.trie(vocab)
            results = {}
            for pid, variants in sources.items():
                for variant, text in variants.items():
                    token_rows = parsed['tokens'][f'{pid}/{variant}']
                    results[pid, variant] = source_analysis(text, vocab, tree=tree,
                        boundaries=None if lexical is None else lexical[pid, variant], tokens=token_rows)
                    pool_records.append({'analysis_ref': f'{arm}/{name}/{pid}/{variant}',
                        'problem_id': pid, 'variant': variant, 'arm': arm, 'pool': name,
                        'analysis': results[pid, variant], 'syntactic_features': parsed['features'][f'{pid}/{variant}']})
            cache[key] = (pool, results)
        pool, analyses = cache[key]
        selected = None
        if measured:
            final = row['final']
            if not set(final['dictionary']) <= set(pool):
                raise ValueError('retained dictionary outside its declared pool')
            selected = pilot.joint.evaluate(sources, final['dictionary'], width, alphabet=[], allow_partial=True,
                                           boundaries=lexical, source_objective='compact')
            for field in ('coverage', 'selections', 'singleton_bits', 'literal_bits', 'package_bytes'):
                if selected[field] != final[field]:
                    raise ValueError('retained comparison/source/policy mismatch: ' + field)
        counts, missing = Counter(), Counter()
        for pid, variants in sources.items():
            options = []
            for variant in variants:
                analysis = analyses[pid, variant]
                expected = sha(sources[pid][variant].encode())
                if analysis['source_sha256'] != expected:
                    raise ValueError('diagnostic source identity drift')
                budget = budget_diagnosis(analysis, width, (pid, variant) in selected['parsed'] if measured else None)
                options.append((analysis, budget))
                records.append({'problem_id': pid, 'variant': variant, 'arm': arm, 'pool': name,
                                'width': width, 'analysis_ref': f'{arm}/{name}/{pid}/{variant}', 'budget': budget})
            # A problem is counted once even when several exact variants exist.
            counts['problems'] += 1
            counts['full_pool_complete'] += any(a['full_pool_complete'] for a, _ in options)
            counts['all_variants_full_pool_incomplete'] += all(not a['full_pool_complete'] for a, _ in options)
            for flag in ('boundary_only_obstruction', 'candidate_text_scarcity', 'path_connectivity_obstruction',
                         'unrestricted_path_connectivity_obstruction'):
                counts['variants_with_' + flag] += sum(a[flag] for a, _ in options)
            for flag in ('individual_constructive_witness_within_budget', 'selection_search_gap_witness', 'minimum_selection_path_over_budget_only'):
                counts[flag] += any(b[flag] for _, b in options)
            # A forced-slot impossibility for the supplied pool must hold for
            # EVERY variant; one difficult variant cannot exclude its problem.
            counts['all_variants_forced_slots_exceed_budget'] += all(b['necessary_forced_slots_exceed_budget'] for _, b in options)
            if measured:
                counts['selected_complete'] += pid in selected['chosen']
            for analysis, _ in options:
                missing.update(analysis['missing_characters_by_category'])
                for gap in analysis['unsupported_spans']:
                    gkey = (arm, name, gap['category'], gap['characters'], gap['text_sha256'])
                    gap_owners.setdefault(gkey, set()).add(pid)
        if not measured:
            counts['selected_complete'] = None
        totals.append({'width': width, 'arm': arm, 'pool': name, 'candidate_entries': len(pool),
            'counts': dict(counts), 'shared_subset_bounds': shared_budget_bounds(analyses),
            'missing_variant_characters_by_category': dict(missing)})
    repeated = [{'arm': arm, 'pool': name, 'category': category, 'characters': length,
                 'distinct_problems': len(owners)}
                for (arm, name, category, length, _), owners in gap_owners.items() if len(owners) >= 2]
    repeated.sort(key=lambda r: (-r['distinct_problems'], r['arm'], r['pool'], r['category'], r['characters']))
    feature_counts = Counter(feature for row in parsed['features'].values() for feature in row)
    aggregate = {'schema': 'gamma.idiom-coverage-diagnostic.v1', 'problems': len(sources),
        'rows': totals, 'repeated_missing_spans': repeated, 'syntactic_feature_source_counts': dict(feature_counts),
        'candidate_executions': 0, 'dictionary_fits': 0, 'source_rewrites': 0,
        'retained_dictionary_comparison_performed': measured,
        'qualification_created': False, 'shared_dictionary_feasibility_proven': False,
        'interpretation': 'Unlimited full-pool reachability and individual path witnesses diagnose this supplied pool only. Over-budget minimum paths are inconclusive unless a necessary forced-slot bound exceeds capacity. Syntactic features are opportunities, not semantic families or split authority.'}
    return {'schema': aggregate['schema'], 'pool_source_analyses': pool_records,
            'records': records, 'aggregate': aggregate}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--node-sha256', required=True)
    parser.add_argument('--comparison', type=Path)
    parser.add_argument('--comparison-pool-sha256')
    parser.add_argument('--pool-only', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.pool_only == bool(args.comparison):
        parser.error('choose exactly one of --pool-only or --comparison')
    if args.comparison and not args.comparison_pool_sha256:
        parser.error('retained comparison requires explicit --comparison-pool-sha256')
    if not args.output.is_absolute() or args.output.exists():
        raise ValueError('new absolute private diagnostic directory required')
    sources, inputs = pilot.load_fitting_inputs(args.config, args.config_sha256)
    if inputs['language'] != 'javascript':
        raise ValueError('this token diagnostic currently requires JavaScript inputs')
    comparison, comparison_sha, contract_sha = None, None, None
    if args.comparison:
        contract, contract_sha = read_json(args.comparison / 'contract.json')
        if contract['fitting_inputs']['config_sha256'] != args.config_sha256:
            raise ValueError('comparison/config identity mismatch')
        comparison, comparison_sha = read_json(args.comparison / 'summary.json')
        if comparison['contract_sha256'] != contract_sha:
            raise ValueError('retained comparison contract mismatch')
    parsed = pilot.syntactic_spans(sources, 'javascript', args.node, args.node_sha256, include_tokens=True)
    boundaries = {(pid, v): frozenset(parsed['boundaries'][f'{pid}/{v}']) for pid, vs in sources.items() for v in vs}
    if args.pool_only:
        pools, _ = pilot.admitted_pools(sources, parsed['spans'], parsed['excluded_units'], 'javascript', boundaries=boundaries)
        pool_sha = sha(json.dumps(pools, sort_keys=True, separators=(',', ':')).encode())
    else:
        pools, pool_sha = read_json(args.comparison / 'candidate-pools.json')
        if pool_sha != args.comparison_pool_sha256 or {k: len(v) for k, v in pools.items()} != contract['pool_sizes']:
            raise ValueError('retained candidate pool pin/size mismatch')
        # Diagnose the actual retained pool even when today's miner differs.
        # This does not admit historical literals under today's fitting policy.
        for name, pool in pools.items():
            if len(pool) != len(set(pool)) or any(not isinstance(s, str) or not s or len(s.encode()) > 160 for s in pool):
                raise ValueError('invalid retained candidate literals')
            owners, _ = pilot.occurrence_index(sources, pool,
                None if name == 'compression_fragments' else boundaries)
            if any(len(owners[s]) < 2 for s in pool):
                raise ValueError('retained candidate lacks distinct-problem source witnesses')
    result = diagnose(sources, parsed, pools, comparison)
    result['aggregate']['inputs'] = {'fitting_config_sha256': args.config_sha256,
        'comparison_sha256': comparison_sha, 'contract_sha256': contract_sha,
        'pool_sha256': pool_sha,
        'diagnostic_code_sha256': sha(Path(__file__).read_bytes()), 'parser_runtime_sha256': args.node_sha256,
        'code_sha256': {p.name: sha(p.read_bytes()) for p in [Path(__file__), Path(pilot.__file__),
            Path(pilot.__file__).with_name('idiom_spans.cjs'), Path(pilot.joint.__file__),
            Path(__file__).with_name('fitting_inputs.py'),
            *[Path(__file__).resolve().parents[2] / 'catalogue' / name for name in
              ('guide_admission.py', 'known_spec_service.py', 'boundary_policy.py', 'catalogue.py')]]}}
    args.output.mkdir()
    pilot.joint.write(args.output / 'diagnostics-private.json', result)
    pilot.joint.write(args.output / 'aggregate.json', result['aggregate'])
    print(json.dumps({'status': 'completed', 'problems': len(sources), 'rows': len(result['aggregate']['rows'])}))


if __name__ == '__main__':
    main()
