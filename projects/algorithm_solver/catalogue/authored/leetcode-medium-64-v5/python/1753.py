"""1753. Maximum Score From Removing Stones: bound pair removals by half the total and the two smaller piles."""


def solve(a: int, b: int, c: int) -> int:
    """O(1) time and O(1) auxiliary space; inputs are read-only."""
    total = a + b + c
    return min(total // 2, total - max(a, b, c))


class Solution:
    def maximumScore(self, a: int, b: int, c: int) -> int:
        return solve(a, b, c)
