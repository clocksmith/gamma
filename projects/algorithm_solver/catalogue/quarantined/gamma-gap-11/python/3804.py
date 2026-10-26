"""3804. Number of Centered Subarrays."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n^2) expected time and O(n) auxiliary space; inputs are preserved."""
    answer = 0
    for left in range(len(nums)):
        total = 0
        values = set()
        for right in range(left, len(nums)):
            total += nums[right]
            values.add(nums[right])
            if total in values:
                answer += 1
    return answer


class Solution:
    def countCenteredSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
