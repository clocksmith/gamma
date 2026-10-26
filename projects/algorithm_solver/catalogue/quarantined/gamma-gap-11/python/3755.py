"""3755. Find Maximum Balanced XOR Subarray Length."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) space; match both prefix XOR and parity-count balance."""
    earliest = {(0, 0): -1}
    combined = balance = answer = 0
    for index, value in enumerate(nums):
        combined ^= value
        balance += 1 if value % 2 == 0 else -1
        key = (combined, balance)
        if key in earliest:
            answer = max(answer, index - earliest[key])
        else:
            earliest[key] = index
    return answer


class Solution:
    def maxBalancedSubarray(self, nums: list[int]) -> int:
        return solve(nums)
