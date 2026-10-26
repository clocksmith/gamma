"""3105. Longest Strictly Increasing or Strictly Decreasing Subarray (Easy).

Specification: https://leetcode.com/problems/longest-strictly-increasing-or-strictly-decreasing-subarray/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; independently track strict increasing and decreasing runs."""
    increasing = decreasing = longest = 1
    for index in range(1, len(nums)):
        increasing = increasing + 1 if nums[index] > nums[index - 1] else 1
        decreasing = decreasing + 1 if nums[index] < nums[index - 1] else 1
        longest = max(longest, increasing, decreasing)
    return longest


class Solution:
    def longestMonotonicSubarray(self, nums: list[int]) -> int:
        return solve(nums)
