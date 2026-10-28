"""477. Total Hamming Distance (Medium).

Specification: https://leetcode.com/problems/total-hamming-distance/description/
"""


def solve(nums: list[int]) -> int:
    total = 0
    for bit in range(32):
        ones = sum(1 for value in nums if (value >> bit) & 1)
        total += ones * (len(nums) - ones)
    return total


class Solution:
    def totalHammingDistance(self, nums: list[int]) -> int:
        return solve(nums)
