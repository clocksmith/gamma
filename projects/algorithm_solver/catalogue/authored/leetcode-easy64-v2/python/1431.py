"""1431. Kids With the Greatest Number of Candies (Easy).

Specification: https://leetcode.com/problems/kids-with-the-greatest-number-of-candies/description/
"""


def solve(candies: list[int], extraCandies: int) -> list[bool]:
    """O(n) time, O(n) output space; preserve candies."""
    greatest = max(candies)
    return [count + extraCandies >= greatest for count in candies]


class Solution:
    def kidsWithCandies(self, candies: list[int], extraCandies: int) -> list[bool]:
        return solve(candies, extraCandies)
