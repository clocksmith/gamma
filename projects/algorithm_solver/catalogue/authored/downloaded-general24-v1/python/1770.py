"""1770. Maximum Score from Performing Multiplication Operations (Medium).

Specification: https://leetcode.com/problems/maximum-score-from-performing-multiplication-operations/description/
"""


def solve(nums: list[int], multipliers: list[int]) -> int:
    n, m = len(nums), len(multipliers)
    memo = {}

    def best(operation, left):
        if operation == m:
            return 0
        key = (operation, left)
        if key in memo:
            return memo[key]
        right = n - 1 - (operation - left)
        take_left = nums[left] * multipliers[operation] + best(operation + 1, left + 1)
        take_right = nums[right] * multipliers[operation] + best(operation + 1, left)
        result = max(take_left, take_right)
        memo[key] = result
        return result

    return best(0, 0)


class Solution:
    def maximumScore(self, nums: list[int], multipliers: list[int]) -> int:
        return solve(nums, multipliers)
