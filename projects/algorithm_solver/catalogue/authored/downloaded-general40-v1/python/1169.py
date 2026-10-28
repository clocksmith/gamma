"""1169. Invalid Transactions (Medium).

Specification: https://leetcode.com/problems/invalid-transactions/description/
"""


def _parse(text):
    parts = text.split(',')
    return {'name': parts[0], 'time': int(parts[1]), 'amount': int(parts[2]), 'city': parts[3]}


def solve(transactions: list[str]) -> list[str]:
    parsed = [_parse(t) for t in transactions]
    result = []
    for i, tx in enumerate(parsed):
        invalid = tx['amount'] > 1000
        if not invalid:
            for j, other in enumerate(parsed):
                if i != j and other['name'] == tx['name'] and other['city'] != tx['city'] and abs(other['time'] - tx['time']) <= 60:
                    invalid = True
                    break
        if invalid:
            result.append(transactions[i])
    return result


class Solution:
    def invalidTransactions(self, transactions: list[str]) -> list[str]:
        return solve(transactions)
