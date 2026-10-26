"""3689. Maximum Total Subarray Value I."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(n) time and O(1) auxiliary space; repeated selection of the full interval is allowed."""
    return (max(nums) - min(nums)) * k


class Solution:
    def maxTotalValue(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
