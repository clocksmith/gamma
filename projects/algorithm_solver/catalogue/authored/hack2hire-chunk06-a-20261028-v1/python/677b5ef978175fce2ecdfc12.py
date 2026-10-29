"""Hack2Hire 677b5ef978175fce2ecdfc12 (End Of Day Balance, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(transactions):
    balance = {}
    for payer, payee, amount in transactions:
        balance[payer] = balance.get(payer, 0) - amount
        balance[payee] = balance.get(payee, 0) + amount
    return [[party, balance[party]] for party in sorted(balance)]


class Solution:
    def endOfDayBalance(self, transactions):
        return solve(transactions)
