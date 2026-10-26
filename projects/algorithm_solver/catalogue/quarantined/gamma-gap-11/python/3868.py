"""3868. Minimum Cost to Equalize Arrays Using Swaps."""
from __future__ import annotations
from collections import Counter


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n) expected time and O(n) space; free reordering reduces the problem to even multiplicities and surplus transfers."""
    difference = Counter(nums1)
    difference.subtract(nums2)
    if any(count % 2 for count in difference.values()):
        return -1
    return sum(count // 2 for count in difference.values() if count > 0)


class Solution:
    def minCost(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
