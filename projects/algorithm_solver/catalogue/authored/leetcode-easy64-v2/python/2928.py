"""2928. Distribute Candies Among Children I (Easy).

Specification: https://leetcode.com/problems/distribute-candies-among-children-i/description/
"""


def solve(n: int, limit: int) -> int:
    """O(min(n, limit) + 1) time, O(1) space; children are distinct."""
    result = 0
    for first in range(min(n, limit) + 1):
        remaining = n - first
        lowest_second = max(0, remaining - limit)
        highest_second = min(limit, remaining)
        result += max(0, highest_second - lowest_second + 1)
    return result


class Solution:
    def distributeCandies(self, n: int, limit: int) -> int:
        return solve(n, limit)
