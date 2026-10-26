"""1551. Minimum Operations to Make Array Equal: sum the symmetric deficits of the arithmetic progression."""


def solve(n: int) -> int:
    """O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    return (n // 2) * ((n + 1) // 2)


class Solution:
    def minOperations(self, n: int) -> int:
        return solve(n)
