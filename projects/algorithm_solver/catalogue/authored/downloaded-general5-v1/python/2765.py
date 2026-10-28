"""2765. Longest Alternating Subarray (Easy).

Specification: https://leetcode.com/problems/longest-alternating-subarray/description/
"""


def solve(nums: list[int]) -> int:
    best = -1
    for i in range(len(nums)):
        expected = 1
        j = i
        while j + 1 < len(nums) and nums[j + 1] - nums[j] == expected:
            j += 1
            expected *= -1
        if j - i + 1 > 1:
            best = max(best, j - i + 1)
    return best


class Solution:
    def alternatingSubarray(self, nums: list[int]) -> int:
        return solve(nums)
