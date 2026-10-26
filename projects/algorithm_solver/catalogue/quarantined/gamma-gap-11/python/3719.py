"""3719. Longest Balanced Subarray I."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n^2) expected time and O(n) auxiliary space; parity counts distinct values, not occurrences."""
    answer = 0
    for left in range(len(nums)):
        seen = set()
        balance = 0
        for right in range(left, len(nums)):
            value = nums[right]
            if value not in seen:
                seen.add(value)
                balance += 1 if value % 2 == 0 else -1
            if balance == 0:
                answer = max(answer, right - left + 1)
    return answer


class Solution:
    def longestBalanced(self, nums: list[int]) -> int:
        return solve(nums)
