"""238. Product of Array Except Self (Medium).

Specification: https://leetcode.com/problems/product-of-array-except-self/description/
"""


def solve(nums: list[int]) -> list[int]:
    answer = [1] * len(nums)
    prefix = 1
    for i, value in enumerate(nums):
        answer[i] = prefix
        prefix *= value
    suffix = 1
    for i in range(len(nums) - 1, -1, -1):
        answer[i] *= suffix
        suffix *= nums[i]
    return answer


class Solution:
    def productExceptSelf(self, nums: list[int]) -> list[int]:
        return solve(nums)
