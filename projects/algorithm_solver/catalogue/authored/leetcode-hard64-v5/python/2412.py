"""2412. Minimum Money Required Before Transactions. Combine all possible losses with the largest final transaction requirement."""


def solve(transactions: list[list[int]]) -> int:
    """O(n) time and O(1) space. Inputs are preserved."""
    losses = 0
    reserve = 0
    for cost, cashback in transactions:
        losses += max(0, cost - cashback)
        reserve = max(reserve, min(cost, cashback))
    return losses + reserve


class Solution:
    def minimumMoney(self, transactions: list[list[int]]) -> int:
        return solve(transactions)
