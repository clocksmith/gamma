"""2367. Number of Arithmetic Triplets (Easy).

Specification: https://leetcode.com/problems/number-of-arithmetic-triplets/description/
"""


def solve(nums: list[int], diff: int) -> int:
    """O(n) expected time, O(n) space; strict increasing order makes value membership sufficient."""
    values = set(nums)
    total = 0
    for value in nums:
        if value + diff in values and value + 2 * diff in values:
            total += 1
    return total


class Solution:
    def arithmeticTriplets(self, nums: list[int], diff: int) -> int:
        return solve(nums, diff)
