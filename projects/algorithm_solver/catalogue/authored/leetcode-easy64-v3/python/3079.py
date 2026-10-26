"""3079. Find the Sum of Encrypted Integers (Easy).

Specification: https://leetcode.com/problems/find-the-sum-of-encrypted-integers/description/
"""


def solve(nums: list[int]) -> int:
    """O(n log M) time, O(1) space; repeat each number's maximum digit arithmetically."""
    total = 0
    for value in nums:
        remaining = value
        maximum = 0
        ones = 0
        while remaining > 0:
            maximum = max(maximum, remaining % 10)
            ones = ones * 10 + 1
            remaining //= 10
        total += maximum * ones
    return total


class Solution:
    def sumOfEncryptedInt(self, nums: list[int]) -> int:
        return solve(nums)
