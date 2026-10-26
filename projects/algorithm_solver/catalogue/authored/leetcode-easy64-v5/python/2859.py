"""2859. Sum of Values at Indices With K Set Bits (Easy).

Specification: https://leetcode.com/problems/sum-of-values-at-indices-with-k-set-bits/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n log(n + 1)) time, O(1) auxiliary space; indices are at most 999."""
    total = 0
    for index, value in enumerate(nums):
        remaining = index
        bits = 0
        while remaining:
            remaining &= remaining - 1
            bits += 1
        if bits == k:
            total += value
    return total


class Solution:
    def sumIndicesWithKSetBits(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
