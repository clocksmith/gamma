"""3757. Number of Effective Subsequences."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n + B * 2^B) time and O(n + 2^B) space, B <= 20; subset zeta counts plus inclusion-exclusion."""
    modulus = 1_000_000_007
    full = 0
    for value in nums:
        full |= value
    width = full.bit_length()
    size = 1 << width
    subset_count = [0] * size
    for value in nums:
        subset_count[value] += 1
    for bit in range(width):
        step = 1 << bit
        for base in range(0, size, 2 * step):
            for offset in range(step):
                subset_count[base + step + offset] += subset_count[base + offset]
    powers = [1] * (len(nums) + 1)
    for index in range(len(nums)):
        powers[index + 1] = powers[index] * 2 % modulus
    exact_full = 0
    mask = full
    while True:
        term = powers[subset_count[mask]]
        exact_full += -term if (full ^ mask).bit_count() % 2 else term
        exact_full %= modulus
        if mask == 0:
            break
        mask = (mask - 1) & full
    return (powers[len(nums)] - exact_full) % modulus


class Solution:
    def countEffective(self, nums: list[int]) -> int:
        return solve(nums)
