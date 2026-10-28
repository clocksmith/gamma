"""795. Number of Subarrays with Bounded Maximum (Medium).

Specification: https://leetcode.com/problems/number-of-subarrays-with-bounded-maximum/description/
"""


def _count_at_most(nums, bound):
    total = 0
    current = 0
    for value in nums:
        if value <= bound:
            current += 1
            total += current
        else:
            current = 0
    return total


def solve(nums: list[int], left: int, right: int) -> int:
    return _count_at_most(nums, right) - _count_at_most(nums, left - 1)


class Solution:
    def numSubarrayBoundedMax(self, nums: list[int], left: int, right: int) -> int:
        return solve(nums, left, right)
