"""575. Distribute Candies (Easy).

Specification: https://leetcode.com/problems/distribute-candies/description/
"""


def solve(candyType: list[int]) -> int:
    """O(n) expected time, O(n) space; distinct types are capped by the number of candies allowed."""
    return min(len(set(candyType)), len(candyType) // 2)


class Solution:
    def distributeCandies(self, candyType: list[int]) -> int:
        return solve(candyType)
