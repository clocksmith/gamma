"""78. Subsets (Medium).

Specification: https://leetcode.com/problems/subsets/description/
"""


def solve(nums: list[int]) -> list[list[int]]:
    result = []

    def backtrack(start, current):
        result.append(current[:])
        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()

    backtrack(0, [])
    return result


class Solution:
    def subsets(self, nums: list[int]) -> list[list[int]]:
        return solve(nums)
