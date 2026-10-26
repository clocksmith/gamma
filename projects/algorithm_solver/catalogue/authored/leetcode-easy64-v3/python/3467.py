"""3467. Transform Array by Parity (Easy).

Specification: https://leetcode.com/problems/transform-array-by-parity/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and output space; count even values and return a fresh sorted array."""
    evens = 0
    for value in nums:
        if value % 2 == 0:
            evens += 1
    result = [1] * len(nums)
    for index in range(evens):
        result[index] = 0
    return result


class Solution:
    def transformArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
