"""918. Maximum Sum Circular Subarray (Medium).

Specification: https://leetcode.com/problems/maximum-sum-circular-subarray/description/
"""


def solve(nums: list[int]) -> int:
    total = sum(nums)
    max_ending = nums[0]
    max_so_far = nums[0]
    min_ending = nums[0]
    min_so_far = nums[0]
    for i in range(1, len(nums)):
        max_ending = max(nums[i], max_ending + nums[i])
        max_so_far = max(max_so_far, max_ending)
        min_ending = min(nums[i], min_ending + nums[i])
        min_so_far = min(min_so_far, min_ending)
    if max_so_far < 0:
        return max_so_far
    return max(max_so_far, total - min_so_far)


class Solution:
    def maxSubarraySumCircular(self, nums: list[int]) -> int:
        return solve(nums)
