"""3781. Maximum Score After Binary Swaps."""
from __future__ import annotations
from heapq import heappop, heappush


def solve(nums: list[int], s: str) -> int:
    """O(n log n) time and O(n) space; each original one supplies a prefix deadline for its selected position."""
    available = []
    answer = 0
    for value, bit in zip(nums, s):
        heappush(available, -value)
        if bit == '1':
            answer -= heappop(available)
    return answer


class Solution:
    def maximumScore(self, nums: list[int], s: str) -> int:
        return solve(nums, s)
