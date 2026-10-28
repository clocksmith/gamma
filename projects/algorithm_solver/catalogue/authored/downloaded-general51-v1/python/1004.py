"""1004. Max Consecutive Ones III (Medium).

Specification: https://leetcode.com/problems/max-consecutive-ones-iii/description/
"""


def solve(nums: list[int], k: int) -> int:
    left = 0
    zeros = 0
    best = 0
    for right, value in enumerate(nums):
        if value == 0:
            zeros += 1
        while zeros > k:
            if nums[left] == 0:
                zeros -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def longestOnes(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
