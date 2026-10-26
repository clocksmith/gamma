"""2829. Determine the Minimum Sum of a k-avoiding Array: take the smaller member of each forbidden-sum pair and continue from k."""


def solve(n: int, k: int) -> int:
    """O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    small = min(n, k // 2)
    remaining = n - small
    return small * (small + 1) // 2 + remaining * (2 * k + remaining - 1) // 2


class Solution:
    def minimumSum(self, n: int, k: int) -> int:
        return solve(n, k)
