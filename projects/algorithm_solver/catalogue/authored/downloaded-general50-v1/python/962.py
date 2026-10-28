"""962. Maximum Width Ramp (Medium).

Specification: https://leetcode.com/problems/maximum-width-ramp/description/
"""


def solve(nums: list[int]) -> int:
    stack = []
    for i, v in enumerate(nums):
        if not stack or nums[stack[-1]] > v:
            stack.append(i)
    best = 0
    for j in range(len(nums) - 1, -1, -1):
        while stack and nums[stack[-1]] <= nums[j]:
            best = max(best, j - stack.pop())
    return best


class Solution:
    def maxWidthRamp(self, nums: list[int]) -> int:
        return solve(nums)
