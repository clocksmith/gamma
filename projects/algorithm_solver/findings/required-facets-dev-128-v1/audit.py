"""Tiny deterministic development audit: fixed retrieval/approval, real sandbox.

Run from Gamma with PYTHONPATH=projects/algorithm_solver:projects/algorithm_solver/tests.
No model, training, fresh/protected data or performance measurement.
"""
import hashlib
import json
from pathlib import Path

from algsolve.answer import answer
from algsolve.required_facets import RequiredFacets, answer_with_required_facets
from algsolve.validate import judge_problem
from test_required_facets import Approved, contract, fixture

ROOT = Path('projects/algorithm_solver')
OUT = ROOT / 'findings/required-facets-dev-128-v1'
STOCK = '''class Solution:
    def profit(self, prices):
        return sum(max(0, b-a) for a, b in zip(prices, prices[1:]))
'''
RANK = '''class Solution:
    def select(self, items, k):
        return sorted(items, reverse=True)[k-1]
'''
CASES = [
    ('stock_complete', 'stock', 'Unlimited transactions. No fees or cooldown. Maximum profit.', True),
    ('stock_paraphrase', 'stock', 'Any number of stock trades. No transaction fee nor waiting days. Most profit.', True),
    ('stock_missing_count', 'stock', 'No fees or cooldown. Maximum profit.', False),
    ('stock_missing_fee', 'stock', 'Unlimited transactions. No cooldown. Maximum profit.', False),
    ('stock_missing_cooldown', 'stock', 'Unlimited transactions. No fees. Maximum profit.', False),
    ('stock_missing_output', 'stock', 'Unlimited transactions. No fees or cooldown.', False),
    ('stock_conflict', 'stock', 'Unlimited transactions. Buy once. No fees or cooldown. Maximum profit.', False),
    ('stock_uncertain', 'stock', 'Maybe unlimited transactions. No fees or cooldown. Maximum profit.', False),
    ('rank_complete', 'rank', 'Return kth largest in one fixed array. Counting duplicate occurrences separately.', True),
    ('rank_paraphrase', 'rank', 'Return rank-th largest in this array. Counting duplicate occurrences separately.', True),
    ('rank_missing_duplicates', 'rank', 'Return kth largest in one fixed array.', False),
    ('rank_contradiction', 'rank', 'Return kth largest in one fixed array. Count each distinct value once.', False),
]


def main():
    rows = []
    for name, family, text, allowed in CASES:
        context, query, gate = fixture(text)
        source = context.entries[0]
        source.references[0]['code'] = STOCK
        oracle = [{'args': [[1, 4, 2, 6]], 'expected': 7}, {'args': [[8, 3, 1]], 'expected': 0}]
        if family == 'rank':
            source.statement = 'Stored occurrence-rank specification'
            source.entry = {'class': 'Solution', 'method': 'select'}
            source.params = [['items', 'List[int]'], ['k', 'int']]
            source.references[0]['code'] = RANK
            query.public_tests = [{'args': [[9, 4, 1], 2], 'expected': 4}]
            gate = RequiredFacets([contract(source.statement, dict(output='kth', updates='batch', duplicates='occurrences'))])
            oracle = [{'args': [[9, 9, 4], 2], 'expected': 9}, {'args': [[-3, -1, -1], 3], 'expected': -3}]
        control = answer(context, query, approved_library=Approved())
        candidate = answer_with_required_facets(context, query, Approved(), gate)
        assert control['decision'] == 'answered', control
        assert candidate['decision'] == ('answered' if allowed else 'abstain'), candidate
        check = None
        if allowed:
            query.entry = source.entry
            check = judge_problem(query, candidate['code'], oracle, wall_seconds=5).to_dict()
            assert check['passed'], check
        rows.append(dict(case=name, expected_answer=allowed,
                         control_decision=control['decision'], candidate_decision=candidate['decision'],
                         candidate_reason=candidate.get('reason'), public_attempts=len(candidate['attempts']),
                         development_oracle=check))
    report = dict(evidence='developer-exposed synthetic behavior; fixed retrieval and test approval stub; real sandbox',
                  cases=rows, control_answers=len(rows), candidate_answers=sum(r['candidate_decision']=='answered' for r in rows),
                  candidate_abstentions=sum(r['candidate_decision']=='abstain' for r in rows),
                  expected_abstentions_blocked=sum(not r['expected_answer'] and r['candidate_decision']=='abstain' for r in rows),
                  expected_answers_lost=sum(r['expected_answer'] and r['candidate_decision']!='answered' for r in rows),
                  declaration='Not a retrieval benchmark, independent qualification, latency result or promotion. No fresh cases replayed.',
                  source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                                 ['algsolve/required_facets.py', 'algsolve/requirement_filter.py', 'algsolve/requirements.py']})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'behavior.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'cases'}, indent=2))


if __name__ == '__main__':
    main()
