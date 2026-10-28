"""1493. Longest Subarray of 1's After Deleting One Element (Medium).

Specification: https://leetcode.com/problems/longest-subarray-of-1s-after-deleting-one-element/description/
"""


def solve(nums: list[int]) -> int:
    left = 0
    zeros = 0
    best = 0
    for right, value in enumerate(nums):
        if value == 0:
            zeros += 1
        while zeros > 1:
            if nums[left] == 0:
                zeros -= 1
            left += 1
        best = max(best, right - left + 1)
    return best - 1


class Solution:
    def longestSubarray(self, nums: list[int]) -> int:
        return solve(nums)
