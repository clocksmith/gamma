"""674. Longest Continuous Increasing Subsequence (Easy).

Specification: https://leetcode.com/problems/longest-continuous-increasing-subsequence/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; reset the current run whenever strict increase ends."""
    longest = current = 0
    for index, value in enumerate(nums):
        current = current + 1 if index > 0 and value > nums[index - 1] else 1
        longest = max(longest, current)
    return longest


class Solution:
    def findLengthOfLCIS(self, nums: list[int]) -> int:
        return solve(nums)
