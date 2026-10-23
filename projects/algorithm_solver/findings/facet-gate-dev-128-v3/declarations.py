"""Write the two facet-gate-dev-128-v3 contract documents (refuses to overwrite).

  python3 findings/facet-gate-dev-128-v3/declarations.py   (from projects/algorithm_solver)

  contracts/facet_gate_dev_128_v3_strict.json    candidate S: no absence defaults
  contracts/facet_gate_dev_128_v3_defaults.json  ablation D: add-on absence defaults (not eligible for confirmation)

Both documents hold the same 66 contracts; only `absence_defaults` differs. Statement hashes come from the
66-entry index in runs/recognition-rebuild-dev-suby-v1/qualified-entries.json. A source is `reviewed` only
when its answer-changing facets were reviewed against same-family siblings *and* material alternative readings
that have no indexed source (the rank failure). Every other source is `unreviewed` and abstains.
"""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ROOT / 'runs/recognition-rebuild-dev-suby-v1/qualified-entries.json'
OUT = {'strict': ROOT / 'contracts/facet_gate_dev_128_v3_strict.json',
       'defaults': ROOT / 'contracts/facet_gate_dev_128_v3_defaults.json'}
DEFAULTS = {'fee': 'none', 'cooldown': 'none', 'layout': 'line', 'deletion': 'none', 'repetition': 'none',
            'border': 'any', 'transform': 'translation', 'changes': 'none', 'updates': 'batch',
            'ordering': 'arbitrary', 'indexing': 'zero'}
COMPATIBLE = [['ordering', 'sorted', 'arbitrary']]

STOCK_MULTI = ['transactions', 'zero_trade', 'fee', 'cooldown', 'holding']
# Reviewed sources: key -> (family, facts, required, review note). Required lists include every facet the review
# found answer-changing, add-ons included; in the strict document each needs explicit evidence.
R = {
    'best-time-to-buy-and-sell-stock': ('stock', dict(transactions='one', zero_trade='allowed', fee='none', cooldown='none'),
        ['transactions', 'zero_trade', 'fee', 'cooldown'], 'at most one purchase (zero allowed) implies holding one share'),
    'best-time-to-buy-and-sell-stock-ii': ('stock', dict(zero_trade='allowed', transactions='unlimited', fee='none', cooldown='none', holding='one_share'), STOCK_MULTI,
        'holding several shares at once changes the answer'),
    'best-time-to-buy-and-sell-stock-iii': ('stock', dict(zero_trade='allowed', transactions='two', fee='none', cooldown='none', holding='one_share'), STOCK_MULTI, ''),
    'best-time-to-buy-and-sell-stock-iv': ('stock', dict(zero_trade='allowed', transactions='k', fee='none', cooldown='none', holding='one_share'), STOCK_MULTI, ''),
    'best-time-to-buy-and-sell-stock-with-cooldown': ('stock', dict(zero_trade='allowed', transactions='unlimited', fee='none', cooldown='one_day', holding='one_share'), STOCK_MULTI, ''),
    'best-time-to-buy-and-sell-stock-with-transaction-fee': ('stock', dict(zero_trade='allowed', transactions='unlimited', fee='per_trade', cooldown='none', holding='one_share'), STOCK_MULTI, ''),
    'kth-largest-element-in-an-array': ('rank', dict(output='kth', duplicates='occurrences', updates='batch'), ['output', 'duplicates', 'updates'],
        'distinct-value reading has no indexed source but is material'),
    'rank-transform-of-an-array': ('rank', dict(output='ranks', duplicates='shared_rank', rank_base='one'), ['output', 'duplicates', 'rank_base'], ''),
    'house-robber': ('houses', dict(layout='line', adjacency='no_adjacent'), ['layout', 'adjacency'], ''),
    'house-robber-ii': ('houses', dict(layout='circle', adjacency='no_adjacent'), ['layout', 'adjacency'], ''),
    'two-sum': ('pair', dict(output='positions', ordering='arbitrary', indexing='zero', solutions='exactly_one', reuse='distinct_positions'),
        ['output', 'ordering', 'indexing', 'solutions', 'reuse'], 'several solutions or reuse would change the answer'),
    'two-sum-ii-input-array-is-sorted': ('pair', dict(output='positions', ordering='sorted', indexing='one', solutions='exactly_one', reuse='distinct_positions'),
        ['output', 'ordering', 'indexing', 'solutions', 'reuse'], ''),
    'course-schedule': ('courses', dict(output='possible'), ['output'], 'prerequisite direction does not change feasibility'),
    'course-schedule-ii': ('courses', dict(output='order', prereq_direction='second_first'), ['output', 'prereq_direction'], 'direction reverses the order'),
    'number-of-islands': ('islands', dict(output='count', connectivity='four', border='any'), ['output', 'connectivity', 'border'],
        'diagonal connectivity has no indexed source but is material'),
    'max-area-of-island': ('islands', dict(output='area', connectivity='four', border='any', changes='none'), ['output', 'connectivity', 'border', 'changes'], ''),
    'top-k-frequent-elements': ('frequency', dict(output='frequent', ties='unique_answer', answer_order='any'), ['output', 'ties', 'answer_order'],
        'tie-breaking and output order would change the answer'),
    'minimum-size-subarray-sum': ('target_window', dict(output='shortest_window', relation='at_least', positivity='positive', fallback='zero', repetition='none'),
        ['output', 'relation', 'positivity', 'fallback', 'repetition'], 'negative values break the sliding window; exact-sum reading is material'),
    'maximum-subarray': ('max_sum', dict(output='max_sum', nonempty='yes', layout='line', deletion='none'), ['output', 'nonempty', 'layout', 'deletion'],
        'an empty subarray reading changes all-negative inputs'),
}
# Unreviewed sources keep v1's family facts for reference only; they abstain.
U = {
    'number-of-closed-islands': ('islands', dict(output='count', border='interior')),
    'number-of-enclaves': ('islands', dict(output='cells', border='interior')),
    'number-of-distinct-islands': ('islands', dict(output='distinct_shapes', transform='translation')),
    'number-of-distinct-islands-ii': ('islands', dict(output='distinct_shapes', transform='rotation_reflection')),
    'making-a-large-island': ('islands', dict(output='area', changes='one_flip')),
    'shortest-bridge': ('islands', dict(output='bridge')),
    'largest-1-bordered-square': ('islands', dict(output='bordered_square')),
    'house-robber-iii': ('houses', dict(layout='tree')),
    'search-insert-position': ('sorted_search', dict(output='insert_position')),
    'find-first-and-last-position-of-element-in-sorted-array': ('sorted_search', dict(output='range')),
    'find-target-indices-after-sorting-array': ('sorted_search', dict(output='target_indices')),
    'maximum-subarray-sum-with-one-deletion': ('max_sum', dict(layout='line', deletion='one')),
    'maximum-sum-circular-subarray': ('max_sum', dict(layout='circle', deletion='none')),
    'minimum-size-subarray-in-infinite-array': ('target_window', dict(output='shortest_window', repetition='infinite')),
    'maximum-number-of-non-overlapping-subarrays-with-sum-equals-target': ('target_window', dict(output='count_nonoverlapping')),
    'find-two-non-overlapping-sub-arrays-each-with-target-sum': ('target_window', dict(output='two_windows')),
    'length-of-the-longest-subsequence-that-sums-to-target': ('target_window', dict(output='longest_subsequence')),
    'least-number-of-unique-integers-after-k-removals': ('frequency', dict(output='remaining_unique')),
    'top-k-frequent-words': ('frequency', dict(output='frequent')),
}


