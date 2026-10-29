"""Hack2Hire 6949b64a89ec36a1b1e2c16d (Reconstruct Billing Status, variant 3 of 3) over an INFERRED spec; qualification unknown."""


def solve(transactions):
    ordered = sorted(transactions, key=lambda row: (int(row[4]), row[0]))
    balance, peak = {}, {}
    for _, user, charge, payment, _ in ordered:
        value = balance.get(user, 0) + (int(charge) if charge else 0) - (int(payment) if payment else 0)
        balance[user] = value
        if value > peak.get(user, 0):
            peak[user] = value
    return [[user, balance[user], peak.get(user, 0)] for user in sorted(balance)]


class Solution:
    def billingHistory(self, transactions):
        return solve(transactions)
