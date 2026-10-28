"""1060. Missing Element in Sorted Array (Medium).

Specification: https://leetcode.com/problems/missing-element-in-sorted-array/description/
"""


def solve(nums: list[int], k: int) -> int:
    for i in range(len(nums) - 1):
        missing = nums[i + 1] - nums[i] - 1
        if k <= missing:
            return nums[i] + k
        k -= missing
    return nums[-1] + k


class Solution:
    def missingElement(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
