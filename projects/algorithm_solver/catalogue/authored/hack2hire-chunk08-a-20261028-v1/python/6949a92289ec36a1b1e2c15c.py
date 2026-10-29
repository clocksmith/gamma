"""Hack2Hire 6949a92289ec36a1b1e2c15c (Reconstruct Billing Status, variant 2 of 3) over an INFERRED spec; qualification unknown."""


def solve(transactions, timestamp):
    balance = {}
    for _, user, charge, payment, when in transactions:
        if int(when) > timestamp:
            continue
        balance[user] = balance.get(user, 0) + (int(charge) if charge else 0) - (int(payment) if payment else 0)
    return [[user, balance[user]] for user in sorted(balance)]


class Solution:
    def billingStatusAt(self, transactions, timestamp):
        return solve(transactions, timestamp)
