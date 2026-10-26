"""3876. Construct Uniform Parity Array II."""
from __future__ import annotations


def solve(nums1: list[int]) -> bool:
    """O(n) time and O(1) space; the minimum cannot change parity, and an odd minimum can convert every larger even value."""
    return min(nums1) % 2 == 1 or all(value % 2 == 0 for value in nums1)


class Solution:
    def uniformArray(self, nums1: list[int]) -> bool:
        return solve(nums1)
