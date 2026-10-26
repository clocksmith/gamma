"""1523. Count Odd Numbers in an Interval Range (Easy).

Specification: https://leetcode.com/problems/count-odd-numbers-in-an-interval-range/description/
"""


def solve(low: int, high: int) -> int:
    """O(1) time and space; both bounds are inclusive."""
    return (high + 1) // 2 - low // 2


class Solution:
    def countOdds(self, low: int, high: int) -> int:
        return solve(low, high)
