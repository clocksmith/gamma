"""152. Maximum Product Subarray (Medium).

Specification: https://leetcode.com/problems/maximum-product-subarray/description/
"""


def solve(nums: list[int]) -> int:
    best = nums[0]
    max_ending = nums[0]
    min_ending = nums[0]
    for i in range(1, len(nums)):
        value = nums[i]
        candidates = [value, max_ending * value, min_ending * value]
        max_ending = max(candidates)
        min_ending = min(candidates)
        best = max(best, max_ending)
    return best


class Solution:
    def maxProduct(self, nums: list[int]) -> int:
        return solve(nums)
