"""2914. Minimum Number of Changes to Make Binary String Beautiful: fix exactly one bit in each unequal adjacent pair."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    return sum(s[index] != s[index + 1] for index in range(0, len(s), 2))


class Solution:
    def minChanges(self, s: str) -> int:
        return solve(s)
