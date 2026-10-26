"""3785. Minimum Swaps to Avoid Forbidden Values."""
from __future__ import annotations
from collections import Counter


def solve(nums: list[int], forbidden: list[int]) -> int:
    """O(n) expected time and O(n) space; feasibility is checked before the dominant-conflict bound."""
    n = len(nums)
    combined = Counter(nums)
    combined.update(forbidden)
    if any(count > n for count in combined.values()):
        return -1
    bad = Counter(value for value, excluded in zip(nums, forbidden) if value == excluded)
    total = sum(bad.values())
    return max((total + 1) // 2, max(bad.values(), default=0))


class Solution:
    def minSwaps(self, nums: list[int], forbidden: list[int]) -> int:
        return solve(nums, forbidden)
