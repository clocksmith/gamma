"""1413. Minimum Value to Get Positive Step by Step Sum (Easy).

Specification: https://leetcode.com/problems/minimum-value-to-get-positive-step-by-step-sum/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; preserve nums."""
    prefix = 0
    lowest = 0
    for value in nums:
        prefix += value
        lowest = min(lowest, prefix)
    return 1 - lowest


class Solution:
    def minStartValue(self, nums: list[int]) -> int:
        return solve(nums)
