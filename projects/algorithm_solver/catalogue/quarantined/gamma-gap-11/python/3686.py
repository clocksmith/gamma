"""3686. Number of Stable Subsequences."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; count nonempty subsequences modulo 1e9+7."""
    modulus = 1_000_000_007
    single = [0, 0]
    double = [0, 0]
    for value in nums:
        parity = value % 2
        opposite = 1 - parity
        added_single = (1 + single[opposite] + double[opposite]) % modulus
        added_double = single[parity]
        single[parity] = (single[parity] + added_single) % modulus
        double[parity] = (double[parity] + added_double) % modulus
    return (sum(single) + sum(double)) % modulus


class Solution:
    def countStableSubsequences(self, nums: list[int]) -> int:
        return solve(nums)
