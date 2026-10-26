"""1553. Minimum Number of Days to Eat N Oranges: memoized division states; O(log(n+1)^2) time and space."""

from functools import lru_cache


def solve(n: int) -> int:
    @lru_cache(None)
    def days(remaining: int) -> int:
        if remaining < 2:
            return remaining
        return 1 + min(remaining % 2 + days(remaining // 2),
                       remaining % 3 + days(remaining // 3))

    return days(n)


class Solution:
    def minDays(self, n: int) -> int:
        return solve(n)
