"""1. Two Sum (Easy).

Specification: https://leetcode.com/problems/two-sum/description/
"""


def solve(nums: list[int], target: int) -> list[int]:
    index_by_value = {}
    for index, value in enumerate(nums):
        needed = target - value
        if needed in index_by_value:
            return [index_by_value[needed], index]
        index_by_value[value] = index
    return []


class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        return solve(nums, target)
