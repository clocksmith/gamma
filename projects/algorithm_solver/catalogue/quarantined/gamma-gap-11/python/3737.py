"""3737. Count Subarrays With Majority Element I."""
from __future__ import annotations


def solve(nums: list[int], target: int) -> int:
    """O(n^2) time and O(1) auxiliary space for n <= 1000."""
    answer = 0
    for left in range(len(nums)):
        balance = 0
        for right in range(left, len(nums)):
            balance += 1 if nums[right] == target else -1
            if balance > 0:
                answer += 1
    return answer


class Solution:
    def countMajoritySubarrays(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
