"""Hack2Hire 6a516506665efda9311f618d (Bank Transaction Mining) over an INFERRED spec; qualification unknown."""


def solve(accounts, transactions):
    index = {number: i for i, (number, _) in enumerate(accounts)}
    balance = [int(b) for _, b in accounts]
    for _, source, target, amount in transactions:
        s, t, value = index.get(source), index.get(target), int(amount)
        if s is not None and t is not None and s != t and balance[s] >= value:
            balance[s] -= value
            balance[t] += value
    order = sorted(range(len(accounts)), key=lambda i: (-balance[i], accounts[i][0]))
    return [[accounts[i][0], str(balance[i])] for i in order]


class Solution:
    def mineTransactions(self, accounts, transactions):
        return solve(accounts, transactions)
