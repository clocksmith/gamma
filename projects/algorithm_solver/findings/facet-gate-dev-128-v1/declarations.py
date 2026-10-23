"""Write contracts/facet_gate_dev_128_v1.json: one reviewed facet contract per indexed source.

  python3 findings/facet-gate-dev-128-v1/declarations.py   (from projects/algorithm_solver; refuses to overwrite)

Statement hashes come from the 66 indexed entries of runs/recognition-rebuild-dev-suby-v1/qualified-entries.json.
Required facets are the ones that separate a source from its same-family siblings, or that have a material
alternative reading (trade count, duplicate policy). Sources with no such distinction declare none, which the
gate treats as a reviewed statement, not as an unbound source.
"""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'contracts/facet_gate_dev_128_v1.json'
ENTRIES = ROOT / 'runs/recognition-rebuild-dev-suby-v1/qualified-entries.json'

ABSENCE_DEFAULTS = {  # add-on features that a request names when they apply
    'fee': 'none', 'cooldown': 'none', 'layout': 'line', 'deletion': 'none', 'repetition': 'none',
    'border': 'any', 'transform': 'translation', 'changes': 'none', 'updates': 'batch',
    'ordering': 'arbitrary', 'indexing': 'zero'}
COMPATIBLE = [['ordering', 'sorted', 'arbitrary']]  # an algorithm for arbitrary input also serves sorted input

FAMILIES = {
    'stock': ('Same prices-only interface for I, II, III and cooldown; trade count has no default reading.',
              ['transactions', 'fee', 'cooldown']),
    'houses': ('House robber I and II share an interface; the circular street is an add-on.', ['layout']),
    'islands': ('Many same-interface grid problems; the output decides which one.', ['output', 'border', 'transform', 'changes']),
    'courses': ('Course schedule I and II share an interface; output decides.', ['output']),
    'pair': ('Two-sum variants: sortedness and position base change the answer.', ['output', 'ordering', 'indexing']),
    'sorted_search': ('Same (nums, target) interface; output decides.', ['output']),
    'max_sum': ('Same nums-only interface; circular layout and one deletion are add-ons.', ['layout', 'deletion']),
    'target_window': ('Same (nums, target) interface; output decides; infinite repetition is an add-on.', ['output', 'repetition']),
    'rank': ('Duplicate policy has no default reading; a stream is an add-on.', ['output', 'duplicates', 'updates']),
    'frequency': ('Same (nums, k) interface for top-k frequent and fewest-unique-after-removals; output decides.', ['output']),
}

