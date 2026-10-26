"""1822. Sign of the Product of an Array (Easy).

Specification: https://leetcode.com/problems/sign-of-the-product-of-an-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; do not form the potentially overflowing product; preserve nums."""
    sign = 1
    for value in nums:
        if value == 0:
            return 0
        if value < 0:
            sign = -sign
    return sign


class Solution:
    def arraySign(self, nums: list[int]) -> int:
        return solve(nums)
