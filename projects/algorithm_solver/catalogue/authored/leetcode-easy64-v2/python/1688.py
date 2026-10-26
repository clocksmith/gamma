"""1688. Count of Matches in Tournament (Easy).

Specification: https://leetcode.com/problems/count-of-matches-in-tournament/description/
"""


def solve(n: int) -> int:
    """O(1) time and space; every match eliminates exactly one of n teams."""
    return n - 1


class Solution:
    def numberOfMatches(self, n: int) -> int:
        return solve(n)
