"""1760. Minimum Limit of Balls in a Bag (Medium).

Specification: https://leetcode.com/problems/minimum-limit-of-balls-in-a-bag/description/
"""


import math


def _feasible(nums, max_operations, limit):
    operations = 0
    for value in nums:
        operations += math.ceil(value / limit) - 1
    return operations <= max_operations


def solve(nums: list[int], maxOperations: int) -> int:
    left, right = 1, max(nums)
    while left < right:
        mid = (left + right) // 2
        if _feasible(nums, maxOperations, mid):
            right = mid
        else:
            left = mid + 1
    return left


class Solution:
    def minimumSize(self, nums: list[int], maxOperations: int) -> int:
        return solve(nums, maxOperations)
