"""1955. Count Number of Special Subsequences."""


def solve(nums: list[int]) -> int:
    """Three stages for nonempty blocks of zeros, ones, and twos; O(n) time and O(1) space. Inputs are preserved."""
    modulus = 1_000_000_007
    ways = [0, 0, 0]
    for value in nums:
        previous = 1 if value == 0 else ways[value - 1]
        ways[value] = (2 * ways[value] + previous) % modulus
    return ways[2]


class Solution:
    def countSpecialSubsequences(self, nums: list[int]) -> int:
        return solve(nums)
