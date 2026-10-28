"""1685. Sum of Absolute Differences in a Sorted Array (Medium).

Specification: https://leetcode.com/problems/sum-of-absolute-differences-in-a-sorted-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    total = sum(nums)
    prefix = 0
    result = []
    for i, value in enumerate(nums):
        left = i * value - prefix
        right = (total - prefix - value) - (len(nums) - 1 - i) * value
        result.append(left + right)
        prefix += value
    return result


class Solution:
    def getSumAbsoluteDifferences(self, nums: list[int]) -> list[int]:
        return solve(nums)
