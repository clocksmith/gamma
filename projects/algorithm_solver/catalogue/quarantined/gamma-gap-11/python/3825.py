"""3825. Longest Strictly Increasing Subsequence With Non-Zero Bitwise AND."""
from __future__ import annotations
from bisect import bisect_left


def solve(nums: list[int]) -> int:
    """O(B n log n) time and O(n) space, B=30; compute strict LIS separately for every possible common bit."""
    answer = 0
    for bit in range(30):
        tails = []
        mask = 1 << bit
        for value in nums:
            if value & mask:
                index = bisect_left(tails, value)
                if index == len(tails):
                    tails.append(value)
                else:
                    tails[index] = value
        answer = max(answer, len(tails))
    return answer


class Solution:
    def longestSubsequence(self, nums: list[int]) -> int:
        return solve(nums)
