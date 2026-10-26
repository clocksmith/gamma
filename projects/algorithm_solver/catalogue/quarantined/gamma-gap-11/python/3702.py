"""3702. Longest Subsequence With Non-Zero Bitwise XOR."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; values fit the stated nonnegative 30-bit domain."""
    combined = 0
    nonzero = False
    for value in nums:
        combined ^= value
        nonzero = nonzero or value != 0
    if combined:
        return len(nums)
    return len(nums) - 1 if nonzero else 0


class Solution:
    def longestSubsequence(self, nums: list[int]) -> int:
        return solve(nums)
