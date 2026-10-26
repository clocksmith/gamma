"""2600. K Items With the Maximum Sum (Easy).

Specification: https://leetcode.com/problems/k-items-with-the-maximum-sum/description/
"""


def solve(numOnes: int, numZeros: int, numNegOnes: int, k: int) -> int:
    """O(1) time and space; take ones, then zeros, then negative ones; k does not exceed available items."""
    positive = min(k, numOnes)
    negative = max(0, k - numOnes - numZeros)
    return positive - negative


class Solution:
    def kItemsWithMaximumSum(self, numOnes: int, numZeros: int, numNegOnes: int, k: int) -> int:
        return solve(numOnes, numZeros, numNegOnes, k)
