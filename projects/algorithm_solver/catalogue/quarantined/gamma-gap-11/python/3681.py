"""3681. Maximum XOR of Subsequences."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(30n) time and O(30) auxiliary space; inputs are preserved."""
    basis = [0] * 30
    for value in nums:
        current = value
        for bit in range(29, -1, -1):
            if current & (1 << bit):
                if basis[bit]:
                    current ^= basis[bit]
                else:
                    basis[bit] = current
                    break
    answer = 0
    for bit in range(29, -1, -1):
        answer = max(answer, answer ^ basis[bit])
    return answer


class Solution:
    def maxXorSubsequences(self, nums: list[int]) -> int:
        return solve(nums)
