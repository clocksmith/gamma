"""713. Subarray Product Less Than K (Medium).

Specification: https://leetcode.com/problems/subarray-product-less-than-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    if k <= 1:
        return 0
    product = 1
    left = 0
    count = 0
    for right, value in enumerate(nums):
        product *= value
        while product >= k:
            product //= nums[left]
            left += 1
        count += right - left + 1
    return count


class Solution:
    def numSubarrayProductLessThanK(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