# key: (family, facts, required, note)
D = {
    'best-time-to-buy-and-sell-stock': ('stock', dict(transactions='one', fee='none', cooldown='none'), None, ''),
    'best-time-to-buy-and-sell-stock-ii': ('stock', dict(transactions='unlimited', fee='none', cooldown='none'), None, ''),
    'best-time-to-buy-and-sell-stock-iii': ('stock', dict(transactions='two', fee='none', cooldown='none'), None, ''),
    'best-time-to-buy-and-sell-stock-iv': ('stock', dict(transactions='k', fee='none', cooldown='none'), None, 'k parameter'),
    'best-time-to-buy-and-sell-stock-with-cooldown': ('stock', dict(transactions='unlimited', fee='none', cooldown='one_day'), None, ''),
    'best-time-to-buy-and-sell-stock-with-transaction-fee': ('stock', dict(transactions='unlimited', fee='per_trade', cooldown='none'), None, 'fee parameter'),
    'house-robber': ('houses', dict(layout='line'), ['layout'], ''),
    'house-robber-ii': ('houses', dict(layout='circle'), ['layout'], ''),
    'house-robber-iii': ('houses', dict(layout='tree'), [], 'TreeNode interface separates it'),
    'number-of-islands': ('islands', dict(output='count', border='any'), ['output', 'border'], 'character grid'),
    'max-area-of-island': ('islands', dict(output='area', border='any', changes='none'), ['output', 'border', 'changes'], ''),
    'making-a-large-island': ('islands', dict(output='area', changes='one_flip'), ['output', 'changes'], ''),
    'number-of-closed-islands': ('islands', dict(output='count', border='interior'), ['output', 'border'], ''),
    'number-of-enclaves': ('islands', dict(output='cells', border='interior'), ['output', 'border'], ''),
    'number-of-distinct-islands': ('islands', dict(output='distinct_shapes', transform='translation'), ['output', 'transform'], ''),
    'number-of-distinct-islands-ii': ('islands', dict(output='distinct_shapes', transform='rotation_reflection'), ['output', 'transform'], ''),
    'shortest-bridge': ('islands', dict(output='bridge'), ['output'], ''),
    'largest-1-bordered-square': ('islands', dict(output='bordered_square'), ['output'], ''),
    'course-schedule': ('courses', dict(output='possible'), ['output'], ''),
    'course-schedule-ii': ('courses', dict(output='order'), ['output'], ''),
    'course-schedule-iii': ('courses', {}, [], 'different interface (course durations)'),
    'course-schedule-iv': ('courses', {}, [], 'different interface (queries)'),
    'parallel-courses-ii': ('courses', {}, [], 'different interface (k per semester)'),
    'two-sum': ('pair', dict(output='positions', ordering='arbitrary', indexing='zero'), None, ''),
    'two-sum-ii-input-array-is-sorted': ('pair', dict(output='positions', ordering='sorted', indexing='one'), None, ''),
    'two-sum-bsts': ('pair', {}, [], 'TreeNode interface separates it'),
    'search-insert-position': ('sorted_search', dict(output='insert_position'), ['output'], ''),
    'find-first-and-last-position-of-element-in-sorted-array': ('sorted_search', dict(output='range'), ['output'], ''),
    'find-target-indices-after-sorting-array': ('sorted_search', dict(output='target_indices'), ['output'], ''),
    'maximum-subarray': ('max_sum', dict(layout='line', deletion='none'), None, ''),
    'maximum-subarray-sum-with-one-deletion': ('max_sum', dict(layout='line', deletion='one'), None, ''),
    'maximum-sum-circular-subarray': ('max_sum', dict(layout='circle', deletion='none'), None, ''),
    'minimum-size-subarray-sum': ('target_window', dict(output='shortest_window', repetition='none'), None, '(target, nums) order'),
    'minimum-size-subarray-in-infinite-array': ('target_window', dict(output='shortest_window', repetition='infinite'), None, ''),
    'maximum-number-of-non-overlapping-subarrays-with-sum-equals-target': ('target_window', dict(output='count_nonoverlapping'), ['output'], ''),
    'find-two-non-overlapping-sub-arrays-each-with-target-sum': ('target_window', dict(output='two_windows'), ['output'], ''),
    'length-of-the-longest-subsequence-that-sums-to-target': ('target_window', dict(output='longest_subsequence'), ['output'], ''),
    'kth-largest-element-in-an-array': ('rank', dict(output='kth', duplicates='occurrences', updates='batch'), None, ''),
    'rank-transform-of-an-array': ('rank', dict(output='ranks', duplicates='shared_rank'), ['output', 'duplicates'], ''),
    'find-k-pairs-with-smallest-sums': ('rank', {}, [], 'different interface (two arrays)'),
    'top-k-frequent-elements': ('frequency', dict(output='frequent'), ['output'], ''),
    'least-number-of-unique-integers-after-k-removals': ('frequency', dict(output='remaining_unique'), ['output'], ''),
    'top-k-frequent-words': ('frequency', dict(output='frequent'), [], 'string interface separates it'),
    'most-frequent-number-following-key-in-an-array': ('frequency', {}, [], 'different interface (key)'),
}
SINGLETON_NOTE = 'No same-interface sibling in the index and no declared material alternative reading.'


def main():
    assert not OUT.exists(), 'refusing to overwrite'
    entries = json.loads(ENTRIES.read_text())
    keys = {e['key'].removeprefix('lc:') for e in entries}
    assert set(D) <= keys, set(D) - keys
    contracts = []
    for e in sorted(entries, key=lambda e: e['key']):
        k = e['key'].removeprefix('lc:')
        family, facts, required, note = D.get(k, ('singleton', {}, [], SINGLETON_NOTE))
        if required is None:
            required = [f for f in FAMILIES[family][1] if f in facts]
        contracts.append({'source_key': e['key'], 'statement_sha256': hashlib.sha256(e['statement'].encode()).hexdigest(),
                          'family': family, 'facts': facts, 'required_facets': sorted(required), 'note': note})
    doc = {'schema_version': 1, 'candidate': 'facet-gate-dev-128-v1',
           'authority': 'Implementer-declared (claude) for the 66-entry development index; pending independent review. '
                        'Necessary conditions, not semantic equivalence.',
           'absence_defaults': ABSENCE_DEFAULTS, 'compatible': COMPATIBLE,
           'families': {k: {'reason': r, 'facets': f} for k, (r, f) in FAMILIES.items()},
           'contracts': contracts}
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + '\n')
    print(len(contracts), hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
