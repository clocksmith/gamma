"""Hack2Hire 69499ed489ec36a1b1e2c13f (Reconstruct Billing Status, variant 1 of 3) over an INFERRED spec; qualification unknown."""


def solve(transactions):
    balance = {}
    for _, user, charge, payment, _ in transactions:
        balance[user] = balance.get(user, 0) + (int(charge) if charge else 0) - (int(payment) if payment else 0)
    return [[user, balance[user]] for user in sorted(balance)]


class Solution:
    def reconstructBilling(self, transactions):
        return solve(transactions)
