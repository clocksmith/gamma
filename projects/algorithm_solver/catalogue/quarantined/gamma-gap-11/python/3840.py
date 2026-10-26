"""3840. House Robber V."""
from __future__ import annotations


def solve(nums: list[int], colors: list[int]) -> int:
    """O(n) time and O(1) space; only equal-color adjacent selections conflict."""
    skipped = taken = 0
    for index, value in enumerate(nums):
        best = max(skipped, taken)
        next_taken = (skipped if index and colors[index] == colors[index - 1] else best) + value
        skipped, taken = best, next_taken
    return max(skipped, taken)


class Solution:
    def rob(self, nums: list[int], colors: list[int]) -> int:
        return solve(nums, colors)
