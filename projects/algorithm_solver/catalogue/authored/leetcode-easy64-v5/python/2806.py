"""2806. Account Balance After Rounded Purchase (Easy).

Specification: https://leetcode.com/problems/account-balance-after-rounded-purchase/description/
"""


def solve(purchaseAmount: int) -> int:
    """O(1) time and space; half-way values round upward, not to an even multiple."""
    rounded = 10 * ((purchaseAmount + 5) // 10)
    return 100 - rounded


class Solution:
    def accountBalanceAfterPurchase(self, purchaseAmount: int) -> int:
        return solve(purchaseAmount)
