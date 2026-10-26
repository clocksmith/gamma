"""3806. Maximum Bitwise AND After Increment Operations."""
from __future__ import annotations


def solve(nums: list[int], k: int, m: int) -> int:
    """O(B n log n) time and O(n) space, B <= 31; exact bounded integers and read-only inputs."""
    answer = 0
    for bit in range((max(nums) + k).bit_length() - 1, -1, -1):
        candidate = answer | (1 << bit)
        costs = []
        for value in nums:
            missing = candidate & ~value
            if missing == 0:
                costs.append(0)
            else:
                pivot = 1 << (missing.bit_length() - 1)
                raised = value - value % (2 * pivot) + pivot + candidate % pivot
                costs.append(raised - value)
        costs.sort()
        if sum(costs[:m]) <= k:
            answer = candidate
    return answer


class Solution:
    def maximumAND(self, nums: list[int], k: int, m: int) -> int:
        return solve(nums, k, m)
