"""1063. Number of Valid Subarrays (Medium).

Specification: https://leetcode.com/problems/number-of-valid-subarrays/description/
"""


def solve(nums: list[int]) -> int:
    stack = []
    total = 0
    for i in range(len(nums) - 1, -1, -1):
        while stack and nums[stack[-1]] >= nums[i]:
            stack.pop()
        next_smaller = len(nums) if not stack else stack[-1]
        total += next_smaller - i
        stack.append(i)
    return total


class Solution:
    def validSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
