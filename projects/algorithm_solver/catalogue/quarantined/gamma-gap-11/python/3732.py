"""3732. Maximum Product of Three Elements After One Replacement."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; replace a third index using the sign that makes the product nonnegative."""
    largest = second = 0
    for value in nums:
        value = abs(value)
        if value >= largest:
            second, largest = largest, value
        elif value > second:
            second = value
    return largest * second * 100_000


class Solution:
    def maxProduct(self, nums: list[int]) -> int:
        return solve(nums)
