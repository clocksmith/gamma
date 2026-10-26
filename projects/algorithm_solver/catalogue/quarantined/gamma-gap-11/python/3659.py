"""3659. Partition Array Into K-Distinct Groups."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> bool:
    """O(n) expected time and O(n) auxiliary space; inputs are preserved."""
    if len(nums) % k != 0:
        return False
    limit = len(nums) // k
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
        if counts[value] > limit:
            return False
    return True


class Solution:
    def partitionArray(self, nums: list[int], k: int) -> bool:
        return solve(nums, k)
