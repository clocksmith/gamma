"""3727. Maximum Alternating Sum of Squares."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are preserved and totals fit safe integers."""
    squares = sorted(value * value for value in nums)
    negative = len(nums) // 2
    return sum(squares[negative:]) - sum(squares[:negative])


class Solution:
    def maxAlternatingSum(self, nums: list[int]) -> int:
        return solve(nums)
