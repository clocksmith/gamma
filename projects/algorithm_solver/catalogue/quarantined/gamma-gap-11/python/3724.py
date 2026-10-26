"""3724. Minimum Operations to Transform Array."""
from __future__ import annotations


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; copy once from the closest required adjustment interval."""
    target = nums2[-1]
    extra = float('inf')
    answer = 1
    for source, destination in zip(nums1, nums2):
        answer += abs(source - destination)
        low, high = min(source, destination), max(source, destination)
        extra = min(extra, max(low - target, target - high, 0))
    return answer + extra


class Solution:
    def minOperations(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
