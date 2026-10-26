"""3761. Minimum Absolute Distance Between Mirror Pairs."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n log M) time and O(n) space; reversal is directional and lookup precedes insertion."""
    latest = {}
    answer = len(nums) + 1
    for index, value in enumerate(nums):
        if value in latest:
            answer = min(answer, index - latest[value])
        reversed_value = 0
        remaining = value
        while remaining:
            reversed_value = reversed_value * 10 + remaining % 10
            remaining //= 10
        latest[reversed_value] = index
    return -1 if answer > len(nums) else answer


class Solution:
    def minMirrorPairDistance(self, nums: list[int]) -> int:
        return solve(nums)
