"""facet-gate-dev-128-v3 synthetic gate behavior on the real 66-entry index contracts (no retrieval, no model).

  python3 findings/facet-gate-dev-128-v3/synthetic.py   (from projects/algorithm_solver)

Each case is a request plus, for named indexed sources (as if retrieval had selected each), the decision the
gate must make in candidate S (strict) and ablation D (add-on defaults). `wrong` marks a request whose intended
reading differs from that source, so accepting it would be a wrong acceptance. Written by the implementer
(claude) and the reviewer's counterexamples (codex, LOG 17:23Z and 17:38Z); software behavior only, not recognition evidence.
The consumed fresh 36 are not reused.
"""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from algsolve.facet_gate import FacetGate
from algsolve.splits import IndexEntry

A, X = 'accept', 'abstain'
S = 'best-time-to-buy-and-sell-stock'
II, CD, III, FEE = S + '-ii', S + '-with-cooldown', S + '-iii', S + '-with-transaction-fee'
KTH, RT = 'kth-largest-element-in-an-array', 'rank-transform-of-an-array'


def both(d, wrong=False):
    return {'S': d, 'D': d, 'wrong': wrong}


def coverage(wrong=False):  # complete in its natural reading but silent on add-ons: S abstains, D accepts
    return {'S': X, 'D': A, 'wrong': wrong}


def risk():  # D accepts a request that means a different source: a wrong acceptance in D
    return {'S': X, 'D': A, 'wrong': True}


CASES = [
    # The consumed failure patterns, in new wording.
    ('stock_count_omitted', 'I can hold at most one share at a time. There are no fees and no cooldown. What is the maximum profit from these daily prices?',
     {S: both(X, True), II: both(X, True), III: both(X, True), CD: both(X, True)}),
    ('stock_count_omitted_2', 'Make the most money buying and selling this stock over the given days, with no transaction fees or waiting days.',
     {S: both(X, True), II: both(X, True), CD: both(X, True)}),
    ('stock_count_hedged', 'Maybe one trade, maybe more; no fees. Return the maximum profit.', {S: both(X, True), II: both(X, True)}),
    ('stock_count_alternative', 'You can do one or two transactions with no fee. Maximum profit?', {S: both(X, True), III: both(X, True)}),
    ('kth_duplicates_omitted', 'Return the k-th largest value in the list.', {KTH: both(X, True)}),
    ('kth_duplicates_omitted_2', 'Find the kth biggest element of nums without fully sorting it.', {KTH: both(X, True)}),
    ('kth_distinct', 'Return the kth largest distinct value in the array.', {KTH: both(X, True)}),
    ('kth_stream', 'For a stream of numbers, report the kth largest after each insertion, counting duplicates separately.', {KTH: both(X, True)}),
    ('rank_duplicates_omitted', 'Replace each element with its rank, starting from 1.', {RT: both(X, True)}),
    # Reviewer counterexamples and unreadable add-on mentions.
    ('codex_brokerage', 'Buy and sell any number of times. A brokerage charge is subtracted on every sale.', {II: both(X, True)}),
    ('codex_nested_negation', 'Buy and sell any number of times. It is not true that there are no fees.', {II: both(X, True)}),
    ('codex_exactly_one', 'You must complete exactly one transaction: buy on one day and sell on a later day, even if it loses money. There are no fees and no cooldown. Return the maximum profit.',
     {S: both(X, True)}),
    ('codex_three', 'You may make multiple trades, at most three transactions, holding at most one share. No fees and no cooldown. Return maximum profit.',
     {II: both(X, True), III: both(X, True)}),
    ('repeatedly_not_unlimited', 'I can repeatedly buy and sell, holding one share at a time, with no fees and no cooldown; doing nothing is allowed. Maximum profit?',
     {II: both(X, True)}),
    ('zero_trade_omitted', 'I can buy and sell as many times as I like, holding at most one share, with no fees and no cooldown. Return the most profit.',
     {II: both(X, True)}),
    ('cooldown_paraphrase', 'Trade as often as you want, holding one share at a time, and doing nothing is allowed; after you sell, you are not allowed to buy on the following day.',
     {II: risk(), CD: both(X)}),
    ('circular_paraphrase', 'Rob the houses without taking two adjacent ones; the street loops back so house n sits beside house 1.',
     {'house-robber': risk(), 'house-robber-ii': both(X)}),
    ('diagonal_islands', 'Count how many islands there are; cells touching at corners belong to the same island.',
     {'number-of-islands': both(X, True)}),
    ('empty_subarray', 'Return the largest sum of a contiguous subarray; the empty subarray with sum zero is allowed.',
     {'maximum-subarray': both(X, True)}),
    ('pair_multiple', 'Return the indices of two numbers adding to target; several pairs may work, return the first one.',
     {'two-sum': both(X, True)}),
    # Fully explicit requests for reviewed sources.
    ('stock_one', 'Given the daily prices, buy once and sell later, or do nothing; there are no fees and no cooldown. What is the maximum profit?',
     {S: both(A), II: both(X, True), III: both(X, True), CD: both(X, True)}),
    ('stock_unlimited', 'I can buy and sell as many times as I like, holding at most one share, with no fees and no cooldown; I may skip trading. Return the most profit.',
     {S: both(X, True), II: both(A), CD: both(X, True), III: both(X, True)}),
    ('stock_two', 'At most two transactions, holding one share at a time, no fees, no cooldown; doing nothing is allowed. Maximum profit?', {III: both(A), II: both(X, True)}),
    ('stock_cooldown', 'Unlimited trades holding at most one share; after selling I must wait one day before buying again. No fees. Doing nothing is allowed. Maximum profit.',
     {CD: both(A), II: both(X, True)}),
    ('stock_fee', 'Any number of trades with at most one share; each trade costs a commission per transaction; no cooldown; I may skip trading.',
     {FEE: both(A), II: both(X, True)}),
    ('kth_complete', 'Return the k-th largest number in this array, where duplicates are counted separately.', {KTH: both(A)}),
    ('rank_complete', 'Replace each element with its rank; equal elements get the same rank and ranks start at 1.', {RT: both(A)}),
    ('houses_line_explicit', 'Houses in a row, not a circle; never rob two adjacent houses. Maximize the money.',
     {'house-robber': both(A), 'house-robber-ii': both(X, True)}),
    ('houses_circle', 'The houses are arranged in a circle, so the first and last are neighbors. Maximize the loot without adjacent picks.',
     {'house-robber': both(X, True), 'house-robber-ii': both(A)}),
    ('pair_unsorted', 'The array is unsorted and has exactly one solution. Return the two zero-based indices whose values add up to the target; the same element cannot be used twice.',
     {'two-sum': both(A), 'two-sum-ii-input-array-is-sorted': both(X, True)}),
    ('pair_sorted', 'The numbers are sorted in ascending order and there is exactly one solution at different positions. Return the two 1-based positions.',
     {'two-sum': both(X, True), 'two-sum-ii-input-array-is-sorted': both(A)}),
    ('courses_possible', 'Given prerequisite pairs, can you finish all the courses? Return true or false.',
     {'course-schedule': both(A), 'course-schedule-ii': both(X, True)}),
    ('courses_order', 'A pair [a, b] means b must be taken before a. Return any ordering of the courses that respects them.',
     {'course-schedule': both(X, True), 'course-schedule-ii': both(A)}),
    ('islands_count', 'Count how many islands are in the grid; land connects 4-directionally and outside the grid is water.',
     {'number-of-islands': both(A)}),
    ('frequent', 'Return the k most frequent elements; the answer is guaranteed unique and any order is fine.', {'top-k-frequent-elements': both(A)}),
    ('window_explicit', 'All numbers are positive. Return the length of the shortest contiguous subarray whose sum is at least the target, or zero if none; the array is used as given.',
     {'minimum-size-subarray-sum': both(A)}),
    ('max_sum_explicit', 'The array is not circular and no deletions are allowed. Return the largest sum of a nonempty contiguous subarray.',
     {'maximum-subarray': both(A)}),
    # Complete in the natural reading but silent on add-ons: the coverage cost of strictness.
    ('stock_one_natural', 'Given the daily prices, I may buy one share once and sell it on a later day, or do nothing. What is the maximum profit?', {S: coverage()}),
    ('houses_line_natural', 'Rob houses along a street, never robbing two adjacent houses. Maximize the money.', {'house-robber': coverage()}),
    ('max_sum_natural', 'Return the largest sum of a nonempty contiguous subarray.', {'maximum-subarray': coverage()}),
    ('kth_natural', 'Return the kth largest element in the array, counting duplicates separately.', {KTH: both(A)}),
    # Unreviewed sources abstain in both arms.
    ('unreviewed_closed', 'Return how many closed islands there are, meaning islands surrounded by water on all sides.', {'number-of-closed-islands': both(X)}),
    ('unreviewed_singleton', 'Given a day, month and year, return the day of the week.', {'day-of-the-week': both(X)}),
]


