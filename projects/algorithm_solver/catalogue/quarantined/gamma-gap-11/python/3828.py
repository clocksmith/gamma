"""3828. Final Element After Subarray Deletions."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(1) time and space; Alice can retain either endpoint, and Bob can retain an original endpoint after any nonfinal move."""
    return max(nums[0], nums[-1])


class Solution:
    def finalElement(self, nums: list[int]) -> int:
        return solve(nums)
