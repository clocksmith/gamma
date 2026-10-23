"""Developer-authored synthetic gate behavior on the real 66-entry index contracts (no retrieval, no model).

  python3 findings/facet-gate-dev-128-v1/synthetic.py   (from projects/algorithm_solver)

Each case is one request and the decision the gate must make for named indexed sources, as if retrieval had
selected each of them. These cases were written by the implementer (claude) while building the grammar, so they
are software behavior checks, not recognition evidence. They never reuse the consumed fresh 36.
"""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from algsolve.facet_gate import FacetGate
from algsolve.splits import IndexEntry

A, X = 'accept', 'abstain'
S = 'best-time-to-buy-and-sell-stock'
CASES = [
    # The two consumed failure patterns, in new wording: an omitted trade count, an omitted duplicate policy.
    ('stock_count_omitted', 'I can hold at most one share at a time. There are no fees and no cooldown. What is the maximum profit from these daily prices?',
     {S: X, S + '-ii': X, S + '-iii': X, S + '-with-cooldown': X}),
    ('stock_count_omitted_2', 'Make the most money buying and selling this stock over the given days, with no transaction fees or waiting days.',
     {S: X, S + '-ii': X, S + '-with-cooldown': X}),
    ('stock_count_hedged', 'Maybe one trade, maybe more; no fees. Return the maximum profit.', {S: X, S + '-ii': X}),
    ('stock_count_alternative', 'You can do one or two transactions with no fee. Maximum profit?', {S: X, S + '-iii': X}),
    ('kth_duplicates_omitted', 'Return the k-th largest value in the list.', {'kth-largest-element-in-an-array': X}),
    ('kth_duplicates_omitted_2', 'Find the kth biggest element of nums without fully sorting it.', {'kth-largest-element-in-an-array': X}),
    ('kth_distinct', 'Return the kth largest distinct value in the array.', {'kth-largest-element-in-an-array': X}),
    ('kth_complete', 'Return the k-th largest number in the array, where duplicates are counted separately.', {'kth-largest-element-in-an-array': A}),
    ('kth_stream', 'For a stream of numbers, report the kth largest after each insertion, counting duplicates separately.', {'kth-largest-element-in-an-array': X}),
    ('rank_complete', 'Replace each element with its rank, where equal elements get the same rank.', {'rank-transform-of-an-array': A}),
    ('rank_duplicates_omitted', 'Replace each element with its rank, starting from 1.', {'rank-transform-of-an-array': X}),
    # Complete stock requests.
    ('stock_one', 'Given the daily prices, I may buy one share once and sell it on a later day. What is the maximum profit?',
     {S: A, S + '-ii': X, S + '-iii': X, S + '-with-cooldown': X}),
    ('stock_unlimited', 'I can buy and sell as many times as I like, holding at most one share. Return the most profit.',
     {S: X, S + '-ii': A, S + '-with-cooldown': X, S + '-iii': X}),
    ('stock_two', 'You may complete at most two transactions and cannot hold more than one share. Maximum profit?',
     {S + '-iii': A, S + '-ii': X}),
    ('stock_cooldown', 'Unlimited trades, but after selling I must wait one day before buying again. No fees. Maximum profit.',
     {S + '-with-cooldown': A, S + '-ii': X}),
    ('stock_fee', 'Any number of trades; each trade costs a commission per transaction. Maximum profit after fees.',
     {S + '-with-transaction-fee': A, S + '-ii': X}),
    # Houses and maximum sums.
    ('houses_line', 'Rob houses along a street, never robbing two adjacent houses. Maximize the money.', {'house-robber': A, 'house-robber-ii': X}),
    ('houses_circle', 'The houses are arranged in a circle, so the first and last are neighbors. Maximize the loot without adjacent picks.',
     {'house-robber': X, 'house-robber-ii': A}),
    ('max_sum_plain', 'Return the largest sum of a nonempty contiguous subarray.',
     {'maximum-subarray': A, 'maximum-sum-circular-subarray': X, 'maximum-subarray-sum-with-one-deletion': X}),
    ('max_sum_circular', 'The array is circular; return the largest possible sum of a nonempty subarray.',
     {'maximum-subarray': X, 'maximum-sum-circular-subarray': A}),
    ('max_sum_deletion', 'Return the maximum subarray sum if you may delete at most one element.',
     {'maximum-subarray': X, 'maximum-subarray-sum-with-one-deletion': X}),
    ('max_sum_deletion_plain', 'Return the maximum sum of a subarray after you delete at most one element from it.',
     {'maximum-subarray': X, 'maximum-subarray-sum-with-one-deletion': A}),
    # Islands.
    ('islands_count', 'Count how many islands are in the grid of land and water.',
     {'number-of-islands': A, 'number-of-closed-islands': X, 'number-of-distinct-islands': X, 'max-area-of-island': X}),
    ('islands_closed', 'Return how many closed islands there are, meaning islands surrounded by water on all sides.',
     {'number-of-islands': X, 'number-of-closed-islands': A, 'number-of-enclaves': X}),
    ('islands_area', 'Return the area of the largest island in the grid.', {'max-area-of-island': A, 'making-a-large-island': X}),
    ('islands_flip', 'Return the size of the largest island after you change at most one 0 to 1.', {'max-area-of-island': X, 'making-a-large-island': A}),
    ('islands_distinct', 'Return the number of distinct islands, where two islands are the same if one can be translated onto the other.',
     {'number-of-islands': X, 'number-of-distinct-islands': A, 'number-of-distinct-islands-ii': X}),
    ('islands_unspecified', 'Here is a grid of zeros and ones. Process the islands.', {'number-of-islands': X, 'max-area-of-island': X}),
    # Courses, pairs, searches, windows, frequency.
    ('courses_possible', 'Given prerequisite pairs, can you finish all the courses? Return true or false.', {'course-schedule': A, 'course-schedule-ii': X}),
    ('courses_order', 'Given prerequisite pairs, return any ordering of the courses that respects them.', {'course-schedule': X, 'course-schedule-ii': A}),
    ('courses_unspecified', 'Here are the courses and their prerequisite pairs; work it out.', {'course-schedule': X, 'course-schedule-ii': X}),
    ('pair_unsorted', 'The array is unsorted. Return the two indices whose values add up to the target.',
     {'two-sum': A, 'two-sum-ii-input-array-is-sorted': X}),
    ('pair_sorted_one_based', 'The numbers are sorted in ascending order. Return the two 1-based positions whose values add up to the target.',
     {'two-sum': X, 'two-sum-ii-input-array-is-sorted': A}),
    ('search_insert', 'In a sorted array, return the index where the target would be inserted.',
     {'search-insert-position': A, 'find-first-and-last-position-of-element-in-sorted-array': X}),
    ('search_range', 'Return the first and last positions of the target in the sorted array.',
     {'search-insert-position': X, 'find-first-and-last-position-of-element-in-sorted-array': A}),
    ('window_shortest', 'Return the length of the shortest contiguous subarray whose sum is at least the target.',
     {'minimum-size-subarray-sum': A, 'minimum-size-subarray-in-infinite-array': X}),
    ('window_infinite', 'The array repeats infinitely. Return the length of the shortest subarray summing exactly to the target.',
     {'minimum-size-subarray-sum': X, 'minimum-size-subarray-in-infinite-array': A}),
    ('frequent', 'Return the k most frequent elements of the array.',
     {'top-k-frequent-elements': A, 'least-number-of-unique-integers-after-k-removals': X}),
    ('fewest_unique', 'After removing exactly k elements, return the least number of unique integers left.',
     {'top-k-frequent-elements': X, 'least-number-of-unique-integers-after-k-removals': A}),
    # A source with no declared distinction keeps the existing route.
    ('singleton', 'Given a day, month and year, return the day of the week.', {'day-of-the-week': A}),
]


