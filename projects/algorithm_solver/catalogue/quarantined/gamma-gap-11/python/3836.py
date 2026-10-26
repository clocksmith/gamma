"""3836. Maximum Score Using Exactly K Pairs."""
from __future__ import annotations


def solve(nums1: list[int], nums2: list[int], k: int) -> int:
    """O(n m k) time and O(m k) space; exact-count ordered-pair DP, including mandatory negative scores."""
    m = len(nums2)
    previous = [[float('-inf')] * (m + 1) for _ in range(k + 1)]
    previous[0] = [0] * (m + 1)
    for length, value in enumerate(nums1, 1):
        current = [row.copy() for row in previous]
        for index, other in enumerate(nums2, 1):
            for count in range(1, min(length, index, k) + 1):
                current[count][index] = max(previous[count][index], current[count][index - 1], previous[count - 1][index - 1] + value * other)
        previous = current
    return previous[k][m]


class Solution:
    def maxScore(self, nums1: list[int], nums2: list[int], k: int) -> int:
        return solve(nums1, nums2, k)
