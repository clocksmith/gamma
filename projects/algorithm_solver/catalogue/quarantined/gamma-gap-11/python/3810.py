"""3810. Minimum Operations to Reach Target Array."""
from __future__ import annotations


def solve(nums: list[int], target: list[int]) -> int:
    """O(n) expected time and O(n) space; count distinct original values at mismatching positions."""
    return len({value for value, desired in zip(nums, target) if value != desired})


class Solution:
    def minOperations(self, nums: list[int], target: list[int]) -> int:
        return solve(nums, target)
