"""376. Wiggle Subsequence (Medium).

Specification: https://leetcode.com/problems/wiggle-subsequence/description/
"""


def solve(nums: list[int]) -> int:
    if len(nums) < 2:
        return len(nums)
    up = 1
    down = 1
    for i in range(1, len(nums)):
        if nums[i] > nums[i - 1]:
            up = down + 1
        elif nums[i] < nums[i - 1]:
            down = up + 1
    return max(up, down)


class Solution:
    def wiggleMaxLength(self, nums: list[int]) -> int:
        return solve(nums)