def main():
    assert not any(p.exists() for p in OUT.values()), 'refusing to overwrite'
    entries = json.loads(ENTRIES.read_text())
    keys = {e['key'].removeprefix('lc:') for e in entries}
    assert set(R) <= keys and set(U) <= keys and not set(R) & set(U)
    contracts = []
    for e in sorted(entries, key=lambda e: e['key']):
        k = e['key'].removeprefix('lc:')
        h = hashlib.sha256(e['statement'].encode()).hexdigest()
        if k in R:
            family, facts, required, note = R[k]
            assert set(required) <= set(facts), k
            contracts.append({'source_key': e['key'], 'statement_sha256': h, 'family': family, 'facts': facts,
                              'required_facets': sorted(required), 'completeness': 'reviewed', 'note': note})
        else:
            family, facts = U.get(k, ('singleton', {}))
            contracts.append({'source_key': e['key'], 'statement_sha256': h, 'family': family, 'facts': facts,
                              'required_facets': [], 'completeness': 'unreviewed', 'note': 'not reviewed for material alternatives; abstains'})
    for arm, path in OUT.items():
        doc = {'schema_version': 1, 'candidate': f'facet-gate-dev-128-v3-{arm}',
               'authority': 'Implementer-declared (claude); review by codex requested. Necessary conditions, not semantic equivalence.',
               'role': 'candidate S (strict)' if arm == 'strict' else 'ablation D (add-on absence defaults); not eligible for confirmation',
               'absence_defaults': {} if arm == 'strict' else DEFAULTS, 'compatible': COMPATIBLE, 'contracts': contracts}
        path.write_text(json.dumps(doc, indent=1, sort_keys=True) + '\n')
        print(arm, len(contracts), sum(c['completeness'] == 'reviewed' for c in contracts), hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