def main():
    doc = json.loads((ROOT / 'contracts/facet_gate_dev_128_v1.json').read_text())
    gate = FacetGate(doc)
    entries = {e['key'].removeprefix('lc:'): IndexEntry(**e)
               for e in json.loads((ROOT / 'runs/recognition-rebuild-dev-suby-v1/qualified-entries.json').read_text())}
    rows, wrong = [], []
    for name, text, expect in CASES:
        for key, want in expect.items():
            r = gate.check(text, entries[key])
            got = A if r['accepted'] else X
            rows.append({'case': name, 'source': key, 'expected': want, 'decision': got, 'reason': r['reason'],
                         'missing': r.get('missing'), 'contradictions': r.get('contradictions'), 'uncertain': r.get('uncertain')})
            if got != want:
                wrong.append(rows[-1])
    must_abstain = [r for r in rows if r['expected'] == X]
    must_accept = [r for r in rows if r['expected'] == A]
    report = {'evidence': 'developer-authored synthetic gate decisions on real index contracts; not recognition evidence',
              'contracts_sha256': hashlib.sha256((ROOT / 'contracts/facet_gate_dev_128_v1.json').read_bytes()).hexdigest(),
              'gate_sha256': hashlib.sha256((ROOT / 'algsolve/facet_gate.py').read_bytes()).hexdigest(),
              'cases': len(CASES), 'decisions': len(rows),
              'must_abstain': len(must_abstain), 'abstained': sum(r['decision'] == X for r in must_abstain),
              'must_accept': len(must_accept), 'accepted': sum(r['decision'] == A for r in must_accept),
              'mismatches': wrong, 'rows': rows}
    (Path(__file__).parent / 'synthetic.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=1))


if __name__ == '__main__':
    main()