def main():
    gates = {arm: FacetGate(json.loads((ROOT / f'contracts/facet_gate_dev_128_v3_{name}.json').read_text()))
             for arm, name in (('S', 'strict'), ('D', 'defaults'))}
    entries = {e['key'].removeprefix('lc:'): IndexEntry(**e)
               for e in json.loads((ROOT / 'runs/recognition-rebuild-dev-suby-v1/qualified-entries.json').read_text())}
    rows = []
    for name, text, expect in CASES:
        for key, e in expect.items():
            row = {'case': name, 'source': key, 'wrong_if_accepted': e['wrong']}
            for arm, gate in gates.items():
                r = gate.check(text, entries[key])
                row[arm] = {'expected': e[arm], 'decision': A if r['accepted'] else X, 'reason': r['reason'],
                            'missing': r.get('missing'), 'uncertain': r.get('uncertain'), 'contradictions': r.get('contradictions')}
            rows.append(row)
    summary = {}
    for arm in gates:
        summary[arm] = {'decisions': len(rows), 'mismatches': sum(r[arm]['decision'] != r[arm]['expected'] for r in rows),
                        'wrong_acceptances': sum(r['wrong_if_accepted'] and r[arm]['decision'] == A for r in rows),
                        'accepted': sum(r[arm]['decision'] == A for r in rows)}
    report = {'evidence': 'developer-authored synthetic gate decisions on real index contracts; not recognition evidence',
              'files_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                               ['algsolve/facet_gate.py', 'contracts/facet_gate_dev_128_v3_strict.json', 'contracts/facet_gate_dev_128_v3_defaults.json']},
              'cases': len(CASES), 'summary': summary,
              'mismatches': [r for r in rows if any(r[a]['decision'] != r[a]['expected'] for a in gates)], 'rows': rows}
    (Path(__file__).parent / 'synthetic.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('rows', 'evidence')}, indent=1))


if __name__ == '__main__':
    main()
