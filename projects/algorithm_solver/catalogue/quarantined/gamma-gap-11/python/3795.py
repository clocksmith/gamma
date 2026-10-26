"""3795. Minimum Subarray Length With Distinct Sum At Least K."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time and O(n) space; positive distinct values permit a monotone sliding window."""
    counts = {}
    total = 0
    left = 0
    answer = len(nums) + 1
    for right, value in enumerate(nums):
        if counts.get(value, 0) == 0:
            total += value
        counts[value] = counts.get(value, 0) + 1
        while total >= k:
            answer = min(answer, right - left + 1)
            removed = nums[left]
            counts[removed] -= 1
            if counts[removed] == 0:
                total -= removed
                del counts[removed]
            left += 1
    return -1 if answer > len(nums) else answer


class Solution:
    def minimumSubarrayLength(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
