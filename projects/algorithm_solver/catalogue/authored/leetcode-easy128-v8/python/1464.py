"""1464. Maximum Product of Two Elements in an Array (Easy).

Specification: https://leetcode.com/problems/maximum-product-of-two-elements-in-an-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; retain the two largest values at distinct indices."""
    largest = second = 0
    for value in nums:
        if value >= largest:
            second, largest = largest, value
        else:
            second = max(second, value)
    return (largest - 1) * (second - 1)


class Solution:
    def maxProduct(self, nums: list[int]) -> int:
        return solve(nums)
